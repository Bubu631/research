#!/usr/bin/env python3
"""Read-only independent audit of allocation, synthetic and finite-file replay.

Reference updates use full 2x2 covariance matrices; terminal-value checks use
quadrature. Original routines are exercised as subjects, not as references.
Only stdout is written. Run from this repository with NumPy/pandas/SciPy.
"""
from __future__ import annotations
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.integrate import quad
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments'))
import allocation as subject
import synthetic
import replay
import common


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left,right,atol=2e-11):
    np.testing.assert_allclose(left,right,rtol=2e-10,atol=atol)


def matrix_update(mean,covariance,loading,observation,noise):
    loading=np.broadcast_to(loading,mean.shape)
    projected=np.einsum('...ij,...j->...i',covariance,loading)
    variance=np.einsum('...i,...i->...',loading,projected)+noise
    residual=observation-np.einsum('...i,...i->...',loading,mean)
    return (mean+projected*(residual/variance)[...,None],
            covariance-projected[..., :,None]*projected[...,None,:]/variance[...,None,None])


def independent_gain(gap,sd):
    distance=np.abs(gap)
    z=np.divide(distance,sd,out=np.full_like(sd,np.inf),where=sd>0)
    answer=sd*norm.pdf(z)-distance*norm.sf(z)
    return np.where(np.isfinite(distance)&(sd>0),np.maximum(answer,0),0)


def other_cutoffs(mean,groups,fraction=.2):
    result=np.empty_like(mean)
    for group in sorted(set(groups)):
        ids=np.flatnonzero(groups==group);k=max(1,int(fraction*len(ids)))
        for i in ids:
            others=ids[ids!=i]
            result[:,i]=np.inf if not len(others) or k>len(others) else np.sort(mean[:,others],axis=1)[:,k-1]
    return result


