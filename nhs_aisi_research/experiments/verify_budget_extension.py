"""Independently recompute stored exploratory summaries from per-replay metrics."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root / 'results'
    manifest = json.loads((folder / 'replay_budget_extension_manifest.json').read_text())
    summary = pd.read_csv(folder / 'replay_budget_extension.csv')
    raw = np.load(folder / 'replay_budget_extension_replication_metrics.npz')
    assert len(summary) == 20 and not summary.duplicated(['budget', 'policy']).any()
    assert sorted(summary.budget.unique().tolist()) == [48, 144, 480, 1440]
    assert set(summary.policy) == set(manifest['policies'])
    errors = []
    for _, row in summary.iterrows():
        prefix = f'b{row.budget}__{row.policy}__'
        for name in ['regret', 'overlap']:
            values = raw[prefix + name]
            assert len(values) == 500
            errors.extend([abs(values.mean() - row[f'{name}_mean']),
                           abs(values.std(ddof=1) / np.sqrt(500) - row[f'{name}_mcse'])])
            for baseline in ['ordinary_kg', 'uniform']:
                differences = values - raw[f'b{row.budget}__{baseline}__{name}']
                mean = differences.mean()
                mcse = differences.std(ddof=1) / np.sqrt(500)
                for key, expected in [('mean', mean), ('mcse', mcse),
                                      ('lo', mean - 1.96 * mcse), ('hi', mean + 1.96 * mcse)]:
                    errors.append(abs(expected - row[f'{name}_diff_{baseline}_{key}']))
        assert np.all(raw[prefix + 'selected_size'] == 9)
        assert np.all(raw[prefix + 'spent'] <= row.budget)
    assert max(errors) < 1e-14
    cal = pd.read_csv(folder / 'replay_budget_extension_calibration.csv', dtype={'state': str})
    old = pd.read_csv(folder / 'replay_calibration.csv', dtype={'state': str})
    old = old[old.scenario == 'unweighted_tilt_05'].drop(columns='scenario').reset_index(drop=True)
    assert list(cal.state) == list(old.state)
    cal_error = float(np.max(np.abs(cal.drop(columns='state').to_numpy()
                                   - old.drop(columns='state').to_numpy())))
    assert cal_error == 0
    output_hashes_match = all(digest(root / name) == value
                              for name, value in manifest['output_sha256'].items())
    primary_hashes_match = all(digest(root / name) == value
                               for name, value in manifest['primary_sha256'].items())
    assert output_hashes_match and primary_hashes_match
    assert manifest['peak_rss_bytes'] < 2_000_000_000
    result = dict(status='all_checks_passed', full_grid_rows=20,
                  unique_paired_replications=500,
                  max_independent_summary_and_interval_error=float(max(errors)),
                  frozen_2023_calibration_discrepancy=cal_error,
                  output_hashes_match=output_hashes_match,
                  original_primary_hashes_still_match=primary_hashes_match,
                  peak_rss_bytes=manifest['peak_rss_bytes'],
                  verified_manifest_sha256=digest(folder / 'replay_budget_extension_manifest.json'),
                  verifier_sha256=digest(Path(__file__)))
    (folder / 'replay_budget_extension_verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
