#!/usr/bin/env python3
"""Exact conditional audit expectations; numerical noise only for G>8 HT arms."""
from __future__ import annotations
import argparse,csv,hashlib,itertools,json,time,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.reward_audit import (completion,completion_path,split_advantages,query_order,
    make_survival,cutoff_probabilities,all_prefix_estimates)


def logistic(z):return 1/(1+np.exp(-np.clip(z,-35,35)))

def generate(rng,g,prevalence,regime):
    z=rng.normal(0,1.2,g)+np.log(prevalence/(1-prevalence))
    p=logistic(z)
    if regime=='calibrated':truth=p
    elif regime=='overconfident':truth=logistic(.45*z)
    elif regime=='shifted':truth=logistic(-.65*z)
    else:raise ValueError(regime)
    r=(rng.random(g)<truth).astype(float)
    # Synthetic costs, not measured execution speed: order of magnitude varies.
    costs=np.exp(rng.normal(0,.55,g));costs/=costs.mean()
    # Fixed linear map represents derivatives of separately clipped coefficients.
    score=rng.normal(size=(g,6));ratios=np.exp(rng.normal(0,.25,g))
    linear=np.vstack((score*(ratios<1.2)[:,None],score*(ratios>.8)[:,None]))/g
    return p,r,costs,linear


def metrics(estimates,weights,target,linear):
    dif=estimates-target
    mean=weights@dif
    gdif=dif@linear
    return dict(coefficient_mse=float(weights@(dif*dif).sum(axis=1)),
                conditional_bias_sq=float(mean@mean),
                gradient_mse=float(weights@(gdif*gdif).sum(axis=1)),
                gradient_bias_sq=float((mean@linear)@(mean@linear)))


def prefix_metrics(path,q,target,linear):
    return metrics(all_prefix_estimates(path,q),cutoff_probabilities(q),target,linear)


def select_exponent(groups,budget,order_mode):
    # Calibration labels are separate and all are counted in the ledger.
    exponents=[0.,.5,1.,2.]
    loss=np.zeros(len(exponents))
    for p,r,c,l in groups:
        order=query_order(p,c,order_mode);path=completion_path(p,r,order);target=path[-1]
        for j,e in enumerate(exponents):
            q=make_survival(len(p),budget*len(p),e,costs=c[order])
            loss[j]+=prefix_metrics(path,q,target,l)['gradient_mse']
    return exponents[int(np.argmin(loss))],loss.tolist()


