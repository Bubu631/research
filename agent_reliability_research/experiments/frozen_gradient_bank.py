"""Frozen Qwen scores for a 32-dimensional output-logit bias.

Float16 frozen logits are cast to float32 before adding B @ eta. These are not
native/full-parameter gradients. No optimization, new rollout or test execution.
"""
import argparse, hashlib, json, os, shutil, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1]
MODEL_ID='Qwen/Qwen2.5-Coder-1.5B-Instruct'
REVISION='2e1fd397ee46e1388853d2af2c993145b0f1098a'
# Official Hugging Face revision API, verified 2026-09-12.
WEIGHT_SHA='c1b9b30e907950516ba3c646bdf570d8084c25a6410a0cdca80cf04b11bc13a8'
WEIGHT_BYTES=3087467144
GIT_BLOBS={'config.json':'b4831594221a81ea1540f0c6aeae93b6a8aeae56',
           'tokenizer.json':'443909a61d429dff23010e5bddd28ff530edda00',
           'tokenizer_config.json':'acee076f49bf3c0298e15de0909d1da7b392f0c3'}
DIM,SEED=32,20260915


def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def model_fingerprint(directory):
    directory=Path(directory);files={}
    if (directory/'model.safetensors').stat().st_size!=WEIGHT_BYTES:
        raise ValueError('Wrong pinned checkpoint size.')
    for name in ('config.json','model.safetensors','tokenizer.json','tokenizer_config.json',
                 'merges.txt','vocab.json','generation_config.json'):
        path=directory/name
        files[name]={'bytes':path.stat().st_size,'sha256':file_hash(path)}
        if name in GIT_BLOBS:
            raw=path.read_bytes()
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if blob!=GIT_BLOBS[name]:raise ValueError('Pinned revision mismatch: '+name)
            files[name]['verified_git_blob']=blob
    if files['model.safetensors']['sha256']!=WEIGHT_SHA:
        raise ValueError('Pinned model weight SHA256 mismatch.')
    return {'model_id':MODEL_ID,'revision':REVISION,'files':files,
            'official_revision_api':f'https://huggingface.co/api/models/{MODEL_ID}/revision/{REVISION}?blobs=true'}


def validate_tokens(ids,attention,score,records,vocab):
    if ids.ndim!=2 or ids.shape!=attention.shape or ids.shape!=score.shape:
        raise ValueError('IDs, attention and score masks need matching 2D shapes.')
    if records.ndim!=1 or len(records)!=len(ids) or not len(records):
        raise ValueError('Need one record ID per nonempty token row.')
    if len(np.unique(records))!=len(records):raise ValueError('Duplicate record IDs.')
    if not np.issubdtype(ids.dtype,np.integer) or np.any(ids<0) or np.any(ids>=vocab):
        raise ValueError('Invalid token IDs.')
    for name,mask in [('attention',attention),('score',score)]:
        if not (np.issubdtype(mask.dtype,np.integer) or mask.dtype==np.bool_):
            raise ValueError(name+' mask must be integer or Boolean.')
        if np.any((mask!=0)&(mask!=1)):raise ValueError(name+' mask must be binary.')
    lengths=attention.sum(axis=1).astype(np.int64)
    prefix=np.arange(ids.shape[1])[None,:]<lengths[:,None]
    if not np.array_equal(attention.astype(bool),prefix):
        raise ValueError('Attention must be contiguous prefix with right padding.')
    if np.any(score.astype(bool)&~prefix):raise ValueError('Scored padding position.')
    if np.any(score[:,0]) or np.any(score.sum(axis=1)==0):
        raise ValueError('Need scored targets, all at positions >=1.')
    return lengths


def make_basis(vocab,dimension=DIM,seed=SEED):
    signed=np.random.default_rng(seed).integers(0,2,(vocab,dimension),dtype=np.int8)*2-1
    return (signed.astype(np.float64)/np.sqrt(dimension)).astype(np.float32)


def projected_logit_score(logits,targets,basis):
    """Sum analytic bias scores and NLL; preserve dtype for CPU verification."""
    if logits.ndim!=2 or basis.ndim!=2 or logits.shape[1]!=basis.shape[0]:
        raise ValueError('Logit/basis shape mismatch.')
    if not torch.isfinite(logits).all():raise ValueError('Nonfinite frozen logits.')
    probs=torch.softmax(logits,dim=-1)
    score=(basis[targets]-probs@basis).sum(dim=0)
    nll=(torch.logsumexp(logits,dim=-1)-logits.gather(1,targets[:,None])[:,0]).sum()
    return score,nll


def atomic_npz(path,**arrays):
    path=Path(path);tmp=path.with_name(path.name+f'.tmp-{os.getpid()}')
    try:
        with tmp.open('wb') as f:
            np.savez_compressed(f,**arrays);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()


