"""Reproducible reporting correction; leaves the original run untouched."""
import csv, hashlib, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'results/estimation';out=ROOT/'results/estimation_corrected';out.mkdir(exist_ok=True)
rows=list(csv.DictReader((src/'per_group.csv').open()))
for r in rows:
    r['base_rate_parameter']=r.pop('prevalence')
    if r['method'] in ('ht_then_normalize','partial_then_normalize'):
        r['complete_group_probability']=float(r['budget'])**int(r['g'])
    m=1024
    for bias,mse in [('conditional_bias_sq','coefficient_mse'),('gradient_bias_sq','gradient_mse')]:
        b=float(r[bias]);a=float(r[mse])
        r[bias+'_mc_corrected']=(m*b-a)/(m-1) if r['expectation_mode']=='Monte Carlo audit masks' else b
with (out/'per_group.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
groups={}
for r in rows:groups.setdefault((r['setting'],r['budget'],r['method']),[]).append(r)
summary=[]
keys=['coefficient_mse','conditional_bias_sq_mc_corrected','gradient_mse','gradient_bias_sq_mc_corrected','expected_cost','complete_group_probability']
for _,rs in groups.items():
    rec={k:rs[0][k] for k in ['setting','g','base_rate_parameter','regime','budget','method','expectation_mode']};rec['groups']=len(rs)
    for k in keys:
        x=np.array([float(r[k]) for r in rs]);rec[k]=x.mean();rec[k+'_se']=x.std(ddof=1)/np.sqrt(len(x))
    summary.append(rec)
with (out/'summary.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
manifest={'status':'complete','operation':'post-run reporting correction; no new experimental observations',
 'source_sha256':hashlib.sha256((src/'per_group.csv').read_bytes()).hexdigest(),
 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'changes':['Independent audit full-group probability is budget**G','Prevalence renamed base-rate parameter',
 'G16 squared conditional bias receives signed finite-MC U-statistic correction; negatives not clipped'],
 'rows':len(rows),'summary_rows':len(summary)}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
