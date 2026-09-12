"""Fixed temporal evaluation and transparent static-rank sensitivity."""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from common import ROOT, save_csv, save_manifest, file_hash, static_shrinkage, first_membership_crossing, pair_crossings

PHI = [0., .3, .6, .85, .97, 1.]
RATIOS = [0., 10., 30., 100., 300., 1000., 3000.]

def load_panel(path):
    frame=pd.read_csv(path,dtype={'org_code':str})
    required=['org_code','org_name','year','benchmark_group','burnout_score','burnout_n','is_trust']
    assert set(required)<=set(frame.columns),set(required)-set(frame.columns)
    frame=frame[frame.is_trust==1].copy()
    assert not frame.duplicated(['org_code','year']).any()
    all_codes=sorted(frame.org_code.unique())
    included=[];excluded=[]
    for code,g in frame.groupby('org_code',sort=True):
        valid=g[g.year.isin(range(2021,2026))].sort_values('year')
        okay=(valid.year.tolist()==list(range(2021,2026)) and
              valid[['burnout_score','burnout_n']].notna().all().all() and
              (valid.burnout_n>0).all() and valid.benchmark_group.nunique()==1)
        if 'historically_comparable' in valid:
            okay=okay and (valid.historically_comparable==1).all()
        (included if okay else excluded).append(code)
    selected=frame[frame.org_code.isin(included)].sort_values(['org_code','year'])
    y=selected.pivot(index='org_code',columns='year',values='burnout_score').loc[included,list(range(2021,2026))].to_numpy(float)
    n=selected.pivot(index='org_code',columns='year',values='burnout_n').loc[included,list(range(2021,2026))].to_numpy(float)
    meta=selected[selected.year==2025].set_index('org_code').loc[included]
    assert np.isfinite(y).all() and ((y>=0)&(y<=10)).all()
    return selected,y,n,meta,{'trust_reporting_codes':len(all_codes),'included':included,'excluded':excluded}

def group_means(y,groups):
    result=np.empty_like(y,dtype=float)
    for group in np.unique(groups):
        ids=groups==group;result[ids]=y[ids].mean(axis=0)
    return result

def predict(y,n,groups,method,phi=None,ratio=None):
    """One-step predictions; no target-year values enter this function."""
    length=y.shape[1];mu=group_means(y,groups);z=y-mu
    if method=='latest':return y[:,-1].copy()
    if method=='equal_history':return y.mean(axis=1)
    if method=='group_centred_equal':return mu[:,-1]+z.mean(axis=1)
    if method=='linear_trend':
        x=np.arange(length);xc=x-x.mean()
        slopes=y@xc/(xc@xc)
        return y.mean(axis=1)+slopes*(length-x.mean())
    if method=='geometric_history':
        w=phi**np.arange(length-1,-1,-1,dtype=float);w/=w.sum()
        return y@w
    if method=='group_mean_reversion':return mu[:,-1]+phi*z[:,-1]
    if method=='working_covariance':
        t=np.arange(length);C=phi**np.abs(t[:,None]-t[None,:])
        matrices=np.broadcast_to(C,(len(y),length,length)).copy()
        matrices[:,t,t]+=ratio/n
        c=phi**np.arange(length,0,-1,dtype=float)
        weights=np.einsum('t,ntj->nj',c,np.linalg.pinv(matrices,rcond=1e-12))
        return mu[:,-1]+np.sum(weights*z,axis=1)
    raise ValueError(method)

def select_within(values,groups,fraction):
    selected=[]
    for group in np.unique(groups):
        ids=np.flatnonzero(groups==group);k=max(1,int(len(ids)*fraction))
        selected.extend(ids[np.argsort(values[ids],kind='stable')[:k]])
    return np.array(selected,dtype=int)

def score(y,pred,groups):
    error=pred-y
    result={'rmse':float(np.sqrt(np.mean(error**2))),
            'mae':float(np.mean(np.abs(error))),
            'spearman':float(spearmanr(y,pred).statistic)}
    for fraction in [.1,.2,.3]:
        actual=set(select_within(y,groups,fraction));chosen=set(select_within(pred,groups,fraction))
        result[f'observed_overlap_{fraction:.1f}']=len(actual&chosen)/len(actual)
    return result

def reporting_entity_ids(codes):
    return np.array(['R1F' if code in {'R1F1','R1F2'} else code for code in codes])

