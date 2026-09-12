"""Conditional information-action illustration, NOT observed NHS resurvey results.

Nominal respondent counts, assumed respondent SD and persistent-offset SDs do
not identify effective precision or real response bias. No future data are drawn.
"""
import numpy as np
import pandas as pd
from allocation import Belief, gaussian_improvement
from common import ROOT, selected, thresholds, write_csv, manifest, sha

def main():
    source=ROOT/'data/processed/nhs_staff_survey_panel_2021_2025.csv'
    frame=pd.read_csv(source)
    frame=frame.loc[frame.year.eq(2025)&frame.is_trust.eq(1)&frame.complete_five_year_history.eq(1)&frame.burnout_score.notna()].sort_values('org_code').reset_index(drop=True)
    groups=pd.factorize(frame.benchmark_group,sort=True)[0]
    score=frame.burnout_score.to_numpy();n=frame.burnout_n.to_numpy()
    mu=frame.groupby('benchmark_group').burnout_score.transform('mean').to_numpy()
    rows=[];summaries=[]
    # All grid values are sensitivity assumptions. ESS multipliers are not estimates.
    for ess_factor in [1.,.25]:
        for beta in [0.,.15,.35,.7]:
            state=Belief.prior(1,len(frame),mu=mu,tau=.35,beta=beta)
            state.update_all_ordinary(score[None,:],2.5**2/(n*ess_factor),n*ess_factor)
            mask=selected(state.mean,groups)[0];K=int(mask.sum())
            cutoff=thresholds(state.mean,groups)
            sd=state.innovation_sd(2.5**2/20,2.5**2/20)
            gain=gaussian_improvement((state.mean-cutoff)[:,:,None],sd)[0]/K
            ratios=gain/np.array([1.,5.])
            best=np.argmax(ratios,axis=1);rank=np.argsort(np.argsort(-ratios.max(axis=1),kind='stable'),kind='stable')+1
            for i,record in frame.iterrows():
                rows.append(dict(org_code=record.org_code,org_name=record.org_name,benchmark_group=record.benchmark_group,
                  ess_factor=ess_factor,assumed_beta=beta,assumed_tau=.35,assumed_individual_sd=2.5,
                  nominal_burnout_n=int(n[i]),observed_burnout=score[i],posterior_mean=state.mean[0,i],
                  posterior_sd=np.sqrt(state.target_var[0,i]),repeat_floor_sd=np.sqrt(state.ordinary_uncertainty_floor()[0,i]),
                  selected=bool(mask[i]),review_slots=K,ordinary_KG=gain[i,0],validation_KG=gain[i,1],
                  ordinary_KG_per_cost=ratios[i,0],validation_KG_per_cost=ratios[i,1],
                  preferred_channel='validation' if best[i] else 'ordinary',action_priority_rank=int(rank[i]),
                  evidence_type='model_conditional_scenario_no_new_NHS_observations'))
            top=np.argsort(-ratios.max(axis=1),kind='stable')[:20]
            summaries.append(dict(ess_factor=ess_factor,assumed_beta=beta,units=len(frame),review_slots=K,
              median_nominal_n=float(np.median(n)),mean_posterior_sd=float(np.sqrt(state.target_var).mean()),
              mean_repeat_floor_sd=float(np.sqrt(state.ordinary_uncertainty_floor()).mean()),
              top20_validation_preferred=int((best[top]==1).sum()),
              greatest_one_step_KG_per_cost=float(ratios.max()),
              evidence_type='model_conditional_scenario_no_new_NHS_observations'))
    write_csv(ROOT/'results/nhs_scenarios.csv',rows)
    write_csv(ROOT/'results/nhs_scenario_summary.csv',summaries)
    manifest(ROOT/'results/nhs_scenario_manifest.json',dict(source_sha256_data={str(source.relative_to(ROOT)):sha(source)},
      assumptions='2025 group-mean plug-in centre; tau=.35, individual SD=2.5, packet20, validation cost5; no new observations; nominal n times sensitivity factor, not estimated ESS',
      grid={'ess_factor':[1.,.25],'beta':[0.,.15,.35,.7]}))
    print(pd.DataFrame(summaries).to_string(index=False))

if __name__=='__main__':main()
