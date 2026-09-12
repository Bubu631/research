#!/usr/bin/env python3
"""Subsequent descriptive balanced-continuation path; protocol fixed before run."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.datasets import load_digits

import digits_upgrade as base

ROOT = Path(__file__).resolve().parents[1]
CONFIG = dict(base.CONFIG, continuation_classes=list(range(10)))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'papers/base_upgrade/results/digits_balanced')
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    dataset = load_digits()
    x, y = dataset.data.astype(np.float64)/16.0, dataset.target
    assert all(CONFIG[k] == v for k, v in base.CONFIG.items()
               if k != 'continuation_classes')
    assert CONFIG['continuation_classes'] == list(range(10))
    snapshots = {}
    for label, path in [('executed_script.py', Path(__file__).resolve()),
                        ('digits_upgrade_helper.py', Path(base.__file__).resolve()),
                        ('executed_protocol.md', ROOT/'docs/digits_balanced_protocol.md')]:
        shutil.copyfile(path, out/label)
        snapshots[label] = sha256(out/label)
    manifest = dict(status='in_progress',
        study='Subsequent descriptive balanced-continuation public digits experiment',
        started_utc=datetime.now(timezone.utc).isoformat(), config=CONFIG,
        protocol_and_source_sha256=snapshots,
        dataset='sklearn.datasets.load_digits; 1797 examples; 64 features; classes 0-9',
        dataset_sha256=hashlib.sha256(x.tobytes()+y.tobytes()).hexdigest(),
        dataset_original='https://archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits',
        versions=dict(python=platform.python_version(), numpy=np.__version__,
                      sklearn=sklearn.__version__),
        caveats=[
            'Protocol fixed after the original selective-continuation study was reviewed.',
            'Both paths use 24 epochs; balanced training has approximately twice the minibatch updates.',
            'Certification/reporting data are reused from the original study: descriptive, not fresh confirmatory certification.',
            'Five seeds share one underlying dataset; seed SD is descriptive, not an independent confidence interval.',
            'No parameters or protocol choices revised after outcomes; every fixed seed is retained.',
            'Small public MLP study, not a foundation-model or translation result.'])
    (out/'manifest_in_progress.json').write_text(json.dumps(manifest, indent=2)+'\n')
    rows, slice_rows, cert_rows, search_rows, loss_rows, ancestry = [], [], [], [], [], []
    for seed in CONFIG['seeds']:
        rng = np.random.default_rng(seed)
        splits = base.split_indices(y, seed)
        tr, dev, cert, report = (splits[k] for k in
            ['train', 'development', 'certification', 'reporting'])
        old, old_loss = base.train(base.initialize(rng), x[tr], y[tr],
                                   CONFIG['old_epochs'], rng)
        original_path = ROOT/f'papers/base_upgrade/results/digits_seed_{seed}.npz'
        with np.load(original_path) as original:
            for k, ids in splits.items():
                np.testing.assert_array_equal(ids, original[k+'_ids'])
            max_diff = max(float(np.max(np.abs(p-original[f'old_parameter_{i}'])))
                           for i, p in enumerate(old))
            if max_diff > 1e-12:
                raise AssertionError(f'Incumbent recreation differs: {max_diff}')
        ancestry.append(dict(seed=seed, original_checkpoint_sha256=sha256(original_path),
                             incumbent_max_abs_recreation_difference=max_diff,
                             split_identity_verified=True))
        updated_ids = tr  # Frozen sole training-path change: continue on all classes.
        new, new_loss = base.train(old, x[updated_ids], y[updated_ids],
                                   CONFIG['continuation_epochs'], rng)
        scalar, scalar_search = base.select_on_development(old, new, x[dev], y[dev],
            [(v, v) for v in np.linspace(0, 1, CONFIG['scalar_candidates'])])
        layer, layer_search = base.select_on_development(old, new, x[dev], y[dev],
            [(a, b) for a in np.linspace(0, 1, CONFIG['layer_grid'])
                    for b in np.linspace(0, 1, CONFIG['layer_grid'])])
        selected_name, selected = max([('scalar', scalar), ('layer', layer)],
            key=lambda z: (z[1]['utility'], z[1]['min_margin'],
                           -z[1]['coeff0']-z[1]['coeff1'], z[0] == 'scalar'))
        coeff = (selected['coeff0'], selected['coeff1'])
        selected_model = base.merge(old, new, coeff)
        old_cert = base.predictions(old, x[cert])
        selected_cert = base.predictions(selected_model, x[cert])
        passed, cs = base.certify_one(old_cert, selected_cert, y[cert],
                                     CONFIG['epsilon'], CONFIG['family_error'])
        if coeff == (0., 0.):
            passed = True
        released = selected_model if passed else old
        models = dict(incumbent=old, updated=new,
            scalar=base.merge(old, new, (scalar['coeff0'], scalar['coeff1'])),
            layer=base.merge(old, new, (layer['coeff0'], layer['coeff1'])),
            released=released)
        base_scores = base.per_slice(base.predictions(old, x[report]), y[report])
        saved = {**{k+'_ids': v for k, v in splits.items()}, 'labels': y,
                 'old_cert_prediction': old_cert,
                 'selected_cert_prediction': selected_cert,
                 'continuation_ids': updated_ids}
        saved.update({f'old_parameter_{i}': p for i, p in enumerate(old)})
        saved.update({f'new_parameter_{i}': p for i, p in enumerate(new)})
        for name, params in models.items():
            pred = base.predictions(params, x[report])
            scores = base.per_slice(pred, y[report])
            saved[name+'_report_prediction'] = pred
            rows.append(dict(seed=seed, policy=name,
                accuracy=float(np.mean(pred == y[report])),
                weighted_accuracy=float(scores @ np.array(CONFIG['objective_weights'])),
                worst_slice_difference=float(np.min(scores-base_scores)),
                selected_policy=selected_name, selected_coeff0=coeff[0],
                selected_coeff1=coeff[1], certification_passed=passed,
                reporting_count=len(report)))
            for k in range(10):
                slice_rows.append(dict(seed=seed, policy=name, slice=k,
                    n=int(np.sum(y[report] == k)), accuracy=float(scores[k]),
                    difference=float(scores[k]-base_scores[k])))
        cert_rows.extend(dict(seed=seed, **c) for c in cs)
        search_rows.extend(dict(seed=seed, policy='scalar', **c) for c in scalar_search)
        search_rows.extend(dict(seed=seed, policy='layer', **c) for c in layer_search)
        loss_rows.extend(dict(seed=seed, phase='incumbent', epoch=i+1, loss=v)
                         for i, v in enumerate(old_loss))
        loss_rows.extend(dict(seed=seed, phase='continuation', epoch=i+1, loss=v)
                         for i, v in enumerate(new_loss))
        np.savez_compressed(out/f'digits_seed_{seed}.npz', **saved)
        print(f'seed={seed} selected={selected_name} coefficients={coeff} '
              f'gate_passed={passed} updated_reporting_accuracy='
              f'{next(r["accuracy"] for r in rows if r["seed"] == seed and r["policy"] == "updated"):.6f}',
              flush=True)
    for name, data in [('digits_summary.csv', rows), ('digits_slices.csv', slice_rows),
                       ('digits_certification.csv', cert_rows), ('digits_search.csv', search_rows),
                       ('digits_training_loss.csv', loss_rows)]:
        base.write_csv(out/name, data)
    aggregate = {}
    for policy in ['incumbent', 'updated', 'scalar', 'layer', 'released']:
        rr = [r for r in rows if r['policy'] == policy]
        aggregate[policy] = {m: dict(mean=float(np.mean([r[m] for r in rr])),
                                    seed_sd=float(np.std([r[m] for r in rr], ddof=1)))
            for m in ['accuracy', 'weighted_accuracy', 'worst_slice_difference']}
    manifest.update(status='completed_subsequent_descriptive_public_data_study',
        completed_utc=datetime.now(timezone.utc).isoformat(),
        runtime_seconds=time.perf_counter()-start, aggregate=aggregate,
        ancestry_checks=ancestry, continuation_count=718,
        minibatch_updates_per_seed=CONFIG['continuation_epochs']*
                                  int(np.ceil(718/CONFIG['batch_size'])),
        certification_pass_count=sum(r['certification_passed'] for r in rows
                                     if r['policy'] == 'released'),
        exact_incumbent_selection_count=sum(r['selected_coeff0'] == 0 and
                                           r['selected_coeff1'] == 0 for r in rows
                                           if r['policy'] == 'released'))
    manifest['output_sha256'] = {p.name: sha256(p) for p in sorted(out.iterdir())
                                if p.is_file() and p.name != 'digits_manifest.json'}
    (out/'digits_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(aggregate, indent=2))


if __name__ == '__main__':
    main()