def study(args):
    start=time.time();rngdev=np.random.default_rng(20260912);rngtest=np.random.default_rng(20260913)
    output=ROOT/'results/estimation';output.mkdir(parents=True,exist_ok=True)
    config=dict(vars(args));config.update(calibration_seed=20260912,evaluation_seed=20260913)
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),ROOT/'src/reward_audit.py']}
    (output/'manifest_in_progress.json').write_text(json.dumps(dict(config=config,source_sha256=sources,status='running'),indent=2))
    rows=[];schedules=[];summary=[]
    for g in args.groups:
      for prevalence in args.prevalence:
       for regime in ['calibrated','overconfident','shifted']:
        dev=[generate(rngdev,g,prevalence,regime) for _ in range(args.calibration)]
        test=[generate(rngtest,g,prevalence,regime) for _ in range(args.evaluation)]
        setting=f'g{g}_p{prevalence}_{regime}'
        # Preserve the exact simulated data and fixed derivative map for replay.
        np.savez_compressed(output/f'{setting}.npz',p=np.stack([x[0] for x in test]),r=np.stack([x[1] for x in test]),costs=np.stack([x[2] for x in test]),linear=np.stack([x[3] for x in test]))
        paths=[]
        for p,r,c,l in test:
            order=query_order(p,c,'uncertainty')
            paths.append((completion_path(p,r,order),order))
        for budget in args.budgets:
         exponent,devloss=select_exponent(dev,budget,'uncertainty')
         schedules.append(dict(setting=setting,budget=budget,exponent=exponent,development_losses=devloss,calibration_full_labels=g*len(dev)))
         for i,((p,r,c,l),(path,order)) in enumerate(zip(test,paths)):
            target=split_advantages(r);base=path[0]
            common=dict(setting=setting,g=g,prevalence=prevalence,regime=regime,budget=budget,group=i)
            variants={}
            variants['full']=(dict(coefficient_mse=0.,conditional_bias_sq=0.,gradient_mse=0.,gradient_bias_sq=0.),float(c.sum()),1.,'exact')
            variants['proxy_completion']=(metrics(base[None],np.ones(1),target,l),0.,0.,'exact')
            qfull=np.full(g,budget)
            variants['whole_group_cv']=(prefix_metrics(path,qfull,target,l),budget*g,budget,'exact')
            quniform=make_survival(g,budget*g,1.,costs=c[order])
            variants['rr_fixed']=(prefix_metrics(path,quniform,target,l),float(quniform@c[order]),float(quniform[-1]),'exact')
            q=make_survival(g,budget*g,exponent,costs=c[order])
            variants['rr_development']=(prefix_metrics(path,q,target,l),float(q@c[order]),float(q[-1]),'exact')
            if g<=8:
                mask=np.array(list(itertools.product([0.,1.],repeat=g)))
                k=mask.sum(axis=1);w=budget**k*(1-budget)**(g-k);mode='exact'
            else:
                mask=(rngtest.random((args.ht_samples,g))<budget).astype(float);w=np.full(len(mask),1/len(mask));mode='Monte Carlo audit masks'
            corrected=p+mask/budget*(r-p)
            variants['ht_then_normalize']=(metrics(split_advantages(corrected),w,target,l),budget*g,0.,mode)
            # Raw proxy probabilities with partial replacement: cheap practical arm.
            partial=p+mask*(r-p)
            variants['partial_then_normalize']=(metrics(split_advantages(partial),w,target,l),budget*g,0.,mode)
            for method,(m,cost,tail,mode) in variants.items():
                rows.append(dict(common,method=method,expected_cost=cost,complete_group_probability=tail,expectation_mode=mode,**m))
         new=[r for r in rows if r['setting']==setting and r['budget']==budget]
         for method in sorted({r['method'] for r in new}):
            selected=[r for r in new if r['method']==method]
            row=dict(setting=setting,g=g,prevalence=prevalence,regime=regime,budget=budget,method=method,groups=len(selected))
            for key in ['coefficient_mse','conditional_bias_sq','gradient_mse','gradient_bias_sq','expected_cost','complete_group_probability']:
                x=np.array([r[key] for r in selected]);row[key]=float(x.mean());row[key+'_se']=float(x.std(ddof=1)/np.sqrt(len(x)))
            summary.append(row)
        print(setting,'completed',round(time.time()-start,1),'s',flush=True)
        for filename,data in [('per_group.csv',rows),('summary.csv',summary)]:
            with (output/filename).open('w') as f:
                w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
        (output/'development_schedules.json').write_text(json.dumps(schedules,indent=2))
    end=dict(config=config,source_sha256=sources,status='complete',runtime_seconds=time.time()-start,rows=len(rows),summary_rows=len(summary),note='Costs are simulated units. No wall-time training speedup inferred. Calibrated scheduling labels are separate and counted in development_schedules.json.')
    (output/'manifest.json').write_text(json.dumps(end,indent=2));print(json.dumps(end,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--groups',type=int,nargs='+',default=[4,8,16]);p.add_argument('--prevalence',type=float,nargs='+',default=[.05,.2,.5,.8,.95]);p.add_argument('--budgets',type=float,nargs='+',default=[.25,.5,.75]);p.add_argument('--calibration',type=int,default=64);p.add_argument('--evaluation',type=int,default=256);p.add_argument('--ht-samples',type=int,default=1024)
    study(p.parse_args())
