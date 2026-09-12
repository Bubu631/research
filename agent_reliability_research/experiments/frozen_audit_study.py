"""Fixed historical group audit diagnostic, declared before gradient extraction.

Original frozen proxy predictions; unit label-reveal cost; no hidden outcome in
schedule selection. Extra gradient-metric model schedule uses exact 2**G model
integration, feasible here at G8. It does not fit calibration truth.
"""
import csv,hashlib,itertools,json,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.reward_audit import (split_advantages,completion_path,query_order,make_survival,
 cutoff_probabilities,all_prefix_estimates,predicted_increment_variances,variance_optimal_survival)

def model_projected_moments(p,order,linear):
    g=len(p);bits=((np.arange(2**g)[:,None]>>np.arange(g))&1).astype(float)
    weight=np.prod(np.where(bits,p,1-p),axis=1)
    values=split_advantages(bits)@linear;moments=[]
    for k in range(g+1):
        codes=(bits[:,order[:k]]@(2**np.arange(k))).astype(int)
        mass=np.bincount(codes,weights=weight,minlength=2**k)
        total=np.zeros((2**k,linear.shape[1]));np.add.at(total,codes,weight[:,None]*values)
        mean=np.divide(total,mass[:,None],out=np.zeros_like(total),where=mass[:,None]>0)
        moments.append(float(np.sum(mass[:,None]*mean**2)))
    v=np.diff(moments)
    if np.min(v)<-1e-10:raise ArithmeticError('Negative model increment moment')
    return np.maximum(v,0),np.asarray(moments)

def metrics(est,w,target,linear):
    dif=est-target;gdiff=dif@linear;mean=w@dif
    return dict(coefficient_mse=float(w@np.sum(dif**2,axis=1)),gradient_mse=float(w@np.sum(gdiff**2,axis=1)),
       coefficient_bias_sq=float(mean@mean),gradient_bias_sq=float((mean@linear)@(mean@linear)))

