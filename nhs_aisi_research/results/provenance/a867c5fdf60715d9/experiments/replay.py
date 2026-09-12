"""Hidden-record replay on real BRFSS outcomes with controlled sampling laws.

All draws are with replacement from the eligible finite file. Outcome-frequency
sampling is exactly equivalent to record sampling for this single-outcome study.
No policy receives a 2024 full-file mean, hidden outcome, or realised channel bias.
"""
import argparse
import time
import numpy as np
import pandas as pd
from allocation import Belief,choose_actions
from common import ROOT,performance,summarise,write_csv,manifest,sha
from synthetic import POLICIES

def load_histograms(year,weighted=False):
    path=ROOT/f'data/processed/brfss_employed_{year}.csv'
    frame=pd.read_csv(path,dtype={'state':str})
    states=sorted(frame.state.unique());support=(30-np.arange(31))/3
    probability=[];sizes=[]
    for state in states:
        records=frame[frame.state==state];sizes.append(len(records))
        counts=np.bincount(records.mental_unhealthy_days.to_numpy(int),
                           weights=records.weight.to_numpy() if weighted else None,minlength=31)
        probability.append(counts/counts.sum())
    p=np.asarray(probability);mean=p@support
    variance=(p*support**2).sum(axis=1)-mean**2
    return dict(states=states,support=support,prob=p,mean=mean,variance=variance,n=np.asarray(sizes),path=path)

def tilted(prob,support,means,standard_deviations,kappa):
    # Actual synthetic sampler can see hidden outcomes; the acquisition policy cannot.
    score=(support[None,:]-means[:,None])/standard_deviations[:,None]
    plus=prob*np.exp(kappa*score);minus=prob*np.exp(-kappa*score)
    return plus/plus.sum(axis=1,keepdims=True),minus/minus.sum(axis=1,keepdims=True)

def calibration(past,kappa):
    plus,minus=tilted(past['prob'],past['support'],past['mean'],np.sqrt(past['variance']),kappa)
    offsets=np.stack([plus@past['support']-past['mean'],minus@past['support']-past['mean']],axis=1)
    bias_mean=offsets.mean(axis=1);bias_sd=offsets.std(axis=1)
    # Estimate packet variances from past sampling distributions, averaging the unknown signs.
    vars_plus=(plus*past['support']**2).sum(axis=1)-(plus@past['support'])**2
    vars_minus=(minus*past['support']**2).sum(axis=1)-(minus@past['support'])**2
    return dict(mu=float(past['mean'].mean()),tau=float(past['mean'].std(ddof=1)),
                beta=bias_sd,bias_mean=bias_mean,ordinary_variance=(vars_plus+vars_minus)/2,
                validation_variance=past['variance'].copy())

def packet_stream(prob,support,rng,reps,packets,packet):
    uniform=rng.random((reps,packets,packet))
    cdf=np.cumsum(prob);cdf[-1]=1.
    values=support[np.searchsorted(cdf,uniform,side='right')]
    return values.mean(axis=2)

def make_replay(current,past,seed,reps,max_packets,kappa=0.,packet=20,n0=20,validation_kappa=0.):
    assert n0==packet,'The declared replay uses one packet for initial observations.'
    rng=np.random.default_rng(seed);units=len(current['states'])
    assert current['states']==past['states']
    # Tilt scale is frozen to the previous year's within-area SD, not recalibrated on held-out outcomes.
    plus,minus=tilted(current['prob'],current['support'],past['mean'],np.sqrt(past['variance']),kappa)
    aplus,aminus=tilted(current['prob'],current['support'],past['mean'],np.sqrt(past['variance']),validation_kappa)
    signs=rng.integers(0,2,(reps,units));audit_signs=rng.integers(0,2,(reps,units))
    ordinary=np.empty((reps,units,max_packets));validation=np.empty_like(ordinary)
    initial=np.empty((reps,units));realised_bias=np.empty((reps,units))
    realised_validation_bias=np.empty((reps,units))
    for i in range(units):
        for sign,prob in enumerate([minus[i],plus[i]]):
            rows=np.flatnonzero(signs[:,i]==sign)
            stream=packet_stream(prob,current['support'],rng,len(rows),max_packets+1,packet)
            initial[rows,i]=stream[:,0];ordinary[rows,i]=stream[:,1:]
            realised_bias[rows,i]=prob@current['support']-current['mean'][i]
        for sign,prob in enumerate([aminus[i],aplus[i]]):
            rows=np.flatnonzero(audit_signs[:,i]==sign)
            validation[rows,i]=packet_stream(prob,current['support'],rng,len(rows),max_packets,packet)
            realised_validation_bias[rows,i]=prob@current['support']-current['mean'][i]
    return dict(initial=initial,ordinary=ordinary,validation=validation,
                truth=np.broadcast_to(current['mean'],(reps,units)).copy(),
                realised_bias=realised_bias,realised_validation_bias=realised_validation_bias,
                indices_reused_across_policies=True)

