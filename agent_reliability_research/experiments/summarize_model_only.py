#!/usr/bin/env python3
"""Descriptive summaries of the frozen model-only extension, no selection."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'results/model_only'
paired=list(csv.DictReader((out/'paired_comparisons.csv').open()))
summary=list(csv.DictReader((out/'summary.csv').open()))
comparisons=[]
for baseline in ['whole_group_cv','rr_fixed']:
 for regime in ['all','calibrated','overconfident','shifted']:
    rr=[r for r in paired if r['baseline']==baseline and (regime=='all' or r['regime']==regime)]
    row=dict(baseline=baseline,regime=regime,settings=len(rr))
    for metric in ['coefficient_mse','gradient_mse']:
        ratio=np.array([float(r[metric+'_ratio_of_means']) for r in rr])
        row[metric]=dict(wins=int((ratio<1).sum()),median_ratio=float(np.median(ratio)),
            min_ratio=float(ratio.min()),max_ratio=float(ratio.max()))
    comparisons.append(row)
timing=[]
for g in [4,8,16]:
 for method in ['whole_group_cv','rr_fixed','rr_model']:
    rr=[r for r in summary if int(r['g'])==g and r['method']==method]
    row=dict(g=g,method=method)
    for k in ['schedule_cpu_seconds','expected_completion_cpu_seconds','total_algorithm_cpu_seconds','complete_group_probability']:
        row[k]=float(np.mean([float(r[k]) for r in rr]))
    timing.append(row)
result=dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'paired_comparisons.csv',out/'summary.csv']},
    comparisons=comparisons,timing=timing,
    caution='Descriptive wins and ratios across the entire grid; settings are not independent because budgets share groups. No multiplicity-adjusted significance claim.')
(out/'descriptive_summary.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
