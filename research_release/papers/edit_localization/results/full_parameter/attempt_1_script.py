#!/usr/bin/env python3
"""Full default-trainable-parameter gradient scope check on public post-edits."""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import time

import numpy as np
import torch
import torch.nn.functional as F
from transformers import MarianMTModel, MarianTokenizer

RELEASE=Path(__file__).resolve().parents[1]
OUT=RELEASE/'papers/edit_localization/results/full_parameter'
FIG=RELEASE/'papers/edit_localization/figures'
CACHE=Path(os.environ.get('PUBLIC_POSTEDIT_CACHE',str(RELEASE/'.cache/public_postedit')))


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def write_json(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n')


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def load_helpers():
    spec=importlib.util.spec_from_file_location('postedit_helpers',RELEASE/'experiments/public_postedit.py')
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.OUT=OUT
    m.CACHE=CACHE
    assert m.MODEL=='Helsinki-NLP/opus-mt-en-de'
    return m


def padded_batch(records,pad,device):
    batch=len(records)
    source=torch.full((batch,max(len(r['source_ids']) for r in records)),pad,dtype=torch.long,device=device)
    target=torch.full((batch,max(len(r['pe_ids']) for r in records)),-100,dtype=torch.long,device=device)
    attention=torch.zeros_like(source)
    mask=torch.zeros_like(target,dtype=torch.float32)
    length=torch.tensor([len(r['pe_ids']) for r in records],dtype=torch.float32,device=device)
    for i,record in enumerate(records):
        s,t=len(record['source_ids']),len(record['pe_ids'])
        source[i,:s]=torch.tensor(record['source_ids'],device=device)
        attention[i,:s]=1
        target[i,:t]=torch.tensor(record['pe_ids'],device=device)
        mask[i,:t]=torch.tensor(record['mask'],device=device,dtype=torch.float32)
    return source,attention,target,mask,length


def curves_from_gram(gram):
    rows,coefficients=[],[]
    unit=np.eye(8)
    for m,name in enumerate(['edit','length','edit_length']):
        pe,pu=unit[0],unit[1]
        qe,qu=unit[2+2*m],unit[3+2*m]
        delta,epsilon=qe-pe,qu-pu
        dot=lambda a,b:float(a@gram@b)
        a,b,c=dot(delta,delta),dot(delta,epsilon),dot(epsilon,epsilon)
        d,e,f=dot(qe,qe),dot(qe,qu),dot(qu,qu)
        coefficients.append(dict(mechanism=name,a=a,b=b,c=c,d=d,e=e,f=f,
             edited_bias_norm=float(np.sqrt(max(a,0))),untouched_bias_norm=float(np.sqrt(max(c,0))),
             q_mean_inner_product=e))
        def squared_ratio(alpha):
            return (a+2*b*alpha+c*alpha*alpha)/(d+2*e*alpha+f*alpha*alpha)
        for alpha in np.linspace(0,1,21):
            bias2=dot(delta+alpha*epsilon,delta+alpha*epsilon)
            qnorm2=dot(qe+alpha*qu,qe+alpha*qu)
            pnorm2=dot(pe+alpha*pu,pe+alpha*pu)
            poly=(b*d-a*e)+(c*d-a*f)*alpha+(c*e-b*f)*alpha**2
            deriv=2*poly/qnorm2**2
            h=1e-5
            numerical=(squared_ratio(alpha+h)-squared_ratio(alpha-h))/(2*h)
            if not np.isclose(deriv,numerical,rtol=1e-5,atol=1e-7):
                raise AssertionError((name,alpha,deriv,numerical))
            rows.append(dict(mechanism=name,alpha=float(alpha),
                 absolute_bias=float(np.sqrt(max(bias2,0))),
                 q_mean_norm=float(np.sqrt(qnorm2)),p_mean_norm=float(np.sqrt(pnorm2)),
                 rho_Q=float(np.sqrt(max(bias2,0)/qnorm2)),
                 rho_P=float(np.sqrt(max(bias2,0)/pnorm2)),
                 squared_rho_Q_derivative=float(deriv)))
    return rows,coefficients


def plot(rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(8.8,3.1))
    for name,color in zip(['edit','length','edit_length'],['#3a7b98','#bd7344','#7470a1']):
        selected=[r for r in rows if r['mechanism']==name]
        for ax,key in zip(axes,['rho_Q','absolute_bias']):
            ax.plot([r['alpha'] for r in selected],[r[key] for r in selected],label=name,color=color,lw=2)
            ax.set_xlabel('Untouched retention alpha');ax.grid(alpha=.2)
    axes[0].set_ylabel('Relative selection bias (Q denominator)')
    axes[1].set_ylabel('Absolute full-parameter gradient bias')
    axes[0].legend(fontsize=8)
    fig.suptitle('Frozen full-model gradients: 256 public English-German post-edits',fontsize=10)
    fig.tight_layout()
    for ext in ['pdf','png']:
        fig.savefig(FIG/f'full_parameter_geometry.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--device',choices=['cpu','mps'],default=None)
    parser.add_argument('--reuse-gram',action='store_true')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
    if args.reuse_gram:
        gram=np.load(OUT/'gram.npy')
        rows,coeff=curves_from_gram(gram)
        write_csv(OUT/'curves.csv',rows);write_csv(OUT/'coefficients.csv',coeff);plot(rows)
        return
    start=time.perf_counter()
    torch.set_num_threads(4);torch.manual_seed(917);np.random.seed(917)
    device=args.device or ('mps' if torch.backends.mps.is_available() else 'cpu')
    helper=load_helpers()
    snapshot,columns,assets=helper.load_assets()
    tokenizer=MarianTokenizer.from_pretrained(snapshot,local_files_only=True)
    selected,pop=helper.population(columns,tokenizer)
    records=selected[256:]
    model=MarianMTModel.from_pretrained(snapshot,local_files_only=True).to(device).eval()
    named=[(name,param) for name,param in model.named_parameters() if param.requires_grad]
    params=tuple(p for _,p in named)
    count=sum(p.numel() for p in params)
    names=['P_E','P_U','Qedit_E','Qedit_U','Qlength_E','Qlength_U','Qedit_length_E','Qedit_length_U']
    probability=[np.full(len(records),1/len(records))]
    probability += [helper.propensity(records,name) for name in ['edit','length','edit_length']]
    probability=[p/p.sum() for p in probability]
    weights=np.repeat(np.stack(probability),2,axis=0)
    cache=CACHE/'full_parameter';cache.mkdir(parents=True,exist_ok=True)
    bankpath=cache/'mean_gradients.float64'
    bank=np.memmap(bankpath,mode='w+',dtype=np.float64,shape=(8,count))
    bank[:]=0.
    protocol=RELEASE/'docs/full_parameter_postedit_protocol.md'
    manifest=dict(completed=False,scope='Full default trainable parameter mean gradients; no optimizer update',
        sample_count=len(records),split='same en-de reporting population',device=device,
        trainable_parameter_count=count,model_parameter_count=sum(p.numel() for p in model.parameters()),
        named_parameters=[dict(name=name,shape=list(p.shape),count=p.numel()) for name,p in named],
        parameter_forms=names,source_ids=[r['line'] for r in records],
        versions=dict(python=platform.python_version(),torch=torch.__version__,numpy=np.__version__),
        script_sha256=sha(__file__),helper_script_sha256=sha(RELEASE/'experiments/public_postedit.py'),
        protocol_sha256=sha(protocol),assets=assets,
        accumulation='float32 autograd; CPU float64 mean accumulation; blockwise float64 Gram',
        run_started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    write_json(OUT/'manifest_in_progress.json',manifest)
    (OUT/'executed_script.py').write_bytes(Path(__file__).read_bytes())
    print(f'Full gradients: {count:,} trainable parameters, {len(records)} records, {device}',flush=True)
    lossrecords=[]
    for left in range(0,len(records),4):
        batch=records[left:left+4]
        source,attention,target,mask,length=padded_batch(batch,tokenizer.pad_token_id,device)
        logits=model(input_ids=source,attention_mask=attention,labels=target,use_cache=False).logits
        tokenloss=F.cross_entropy(logits.reshape(-1,logits.shape[-1]),target.reshape(-1),
                                  ignore_index=-100,reduction='none').reshape(target.shape)
        lossE=(tokenloss*mask).sum(1)/length
        lossU=(tokenloss*(1-mask)).sum(1)/length
        total=tokenloss.sum(1)/length
        if not torch.allclose(lossE+lossU,total,atol=2e-6,rtol=1e-6):
            raise AssertionError('Loss decomposition failed')
        for i,r in enumerate(batch):
            lossrecords.append(dict(line=r['line'],edited_loss=float(lossE[i].detach().cpu()),
                                   untouched_loss=float(lossU[i].detach().cpu()),
                                   full_loss=float(total[i].detach().cpu())))
        for j in range(8):
            ww=torch.tensor(weights[j,left:left+len(batch)],dtype=lossE.dtype,device=device)
            objective=((lossE if j%2==0 else lossU)*ww).sum()
            gradients=torch.autograd.grad(objective,params,retain_graph=j<7)
            offset=0
            for grad in gradients:
                size=grad.numel()
                bank[j,offset:offset+size] += grad.detach().cpu().numpy().reshape(-1)
                offset += size
            del gradients
        del logits,tokenloss,lossE,lossU,total
        if (left+len(batch))%32==0:
            bank.flush()
            print(f'Full gradients {left+len(batch)}/{len(records)}; elapsed={time.perf_counter()-start:.1f}s',flush=True)
    bank.flush()
    gram=np.zeros((8,8),np.float64)
    for offset in range(0,count,1_000_000):
        block=np.asarray(bank[:,offset:offset+1_000_000])
        gram += block@block.T
    np.save(OUT/'gram.npy',gram)
    write_csv(OUT/'per_sentence_losses.csv',lossrecords)
    rows,coeff=curves_from_gram(gram)
    write_csv(OUT/'curves.csv',rows);write_csv(OUT/'coefficients.csv',coeff);plot(rows)
    eig=np.linalg.eigvalsh(gram)
    manifest.update(completed=True,runtime_seconds=time.perf_counter()-start,
        gram_symmetry_max_abs=float(np.max(np.abs(gram-gram.T))),
        gram_min_eigenvalue=float(eig.min()),mean_gradient_bank_sha256=sha(bankpath),
        mean_gradient_bank_bytes=bankpath.stat().st_size,
        endpoints=[r for r in rows if r['alpha'] in [0.,1.]],
        outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and 'manifest' not in p.name})
    write_json(OUT/'manifest.json',manifest)
    print(json.dumps(dict(completed=True,seconds=manifest['runtime_seconds'],endpoints=manifest['endpoints']),indent=2),flush=True)


if __name__=='__main__':
    main()
