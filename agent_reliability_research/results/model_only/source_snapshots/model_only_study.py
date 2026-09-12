#!/usr/bin/env python3
"""Post-primary, label-free scheduling study; exact conditional audit moments."""
from __future__ import annotations
import argparse,csv,hashlib,json,platform,sys,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.reward_audit import (completion,split_advantages,query_order,make_survival,
    cutoff_probabilities,all_prefix_estimates,predicted_increment_variances,
    variance_optimal_survival)

METHODS=('whole_group_cv','rr_fixed','rr_model')
BUDGETS=(.25,.5,.75)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stamp():return datetime.now(timezone.utc).isoformat()
def logistic(z):return 1/(1+np.exp(-np.clip(z,-35,35)))
def timed(f,*args,**kwargs):
    w=time.perf_counter();c=time.process_time();out=f(*args,**kwargs)
    return out,time.process_time()-c,time.perf_counter()-w

def generate(rng,g,base_rate_parameter,regime):
    z=rng.normal(0,1.2,g)+np.log(base_rate_parameter/(1-base_rate_parameter))
    p=logistic(z)
    truth=logistic(z*{'calibrated':1.,'overconfident':.45,'shifted':-.65}[regime])
    r=(rng.random(g)<truth).astype(float)
    costs=np.exp(rng.normal(0,.55,g));costs/=costs.mean()
    score=rng.normal(size=(g,6));ratios=np.exp(rng.normal(0,.25,g))
    linear=np.vstack((score*(ratios<1.2)[:,None],score*(ratios>.8)[:,None]))/g
    return dict(p=p,r=r,true_probability=truth,costs=costs,score=score,ratios=ratios,linear=linear)

def metrics(path,q,target,linear):
    mass=cutoff_probabilities(q);est=all_prefix_estimates(path,q)
    d=est-target;mean=mass@d;gd=d@linear
    return dict(coefficient_mse=float(mass@np.sum(d*d,axis=1)),
        conditional_bias_sq=float(mean@mean),gradient_mse=float(mass@np.sum(gd*gd,axis=1)),
        gradient_bias_sq=float((mean@linear)@(mean@linear)))

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def aggregate(rows):
    keys=['coefficient_mse','gradient_mse','conditional_bias_sq','gradient_bias_sq',
        'expected_cost','expected_query_count','complete_group_probability',
        'schedule_cpu_seconds','schedule_wall_seconds','expected_completion_cpu_seconds',
        'total_algorithm_cpu_seconds','realized_success_fraction','true_probability_mean']
    result=[]
    for setting in sorted({r['setting'] for r in rows}):
      for budget in BUDGETS:
       for method in METHODS:
        rr=[r for r in rows if r['setting']==setting and r['budget_fraction']==budget and r['method']==method]
        d={k:rr[0][k] for k in ['setting','g','base_rate_parameter','regime','budget_fraction','method']}
        d['groups']=len(rr)
        for k in keys:
            a=np.array([r[k] for r in rr]);d[k]=float(a.mean());d[k+'_se']=float(a.std(ddof=1)/np.sqrt(len(a)))
        result.append(d)
    return result

def paired(rows):
    indexed={(r['setting'],r['budget_fraction'],r['group'],r['method']):r for r in rows}
    result=[]
    for setting in sorted({r['setting'] for r in rows}):
      groups=sorted({r['group'] for r in rows if r['setting']==setting})
      for budget in BUDGETS:
       for baseline in ['whole_group_cv','rr_fixed']:
        a=[indexed[(setting,budget,i,'rr_model')] for i in groups]
        b=[indexed[(setting,budget,i,baseline)] for i in groups]
        d={k:a[0][k] for k in ['setting','g','base_rate_parameter','regime','budget_fraction']}
        d.update(baseline=baseline,groups=len(groups))
        for k in ['coefficient_mse','gradient_mse','expected_cost','total_algorithm_cpu_seconds']:
            aa=np.array([x[k] for x in a]);bb=np.array([x[k] for x in b]);delta=aa-bb
            d[k+'_difference']=float(delta.mean());d[k+'_difference_se']=float(delta.std(ddof=1)/np.sqrt(len(delta)))
            d[k+'_ratio_of_means']=float(aa.mean()/bb.mean()) if bb.mean()>0 else float('nan')
        result.append(d)
    return result

