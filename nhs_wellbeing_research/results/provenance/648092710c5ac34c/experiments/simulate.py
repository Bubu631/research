"""Execute the declared latent-truth experiments; no NHS outcomes used."""
from __future__ import annotations
import argparse
import itertools
import time
import numpy as np
from common import (ROOT, save_csv, save_manifest, gaussian_weights,
                    bottom_indices, row_selected_mean, overlap_rows, summarise)

def generate(rng, reps, units, length, n, tau=.35, sigma2=6.25, phi=.85,
             psi=0., trend=0., error_kind='gaussian', response_bias=0.):
    theta = np.empty((reps,length+1,units))
    error = np.empty_like(theta)
    theta[:,0] = rng.normal(0,tau,(reps,units))
    se = np.sqrt(sigma2/n)
    if error_kind == 't3':
        innovations = rng.standard_t(3,theta.shape)/np.sqrt(3)
    else:
        innovations = rng.normal(size=theta.shape)
    error[:,0] = innovations[:,0]*se
    for t in range(1,length+1):
        theta[:,t] = phi*theta[:,t-1] + rng.normal(0,tau*np.sqrt(1-phi**2),(reps,units))
        error[:,t] = psi*error[:,t-1] + innovations[:,t]*se*np.sqrt(1-psi**2)
    bias = rng.normal(0,response_bias,(reps,1,units))
    mu = 5+trend*np.arange(length+1)
    y = theta+mu[None,:,None]+error+bias
    return theta+mu[None,:,None], y, mu

def evaluate_cell(seed, reps, lo, hi, phi, sigma2, psi, units=80,
                  trend=0., error_kind='gaussian', response_bias=0., cell_id=0):
    rng = np.random.default_rng(seed)
    n = np.rint(np.exp(rng.uniform(np.log(lo),np.log(hi),units))).astype(int)
    theta,y,mu = generate(rng,reps,units,5,n,phi=phi,sigma2=sigma2,psi=psi,
                          trend=trend,error_kind=error_kind,response_bias=response_bias)
    observations=y[:,:5]-mu[None,:5,None]
    sw,fw,pv,fv=gaussian_weights(n,.35**2,sigma2,phi,psi,5)
    sw_ind,_,_,_=gaussian_weights(n,.35**2,sigma2,phi,0.,5)
    weights=phi**np.arange(4,-1,-1,dtype=float); weights/=weights.sum()
    methods={'raw':y[:,4], 'equal_history':observations.mean(axis=1)+mu[4],
             'geometric_history':np.einsum('t,rtn->rn',weights,observations)+mu[4],
             'gaussian_posterior':np.einsum('nt,rtn->rn',sw,observations)+mu[4],
             'independent_error_posterior':np.einsum('nt,rtn->rn',sw_ind,observations)+mu[4]}
    predicted_next=np.einsum('nt,rtn->rn',fw,observations)+mu[5]
    predicted_rebound=predicted_next-y[:,4]
    gaussian_exact=(error_kind=='gaussian' and response_bias==0.)
    rows=[]
    true=theta[:,4]
    out_of_range=float(np.mean((y<0)|(y>10)))
    for frac in [.1,.2,.4]:
        k=max(1,int(units*frac)); true_idx=bottom_indices(true,k)
        oracle_sum=row_selected_mean(true,true_idx)
        for name,estimate in methods.items():
            idx=bottom_indices(estimate,k)
            stats={'hit':overlap_rows(idx,true_idx,units),
                   'latent_regret':row_selected_mean(true,idx)-oracle_sum,
                   'state_mse':np.mean((estimate-true)**2,axis=1),
                   'rebound':row_selected_mean(y[:,5]-y[:,4],idx),
                   'predicted_rebound':row_selected_mean(predicted_rebound,idx),
                   'rebound_residual':row_selected_mean(y[:,5]-predicted_next,idx)}
            row=dict(cell_id=cell_id,seed=int(seed),reps=reps,units=units,
                     n_lo=lo,n_hi=hi,n_min=int(n.min()),n_max=int(n.max()),
                     phi=phi,sigma2=sigma2,psi=psi,trend=trend,error_kind=error_kind,
                     response_bias=response_bias,gaussian_exact=gaussian_exact,
                     fraction=frac,k=k,method=name,out_of_range_fraction=out_of_range)
            for metric,values in stats.items():
                row.update({f'{metric}_{key}':value for key,value in summarise(values).items()})
            rows.append(row)
    return rows

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--reps',type=int,default=5000)
    parser.add_argument('--seed',type=int,default=2026091101)
    parser.add_argument('--output',default='simulation')
    args=parser.parse_args(); start=time.perf_counter(); all_rows=[]
    settings=list(itertools.product([(20,120),(40,250),(150,600),(800,3000)],
                                   [0.,.3,.6,.85,.97],[1.,6.25,25.],[0.,.5]))
    seeds=np.random.SeedSequence(args.seed).spawn(len(settings)+4)
    for c,(bounds,phi,sigma2,psi) in enumerate(settings):
        seed=int(seeds[c].generate_state(1,dtype=np.uint64)[0])
        all_rows.extend(evaluate_cell(seed,args.reps,*bounds,phi,sigma2,psi,cell_id=c))
        if (c+1)%20==0:
            print(f'Completed {c+1}/{len(settings)} declared Gaussian cells',flush=True)
    save_csv(ROOT/'results'/f'{args.output}.csv',all_rows)
    stresses=[dict(error_kind='t3'),dict(trend=-.25),
              dict(response_bias=.3),dict(psi=.9)]
    stress_rows=[]
    for j,extra in enumerate(stresses):
        seed=int(seeds[len(settings)+j].generate_state(1,dtype=np.uint64)[0])
        params=dict(phi=.85,sigma2=6.25,psi=0.);params.update(extra)
        stress_rows.extend(evaluate_cell(seed,args.reps,20,120,**params,cell_id=j))
    save_csv(ROOT/'results'/f'{args.output}_stress.csv',stress_rows)
    save_manifest(ROOT/'results'/f'{args.output}_manifest.json',
                  dict(completed=True,seed=args.seed,reps_per_cell=args.reps,
                       independent_gaussian_cells=len(settings),
                       independent_gaussian_panel_draws=len(settings)*args.reps,
                       methods=5,fractions=3,shared_draws_across_methods_and_fractions=True,
                       stress_cells=len(stresses),elapsed_seconds=time.perf_counter()-start,
                       gaussian_score_bounds_enforced=False))
    print(f'Completed all simulations in {time.perf_counter()-start:.1f} seconds',flush=True)

if __name__=='__main__':main()
