"""Historical-vintage backtest with separately archived predictor releases."""
import json
import time
import numpy as np
import pandas as pd
from common import ROOT,save_csv,save_manifest,file_hash
from empirical import PHI,RATIOS,load_panel,predict,score,bootstrap_differences,reporting_entity_ids

def main():
    start=time.perf_counter()
    primary=ROOT/'data/processed/nhs_staff_survey_panel_2021_2025.csv'
    vintage=ROOT/'vintage_data/benchmark_vintage_panel.csv'
    frame,y,_,meta,cohort=load_panel(primary)
    archive=pd.read_csv(vintage,dtype={'org_code':str})
    codes=list(meta.index)
    matrices={};sizes={};groups_by_vintage={}
    for version,last in [(2023,2023),(2024,2024)]:
        part=archive[(archive.release_vintage==version)&archive.org_code.isin(codes)&archive.year.between(2021,last)].copy()
        assert len(part)==len(codes)*(last-2020)
        assert (part.historically_comparable==1).all() and (part.is_trust==1).all()
        assert not part.duplicated(['org_code','year']).any()
        years=list(range(2021,last+1))
        matrices[version]=part.pivot(index='org_code',columns='year',values='burnout_score').loc[codes,years].to_numpy(float)
        sizes[version]=part.pivot(index='org_code',columns='year',values='burnout_n').loc[codes,years].to_numpy(float)
        groups_by_vintage[version]=part[part.year==last].set_index('org_code').loc[codes,'benchmark_group'].to_numpy()
        assert np.isfinite(matrices[version]).all() and np.isfinite(sizes[version]).all()
    groups=meta.benchmark_group.to_numpy()
    assert np.array_equal(groups_by_vintage[2023],groups) and np.array_equal(groups_by_vintage[2024],groups)
    output=ROOT/'results/vintage';output.mkdir(parents=True,exist_ok=True)
    candidates=[(m,None,None) for m in ['latest','equal_history','group_centred_equal','linear_trend']]
    candidates += [('geometric_history',p,None) for p in PHI]
    candidates += [('group_mean_reversion',p,None) for p in PHI]
    candidates += [('working_covariance',p,r) for p in PHI for r in RATIOS]
    dev=[];chosen={};dev_target=matrices[2024][:,-1]
    for ordinal,(method,phi,ratio) in enumerate(candidates):
        prediction=predict(matrices[2023],sizes[2023],groups_by_vintage[2023],method,phi,ratio)
        mse=float(np.mean((prediction-dev_target)**2))
        row=dict(candidate_order=ordinal,method=method,phi=phi,ratio=ratio,development_mse=mse)
        dev.append(row)
        if method not in chosen or mse<chosen[method]['development_mse']-1e-14:chosen[method]=row
    save_csv(output/'development_grid.csv',dev)
    (output/'selected_hyperparameters.json').write_text(json.dumps(chosen,indent=2)+'\n')
    predictions={m:predict(matrices[2024],sizes[2024],groups_by_vintage[2024],m,c['phi'],c['ratio']) for m,c in chosen.items()}
    test=y[:,4];records=[]
    for i,code in enumerate(codes):
        row=dict(org_code=code,org_name=meta.loc[code,'org_name'],benchmark_group=groups[i],
                 observed_2024=float(matrices[2024][i,-1]),observed_2025=float(test[i]))
        row.update({m:float(p[i]) for m,p in predictions.items()});records.append(row)
    save_csv(output/'frozen_2025_predictions.csv',records)
    save_csv(output/'test_metrics.csv',[dict(method=m,**score(test,p,groups)) for m,p in predictions.items()])
    save_csv(output/'paired_bootstrap.csv',bootstrap_differences(test,predictions,groups,entity_ids=reporting_entity_ids(codes)))
    rows=[]
    for group in np.unique(groups):
        ids=groups==group
        for m,p in predictions.items():rows.append(dict(benchmark_group=group,units=int(ids.sum()),method=m,**score(test[ids],p[ids],groups[ids])))
    save_csv(output/'group_test_metrics.csv',rows)
    revisions=[]
    for version in [2023,2024]:
        length=version-2020;difference=matrices[version]-y[:,:length]
        for i,code in enumerate(codes):
            for t in range(length):
                revisions.append(dict(org_code=code,year=2021+t,release_vintage=version,
                                      historical_value=float(matrices[version][i,t]),
                                      value_in_2025_release=float(y[i,t]),difference=float(difference[i,t])))
    save_csv(output/'score_revisions.csv',revisions)
    save_manifest(output/'manifest.json',dict(completed=True,cohort=cohort,units=len(codes),
                    historical_workbook_panel_sha256=file_hash(vintage),target_panel_sha256=file_hash(primary),
                    development_predictor_release=2023,development_target_release=2024,
                    test_predictor_release=2024,test_target_release=2025,
                    training_target_years=[2024,2025],candidate_count=len(candidates),
                    bootstrap_entity_clusters=len(np.unique(reporting_entity_ids(codes))),
                    source='Archived NHS official benchmark workbooks; hashes/capture times in vintage_data manifests',
                    interpretation='Retrospective backtest respecting captured historical predictor vintages; not a prospectively deployed prediction',
                    elapsed_seconds=time.perf_counter()-start))
    print(json.dumps({'completed':'vintage','units':len(codes),'methods':len(chosen)},indent=2))

if __name__=='__main__':main()