def main():
    start=time.perf_counter();out=ROOT/'results/frozen_audit';out.mkdir(exist_ok=True)
    source_files=[Path(__file__),ROOT/'src/reward_audit.py',ROOT/'results/frozen_model/gradient_bank.npz',
                  ROOT/'data/swe_gym/processed/heterogeneous_groups_g8.jsonl']
    hashes={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in source_files}
    bank=np.load(ROOT/'results/frozen_model/gradient_bank.npz',allow_pickle=False)
    lookup={s:v for s,v in zip(bank['record_ids'],bank['gradients'])}
    groups=[json.loads(x) for x in source_files[-1].read_text().splitlines()];groups=[x for x in groups if x['split']=='heldout']
    assert len(groups)==49 and len(lookup)==392
    assert len({x["instance_id"] for x in groups})==len(groups)
    all_ids=[i for x in groups for i in x["record_ids"]]
    assert len(set(all_ids))==len(all_ids) and set(all_ids)==set(lookup)
    rows=[];schedule_rows=[]
    for j,group in enumerate(groups):
        p=np.array(group['proxy_probabilities']);g=len(p);costs=np.ones(g)
        score=np.stack([lookup[x] for x in group['record_ids']]);linear=np.vstack((score,score))/g
        order=query_order(p,costs);ts=time.perf_counter();vc,_=predicted_increment_variances(p,order);coeff_time=time.perf_counter()-ts
        ts=time.perf_counter();vg,_=model_projected_moments(p,order,linear);grad_time=time.perf_counter()-ts
        # Only below this boundary are reference labels consumed for evaluation.
        r=np.array(group['labels']);target=split_advantages(r);path=completion_path(p,r,order)
        for budget in [.25,.5,.75]:
            schedules={'whole_group_cv':np.full(g,budget),'rr_fixed':make_survival(g,budget*g,1),
                'rr_model_coefficient':variance_optimal_survival(vc,costs,budget*g),
                'rr_model_gradient':variance_optimal_survival(vg,costs,budget*g)}
            variants={}
            for name,q in schedules.items():
                variants[name]=(all_prefix_estimates(path,q),cutoff_probabilities(q),float(q.sum()),float(q[-1]))
                schedule_rows.append(dict(group_id=group['group_id'],budget=budget,method=name,q=q.tolist(),
                     model_moment_seconds=grad_time if name=='rr_model_gradient' else coeff_time if name=='rr_model_coefficient' else 0))
            variants['full']=(target[None],np.ones(1),g,1)
            variants['proxy_completion']=(path[:1],np.ones(1),0,0)
            mask=np.array(list(itertools.product([0.,1.],repeat=g)));k=mask.sum(1);w=budget**k*(1-budget)**(g-k)
            variants['ht_then_normalize']=(split_advantages(p+mask/budget*(r-p)),w,budget*g,budget**g)
            variants['partial_then_normalize']=(split_advantages(p+mask*(r-p)),w,budget*g,budget**g)
            for name,(est,w,cost,tail) in variants.items():
                rows.append(dict(group_id=group['group_id'],instance_id=group['instance_id'],budget=budget,method=name,
                      successes=int(r.sum()),target_gradient_norm=float(np.linalg.norm(target@linear)),
                      expected_label_reveals=cost,full_group_probability=tail,**metrics(est,w,target,linear)))
    with (out/'per_group.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary=[];rng=np.random.default_rng(20260916);boot=rng.integers(0,len(groups),size=(10000,len(groups)))
    for budget in [.25,.5,.75]:
        for method in sorted(set(x['method'] for x in rows)):
            select=[x for x in rows if x['budget']==budget and x['method']==method]
            base=[x for x in rows if x['budget']==budget and x['method']=='whole_group_cv']
            assert [x['group_id'] for x in select]==[x['group_id'] for x in base]
            rec=dict(budget=budget,method=method,groups=len(select))
            for key in ['coefficient_mse','gradient_mse','coefficient_bias_sq','gradient_bias_sq','expected_label_reveals','full_group_probability']:
                a=np.array([x[key] for x in select]);rec[key]=float(a.mean());rec[key+'_se']=float(a.std(ddof=1)/np.sqrt(len(a)))
            a=np.array([x['gradient_mse'] for x in select]);b=np.array([x['gradient_mse'] for x in base])
            if b.mean()<=0 or np.any(b[boot].mean(1)<=0):raise ValueError('Undefined MSE ratio: zero baseline denominator')
            rec['gradient_mse_ratio_to_whole']=float(a.mean()/b.mean())
            lo,hi=np.quantile(a[boot].mean(1)/b[boot].mean(1),[.025,.975]);rec['ratio_bootstrap_low']=float(lo);rec['ratio_bootstrap_high']=float(hi)
            summary.append(rec)
    with (out/'summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    (out/'schedules.json').write_text(json.dumps(schedule_rows,indent=2))
    meta=dict(status='complete',source_sha256=hashes,groups=49,records=392,mixed_groups=sum(0<x['success_count']<8 for x in groups),
     methods=8,budgets=[.25,.5,.75],rows=len(rows),bootstrap_replicates=10000,bootstrap_seed=20260916,
     bootstrap_unit='task; exactly one G8 group per heldout task; pointwise percentile ratio intervals, not simultaneous',
     elapsed_seconds=time.perf_counter()-start,expectations='exact enumeration of all audit stopping paths or all 256 masks',
     additional_true_label_calibration_cost=0,cost_unit='cached reference verdict reveal; not measured real test execution time',
     target='32-dimensional added-logit-bias score of final assistant action under declared truncated frozen-checkpoint serialization; empirical ratios one',
     limitations=['historical heterogeneous groups','no on-policy inference','no fresh test execution','no policy training','no full-parameter gradient'])
    (out/'manifest.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
    for x in summary:
        if x['method'].startswith('rr_model'):print(x['budget'],x['method'],x['gradient_mse_ratio_to_whole'],x['ratio_bootstrap_low'],x['ratio_bootstrap_high'])
if __name__=='__main__':main()