def ref_choices(mean,cov,policy,groups,remaining,costs,noise,audit_noise,rng,return_scores=False):
    reps,units=mean.shape[:2]
    scores=np.full((reps,units,2),-np.inf)
    if policy in {'uniform','uniform_blind','two_channel_uniform','validation_only','balanced_mix'}:
        scores=rng.random((reps,units,2))
        if policy in {'uniform','uniform_blind'}:scores[:,:,1]=-np.inf
        if policy=='validation_only':scores[:,:,0]=-np.inf
        if policy=='balanced_mix':
            ask_audit=rng.random(reps)<costs[0]/sum(costs)
            scores[:,:,0][ask_audit]=-np.inf;scores[:,:,1][~ask_audit]=-np.inf
            fallback=ask_audit&(remaining<costs[1])
            scores[fallback,:,0]=rng.random((int(fallback.sum()),units))
    elif policy=='uncertainty':
        scores[:,:,0]=cov[:,:,0,0]
    elif policy=='boundary':
        scores[:,:,0]=2*np.sqrt(cov[:,:,0,0])-abs(mean[:,:,0]-other_cutoffs(mean[:,:,0],groups))
    else:
        gaps=mean[:,:,0]-other_cutoffs(mean[:,:,0],groups)
        for channel,h in enumerate(([1.,1.],[1.,0.])):
            h=np.asarray(h)
            innovation=np.einsum('...ij,j->...i',cov,h)
            obs_var=np.einsum('i,...ij,j->...',h,cov,h)+(noise if channel==0 else audit_noise)
            sd=np.abs(innovation[:,:,0])/np.sqrt(obs_var)
            scores[:,:,channel]=independent_gain(gaps,sd)/costs[channel]
        if policy in {'ordinary_kg','bias_blind_kg'}:scores[:,:,1]=-np.inf
        elif policy not in {'two_channel_kg','two_channel_kg_terminal'}:raise ValueError(policy)
        if policy=='two_channel_kg_terminal':
            last=remaining<2*min(costs);scores[last]*=np.asarray(costs)
    scores=np.where(np.asarray(costs)[None,None,:]<=remaining[:,None,None],scores,-np.inf)
    best=np.argmax(scores.reshape(reps,-1),axis=1)
    available=np.isfinite(scores.reshape(reps,-1)[np.arange(reps),best])
    result=(best//2,best%2,available)
    return (*result,scores) if return_scores else result


def masks(values,groups):
    result=np.zeros(values.shape,dtype=bool)
    for r,row in enumerate(values):
        for group in sorted(set(groups)):
            ids=np.flatnonzero(groups==group);k=max(1,int(.2*len(ids)))
            result[r,sorted(ids,key=lambda i:(row[i],i))[:k]]=True
    return result


def independent_metrics(mean,cov,truth,groups):
    a,b=masks(mean[:,:,0],groups),masks(truth,groups)
    k=a.sum(axis=1)
    return dict(regret=np.array([(truth[r,a[r]].sum()-truth[r,b[r]].sum())/k[r] for r in range(len(a))]),
                overlap=(a&b).sum(axis=1)/k,mse=((mean[:,:,0]-truth)**2).mean(axis=1),
                coverage=(abs(mean[:,:,0]-truth)<=norm.ppf(.975)*np.sqrt(cov[:,:,0,0])).mean(axis=1),
                selected_size=k)


def ref_run(data,policy,cal,budget,cost,seed,groups,expected_trace=None,branch_audit=None):
    reps,units=data['initial'].shape
    m=np.zeros((reps,units,2));m[:,:,0]=cal['mu']
    cov=np.zeros((reps,units,2,2));cov[:,:,0,0]=cal['tau']**2
    if policy not in {'uniform_blind','bias_blind_kg'}:
        m[:,:,1]=cal['bias_mean'];cov[:,:,1,1]=np.asarray(cal['beta'])**2
    m,cov=matrix_update(m,cov,np.array([1.,1.]),data['initial'],np.asarray(cal['ordinary_variance'])/20)
    n=np.zeros((reps,units,2),dtype=int);n[:,:,0]=1
    counters=np.zeros((reps,units,2),dtype=int)
    remaining=np.full(reps,budget,dtype=int);costs=np.array([1,cost]);rng=np.random.default_rng(seed)
    trace=[];noise=np.broadcast_to(np.asarray(cal['ordinary_variance'])/20,(units,))
    audit_noise=np.broadcast_to(np.asarray(cal['validation_variance'])/20,(units,))
    for step in range(budget):
        unit,channel,available,scores=ref_choices(m,cov,policy,groups,remaining,costs,noise,audit_noise,rng,True)
        if expected_trace is not None:
            original_unit,original_channel,original_available=expected_trace[step]
            np.testing.assert_array_equal(available,original_available)
            rr=np.flatnonzero(available)
            best_value=scores.reshape(reps,-1).max(axis=1)[rr]
            chosen_value=scores[rr,original_unit[rr],original_channel[rr]]
            deficiency=best_value-chosen_value
            assert np.all(np.isfinite(chosen_value))
            assert np.all(deficiency<=2e-12*np.maximum(1,abs(best_value)))
            different=rr[(unit[rr]!=original_unit[rr])|(channel[rr]!=original_channel[rr])]
            if len(different):
                assert policy in {'ordinary_kg','two_channel_kg'}
                if branch_audit is not None:
                    branch_audit.append(dict(step=step,replications=different.tolist(),
                        largest_independent_KG_deficiency=float(deficiency.max()),
                        interpretation='Original trace retained only after independent greedy-value verification; full-matrix rounding may resolve a numerical tie differently'))
            unit,channel=original_unit,original_channel
        trace.append((unit.copy(),channel.copy(),available.copy()))
        rr=np.flatnonzero(available)
        if len(rr)==0:break
        ii,cc=unit[rr],channel[rr];kk=counters[rr,ii,cc]
        observations=np.array([data['ordinary' if c==0 else 'validation'][r,i,k] for r,i,c,k in zip(rr,ii,cc,kk)])
        loading=np.column_stack((np.ones(len(rr)),1-cc))
        updated_m,updated_cov=matrix_update(m[rr,ii],cov[rr,ii],loading,observations,
                                            np.where(cc==0,noise[ii],audit_noise[ii]))
        m[rr,ii]=updated_m;cov[rr,ii]=updated_cov
        n[rr,ii,cc]+=1;counters[rr,ii,cc]+=1;remaining[rr]-=costs[cc]
        assert np.all(remaining>=0)
        assert np.linalg.eigvalsh(cov).min()>-2e-13
    metric=independent_metrics(m,cov,data['truth'],groups)
    metric.update(spent=budget-remaining,regular_packets=counters[:,:,0].sum(axis=1),
                  validation_packets=counters[:,:,1].sum(axis=1),
                  validation_fraction=counters[:,:,1].sum(axis=1)*cost/budget,
                  posterior_sd=np.sqrt(cov[:,:,0,0]).mean(axis=1))
    total_signal=cov[:,:,0,0]+cov[:,:,1,1]+2*cov[:,:,0,1]
    decrease=np.divide((cov[:,:,0,0]+cov[:,:,0,1])**2,total_signal,out=np.zeros_like(total_signal),where=total_signal>1e-30)
    metric['repeat_floor']=np.maximum(0,cov[:,:,0,0]-decrease).mean(axis=1)
    return metric,m,cov,n,trace


def capture(module,function,*args,**kwargs):
    original_choose=module.choose_actions;original_performance=module.performance
    trace=[];final={}
    def chooser(*a,**kw):
        result=original_choose(*a,**kw);trace.append(tuple(x.copy() for x in result));return result
    def evaluation(mean,var,truth,groups,*a,**kw):
        final['mean']=mean.copy();final['variance']=var.copy()
        return original_performance(mean,var,truth,groups,*a,**kw)
    module.choose_actions=chooser;module.performance=evaluation
    try: result=function(*args,**kwargs)
    finally:module.choose_actions=original_choose;module.performance=original_performance
    return result,trace,final


def check_trace(actual,expected):
    assert len(actual)==len(expected)
    for aa,ee in zip(actual,expected):
        for a,e in zip(aa,ee):np.testing.assert_array_equal(a,e)


def check_updates_and_value():
    rng=np.random.default_rng(270911)
    reps,units=7,5
    state=subject.Belief.prior(reps,units,mu=4.9,tau=.7,beta=.4)
    mean=np.zeros((reps,units,2));mean[:,:,0]=4.9
    cov=np.broadcast_to(np.diag([.7**2,.4**2]),(reps,units,2,2)).copy()
    initial=rng.normal(5,.8,(reps,units));noise=rng.uniform(.1,.6,(reps,units))
    state.update_all_ordinary(initial,noise,20)
    mean,cov=matrix_update(mean,cov,np.array([1.,1.]),initial,noise)
    largest=0.
    for _ in range(100):
        rows=np.arange(reps);unit=rng.integers(units,size=reps);channel=rng.integers(2,size=reps)
        obs=rng.normal(5,1,size=reps);v=rng.uniform(.02,1,size=reps)
        state.update(rows,unit,channel,obs,v,20)
        mm,pp=matrix_update(mean[rows,unit],cov[rows,unit],np.column_stack((np.ones(reps),1-channel)),obs,v)
        mean[rows,unit]=mm;cov[rows,unit]=pp
        for a,b in [(state.mean,mean[:,:,0]),(state.bias_mean,mean[:,:,1]),(state.target_var,cov[:,:,0,0]),
                    (state.bias_var,cov[:,:,1,1]),(state.cross,cov[:,:,0,1])]:
            close(a,b);largest=max(largest,float(np.max(abs(a-b))))
        assert np.linalg.eigvalsh(cov).min()>-1e-13
    errors=[]
    for _ in range(80):
        m=rng.normal(size=8);k=int(rng.integers(1,8));i=int(rng.integers(8));sd=float(rng.uniform(.03,2))
        threshold=np.sort(np.delete(m,i))[k-1];before=np.sort(m)[:k].sum()
        def integrand(z):
            updated=m.copy();updated[i]+=sd*z
            return (before-np.sort(updated)[:k].sum())*norm.pdf(z)
        kink=(threshold-m[i])/sd
        value,_=quad(integrand,-12,12,points=[kink] if abs(kink)<12 else None,epsabs=2e-11)
        actual=float(subject.gaussian_improvement(np.array([m[i]-threshold]),np.array([sd]))[0])
        errors.append(abs(value-actual))
    assert max(errors)<2e-9
    # One selected slot per group of one makes every action's decision value zero.
    close(subject.gaussian_improvement(np.array([np.inf,0.,100.]),np.array([1.,0.,1.])),[0.,0.,0.])
    return dict(sequential_matrix_updates=700,max_state_error=largest,
                terminal_sum_quadrature_cases=80,max_terminal_value_error=max(errors),
                scope='Gain applies to terminal sum of selected means; division by fixed total k does not change action argmax')


def independent_histograms(year,weighted=False):
    counts={};sizes=Counter();support=(30-np.arange(31))/3
    with (ROOT/f'data/processed/brfss_employed_{year}.csv').open() as stream:
        for r in csv.DictReader(stream):
            counts.setdefault(r['state'],np.zeros(31))[int(r['mental_unhealthy_days'])]+=float(r['weight']) if weighted else 1
            sizes[r['state']]+=1
    states=sorted(counts);p=np.array([counts[s]/sum(counts[s]) for s in states])
    means=np.array([sum(prob*support) for prob in p])
    variance=np.array([sum(prob*(support-mu)**2) for prob,mu in zip(p,means)])
    return dict(states=states,prob=p,support=support,mean=means,variance=variance,n=np.array([sizes[s] for s in states]))


def independent_calibration(past,kappa):
    locations=[];biases=[];noises=[]
    for prob,mu,var in zip(past['prob'],past['mean'],past['variance']):
        offset=[];sampling_var=[]
        for sign in (1,-1):
            unnormalised=prob*np.exp(sign*kappa*past['support']/np.sqrt(var))
            p=unnormalised/unnormalised.sum()
            location=sum(p*past['support'])
            offset.append(location-mu);sampling_var.append(sum(p*(past['support']-location)**2))
        locations.append(sum(offset)/2);biases.append(abs(offset[0]-offset[1])/2);noises.append(sum(sampling_var)/2)
    return dict(mu=float(past['mean'].mean()),tau=float(past['mean'].std(ddof=1)),
                bias_mean=np.array(locations),beta=np.array(biases),ordinary_variance=np.array(noises),
                validation_variance=past['variance'])


def check_small_paths():
    data=synthetic.world(901,5,12,17,beta=.35)
    groups=np.repeat(np.arange(4),3)
    cal=dict(mu=5.,tau=.35,beta=.35,bias_mean=0.,ordinary_variance=6.25,validation_variance=6.25)
    cases=0
    for policy in synthetic.POLICIES:
        for budget,cost in [(7,5),(17,2)]:
            expected,m,cov,n,trace=ref_run(data,policy,cal,budget,cost,404,groups)
            actual,actual_trace,final=capture(synthetic,synthetic.run_policy,data,policy,budget,cost,seed=404,groups=groups)
            check_trace(actual_trace,trace)
            close(final['mean'],m[:,:,0]);close(final['variance'],cov[:,:,0,0])
            for key in actual:close(actual[key],expected[key])
            assert np.all(actual['spent']==actual['regular_packets']+cost*actual['validation_packets'])
            assert np.all(n.sum(axis=(1,2))*20==12*20+(actual['regular_packets']+actual['validation_packets'])*20)
            cases+=1
    return dict(synthetic_policy_budget_cases=cases,replications_each=5,all_action_traces_and_posterior_fields_match=True)


def check_replay_and_no_leakage():
    past=independent_histograms(2023)
    current=independent_histograms(2024)
    # Altering mean metadata cannot affect draws: backend probabilities encode
    # the frame and past scales alone define the tilt. It changes only evaluation.
    ref=independent_calibration(past,.5)
    cal=replay.calibration(replay.load_histograms(2023),.5)
    for key in cal:close(cal[key],ref[key])
    d=replay.make_replay(current,past,991,4,19,kappa=.5)
    altered=dict(current,mean=10-current['mean'],variance=current['variance']*999,n=current['n']*7)
    dd=replay.make_replay(altered,past,991,4,19,kappa=.5)
    for key in ('initial','ordinary','validation'):np.testing.assert_array_equal(d[key],dd[key])
    assert not np.array_equal(d['truth'],dd['truth'])
    groups=np.zeros(48,dtype=int);cases=0;changed_evaluations=0
    for policy in synthetic.POLICIES:
        expected,m,cov,n,trace=ref_run(d,policy,ref,19,5,721,groups)
        (metric,state),actual_trace,final=capture(replay,replay.run_replay,d,policy,cal,19,5,721)
        check_trace(actual_trace,trace)
        close(final['mean'],m[:,:,0]);close(final['variance'],cov[:,:,0,0])
        close(state.bias_mean,m[:,:,1]);close(state.bias_var,cov[:,:,1,1]);close(state.cross,cov[:,:,0,1])
        close(state.ordinary_n,n[:,:,0]*20);close(state.validation_n,n[:,:,1]*20)
        for key in metric:close(metric[key],expected[key])
        (mm,ss),changed_trace,changed_final=capture(replay,replay.run_replay,dd,policy,cal,19,5,721)
        check_trace(changed_trace,actual_trace)
        for key in final:np.testing.assert_array_equal(final[key],changed_final[key])
        np.testing.assert_array_equal(ss.mean,state.mean)
        assert not np.array_equal(mm['mse'],metric['mse'])
        changed_evaluations+=1;cases+=1
    # A sample mean from weight-proportional iid draws targets the full weighted
    # finite distribution. It does not compute a ratio of a uniformly sampled subset.
    weighted=independent_histograms(2023,True)
    actual_weighted=replay.load_histograms(2023,True)
    close(weighted['prob'],actual_weighted['prob']);close(weighted['mean'],actual_weighted['mean'])
    return dict(replay_policy_cases=cases,replications_each=4,
                independent_2023_calibration_matches=True,
                oracle_metadata_perturbation_all_draw_streams_actions_and_posteriors_unchanged=True,
                oracle_perturbation_changed_evaluations=changed_evaluations,
                weighted_histogram_reference_matches=True)


def check_sampling_and_saved_calibration():
    # Quantile sampling of a histogram must reproduce uniform record draws
    # when records are ordered by outcome. Zero-frequency bins are included.
    records=np.array([10.,10.,4.,1.,1.,1.])
    support=np.array([10.,7.,4.,1.]);prob=np.array([2.,0.,1.,3.])/6
    uniforms=np.random.default_rng(510).random((7,11,20))
    expected=records[np.floor(uniforms*len(records)).astype(int)].mean(axis=2)
    actual=replay.packet_stream(prob,support,np.random.default_rng(510),7,11,20)
    np.testing.assert_array_equal(actual,expected)
    with (ROOT/'results/replay_calibration.csv').open() as stream:
        rows=list(csv.DictReader(stream))
    settings={'unweighted_uniform':(False,0.),'unweighted_tilt_025':(False,.25),
              'unweighted_tilt_05':(False,.5),'weighted_tilt_05':(True,.5),
              'validation_tilt_025':(False,.5)}
    loaded={w:independent_histograms(2023,w) for w in (False,True)}
    computed={name:independent_calibration(loaded[w],k) for name,(w,k) in settings.items()}
    for row in rows:
        name=row['scenario'];state=row['state'];ref=computed[name]
        i=loaded[settings[name][0]]['states'].index(state)
        for key in ('mu','tau'):close(float(row[key]),ref[key])
        for output,key in [('bias_mean','bias_mean'),('bias_sd','beta'),('ordinary_variance','ordinary_variance'),('validation_variance','validation_variance')]:
            close(float(row[output]),ref[key][i])
    assert len(rows)==240
    return dict(histogram_vs_uniform_record_packets=77,draws_per_packet=20,
                zero_probability_bin_checked=True,saved_2023_calibration_rows_independently_checked=len(rows))


def summarised(values):
    values=np.asarray(values);mean=float(np.mean(values));se=float(np.std(values,ddof=1)/np.sqrt(len(values)))
    return dict(mean=mean,mcse=se,lo=mean-1.96*se,hi=mean+1.96*se)


def check_saved_rows():
    """Reproduce bounded selected saved rows, not the complete experiment suite."""
    checked=[]
    with (ROOT/'results/synthetic.csv').open() as stream:synthetic_rows=list(csv.DictReader(stream))
    manifest=json.loads((ROOT/'results/synthetic_manifest.json').read_text())
    # Exact same full world size is required: NumPy stream layout depends on it.
    data=synthetic.world(manifest['seed']+2,manifest['reps'],40,120,beta=.35)
    cal=dict(mu=5.,tau=.35,beta=.35,bias_mean=0.,ordinary_variance=6.25,validation_variance=6.25)
    for policy in ('ordinary_kg','two_channel_kg'):
        _,executed_trace,_=capture(synthetic,synthetic.run_policy,data,policy,40,5,seed=manifest['seed']+102)
        branches=[]
        metric,*_=ref_run(data,policy,cal,40,5,manifest['seed']+102,np.repeat(np.arange(4),10),executed_trace,branches)
        row=next(r for r in synthetic_rows if r['policy']==policy and float(r['bias_sd'])==.35 and int(r['budget'])==40 and int(r['audit_cost'])==5)
        for key in ('regret','overlap','mse','coverage','spent','validation_fraction','posterior_sd','repeat_floor'):
            for label,value in summarised(metric[key]).items():close(float(row[f'{key}_{label}']),value)
        checked.append(dict(dataset='synthetic',policy=policy,reps=manifest['reps'],budget=40,audit_cost=5,
                            independent_regret_mean=float(metric['regret'].mean()),numerical_tie_branch_checks=branches))
    del data
    with (ROOT/'results/replay.csv').open() as stream:replay_rows=list(csv.DictReader(stream))
    manifest=json.loads((ROOT/'results/replay_manifest.json').read_text())
    past=independent_histograms(2023);current=independent_histograms(2024)
    cal=independent_calibration(past,.5)
    # Use the original backend only to reproduce the already checked packet
    # sampling stream; beliefs, selection, costs and metrics are independent.
    data=replay.make_replay(current,past,manifest['seed']+2,manifest['reps'],144,kappa=.5)
    for policy in ('ordinary_kg','two_channel_kg'):
        original_cal=replay.calibration(replay.load_histograms(2023),.5)
        _,executed_trace,_=capture(replay,replay.run_replay,data,policy,original_cal,48,5,manifest['seed']+102)
        branches=[]
        metric,*_=ref_run(data,policy,cal,48,5,manifest['seed']+102,np.zeros(48,dtype=int),executed_trace,branches)
        row=next(r for r in replay_rows if r['policy']==policy and r['scenario']=='unweighted_tilt_05' and int(r['budget'])==48 and int(r['audit_cost'])==5)
        for key in ('regret','overlap','mse','coverage','spent','validation_fraction','posterior_sd'):
            for label,value in summarised(metric[key]).items():close(float(row[f'{key}_{label}']),value)
        checked.append(dict(dataset='replay',policy=policy,reps=manifest['reps'],budget=48,audit_cost=5,
                            independent_regret_mean=float(metric['regret'].mean()),numerical_tie_branch_checks=branches))
    return checked


def main():
    paths=[ROOT/'experiments'/n for n in ('allocation.py','synthetic.py','replay.py','common.py')]
    paths+=sorted(p for p in (ROOT/'results').glob('*') if p.is_file())
    paths+=[ROOT/f'data/processed/brfss_employed_{year}.csv' for year in (2023,2024)]
    before={str(p.relative_to(ROOT)):sha(p) for p in paths}
    result=dict(status='passed',run_at_utc=datetime.now(timezone.utc).isoformat(),
                matrix_and_value_checks=check_updates_and_value(),small_synthetic_paths=check_small_paths(),
                replay_and_information_flow=check_replay_and_no_leakage(),
                sampling_and_calibration=check_sampling_and_saved_calibration(),saved_rows=check_saved_rows())
    assert before=={str(p.relative_to(ROOT)):sha(p) for p in paths}, 'Protected inputs/results changed during audit'
    result.update(protected_files_unchanged=True,protected_sha256=before,verifier_sha256=sha(Path(__file__)),
                  scope='Independent implementation/finite-file checks; not global budget optimality, clinical validation, or a guarantee of real-world posterior coverage')
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
