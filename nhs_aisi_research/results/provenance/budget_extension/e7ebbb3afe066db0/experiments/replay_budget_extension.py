"""Post-primary-run exploratory BRFSS budget extension; fixed protocol/grid.

Reuses the original replay functions; never edits primary files. All simulated
draws, including streams across budgets, are paired by replication index.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import resource
import shutil
import sys
import time
import numpy as np
import pandas as pd
from common import ROOT, sha, summarise, write_csv
from replay import load_histograms, calibration, make_replay, run_replay

REPS = 500
SEED = 2026091121
BUDGETS = [48, 144, 480, 1440]
POLICIES = ['ordinary_kg', 'two_channel_kg', 'balanced_mix', 'validation_only', 'uniform']
MEMORY_LIMIT_BYTES = 2_000_000_000


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def peak_rss_bytes():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(rss if sys.platform == 'darwin' else rss * 1024)


def check_memory():
    peak = peak_rss_bytes()
    if peak >= MEMORY_LIMIT_BYTES:
        raise RuntimeError(f'Peak RSS {peak} exceeded declared task bound')
    return peak


def main():
    start = time.perf_counter()
    started = utcnow()
    protocol = ROOT / 'docs/budget_extension_protocol.md'
    assert protocol.is_file(), 'Record the extension protocol before running.'
    primary_files = ['results/replay.csv', 'results/replay_manifest.json',
                     'results/replay_calibration.csv', 'results/replay_allocations.csv',
                     'experiments/replay.py', 'experiments/allocation.py', 'experiments/common.py']
    primary_before = {name: sha(ROOT / name) for name in primary_files}
    source_names = ['experiments/replay_budget_extension.py', 'experiments/replay.py',
                    'experiments/allocation.py', 'experiments/common.py', 'experiments/synthetic.py',
                    'docs/budget_extension_protocol.md']
    source_hashes = {name: sha(ROOT / name) for name in source_names}
    signature = hashlib.sha256(json.dumps(source_hashes, sort_keys=True).encode()).hexdigest()[:16]
    snapshot = ROOT / 'results/provenance/budget_extension' / signature
    for name in source_names:
        target = snapshot / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)

    past = load_histograms(2023, weighted=False)
    current = load_histograms(2024, weighted=False)
    assert len(current['states']) == 48 and current['states'] == past['states']
    cal = calibration(past, 0.5)
    data = make_replay(current, past, SEED, REPS, max(BUDGETS), kappa=0.5,
                       packet=20, n0=20, validation_kappa=0.0)
    bank_bytes = int(data['ordinary'].nbytes + data['validation'].nbytes)
    print(f'Paired packet bank ready: {bank_bytes:,} bytes; '
          f'peak RSS {check_memory():,}; elapsed {time.perf_counter()-start:.2f}s', flush=True)
    rows, allocations, raw = [], [], {}
    for budget in BUDGETS:
        metrics = {}
        setting = dict(analysis_stage='post_primary_exploratory',
                       scenario='unweighted_tilt_05', weighted=False, kappa=0.5,
                       validation_kappa=0.0, audit_cost=5, budget=budget, units=48, k=9)
        budget_rows = []
        for policy in POLICIES:
            result, state = run_replay(data, policy, cal, budget, 5, SEED + 100)
            assert np.all(result['selected_size'] == 9)
            assert np.all(result['spent'] <= budget)
            metrics[policy] = result
            row = dict(**setting, policy=policy, reps=REPS)
            for name, values in result.items():
                raw[f'b{budget}__{policy}__{name}'] = np.asarray(values)
                if name != 'selected_size':
                    row.update({f'{name}_{key}': val for key, val in summarise(values).items()})
            budget_rows.append(row)
            for i, area in enumerate(current['states']):
                allocations.append(dict(**setting, policy=policy, state=area,
                                        ordinary_count_mean=float(state.ordinary_n[:, i].mean()),
                                        validation_count_mean=float(state.validation_n[:, i].mean()),
                                        mean_estimate=float(state.mean[:, i].mean()),
                                        reference=float(current['mean'][i])))
            del state
            check_memory()
            print(f'Completed B={budget}, policy={policy}, '
                  f'regret={row["regret_mean"]:.6f}, elapsed={time.perf_counter()-start:.2f}s', flush=True)
        for row in budget_rows:
            for baseline in ['ordinary_kg', 'uniform']:
                for name in ['regret', 'overlap']:
                    difference = metrics[row['policy']][name] - metrics[baseline][name]
                    row.update({f'{name}_diff_{baseline}_{key}': value
                                for key, value in summarise(difference).items()})
        rows.extend(budget_rows)
    result_dir = ROOT / 'results'
    stem = 'replay_budget_extension'
    write_csv(result_dir / f'{stem}.csv', rows)
    write_csv(result_dir / f'{stem}_allocations.csv', allocations)
    calibration_rows = [dict(state=state, mu=cal['mu'], tau=cal['tau'],
                             bias_mean=cal['bias_mean'][i], bias_sd=cal['beta'][i],
                             ordinary_variance=cal['ordinary_variance'][i],
                             validation_variance=cal['validation_variance'][i])
                        for i, state in enumerate(past['states'])]
    write_csv(result_dir / f'{stem}_calibration.csv', calibration_rows)
    np.savez_compressed(result_dir / f'{stem}_replication_metrics.npz', **raw)
    primary_after = {name: sha(ROOT / name) for name in primary_files}
    assert primary_before == primary_after, 'An original source/result changed during this extension.'
    details = dict(completed=True, analysis_stage='post-primary-run exploratory',
                   started_at_utc=started, completed_at_utc=utcnow(),
                   elapsed_seconds=time.perf_counter() - start,
                   reps=REPS, backend_seed=SEED, policy_seed=SEED + 100,
                   budgets=BUDGETS, audit_cost=5, policies=POLICIES,
                   kappa=0.5, validation_kappa=0.0, weighted=False,
                   units=48, selected_units=9, packet_draws=20, initial_draws_per_area=20,
                   peak_rss_bytes=check_memory(), memory_limit_bytes=MEMORY_LIMIT_BYTES,
                   packet_bank_bytes=bank_bytes, policies_and_budgets_share_streams=True,
                   original_primary_result_and_function_hashes_preserved=True,
                   primary_sha256=primary_before,
                   source_sha256=source_hashes,
                   source_snapshot=str(snapshot.relative_to(ROOT)),
                   source_sha256_data={str(p['path'].relative_to(ROOT)): sha(p['path'])
                                       for p in [past, current]},
                   python=platform.python_version(), numpy=np.__version__,
                   platform=platform.platform(),
                   intervals='Monte Carlo mean +/- 1.96 MCSE, conditional on fixed frame/scenario',
                   posterior='Working Gaussian target/offset model; not exact finite-frame posterior',
                   real_additional_respondents_recruited=False)
    artifacts = [result_dir / f'{stem}{suffix}' for suffix in
                 ['.csv', '_allocations.csv', '_calibration.csv', '_replication_metrics.npz']]
    details['output_sha256'] = {str(p.relative_to(ROOT)): sha(p) for p in artifacts}
    (result_dir / f'{stem}_manifest.json').write_text(json.dumps(details, indent=2) + '\n')
    print(json.dumps({key: details[key] for key in ['completed', 'elapsed_seconds', 'peak_rss_bytes',
                                                   'original_primary_result_and_function_hashes_preserved']},
                     indent=2), flush=True)


if __name__ == '__main__':
    main()
