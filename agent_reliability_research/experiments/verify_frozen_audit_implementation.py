#!/usr/bin/env python3
"""Constructed-input independent audit; never loads the actual gradient bank."""
import hashlib,itertools,json,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments'));sys.path.insert(0,str(ROOT))
from frozen_audit_study import model_projected_moments,metrics
from src.reward_audit import variance_optimal_survival

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def phi(r):
    x=np.asarray(r,dtype=float);mean=sum(x)/len(x)
    variance=sum((x-mean)**2)/len(x)
    a=(x-mean)/np.sqrt(variance) if variance>0 else np.zeros_like(x)
    return np.r_[np.maximum(a,0),np.minimum(a,0)]

def independent_prefixes(p,order,L):
    """Directly sum each conditional completion using its unknown labels."""
    G=len(p);cache={};M=[]
    for k in range(G+1):
        mk=0.
        for prefix in itertools.product([0,1],repeat=k):
            prior=np.prod([p[i] if bit else 1-p[i] for i,bit in zip(order[:k],prefix)])
            completion=np.zeros(2*G)
            for suffix in itertools.product([0,1],repeat=G-k):
                r=np.zeros(G);r[order]=prefix+suffix
                weight=np.prod([p[i] if bit else 1-p[i] for i,bit in zip(order[k:],suffix)])
                completion+=weight*phi(r)
            cache[(k,prefix)]=completion
            projected=completion@L;mk+=prior*float(projected@projected)
        M.append(mk)
    return np.array(M),cache

def main():
    began=time.time();rng=np.random.default_rng(2026091607);checks=[]
    for G in [2,3,4,6,8]:
     for scenario in ['general_map','ratio_one','degenerate_probabilities']:
        p=rng.uniform(.03,.97,G);order=rng.permutation(G);L=rng.normal(size=(2*G,5))
        if scenario=='ratio_one':L=np.vstack((L[:G],L[:G]))/G
        if scenario=='degenerate_probabilities':p[0]=0.;p[-1]=1.
        expected,cache=independent_prefixes(p,order,L)
        v,actual=model_projected_moments(p,order,L)
        error=float(np.max(abs(actual-expected)));assert error<1e-10
        assert np.all(v>=0)
        Q=variance_optimal_survival(v,np.ones(G),.5*G)
        scaled,_=model_projected_moments(p,order,L*1e-8)
        qs=variance_optimal_survival(scaled,np.ones(G),.5*G)
        assert np.max(abs(qs-Q))<1e-8
        assert np.sum(Q)<=G*.5+1e-10 and np.all(np.diff(Q)<=1e-12)
        weights=np.r_[1-Q[0],Q[:-1]-Q[1:],Q[-1]]
        risk=0.;bias=0.;metricerror=0.
        for labels in itertools.product([0,1],repeat=G):
            r=np.array(labels);prior=np.prod(np.where(r,p,1-p));target=phi(r)
            path=np.array([cache[(k,tuple(r[order[:k]]))] for k in range(G+1)])
            accum=path[0].copy();estimate=[accum.copy()]
            for k in range(G):
                accum+=(path[k+1]-path[k])/Q[k];estimate.append(accum.copy())
            estimate=np.array(estimate);diff=estimate-target
            gd=diff@L;reference=sum(float(w)*float(x@x) for w,x in zip(weights,gd))
            root=metrics(estimate,weights,target,L)
            metricerror=max(metricerror,abs(reference-root['gradient_mse']))
            mean=sum(w*x for w,x in zip(weights,gd));bias=max(bias,float(mean@mean))
            risk+=prior*reference
        theory=float(np.sum((1/Q-1)*np.diff(expected)))
        riskerror=abs(risk-theory)
        assert riskerror<1e-9 and bias<1e-20 and metricerror<1e-10
        checks.append(dict(g=G,scenario=scenario,moment_max_error=error,
            expected_model_risk=risk,martingale_risk_formula_error=riskerror,
            conditional_projected_bias_sq_max=bias,metric_max_error=metricerror,
            expected_cost=float(Q.sum()),full_group_probability=float(Q[-1]),
            scale_invariant_schedule_error=float(np.max(abs(qs-Q)))))
    groupsfile=ROOT/'data/swe_gym/processed/heterogeneous_groups_g8.jsonl'
    groups=[json.loads(x) for x in groupsfile.read_text().splitlines()]
    groups=[x for x in groups if x['split']=='heldout']
    assert len(groups)==49 and len({x['instance_id'] for x in groups})==49
    assert len({x['group_id'] for x in groups})==49
    assert len({r for x in groups for r in x['record_ids']})==392
    # Constructed paired task bootstrap; actual model output is not read.
    b=np.exp(rng.normal(size=49));a=b*np.exp(rng.normal(-.1,.2,49))
    boot=np.random.default_rng(20260916).integers(0,49,size=(10000,49))
    ratio=a[boot].mean(1)/b[boot].mean(1)
    manual=np.array([sum(a[i] for i in ids)/sum(b[i] for i in ids) for ids in boot[:50]])
    booterr=float(np.max(abs(ratio[:50]-manual)));assert booterr<1e-12
    assert np.allclose((.5*b)[boot].mean(1)/b[boot].mean(1),.5)
    result=dict(status='passed',runtime_seconds=time.time()-began,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'experiments/frozen_audit_study.py',ROOT/'src/reward_audit.py']},
        actual_gradient_bank_loaded=False,constructed_checks=checks,
        heldout_metadata=dict(groups=49,unique_tasks=49,unique_records=392,source_sha256=sha(groupsfile)),
        paired_bootstrap=dict(replicates=10000,seed=20260916,manual_50_replicates_max_error=booterr,
            constant_ratio_control=.5,scope='Tasks are resampled jointly across methods; conditional diagnostic, not representative-population or simultaneous inference.'),
        scope=['L=stack(score,score)/G corresponds to ratio=1; no clipping activation is tested.',
          'Supplied p/order/L determine moments; actual reward labels are absent from the tested function.',
          'Unit cost counts cached verdict reveals only; no real environment execution-time claim.',
          'Current source assumes nonzero whole-group mean/replicate denominator; explicit checks recommended.'])
    path=ROOT/'results/frozen_audit_implementation_checks.json';path.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