def study(args):
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    if (output/'manifest.json').exists():raise FileExistsError('Use a new output directory; finished studies are not overwritten.')
    begin=stamp();wall=time.perf_counter();cpu=time.process_time();rng=np.random.default_rng(20260914)
    sourcefiles=[Path(__file__),ROOT/'src/reward_audit.py',ROOT/'docs/model_only_protocol.md',ROOT/'tests/test_model_schedule_independent.py']
    sourcehash={str(p.relative_to(ROOT)):sha(p) for p in sourcefiles}
    snapshots=output/'source_snapshots';snapshots.mkdir(exist_ok=True)
    for p in sourcefiles:(snapshots/p.name).write_bytes(p.read_bytes())
    config=dict(seed=20260914,groups=[4,8,16],base_rate_parameters=[.05,.2,.5,.8,.95],
        regimes=['calibrated','overconfident','shifted'],budgets=list(BUDGETS),evaluation_groups=args.evaluation,
        methods=list(METHODS),survival_floor=.005,calibration_labels=0,phase='post-primary extension with fresh confirmatory draws')
    (output/'manifest_in_progress.json').write_text(json.dumps(dict(status='running',started_at=begin,config=config,source_sha256=sourcehash),indent=2))
    rows=[]
    for g in config['groups']:
     for rate in config['base_rate_parameters']:
      for regime in config['regimes']:
        setting=f'g{g}_base{rate}_{regime}';raw=[]
        for index in range(args.evaluation):
            d=generate(rng,g,rate,regime);p,r,c,l=(d[k] for k in ['p','r','costs','linear'])
            order,oc,ow=timed(query_order,p,c);d['order']=order
            base,bc,bw=timed(completion,p);path=[base];step_cpu=[];step_wall=[];observed=p.copy()
            for i in order:
                observed[i]=r[i];new,cc,cw=timed(completion,observed);path.append(new);step_cpu.append(cc);step_wall.append(cw)
            path=np.stack(path);d['path']=path
            target,tc,tw=timed(split_advantages,r)
            (v,M),mc,mw=timed(predicted_increment_variances,p,order)
            d.update(increment_variances=v,model_moments=M,order_cpu=oc,order_wall=ow,
                base_completion_cpu=bc,base_completion_wall=bw,target_cpu=tc,target_wall=tw,
                step_completion_cpu=np.array(step_cpu),step_completion_wall=np.array(step_wall),
                model_moments_cpu=mc,model_moments_wall=mw)
            qq=[];schedule_cpu=[];schedule_wall=[]
            for budget in BUDGETS:
                q0,q0c,q0w=timed(np.full,g,budget)
                q1,q1c,q1w=timed(make_survival,g,budget*g,1.,costs=c[order])
                q2,q2c,q2w=timed(variance_optimal_survival,v,c[order],budget*g)
                qs=[q0,q1,q2];sc=[q0c,oc+q1c,oc+mc+q2c];sw=[q0w,ow+q1w,ow+mw+q2w]
                qq.append(qs);schedule_cpu.append(sc);schedule_wall.append(sw)
                for j,(method,q) in enumerate(zip(METHODS,qs)):
                    measure=metrics(path,q,target,l)
                    assert measure['conditional_bias_sq']<1e-20
                    assert np.all(q>0) and np.all(np.diff(q)<=1e-12)
                    expectedcost=float(q@c[order]);assert expectedcost<=budget*g+1e-9
                    compcpu=bc+budget*tc if method=='whole_group_cv' else bc+float(q@step_cpu)
                    rows.append(dict(setting=setting,g=g,base_rate_parameter=rate,regime=regime,
                        budget_fraction=budget,group=index,method=method,expectation_mode='exact over all stopping depths',
                        **measure,expected_cost=expectedcost,expected_query_count=float(q.sum()),
                        complete_group_probability=float(q[-1]),max_query_cost=float(c.sum()),
                        schedule_cpu_seconds=sc[j],schedule_wall_seconds=sw[j],
                        expected_completion_cpu_seconds=compcpu,total_algorithm_cpu_seconds=sc[j]+compcpu,
                        realized_success_fraction=float(r.mean()),true_probability_mean=float(d['true_probability'].mean())))
            d.update(survival=np.array(qq),schedule_cpu=np.array(schedule_cpu),schedule_wall=np.array(schedule_wall))
            raw.append(d)
        np.savez_compressed(output/f'{setting}.npz',**{k:np.stack([d[k] for d in raw]) for k in raw[0]},
            budget_fractions=np.array(BUDGETS),methods=np.array(METHODS))
        print(f'{setting}: {len(rows)} accumulated rows; {time.perf_counter()-wall:.1f}s',flush=True)
    write_csv(output/'per_group.csv',rows);write_csv(output/'summary.csv',aggregate(rows));write_csv(output/'paired_comparisons.csv',paired(rows))
    artifacts={str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='manifest_in_progress.json'}
    final=dict(status='complete',started_at=begin,finished_at=stamp(),config=config,
        source_sha256=sourcehash,source_unchanged=all(sha(p)==sourcehash[str(p.relative_to(ROOT))] for p in sourcefiles),
        outputs_sha256=artifacts,runtime_wall_seconds=time.perf_counter()-wall,runtime_cpu_seconds=time.process_time()-cpu,
        python=sys.version,numpy=np.__version__,platform=platform.platform(),rows=len(rows),summary_rows=405,
        base_settings=45,budget_settings=135,unique_groups=45*args.evaluation,
        offline_reference_labels=sum(config['groups'])*15*args.evaluation,calibration_labels=0,
        max_conditional_bias_sq=max(r['conditional_bias_sq'] for r in rows),
        notes=['Reference labels define offline evaluation targets; they are not used to design schedules.',
          'The supplied probability model is not learned in this experiment.',
          'Fixed six-dimensional linear update metric is not a measured language-model gradient.',
          'Moment timing is fully charged once per independent budget; shared three-budget reuse is saved in raw NPZ.',
          'Model-optimal means coefficient Euclidean model risk at a fixed order; not arbitrary gradient risk under misspecification.'])
    (output/'manifest.json').write_text(json.dumps(final,indent=2));print(json.dumps({k:v for k,v in final.items() if k not in ['outputs_sha256','notes']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(ROOT/'results/model_only'))
    parser.add_argument('--evaluation',type=int,default=256);study(parser.parse_args())