def atomic_json(path,value):
    path=Path(path);tmp=path.with_name(path.name+f'.tmp-{os.getpid()}')
    try:
        with tmp.open('w') as f:
            json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()


def read_partial(path,fingerprint,records,n):
    with np.load(path,allow_pickle=False) as prev:
        if 'fingerprint_json' not in prev.files:raise ValueError('Legacy cache has no provenance; use --fresh.')
        old=json.loads(str(prev['fingerprint_json'].item()))
        if old!=fingerprint:
            changed=sorted(k for k in old.keys()|fingerprint.keys() if old.get(k)!=fingerprint.get(k))
            raise ValueError('Resume fingerprint mismatch: '+', '.join(changed))
        done=len(prev['record_ids'])
        if not 0<=done<=n or not np.array_equal(prev['record_ids'],records[:done]):
            raise ValueError('Resume count/record order mismatch.')
        arrays={k:prev[k].copy() for k in ('gradients','nll','scored_tokens','seconds')}
        if arrays['gradients'].shape!=(done,DIM):raise ValueError('Bad cached gradient shape.')
        if any(arrays[k].shape!=(done,) for k in ('nll','scored_tokens','seconds')):
            raise ValueError('Bad cached scalar-array shape.')
        if any(not np.isfinite(v).all() for v in arrays.values()):
            raise ValueError('Nonfinite cache.')
        if np.any(arrays['scored_tokens']<=0) or np.any(arrays['seconds']<0):
            raise ValueError('Invalid cached count or timing.')
    return done,arrays


