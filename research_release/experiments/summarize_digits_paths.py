#!/usr/bin/env python3
"""Audit saved predictions and render both completed digits paths without fitting."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.datasets import load_digits

import digits_upgrade as base

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT/'papers/base_upgrade/results'
PATHS = [('Selective', RESULTS), ('Balanced', RESULTS/'digits_balanced')]
POLICIES = ['incumbent', 'updated', 'scalar', 'layer', 'released']
LABELS = ['Incumbent', 'Continued checkpoint', 'Scalar proposal', 'Layer proposal', 'Released']


def read_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def main():
    data = load_digits()
    x, y = data.data.astype(np.float64)/16, data.target
    aggregate, per_seed, inputs = [], [], {}
    for label, path in PATHS:
        manifest = json.loads((path/'digits_manifest.json').read_text())
        inputs[str((path/'digits_manifest.json').relative_to(ROOT))] = hashlib.sha256(
            (path/'digits_manifest.json').read_bytes()).hexdigest()
        if label == 'Balanced':
            for filename, expected in manifest['output_sha256'].items():
                assert hashlib.sha256((path/filename).read_bytes()).hexdigest() == expected
        summary, certrows = read_csv(path/'digits_summary.csv'), read_csv(path/'digits_certification.csv')
        for seed in base.CONFIG['seeds']:
            rows = {r['policy']: r for r in summary if int(r['seed']) == seed}
            with np.load(path/f'digits_seed_{seed}.npz') as saved:
                report, cert = saved['reporting_ids'], saved['certification_ids']
                old = [saved[f'old_parameter_{i}'] for i in range(4)]
                new = [saved[f'new_parameter_{i}'] for i in range(4)]
                np.testing.assert_array_equal(base.predictions(old, x[report]),
                                               saved['incumbent_report_prediction'])
                np.testing.assert_array_equal(base.predictions(new, x[report]),
                                               saved['updated_report_prediction'])
                base_scores = np.array([np.mean(saved['incumbent_report_prediction'][y[report] == k] == k)
                                        for k in range(10)])
                for policy in POLICIES:
                    pred = saved[policy+'_report_prediction']
                    scores = np.array([np.mean(pred[y[report] == k] == k) for k in range(10)])
                    np.testing.assert_allclose([np.mean(pred == y[report]), scores@np.array(base.CONFIG['objective_weights']),
                                                 np.min(scores-base_scores)],
                        [float(rows[policy][m]) for m in ['accuracy', 'weighted_accuracy', 'worst_slice_difference']],
                        atol=1e-14, rtol=0)
                delta = ((saved['selected_cert_prediction'] == y[cert]).astype(float)
                         -(saved['old_cert_prediction'] == y[cert]).astype(float))
                lower = []
                for k in range(10):
                    dk = delta[y[cert] == k]
                    val = dk.mean()-np.sqrt(2*np.log(20)/len(dk))
                    cr = next(r for r in certrows if int(r['seed']) == seed and int(r['slice']) == k)
                    np.testing.assert_allclose(val, float(cr['lower']), atol=1e-14, rtol=0)
                    assert (val >= -.03) == (cr['passed'] == 'True')
                    lower.append(val)
                r = rows['released']
                gate = all(v >= -.03 for v in lower) or (float(r['selected_coeff0']) == 0 and float(r['selected_coeff1']) == 0)
                assert gate == (r['certification_passed'] == 'True')
                if not gate:
                    np.testing.assert_array_equal(saved['released_report_prediction'], saved['incumbent_report_prediction'])
                chosen = rows[r['selected_policy']]
                per_seed.append(dict(path=label, seed=seed,
                    incumbent_accuracy=float(rows['incumbent']['accuracy']),
                    updated_accuracy=float(rows['updated']['accuracy']),
                    scalar_accuracy=float(rows['scalar']['accuracy']),
                    layer_accuracy=float(rows['layer']['accuracy']),
                    chosen_policy=r['selected_policy'], chosen_coeff0=float(r['selected_coeff0']),
                    chosen_coeff1=float(r['selected_coeff1']),
                    chosen_accuracy=float(chosen['accuracy']),
                    chosen_worst_slice_difference=float(chosen['worst_slice_difference']),
                    minimum_certification_lower_bound=min(lower), gate_passed=gate))
        for policy in POLICIES:
            rr = [r for r in summary if r['policy'] == policy]
            record = dict(path=label, policy=policy)
            for metric in ['accuracy', 'weighted_accuracy', 'worst_slice_difference']:
                vals = [float(r[metric]) for r in rr]
                record[metric+'_mean'] = float(np.mean(vals))
                record[metric+'_seed_sd'] = float(np.std(vals, ddof=1))
                record[metric+'_minimum'] = float(np.min(vals))
            aggregate.append(record)
    base.write_csv(RESULTS/'digits_path_comparison.csv', aggregate)
    base.write_csv(RESULTS/'digits_path_all_seeds.csv', per_seed)
    lines = [r'\begin{tabular}{llrrr}', r'\toprule',
             r'Path & Model & Accuracy & Weighted accuracy & Worst slice $\Delta$ \\', r'\midrule']
    for path, _ in PATHS:
        for policy, name in zip(POLICIES, LABELS):
            row = next(r for r in aggregate if r['path'] == path and r['policy'] == policy)
            cells = [path if policy == 'incumbent' else '', name]
            for metric in ['accuracy', 'weighted_accuracy', 'worst_slice_difference']:
                cells.append(f"${row[metric+'_mean']:.4f}\\pm{row[metric+'_seed_sd']:.4f}$")
            lines.append(' & '.join(cells)+r' \\')
        if path == 'Selective':
            lines.append(r'\midrule')
    lines += [r'\bottomrule', r'\end{tabular}']
    (RESULTS/'digits_path_comparison.tex').write_text('\n'.join(lines)+'\n')
    lines = [r'\begin{tabular}{lrrrrlrr}', r'\toprule',
             r'Path/seed & Old & Updated & Scalar & Layer & Chosen $(\lambda_1,\lambda_2)$ & Min.\ $\Delta$ & Gate \\',
             r'\midrule']
    for i, row in enumerate(per_seed):
        label = ('S' if row['path'] == 'Selective' else 'B')+f"/{row['seed']}"
        vals = [label]+[f"{row[m+'_accuracy']:.4f}" for m in ['incumbent', 'updated', 'scalar', 'layer']]
        vals += [f"{row['chosen_policy'][0].upper()} $({row['chosen_coeff0']:.3f},{row['chosen_coeff1']:.3f})$",
                 f"{row['chosen_worst_slice_difference']:.4f}", 'Pass' if row['gate_passed'] else 'Fail']
        lines.append(' & '.join(vals)+r' \\')
        if i == 4:
            lines.append(r'\midrule')
    lines += [r'\bottomrule', r'\end{tabular}']
    (RESULTS/'digits_path_all_seeds.tex').write_text('\n'.join(lines)+'\n')
    outputs = {name: hashlib.sha256((RESULTS/name).read_bytes()).hexdigest()
               for name in ['digits_path_comparison.csv', 'digits_path_all_seeds.csv',
                            'digits_path_comparison.tex', 'digits_path_all_seeds.tex']}
    audit = dict(prediction_and_gate_recalculation='passed_all_10_seed_path_runs',
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_manifest_sha256=inputs, output_sha256=outputs,
        interpretation='Subsequent balanced path reuses existing holdouts: descriptive, not a new confirmatory certification.')
    (RESULTS/'digits_path_comparison_manifest.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps(dict(audit=audit, all_seeds=per_seed), indent=2))


if __name__ == '__main__':
    main()
