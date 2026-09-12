"""Paired latent-truth experiments for budgeted information acquisition."""
from pathlib import Path
import argparse
import json
import time
import numpy as np
from allocation import Belief,choose_actions
from common import ROOT,performance,summarise,write_csv,manifest

POLICIES=['uniform','uniform_blind','uncertainty','boundary','bias_blind_kg','ordinary_kg',
          'two_channel_uniform','balanced_mix','validation_only','two_channel_kg']

def world(seed,reps,units,max_packets,beta=.35,sigma=2.5,n0=20,packet=20,
          audit_bias=0.,heavy_tail=False,drift=0.,heteroscedastic=False,shared_group_bias=False):
    rng=np.random.default_rng(seed)
    theta=5+rng.normal(0,.35,(reps,units))
    bias=(np.repeat(rng.normal(0,beta,(reps,4)),units//4,axis=1) if shared_group_bias
          else rng.normal(0,beta,(reps,units)))
    validation_bias=rng.normal(0,audit_bias,(reps,units))
    # Explicitly separate independent validation bias from regular-channel bias.
    sigma_i=sigma*np.exp(rng.normal(0,.4,(reps,units))) if heteroscedastic else np.full((reps,units),sigma)
    draw=lambda shape:rng.standard_t(3,shape)/np.sqrt(3) if heavy_tail else rng.normal(size=shape)
    initial=theta+bias+sigma_i/np.sqrt(n0)*draw((reps,units))
    ordinary=theta[:,:,None]+bias[:,:,None]+sigma_i[:,:,None]/np.sqrt(packet)*draw((reps,units,max_packets))
    validation=theta[:,:,None]+validation_bias[:,:,None]+sigma_i[:,:,None]/np.sqrt(packet)*draw((reps,units,max_packets))
    # Drift is a target shift after the initial survey and before all acquisitions.
    shift=rng.normal(0,drift,(reps,units))
    ordinary+=shift[:,:,None];validation+=shift[:,:,None];theta+=shift
    return dict(truth=theta,initial=initial,ordinary=ordinary,validation=validation,
                realised_bias=bias,sigma_i=sigma_i)

def run_policy(data,policy,budget,cost,assumed_beta=.35,assumed_sigma=2.5,seed=1,
               n0=20,packet=20,groups=None):
    reps,units=data['truth'].shape
    if groups is None:groups=np.repeat(np.arange(4),units//4)
    beta=0 if policy in {'uniform_blind','bias_blind_kg'} else assumed_beta
    state=Belief.prior(reps,units,beta=beta)
    state.update_all_ordinary(data['initial'],assumed_sigma**2/n0,n0)
    costs=np.array([1,cost]);remaining=np.full(reps,budget,dtype=int)
    regular_index=np.zeros((reps,units),int);audit_index=regular_index.copy()
    validation_spend=np.zeros(reps);ordinary_spend=np.zeros(reps)
    noise=assumed_sigma**2/packet;rng=np.random.default_rng(seed)
    for step in range(budget):
        unit,channel,available=choose_actions(state,policy,groups,remaining,costs,noise,noise,rng)
        rows=np.flatnonzero(available)
        if not len(rows):break
        uu=unit[rows];cc=channel[rows]
        index=np.where(cc==0,regular_index[rows,uu],audit_index[rows,uu])
        obs=np.where(cc==0,data['ordinary'][rows,uu,index],data['validation'][rows,uu,index])
        state.update(rows,uu,cc,obs,noise,packet)
        regular_index[rows,uu]+=cc==0;audit_index[rows,uu]+=cc==1
        remaining[rows]-=costs[cc]
        validation_spend[rows]+=np.where(cc==1,cost,0);ordinary_spend[rows]+=cc==0
    metric=performance(state.mean,state.target_var,data['truth'],groups)
    metric.update(spent=budget-remaining,validation_fraction=validation_spend/budget,
                  regular_packets=ordinary_spend,validation_packets=validation_spend/cost,
                  posterior_sd=np.sqrt(state.target_var).mean(axis=1),
                  repeat_floor=state.ordinary_uncertainty_floor().mean(axis=1))
    assert np.all(metric['spent']<=budget)
    return metric

def experiment(data,settings,policies,seed):
    result={};rows=[];rep_records=[]
    for policy in policies:
        metric=run_policy(data,policy,settings['budget'],settings['audit_cost'],
                          settings['assumed_beta'],seed=seed)
        result[policy]=metric
        row=dict(**settings,policy=policy,reps=len(data['truth']))
        for name,value in metric.items():
            if name=='selected_size':continue
            row.update({f'{name}_{key}':val for key,val in summarise(value).items()})
        rows.append(row)
    for row in rows:
        m=result[row['policy']]
        for comparator in ['uniform','ordinary_kg']:
            for name in ['regret','overlap']:
                d=m[name]-result[comparator][name]
                row.update({f'{name}_diff_{comparator}_{k}':v for k,v in summarise(d).items()})
    return rows,result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reps',type=int,default=2000)
    parser.add_argument('--seed',type=int,default=2026091107)
    parser.add_argument('--output',default='synthetic');parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args();start=time.perf_counter();rows=[];units=40
    betas=[0,.15,.35,.7];costs=[2,5,10];budgets=[40,120]
    if args.smoke:betas=[0,.35];costs=[5];budgets=[40]
    for j,beta in enumerate(betas):
        data=world(args.seed+j,args.reps,units,max(budgets),beta=beta)
        for cost in costs:
            for budget in budgets:
                settings=dict(scenario='gaussian',bias_sd=beta,assumed_beta=beta,audit_cost=cost,budget=budget)
                rr,_=experiment(data,settings,POLICIES,args.seed+100+j);rows.extend(rr)
                print('Completed',settings,flush=True)
    stresses=[('underestimated_bias',.7,.15,0.,False,0.,False,False),
              ('overestimated_bias',.0,.7,0.,False,0.,False,False),
              ('biased_validation',.35,.35,.35,False,0.,False,False),
              ('heavy_tails',.35,.35,0.,True,0.,False,False),
              ('target_drift',.35,.35,0.,False,.35,False,False),
              ('heteroscedastic',.35,.35,0.,False,0.,True,False),
              ('shared_group_bias',.7,.7,0.,False,0.,False,True)]
    stressrows=[]
    for j,(name,beta,assumed,auditbias,heavy,drift,hetero,shared) in enumerate(stresses):
        data=world(args.seed+1000+j,args.reps,units,120,beta=beta,audit_bias=auditbias,
                   heavy_tail=heavy,drift=drift,heteroscedastic=hetero,shared_group_bias=shared)
        settings=dict(scenario=name,bias_sd=beta,assumed_beta=assumed,audit_cost=5,budget=120)
        rr,_=experiment(data,settings,POLICIES,args.seed+2000+j);stressrows.extend(rr)
        print('Completed stress',name,flush=True)
    output=ROOT/'results';output.mkdir(exist_ok=True)
    write_csv(output/f'{args.output}.csv',rows);write_csv(output/f'{args.output}_stress.csv',stressrows)
    manifest(output/f'{args.output}_manifest.json',dict(completed=True,reps=args.reps,units=units,
             seed=args.seed,base_worlds=len(betas),paired_cells=len(betas)*len(costs)*len(budgets),
             shared_worlds_across_cost_and_budget=True,stress_worlds=len(stresses),policies=POLICIES,
             elapsed_seconds=time.perf_counter()-start,not_nhs_measurements=True))
    print('Finished in',time.perf_counter()-start,'seconds',flush=True)

if __name__=='__main__':main()