def run_replay(data,policy,cal,budget,audit_cost,seed,packet=20,n0=20):
    # This function's inputs contain the backend in data, but only observations below
    # enter the belief or action selector. Evaluation truth is accessed after sampling.
    reps,units=data['initial'].shape;groups=np.zeros(units,int)
    blind=policy in {'bias_blind_kg','uniform_blind'}
    state=Belief.prior(reps,units,mu=cal['mu'],tau=cal['tau'],beta=0. if blind else cal['beta'])
    if not blind:state.bias_mean[:]=cal['bias_mean']
    state.update_all_ordinary(data['initial'],cal['ordinary_variance']/n0,n0)
    noise=cal['ordinary_variance']/packet;audit_noise=cal['validation_variance']/packet
    costs=np.array([1,audit_cost]);remaining=np.full(reps,budget,int)
    oi=np.zeros((reps,units),int);ai=oi.copy();validation_cost=np.zeros(reps)
    rng=np.random.default_rng(seed)
    for _ in range(budget):
        unit,channel,available=choose_actions(state,policy,groups,remaining,costs,noise,audit_noise,rng)
        rows=np.flatnonzero(available)
        if not len(rows):break
        uu=unit[rows];cc=channel[rows];index=np.where(cc==0,oi[rows,uu],ai[rows,uu])
        observation=np.where(cc==0,data['ordinary'][rows,uu,index],data['validation'][rows,uu,index])
        state.update(rows,uu,cc,observation,np.where(cc==0,noise[uu],audit_noise[uu]),packet)
        oi[rows,uu]+=cc==0;ai[rows,uu]+=cc==1
        remaining[rows]-=costs[cc];validation_cost[rows]+=np.where(cc==1,audit_cost,0)
    metric=performance(state.mean,state.target_var,data['truth'],groups)
    metric.update(spent=budget-remaining,validation_fraction=validation_cost/budget,
                  regular_packets=oi.sum(axis=1),validation_packets=ai.sum(axis=1),
                  posterior_sd=np.sqrt(state.target_var).mean(axis=1))
    assert np.all(metric['spent']<=budget)
    return metric,state

def compare(data,cal,settings,policies,seed):
    results={};rows=[];state_rows=[]
    for policy in policies:
        result,state=run_replay(data,policy,cal,settings['budget'],settings['audit_cost'],seed)
        results[policy]=result;row=dict(**settings,policy=policy,reps=len(data['initial']))
        for name,value in result.items():
            if name=='selected_size':continue
            row.update({f'{name}_{k}':v for k,v in summarise(value).items()})
        rows.append(row)
        for i in range(state.mean.shape[1]):
            state_rows.append(dict(**settings,policy=policy,state_index=i,
                    ordinary_count_mean=float(state.ordinary_n[:,i].mean()),
                    validation_count_mean=float(state.validation_n[:,i].mean()),
                    mean_estimate=float(state.mean[:,i].mean()),
                    reference=float(data['truth'][0,i])))
    for row in rows:
        for baseline in ['uniform','ordinary_kg']:
            for name in ['regret','overlap']:
                diff=results[row['policy']][name]-results[baseline][name]
                row.update({f'{name}_diff_{baseline}_{k}':v for k,v in summarise(diff).items()})
    return rows,state_rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reps',type=int,default=1000)
    parser.add_argument('--seed',type=int,default=2026091113);parser.add_argument('--output',default='replay')
    parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
    start=time.perf_counter();rows=[];allocations=[];calrows=[];sourcehash={}
    base_scenarios=[('unweighted_uniform',False,0.,0.),('unweighted_tilt_025',False,.25,0.),
                    ('unweighted_tilt_05',False,.5,0.),('weighted_tilt_05',True,.5,0.),
                    ('validation_tilt_025',False,.5,.25)]
    if args.smoke:base_scenarios=base_scenarios[:2]
    for j,(name,weighted,kappa,akappa) in enumerate(base_scenarios):
        past=load_histograms(2023,weighted);current=load_histograms(2024,weighted)
        units=len(current['states']);budgets=[units,units*3];costs=[2,5,10] if j in [0,2] else [5]
        if args.smoke:budgets=[units];costs=[5]
        cal=calibration(past,kappa)
        for i,state in enumerate(past['states']):
            calrows.append(dict(scenario=name,state=state,mu=cal['mu'],tau=cal['tau'],
                        bias_mean=cal['bias_mean'][i],bias_sd=cal['beta'][i],
                        ordinary_variance=cal['ordinary_variance'][i],validation_variance=cal['validation_variance'][i]))
        data=make_replay(current,past,args.seed+j,args.reps,max(budgets),kappa=kappa,validation_kappa=akappa)
        for cost in costs:
            for budget in budgets:
                setting=dict(scenario=name,weighted=weighted,kappa=kappa,validation_kappa=akappa,
                             audit_cost=cost,budget=budget,units=units,k=max(1,int(.2*units)))
                rr,aa=compare(data,cal,setting,POLICIES,args.seed+100+j);rows.extend(rr)
                for a in aa:a['state']=current['states'][a.pop('state_index')]
                allocations.extend(aa)
                print('Completed',setting,flush=True)
        for src in [past['path'],current['path']]:sourcehash[str(src.relative_to(ROOT))]=sha(src)
    base=ROOT/'results';write_csv(base/f'{args.output}.csv',rows)
    write_csv(base/f'{args.output}_allocations.csv',allocations);write_csv(base/f'{args.output}_calibration.csv',calrows)
    manifest(base/f'{args.output}_manifest.json',dict(completed=True,reps=args.reps,seed=args.seed,
         source_sha256_data=sourcehash,scenarios=base_scenarios,policies=POLICIES,
         sampling='with replacement from eligible finite-file outcome distributions',
         scenario_cost_budget_shared_draws=True,actual_additional_respondents_recruited=False,
         elapsed_seconds=time.perf_counter()-start))
    print('Completed replay in',time.perf_counter()-start,'seconds',flush=True)

if __name__=='__main__':main()
