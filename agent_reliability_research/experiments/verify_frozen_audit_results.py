#!/usr/bin/env python3
"""Independent final-bank audit from saved records; imports no root estimator."""
import csv,hashlib,itertools,json,time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def independent_phi(values):
    x=np.asarray(values,dtype=float);m=np.sum(x,axis=-1,keepdims=True)/x.shape[-1]
    centered=x-m;sd=np.sqrt(np.sum(centered**2,axis=-1,keepdims=True)/x.shape[-1])
    a=np.divide(centered,sd,out=np.zeros_like(centered),where=sd>0)
    return np.concatenate([np.maximum(a,0),np.minimum(a,0)],axis=-1)

def moments_by_definition(bits,phi,weight,order,L):
    projected=phi@L;M=[]
    for k in range(len(order)+1):
        mk=0.
        for prefix in itertools.product([0,1],repeat=k):
            keep=np.all(bits[:,order[:k]]==prefix,axis=1);w=weight[keep]
            mass=w.sum()
            if mass>0:
                conditional=np.sum(w[:,None]*projected[keep],axis=0)/mass
                mk+=mass*float(conditional@conditional)
        M.append(mk)
    return np.array(M)

def direct_metrics(estimates,probability,target,L):
    error=estimates-target;projected=error@L
    mean=np.sum(probability[:,None]*error,axis=0)
    return dict(coefficient_mse=float(sum(w*float(d@d) for w,d in zip(probability,error))),
        gradient_mse=float(sum(w*float(d@d) for w,d in zip(probability,projected))),
        coefficient_bias_sq=float(mean@mean),gradient_bias_sq=float((mean@L)@(mean@L)))