def main(a):
    import transformers
    from transformers import AutoModelForCausalLM
    t=time.perf_counter();torch.set_num_threads(4)
    if a.limit is not None and a.limit<=0:raise ValueError('--limit must be positive.')
    output=Path(a.output) if a.output else ROOT/'results/frozen_model'
    output.mkdir(parents=True,exist_ok=True)
    token_hash=file_hash(a.tokens)
    with np.load(a.tokens,allow_pickle=False) as data:
        ids,attention,score,records=(data[k].copy() for k in
                                   ('input_ids','attention_mask','score_mask','record_ids'))
    source=model_fingerprint(a.model)  # Each weight file hashed once per invocation.
    config=json.loads((Path(a.model)/'config.json').read_text())
    if config.get('model_type')!='qwen2':raise ValueError('Only the pinned Qwen2 extraction is audited.')
    vocab=int(config['vocab_size']);lengths=validate_tokens(ids,attention,score,records,vocab)
    if lengths.max()>int(config['max_position_embeddings']):raise ValueError('Context limit exceeded.')
    n=len(records) if a.limit is None else min(a.limit,len(records))
    basis=make_basis(vocab);basis_hash=hashlib.sha256(basis.tobytes(order='C')).hexdigest()
    scope='full' if a.limit is None else 'smoke'
    fp=dict(schema_version=2,token_artifact_sha256=token_hash,model_source=source,
            script_sha256=file_hash(__file__),requested_records=n,scope=scope,device=a.device,
            model_dtype='float16',score_dtype='float32',export_dtype='float64',dimension=DIM,
            basis_seed=SEED,basis_sha256=basis_hash,python=sys.version,torch=torch.__version__,
            numpy=np.__version__,transformers=transformers.__version__,
            score_definition='mean masked target log-prob derivative for float32 bias after float16 frozen logits',
            shift='hidden[target_position-1]; right padding removed; no scored position0')
    fp_json=json.dumps(fp,sort_keys=True,separators=(',',':'))
    cache=output/f'gradient_bank.{scope}.partial.npz'
    final=output/('gradient_bank.npz' if scope=='full' else 'smoke_gradient_bank.npz')
    manifest_path=output/('manifest.json' if scope=='full' else 'smoke_manifest.json')
    if a.fresh:
        existing=[p for p in (cache,final,manifest_path) if p.exists()]
        if existing:
            archive=output/'previous_runs'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            archive.mkdir(parents=True)
            for p in existing:shutil.move(str(p),str(archive/p.name))
    gradients=np.zeros((n,DIM));nll=np.zeros(n);tokens=np.zeros(n,dtype=np.int64);seconds=np.zeros(n)
    done=0
    if cache.exists():
        done,prev=read_partial(cache,fp,records,n)
        gradients[:done]=prev['gradients'];nll[:done]=prev['nll']
        tokens[:done]=prev['scored_tokens'];seconds[:done]=prev['seconds']
        if not np.array_equal(tokens[:done],score[:done].sum(axis=1)):
            raise ValueError('Cached target counts differ from mask.')
    elif final.exists():
        raise ValueError('Completed output without matching cache; choose new --output or --fresh.')
    source_dir=output/'executed_source'/hashlib.sha256(fp_json.encode()).hexdigest()[:16]
    source_dir.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(__file__,source_dir/Path(__file__).name);atomic_json(source_dir/'fingerprint.json',fp)
    model=AutoModelForCausalLM.from_pretrained(a.model,dtype=torch.float16,local_files_only=True,
                                             attn_implementation='sdpa').eval().to(a.device)
    for p in model.parameters():p.requires_grad_(False)
    if model.lm_head.weight.shape[0]!=vocab:raise ValueError('Output head vocabulary mismatch.')
    b=torch.from_numpy(basis).to(a.device,dtype=torch.float32)
    print('model loaded; records',n,'resume',done,'seconds',time.perf_counter()-t,flush=True)
    with torch.inference_mode():
        for j in range(done,n):
            if a.device=='mps':torch.mps.synchronize()
            ts=time.perf_counter();length=int(lengths[j]);idx=np.flatnonzero(score[j,:length])
            x=torch.from_numpy(ids[j,:length].astype(np.int64)).to(a.device)[None]
            hidden=model.model(input_ids=x,attention_mask=torch.ones_like(x),use_cache=False).last_hidden_state[0]
            accum=torch.zeros(DIM,device=a.device,dtype=torch.float32)
            loss=torch.zeros((),device=a.device,dtype=torch.float32)
            for start in range(0,len(idx),32):
                positions=torch.from_numpy(idx[start:start+32].astype(np.int64)).to(a.device)
                logits=model.lm_head(hidden[positions-1]).float()
                inc,loss_inc=projected_logit_score(logits,x[0,positions],b)
                accum+=inc;loss+=loss_inc
                del logits,inc,loss_inc
            gradients[j]=accum.cpu().numpy()/len(idx);nll[j]=loss.item()/len(idx);tokens[j]=len(idx)
            if not np.isfinite(gradients[j]).all() or not np.isfinite(nll[j]):
                raise ValueError('Nonfinite result; no checkpoint written.')
            if a.device=='mps':torch.mps.synchronize()
            seconds[j]=time.perf_counter()-ts;del hidden,x
            atomic_npz(cache,record_ids=records[:j+1],gradients=gradients[:j+1],nll=nll[:j+1],
                       scored_tokens=tokens[:j+1],seconds=seconds[:j+1],fingerprint_json=np.asarray(fp_json))
            print(j+1,'/',n,'tokens',length,'scored',len(idx),'seconds',round(seconds[j],2),flush=True)
    if file_hash(a.tokens)!=token_hash:raise ValueError('Token artifact changed during execution.')
    atomic_npz(final,record_ids=records[:n],gradients=gradients,nll=nll,scored_tokens=tokens,seconds=seconds,
               basis_seed=SEED,basis_dim=DIM,basis_sha256=np.asarray(basis_hash),fingerprint_json=np.asarray(fp_json))
    meta=dict(status='complete',records=n,resumed_records=done,model=MODEL_ID,revision=REVISION,
              model_path=str(Path(a.model).resolve()),fingerprint=fp,
              parameterization='float32 logits_eta=float32(frozen float16 logits)+B@eta; eta=0; B Rademacher/sqrt(32)',
              target='mean target-token log-prob score; fixed empirical historical surrogate; no behavior-policy correction',
              dimension=DIM,device=a.device,model_dtype='float16',score_accumulation_dtype='float32',
              numpy_export_dtype='float64 (does not add precision)',torch=torch.__version__,numpy=np.__version__,
              transformers=transformers.__version__,this_invocation_elapsed_seconds=time.perf_counter()-t,
              recorded_forward_score_seconds=float(seconds.sum()),token_artifact_sha256=token_hash,
              script_sha256=fp['script_sha256'],output_sha256=file_hash(final),
              executed_source=str(source_dir.relative_to(output)),
              limitations=['No new model training','No native or full-parameter gradient','No on-policy experiment',
                           'Cached verdict replay; no tests re-executed',
                           'Transcript canonicalization/mask semantics require the separate input-artifact audit',
                           'Analytic score conditional on finite-precision fixed logits; not fp32-base equivalence'])
    atomic_json(manifest_path,meta);print(json.dumps(meta,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--tokens',default='/Users/shengweizhang/.cache/shengwei-agent-audit/swe_tokens.npz')
    p.add_argument('--model',default='/Users/shengweizhang/.cache/shengwei-agent-audit/models/qwen1.5b')
    p.add_argument('--device',choices=('mps','cpu'),default='mps')
    p.add_argument('--limit',type=int);p.add_argument('--fresh',action='store_true');p.add_argument('--output')
    main(p.parse_args())

