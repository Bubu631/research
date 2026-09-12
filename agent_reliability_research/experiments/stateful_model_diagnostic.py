"""Post-smoke analytical diagnostic; no outcomes or training parameters fitted.

The fixed homogeneous completion prior used in stateful_training can make the
model-optimal monotone schedule coincide with whole-group residual correction.
The metric is coefficient-vector squared error under the completion model, not
actual policy-gradient MSE or downstream training success.
"""
from pathlib import Path
import sys
import json
import hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.reward_audit import predicted_increment_variances,variance_optimal_survival

rows=[]
for m in range(1,9):
    p=np.r_[np.full(m,.55),np.zeros(8-m)]
    variance,_=predicted_increment_variances(p)
    q=variance_optimal_survival(variance[:m],np.ones(m),.5*m)
    rows.append(dict(unknown_candidates=m,known_negative_labels=8-m,
                     prior_probability=.55, increment_second_moments=variance[:m].tolist(),
                     model_optimal_survival=q.tolist(),
                     matches_whole_group_residual=bool(np.allclose(q,.5,atol=1e-12,rtol=0))))
result=dict(scope=__doc__.strip(),diagnostic_timing='after smoke, during frozen primary training; no outcome labels used',
            group_size=8,rows=rows,
            source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [Path(__file__),ROOT/'src/reward_audit.py']})
out=ROOT/'results/stateful_model_diagnostic.json'
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(output=str(out),all_match_whole_group=all(r['matches_whole_group_residual'] for r in rows))))