def main():
    start=time.time();out=ROOT/'results/frozen_audit';bankpath=ROOT/'results/frozen_model/gradient_bank.npz'
    groupfile=ROOT/'data/swe_gym/processed/heterogeneous_groups_g8.jsonl'
    protected=[bankpath,groupfile,out/'manifest.json',out/'per_group.csv',out/'summary.csv',out/'schedules.json']
    before={str(p.relative_to(ROOT)):sha(p) for p in protected}
    manifest=json.loads((out/'manifest.json').read_text())
    for name,h in manifest['source_sha256'].items():assert sha(ROOT/name)==h,name
    with np.load(bankpath,allow_pickle=False) as data:
        ids=data['record_ids'];gradient=data['gradients']
    assert gradient.shape==(392,32) and np.all(np.isfinite(gradient))
    lookup=dict(zip(ids,gradient));assert len(lookup)==392
    groups=[json.loads(line) for line in groupfile.read_text().splitlines()]
    groups=[x for x in groups if x['split']=='heldout']
    assert len(groups)==len({x['instance_id'] for x in groups})==len({x['group_id'] for x in groups})==49
    assert set(lookup)=={record for x in groups for record in x['record_ids']}
    rows=list(csv.DictReader((out/'per_group.csv').open()));summaries=list(csv.DictReader((out/'summary.csv').open()))
    indexed={(r['group_id'],float(r['budget']),r['method']):r for r in rows}
    assert len(rows)==len(indexed)==1176 and len(summaries)==24
    schedules=json.loads((out/'schedules.json').read_text())
    Qs={(r['group_id'],float(r['budget']),r['method']):np.asarray(r['q']) for r in schedules}
    assert len(Qs)==49*3*4
    methods=sorted({r['method'] for r in rows});assert len(methods)==8
    bits=np.array(list(itertools.product([0,1],repeat=8)));phi=independent_phi(bits)
    metric_error={key:0. for key in ['coefficient_mse','gradient_mse','coefficient_bias_sq','gradient_bias_sq']}
    costerror=0.;tailerror=0.;wholeerror=0.;selected=[];recomputed={}
    # Three predetermined actual rows; full-label means are nevertheless rebuilt for every task.
    for gi,group in enumerate(groups):
        gid=group['group_id'];p=np.asarray(group['proxy_probabilities']);r=np.asarray(group['labels'])
        assert len(p)==8 and np.all((p>0)&(p<1))
        order=np.argsort(-p*(1-p),kind='stable')
        score=np.stack([lookup[x] for x in group['record_ids']]);L=np.concatenate([score,score])/8
        weight=np.prod(np.where(bits,p,1-p),axis=1);target=independent_phi(r);path=[]
        for k in range(9):
            keep=np.all(bits[:,order[:k]]==r[order[:k]],axis=1)
            w=weight[keep];path.append(np.sum(w[:,None]*phi[keep],axis=0)/w.sum())
        path=np.array(path);assert np.max(abs(path[-1]-target))<1e-12
        for budget in [.25,.5,.75]:
          for method in methods:
            row=indexed[(gid,budget,method)]
            assert row['instance_id']==group['instance_id'] and int(row['successes'])==int(r.sum())
            assert abs(float(row['target_gradient_norm'])-np.linalg.norm(target@L))<1e-12
            if method in ['whole_group_cv','rr_fixed','rr_model_coefficient','rr_model_gradient']:
                Q=Qs[(gid,budget,method)];assert np.all(Q>0) and np.all(np.diff(Q)<=1e-12)
                assert np.sum(Q)<=budget*8+1e-10
                probability=np.r_[1-Q[0],Q[:-1]-Q[1:],Q[-1]]
                now=path[0].copy();estimates=[now.copy()]
                for k in range(8):
                    now=now+(path[k+1]-path[k])/Q[k];estimates.append(now.copy())
                estimates=np.array(estimates);cost=float(Q.sum());tail=float(Q[-1])
                if method=='whole_group_cv':assert np.allclose(Q,budget)
            elif method=='full':
                estimates=target[None];probability=np.ones(1);cost=8.;tail=1.
            elif method=='proxy_completion':
                estimates=path[:1];probability=np.ones(1);cost=0.;tail=0.
            else:
                probability=np.prod(np.where(bits,budget,1-budget),axis=1)
                corrected=p+bits*(r-p)/(budget if method=='ht_then_normalize' else 1.)
                estimates=independent_phi(corrected);cost=8*budget;tail=budget**8
            metrics=direct_metrics(estimates,probability,target,L)
            for key,value in metrics.items():metric_error[key]=max(metric_error[key],abs(value-float(row[key])))
            costerror=max(costerror,abs(cost-float(row['expected_label_reveals'])))
            tailerror=max(tailerror,abs(tail-float(row['full_group_probability'])))
            if method=='whole_group_cv':
                closed=(1/budget-1)*np.sum(((target-path[0])@L)**2)
                wholeerror=max(wholeerror,abs(closed-float(row['gradient_mse'])))
            recomputed[(gid,budget,method)]=dict(metrics,expected_label_reveals=cost,full_group_probability=tail)
        if gi in [0,24,48]:
            Mc=moments_by_definition(bits,phi,weight,order,np.eye(16))
            Mg=moments_by_definition(bits,phi,weight,order,L)
            assert np.min(np.diff(Mc))>-1e-10 and np.min(np.diff(Mg))>-1e-15
            optimal_checks=[]
            for method,M in [('rr_model_coefficient',Mc),('rr_model_gradient',Mg)]:
              v=np.maximum(np.diff(M),0)
              normalized=v/v.max() if v.max()>0 else v
              for budget in [.25,.5,.75]:
                Q=Qs[(gid,budget,method)]
                fit=minimize(lambda q:float(np.sum(normalized/q)),np.full(8,budget),
                    jac=lambda q:-normalized/q**2,method='SLSQP',bounds=[(.005,1.)]*8,
                    constraints=[{'type':'ineq','fun':lambda q:q[:-1]-q[1:]},
                        {'type':'ineq','fun':lambda q,cap=budget*8:cap-q.sum()}],
                    options={'ftol':1e-11,'maxiter':1000})
                gap=abs(float(np.sum(normalized/Q))-fit.fun)
                assert gap<1e-6,(gid,method,budget,gap,fit.message)
                optimal_checks.append(dict(method=method,budget=budget,independent_objective_gap=gap,
                    optimizer_success=bool(fit.success),model_risk=float(np.sum(v*(1/Q-1)))))
            selected.append(dict(group_index=gi,group_id=gid,instance_id=group['instance_id'],success_count=int(r.sum()),
                coefficient_moments=Mc.tolist(),projected_moments=Mg.tolist(),target_projected_norm=float(np.linalg.norm(target@L)),
                schedule_optimality=optimal_checks))
    assert max(metric_error.values())<1e-9 and costerror<1e-12 and tailerror<1e-12 and wholeerror<1e-12
    boot=np.random.default_rng(20260916).integers(0,49,size=(10000,49));booterror=0.;summaryerror=0.;min_denominator=float('inf');ratios=[]
    for record in summaries:
        budget=float(record['budget']);method=record['method']
        a=np.array([recomputed[(g['group_id'],budget,method)]['gradient_mse'] for g in groups])
        b=np.array([recomputed[(g['group_id'],budget,'whole_group_cv')]['gradient_mse'] for g in groups])
        denom=b[boot].mean(1);assert np.all(denom>0);min_denominator=min(min_denominator,float(denom.min()))
        ratio=a.mean()/b.mean();interval=np.quantile(a[boot].mean(1)/denom,[.025,.975])
        booterror=max(booterror,abs(ratio-float(record['gradient_mse_ratio_to_whole'])),
            abs(interval[0]-float(record['ratio_bootstrap_low'])),abs(interval[1]-float(record['ratio_bootstrap_high'])))
        for key in list(metric_error)+['expected_label_reveals','full_group_probability']:
            value=np.array([recomputed[(g['group_id'],budget,method)][key] for g in groups])
            summaryerror=max(summaryerror,abs(value.mean()-float(record[key])),
                abs(value.std(ddof=1)/7-float(record[key+'_se'])))
        if method in ['rr_model_coefficient','rr_model_gradient']:
            ratios.append(dict(method=method,budget=budget,ratio=float(ratio),pointwise_percentile_95=interval.tolist()))
    assert booterror<1e-9 and summaryerror<1e-9
    assert before=={str(p.relative_to(ROOT)):sha(p) for p in protected}
    result=dict(status='passed',runtime_seconds=time.time()-start,source_sha256=sha(Path(__file__)),
        protected_inputs_sha256=before,source_manifest_hashes_match=True,protected_inputs_unchanged=True,
        gradient_shape=list(gradient.shape),groups=49,unique_tasks=49,unique_records=392,checked_method_rows=1176,
        full_cube_path_reconstructions=49,full_cube_moment_and_independent_schedule_checks=selected,
        metric_max_absolute_errors=metric_error,cost_max_absolute_error=costerror,tail_max_absolute_error=tailerror,
        whole_group_closed_form_gradient_mse_max_error=wholeerror,summary_mean_se_max_error=summaryerror,
        paired_bootstrap_replicates=10000,paired_bootstrap_seed=20260916,paired_bootstrap_max_error=booterror,
        zero_bootstrap_denominators=0,minimum_bootstrap_denominator=min_denominator,model_method_ratios=ratios,
        interpretation='Fixed historical 32-dimensional logit-bias update at ratio one. Pointwise task-bootstrap diagnostic; no simultaneous coverage, clipping-active, on-policy, training, or fresh test-execution claim.')
    (out/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