def bootstrap_differences(y,predictions,groups,reps=5000,entity_ids=None):
    rng=np.random.default_rng(2026091103)
    if entity_ids is None:
        entity_ids=np.arange(len(y))
    clusters,inverse=np.unique(entity_ids,return_inverse=True)
    draws=rng.multinomial(len(clusters),np.ones(len(clusters))/len(clusters),size=reps)
    weights=draws[:,inverse]
    denominator=weights.sum(axis=1)
    base=predictions['latest']-y; out=[]
    for name,pred in predictions.items():
        error=pred-y
        dr=np.sqrt((weights@(error**2))/denominator)-np.sqrt((weights@(base**2))/denominator)
        dm=(weights@np.abs(error))/denominator-(weights@np.abs(base))/denominator
        out.append(dict(method=name,bootstrap_repetitions=reps,
                        resampling_clusters=len(clusters),resampling_unit='known legal entity',
                        rmse_difference=float(np.sqrt(np.mean(error**2))-np.sqrt(np.mean(base**2))),
                        rmse_difference_lo=float(np.quantile(dr,.025)),rmse_difference_hi=float(np.quantile(dr,.975)),
                        mae_difference=float(np.mean(abs(error))-np.mean(abs(base))),
                        mae_difference_lo=float(np.quantile(dm,.025)),mae_difference_hi=float(np.quantile(dm,.975))))
    return out

def followup(y,groups):
    mu=group_means(y,groups);z=y-mu;rows=[]
    for t in range(4):
        chosen=select_within(y[:,t],groups,.2)
        change=y[:,t+1]-y[:,t]
        group_change=mu[:,t+1]-mu[:,t]
        rows.append(dict(selection_year=2021+t,followup_year=2022+t,selected_units=len(chosen),
                         baseline_mean=float(y[chosen,t].mean()),followup_mean=float(y[chosen,t+1].mean()),
                         observed_selected_change=float(change[chosen].mean()),
                         corresponding_group_change=float(group_change[chosen].mean()),
                         group_centred_change=float((change-group_change)[chosen].mean()),
                         retained_in_next_observed_bottom=float(len(set(chosen)&set(select_within(y[:,t+1],groups,.2)))/len(chosen))))
    return rows

