"""Summarize and audit all frozen stateful runs without further training."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/stateful_training'
read=lambda name:list(csv.DictReader((OUT/name).open()))
summary,paired,training,evaluation,query_view=map(read,
    ('summary.csv','paired_endpoint.csv','training.csv','evaluation.csv','query_ceiling_view.csv'))
manifest=json.loads((OUT/'manifest.json').read_text())
T9=2.262157162798205
endpoints=[r for r in summary if int(r['update'])==300]
comparisons=[]
for r in paired:
    if r['method']=='rr_completion' and r['baseline'] in ('full','whole_group_residual'):
        mean,se=float(r['success_difference']),float(r['paired_seed_se'])
        comparisons.append(dict(horizon=int(r['horizon']),baseline=r['baseline'],difference=mean,
                                paired_seed_se=se,pointwise_t95=[mean-T9*se,mean+T9*se]))
hash_checks={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest
             for name,digest in manifest['numeric_sha256'].items()}
source_checks={name:hashlib.sha256((OUT/'executed_source'/name).read_bytes()).hexdigest()==digest
               for name,digest in manifest['source_sha256'].items()}
assert all(hash_checks.values()) and all(source_checks.values())
assert len(training)==180*300 and len(evaluation)==180*13
ledger_queries=0
ledger_trajectories=0
actions=0
task_banks={}
initial_reports={}
npz_count=0
for path in sorted((OUT/'trajectories').glob('*.npz')):
    data=np.load(path,allow_pickle=False)
    h=int(path.stem.split('_h')[-1].split('_s')[0])
    seed=int(path.stem.split('_s')[-1])
    mask=data['purchased_mask']
    truth=data['reference_rewards_offline']
    proxy=data['cheap_rewards']
    assert data['actions'].shape==(300,8,h)
    assert np.all((truth==0)|(truth==1)) and np.all((proxy==0)|(proxy==1))
    assert np.all(truth<=proxy)
    assert np.all(data['purchased_labels'][mask]==truth[mask])
    assert np.all(data['purchased_labels'][~mask]==-1)
    assert not np.any(mask&(proxy==0))
    assert np.all(np.isfinite(data['policy_weights']))
    assert np.all(np.isfinite(data['split_coefficients']))
    key=h,seed
    if key in task_banks:
        assert np.array_equal(task_banks[key],data['changed_component'])
        assert np.array_equal(initial_reports[key],data['reporting_reference'][0])
    else:
        task_banks[key]=data['changed_component'].copy()
        initial_reports[key]=data['reporting_reference'][0].copy()
    ledger_queries+=int(mask.sum())
    ledger_trajectories+=truth.size
    actions+=data['actions'].size
    npz_count+=1
assert npz_count==180
assert ledger_queries==sum(int(r['purchased_queries']) for r in training)
assert ledger_queries==sum(r['purchased_reference_queries'] for r in manifest['runs'])
timings=[]
for method in sorted({r['method'] for r in manifest['runs']}):
    rows=[r for r in manifest['runs'] if r['method']==method]
    timings.append(dict(method=method,
                        training_seconds=sum(r['timings'][k] for r in rows for k in
                                             ('rollout_seconds','estimation_seconds','optimization_seconds')),
                        estimation_seconds=sum(r['timings']['estimation_seconds'] for r in rows),
                        purchased_queries=sum(r['purchased_reference_queries'] for r in rows)))
view=[]
for h in (12,24,48):
    for method in sorted({r['method'] for r in query_view}):
        rows=[r for r in query_view if int(r['horizon'])==h and r['method']==method]
        view.append(dict(horizon=h,method=method,
                         mean_success=float(np.mean([float(r['reference_success']) for r in rows])),
                         mean_actual_queries=float(np.mean([float(r['actual_queries']) for r in rows])),
                         mean_updates=float(np.mean([float(r['update']) for r in rows])),
                         ceiling=float(rows[0]['shared_query_ceiling'])))
checks=dict(status='passed',numeric_hashes=hash_checks,executed_source_hashes=source_checks,
            npz_runs=npz_count,training_rows=len(training),evaluation_rows=len(evaluation),
            purchased_labels_match_offline_replay=True,unbought_labels_masked=True,
            paired_task_streams_match=True,paired_initial_evaluation_matches=True,
            training_trajectories=ledger_trajectories,training_tool_actions=actions,
            purchased_training_reference_queries=ledger_queries,
            all_policy_weights_and_coefficients_finite=True,
            maximum_gradient_norm=max(float(r['gradient_norm']) for r in training),
            clipped_updates=sum(float(r['gradient_clip_factor'])<1 for r in training))
report=dict(scope='Frozen complete constructed stateful training; no LLM result.',
            endpoints=endpoints,paired_rr_comparisons=comparisons,
            interval_note='Pointwise Student t intervals over 10 paired training seeds, df=9; no multiplicity adjustment or noninferiority test.',
            timing=timings,descriptive_query_ceiling_view=view,checks=checks,
            wall_seconds=manifest['wall_seconds'])
(ROOT/'results/stateful_result_summary.json').write_text(json.dumps(report,indent=2)+'\n')

lines=['# Constructed stateful training: complete result record','',
       'Executed 2026-09-12 with the frozen protocol: 6 methods × 3 horizons × 10 seeds × 300 updates, group size 8. All 180 runs completed. This is actual NumPy softmax policy optimization over deterministic stateful tools, with a scripted initial policy; it is not an LLM or public software benchmark.','',
       f'Complete wall time: {manifest["wall_seconds"]:.3f} seconds. Training generated {ledger_trajectories:,} trajectories and executed {actions:,} tool actions.','',
       '## Same-rollout endpoints','',
       'All rows use 2,400 training trajectories per run. Success is stochastic reference-verifier success on independent reporting episodes, averaged over 10 training seeds. SE is across seeds. Purchased queries are the per-run average; certified cheap negatives are free under all methods.','',
       '| H | Method | Reference success ± seed SE | Cheap success | Purchased queries |','|---:|---|---:|---:|---:|']
for r in endpoints:
    lines.append(f'| {r["horizon"]} | {r["method"]} | {100*float(r["reference_success_mean"]):.2f}% ± {100*float(r["reference_success_seed_se"]):.2f} pp | {100*float(r["cheap_success_mean"]):.2f}% | {float(r["mean_purchased_queries"]):.1f} |')
lines+=['','## Paired comparisons and limits','',
        '| H | RR minus baseline | Difference, pp | Pointwise 95% t interval, pp |',
        '|---:|---|---:|---:|']
for r in comparisons:
    lo,hi=r['pointwise_t95']
    lines.append(f'| {r["horizon"]} | {r["baseline"]} | {100*r["difference"]:+.3f} | [{100*lo:+.3f}, {100*hi:+.3f}] |')
lines+=['',
        'RR and whole-group residual have close mean performance; all three pointwise RR-minus-whole-group intervals include zero. This study does not establish a distinct benefit from the fixed sequential schedule. RR also has slightly lower mean success than full-label training at every horizon; intervals overlapping zero are not proof of equivalence or non-regression.',
        '',
        'Proxy optimization reaches high cheap-check scores while reference success can remain low or deteriorate. This demonstrates the specified omitted-invariant mechanism in the constructed environment, not general evidence about deceptive intent or all real-world verifiers.',
        '',
        'The model-only analytical diagnostic, computed after smoke without outcome labels, gives Q_j=.5 for every candidate count M=1,...,8. Under this homogeneous p=.55 completion model and Euclidean coefficient metric, the monotone variance-optimal schedule is exactly whole-group residual correction. This is a meaningful degeneration boundary, not a reason to alter the frozen primary run.',
        '',
        '## Real time and query accounting','',
        '| Method | Training seconds, summed over 30 runs | Estimation seconds | Purchased labels |',
        '|---|---:|---:|---:|']
for r in timings:
    lines.append(f'| {r["method"]} | {r["training_seconds"]:.3f} | {r["estimation_seconds"]:.3f} | {r["purchased_queries"]:,} |')
lines+=['',
        'The reference checker is extremely cheap here. RR has higher measured local training time than full verification and whole-group residual; reduced query count is not an end-to-end speedup. No synthetic sleep or artificial latency was added. These are diagnostic wall times on a shared host with a fixed method order, not an isolated randomized systems benchmark.',
        '',
        f'Purchased training checks: {ledger_queries:,}. Separately counted reporting checks: {sum(r["reporting_reference_queries"] for r in manifest["runs"]):,}. Post-training offline diagnostic checks: {sum(r["offline_diagnostic_reference_queries"] for r in manifest["runs"]):,}. The latter labels were generated only after each complete optimization run and did not enter its updates.',
        '',
        'The secondary `query_ceiling_view.csv` selects actual recorded checkpoints below a common descriptive ceiling and reports actual query/rollout counts. It is not an exactly matched-budget experiment; sparse checkpoints leave unequal unspent budget, and methods that buy fewer labels may execute more training trajectories. It must not be used to claim equal total compute.',
        '',
        '## Independent checks and artifacts','',
        f'All six numerical CSV hashes and all four executed-source snapshots match the run manifest. All {npz_count} trajectory banks have finite coefficients/weights; query masks match purchased labels and independent post-run replay truth; no cheap-negative label is bought. Task streams and initial reporting outcomes match across paired methods. Maximum observed gradient norm {checks["maximum_gradient_norm"]:.6f}; clipped updates {checks["clipped_updates"]}/{len(training)}.',
        '',
        'Before full training, held-action score finite differences agreed to 1.40e-11, and exact integration over every RR stopping cutoff on generated releases agreed with the complete sign-split target to 4.44e-16. These checks do not claim independent re-execution of all 180 training runs.',
        '',
        'Primary outputs: `results/stateful_training/{training,evaluation,summary,paired_endpoint,query_ceiling_view}.csv`, `manifest.json`, all action/policy/label banks under `trajectories/`, and the exact executed source under `executed_source/`. Machine-readable summary and ledger audit: `results/stateful_result_summary.json`.',
        '',
        'The initial greedy policy already follows the known repair workflow. Reported improvement concerns stochastic execution reliability in this task family. Reporting draws are independent episodes, not unseen repositories or newly held-out task structures. Horizon and dependency-chain size co-vary, so their separate effects are not identified.']
# The runner currently writes five numeric CSVs; report this from the manifest.
lines=[s.replace('All six numerical CSV hashes',f'All {len(hash_checks)} numerical CSV hashes') for s in lines]
(ROOT/'docs/stateful_results.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(checks=checks,paired=comparisons),indent=2))
