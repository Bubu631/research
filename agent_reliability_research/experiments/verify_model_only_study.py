#!/usr/bin/env python3
"""Independently recompute saved model-only outputs from sufficient statistics."""
import csv,hashlib,json,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments'))
from verify_model_completion_lemma import moment_by_all_patterns

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def exhaustive_path(p,r,order):
    g=len(p);mask=np.arange(1<<g,dtype=np.int64)
    y=((mask[:,None]>>np.arange(g))&1).astype(float)
    mean=y.mean(1);sd=np.sqrt(mean*(1-mean))
    a=np.divide(y-mean[:,None],sd[:,None],out=np.zeros_like(y),where=sd[:,None]>0)
    phi=np.c_[np.maximum(a,0),np.minimum(a,0)]
    weight=np.prod(np.where(y,p,1-p),axis=1);path=[]
    for k in range(g+1):
        selected=np.all(y[:,order[:k]]==r[order[:k]],axis=1)
        w=weight*selected;path.append((w@phi)/w.sum())
    return np.array(path)

def main():
    start=time.time();out=ROOT/'results/model_only';manifest=json.loads((out/'manifest.json').read_text())
    for p,h in manifest['outputs_sha256'].items():assert sha(out/p)==h,p
    rows=list(csv.DictReader((out/'per_group.csv').open()))
    index={(r['setting'],float(r['budget_fraction']),r['method'],int(r['group'])):r for r in rows}
    maxcost=0.;maxwhole=0.;costcount=0
    for file in sorted(out.glob('*.npz')):
        with np.load(file) as stored:data={key:stored[key] for key in stored.files}
        g=data['p'].shape[1]
        for i in range(len(data['p'])):
            costs=data['costs'][i,data['order'][i]];q=data['survival'][i]
            for b,budget in enumerate(data['budget_fractions']):
                assert np.all(q[b]>0) and np.all(np.diff(q[b],axis=1)<=1e-12)
                target=data['path'][i,-1];base=data['path'][i,0]
                for j,method in enumerate(data['methods']):
                    row=index[(file.stem,float(budget),str(method),i)]
                    actual=float(q[b,j]@costs)
                    maxcost=max(maxcost,abs(actual-float(row['expected_cost'])));costcount+=1
                    assert actual<=budget*g+1e-9
                    assert abs(q[b,j,-1]-float(row['complete_group_probability']))<1e-12
                    assert abs(q[b,j].sum()-float(row['expected_query_count']))<1e-12
                    if j==0:
                        reference=(1/budget-1)*np.sum((target-base)**2)
                        maxwhole=max(maxwhole,abs(reference-float(row['coefficient_mse'])))
    assert maxwhole<1e-10 and maxcost<1e-12
    checks=[]
    for g,regime,rate in [(4,'shifted','0.2'),(8,'calibrated','0.8'),(16,'overconfident','0.05')]:
        setting=f'g{g}_base{rate}_{regime}';d=np.load(out/f'{setting}.npz');i=0
        p,r,c,l,order=(d[k][i] for k in ['p','r','costs','linear','order'])
        path=exhaustive_path(p,r,order)
        moments=moment_by_all_patterns(p[order])
        perr=float(abs(path-d['path'][i]).max());merr=float(abs(moments-d['model_moments'][i]).max())
        assert perr<1e-10 and merr<1e-10
        metricerr=0.
        for bi,b in enumerate(d['budget_fractions']):
          for mi,method in enumerate(d['methods']):
            Q=d['survival'][i,bi,mi]
            estimate=path[0].copy();estimates=[estimate.copy()]
            for k in range(g):
                estimate=estimate+(path[k+1]-path[k])/Q[k];estimates.append(estimate.copy())
            weights=np.array([1-Q[0]]+[Q[k-1]-Q[k] for k in range(1,g)]+[Q[-1]])
            diff=np.array(estimates)-path[-1]
            reference=[sum(w*float(x@x) for w,x in zip(weights,diff)),
                       sum(w*float((x@l)@(x@l)) for w,x in zip(weights,diff))]
            row=index[(setting,float(b),str(method),i)]
            metricerr=max(metricerr,abs(reference[0]-float(row['coefficient_mse'])),abs(reference[1]-float(row['gradient_mse'])))
        assert metricerr<1e-9
        checks.append(dict(setting=setting,group=0,full_pattern_count=2**g,
            completion_path_max_error=perr,model_moments_max_error=merr,metric_max_error=metricerr))
    result=dict(status='passed',runtime_seconds=time.time()-start,
        source_sha256=sha(Path(__file__)),protected_manifest_sha256=sha(out/'manifest.json'),
        checked_cost_rows=costcount,max_cost_discrepancy=maxcost,max_whole_group_closed_form_error=maxwhole,
        exact_saved_group_recomputations=checks,
        no_oracle_in_schedule='Source inspected: schedule calls receive only p, order, costs, predicted moments, budget. True probability and r are evaluation-only.',
        scope='No re-execution or replacement of the 135-setting study; independent full-label-pattern and stopping-depth calculation for selected groups.')
    (out/'independent_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