def sensitivity(y,n,groups,meta):
    centred=y[:,-1]-group_means(y,groups)[:,-1]
    raw=set(select_within(centred,groups,.2));sets=[];membership=[];thresholds=[]
    # Include all exact crossing intervals, not just plotted grid points.
    all_endpoints={0.,3000.}
    for group in np.unique(groups):
        ids=np.flatnonzero(groups==group);k=max(1,int(len(ids)*.2))
        crossings=pair_crossings(centred[ids],n[ids,-1],3000)
        all_endpoints.update(v for v,_,_ in crossings)
        first=first_membership_crossing(centred[ids],n[ids,-1],k)
        thresholds.append(dict(benchmark_group=group,units=len(ids),k=k,
                               first_membership_crossing=None if np.isinf(first) else first,
                               stable_through_3000=bool(first>3000),pair_crossings_0_3000=len(crossings)))
    sorted_endpoints=sorted(all_endpoints)
    probes=sorted(set(RATIOS+sorted_endpoints+[(a+b)/2 for a,b in zip(sorted_endpoints[:-1],sorted_endpoints[1:])]))
    union=set();intersection=None
    for ratio in probes:
        scores=static_shrinkage(centred,n[:,-1],ratio)
        chosen=set(select_within(scores,groups,.2))
        union.update(chosen);intersection=chosen if intersection is None else intersection&chosen
        if ratio in RATIOS:
            sets.append(dict(ratio=ratio,selected=len(chosen),retained_from_raw=len(raw&chosen),
                             overlap_with_raw=len(raw&chosen)/len(raw),changed_members=len(raw-chosen)))
            for i in range(len(meta)):
                membership.append(dict(org_code=meta.index[i],org_name=meta.iloc[i].org_name,
                                       benchmark_group=groups[i],ratio=ratio,
                                       centred_score=float(centred[i]),burnout_n=float(n[i,-1]),
                                       working_posterior_score=float(scores[i]),selected=int(i in chosen)))
    envelope=[]
    for i in range(len(meta)):
        envelope.append(dict(org_code=meta.index[i],org_name=meta.iloc[i].org_name,
                             benchmark_group=groups[i],raw_selected=int(i in raw),
                             selected_somewhere_0_3000=int(i in union),selected_everywhere_0_3000=int(i in intersection),
                             boundary_ties='stable organisation-code order'))
    return sets,membership,thresholds,envelope

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--panel',type=Path,default=ROOT/'data/processed/nhs_staff_survey_panel_2021_2025.csv')
    parser.add_argument('--prefix',default='harmonised')
    args=parser.parse_args();start=time.perf_counter()
    frame,y,n,meta,cohort=load_panel(args.panel);groups=meta.benchmark_group.to_numpy()
    output=ROOT/'results'/args.prefix;output.mkdir(parents=True,exist_ok=True)
    frame.to_csv(output/'analysis_cohort.csv',index=False)
    candidates=[]
    for method in ['latest','equal_history','group_centred_equal','linear_trend']:
        candidates.append((method,None,None))
    candidates.extend(('geometric_history',phi,None) for phi in PHI)
    candidates.extend(('group_mean_reversion',phi,None) for phi in PHI)
    candidates.extend(('working_covariance',phi,ratio) for phi in PHI for ratio in RATIOS)
    dev=[];chosen={}
    for ordinal,(method,phi,ratio) in enumerate(candidates):
        prediction=predict(y[:,:3],n[:,:3],groups,method,phi,ratio)
        mse=float(np.mean((prediction-y[:,3])**2))
        row=dict(candidate_order=ordinal,method=method,phi=phi,ratio=ratio,development_mse=mse)
        dev.append(row)
        if method not in chosen or mse < chosen[method]['development_mse']-1e-14:
            chosen[method]=row
    save_csv(output/'development_grid.csv',dev)
    (output/'selected_hyperparameters.json').write_text(json.dumps(chosen,indent=2)+'\n')
    # All model settings are fixed here before any 2025 performance calculation.
    predictions={name:predict(y[:,:4],n[:,:4],groups,name,info['phi'],info['ratio'])
                 for name,info in chosen.items()}
    records=[]
    for i,code in enumerate(meta.index):
        row=dict(org_code=code,org_name=meta.iloc[i].org_name,benchmark_group=groups[i],
                 observed_2024=float(y[i,3]),observed_2025=float(y[i,4]))
        row.update({name:float(pred[i]) for name,pred in predictions.items()});records.append(row)
    save_csv(output/'frozen_2025_predictions.csv',records)
    save_csv(output/'test_metrics.csv',[dict(method=name,**score(y[:,4],pred,groups)) for name,pred in predictions.items()])
    save_csv(output/'paired_bootstrap.csv',bootstrap_differences(y[:,4],predictions,groups,entity_ids=reporting_entity_ids(meta.index)))
    group_rows=[]
    for group in np.unique(groups):
        ids=groups==group
        for name,pred in predictions.items():
            group_rows.append(dict(benchmark_group=group,units=int(ids.sum()),method=name,
                                   **score(y[ids,4],pred[ids],groups[ids])))
    save_csv(output/'group_test_metrics.csv',group_rows)
    save_csv(output/'observational_followup.csv',followup(y,groups))
    summaries,membership,thresholds,envelope=sensitivity(y,n,groups,meta)
    save_csv(output/'rank_sensitivity.csv',summaries);save_csv(output/'rank_membership.csv',membership)
    save_csv(output/'rank_thresholds.csv',thresholds);save_csv(output/'rank_envelope.csv',envelope)
    save_manifest(output/'manifest.json',dict(completed=True,panel_path=str(args.panel.relative_to(ROOT)),
                   panel_sha256=file_hash(args.panel),prefix=args.prefix,cohort=cohort,
                   organisation_years=len(frame),development_target=2024,test_target=2025,
                   candidate_count=len(candidates),methods=len(chosen),bootstrap_repetitions=5000,
                   bootstrap_entity_clusters=len(np.unique(reporting_entity_ids(meta.index))),
                   interpretation='Prediction of observed scores; not identification of latent need or causal benefit',
                   elapsed_seconds=time.perf_counter()-start))
    print(json.dumps({'completed':args.prefix,'units':len(meta),'method_count':len(chosen)},indent=2))

if __name__=='__main__':main()
