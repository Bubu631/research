#!/usr/bin/env python3
"""Public-data CPU integration study; not a foundation-model benchmark.

The protocol below was fixed before its first complete execution. No parameters
are selected on certification or reporting data. All results, including fallback,
are retained. This study assesses a real weight-merge pipeline, not SOTA accuracy.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import sklearn
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
CONFIG = dict(seeds=[1701, 1702, 1703, 1704, 1705], hidden=48,
              old_epochs=12, continuation_epochs=24, batch_size=128,
              learning_rate=0.15, momentum=0.9, epsilon=0.03,
              family_error=0.05, scalar_candidates=121, layer_grid=11,
              training_fraction=0.4, development_fraction=0.2,
              certification_fraction=0.2, reporting_fraction=0.2,
              continuation_classes=list(range(5)),
              objective_weights=[0.16]*5 + [0.04]*5)


def initialize(rng, hidden=48):
    return [rng.normal(0, np.sqrt(2/64), (64, hidden)), np.zeros(hidden),
            rng.normal(0, np.sqrt(2/hidden), (hidden, 10)), np.zeros(10)]


def forward(params, x):
    hidden = np.maximum(x @ params[0] + params[1], 0)
    logits = hidden @ params[2] + params[3]
    logits -= logits.max(axis=1, keepdims=True)
    probs = np.exp(logits)
    probs /= probs.sum(axis=1, keepdims=True)
    return hidden, probs


def loss_grads(params, x, y):
    hidden, probs = forward(params, x)
    loss = -np.log(probs[np.arange(len(y)), y]).mean()
    dz = probs.copy()
    dz[np.arange(len(y)), y] -= 1
    dz /= len(y)
    dh = dz @ params[2].T
    dh *= hidden > 0
    return float(loss), [x.T @ dh, dh.sum(0), hidden.T @ dz, dz.sum(0)]


def train(params, x, y, epochs, rng):
    params = [p.copy() for p in params]
    velocity = [np.zeros_like(p) for p in params]
    losses = []
    for epoch in range(epochs):
        order = rng.permutation(len(y))
        for start in range(0, len(y), CONFIG['batch_size']):
            ids = order[start:start + CONFIG['batch_size']]
            _, grads = loss_grads(params, x[ids], y[ids])
            for i, grad in enumerate(grads):
                velocity[i] = CONFIG['momentum']*velocity[i] + grad
                params[i] -= CONFIG['learning_rate']*velocity[i]
        losses.append(loss_grads(params, x, y)[0])
    return params, losses


def merge(old, new, coeff):
    return [(1-coeff[i//2])*a + coeff[i//2]*b
            for i, (a, b) in enumerate(zip(old, new))]


def predictions(params, x):
    return forward(params, x)[1].argmax(axis=1)


def per_slice(pred, y):
    return np.array([np.mean(pred[y == k] == k) for k in range(10)])


def split_indices(y, seed):
    # Four mutually exclusive stratified partitions. No duplicated observations.
    idx = np.arange(len(y))
    tr, rem = train_test_split(idx, train_size=0.4, stratify=y, random_state=seed)
    dev, rem = train_test_split(rem, train_size=1/3, stratify=y[rem], random_state=seed+1)
    cert, report = train_test_split(rem, test_size=0.5, stratify=y[rem], random_state=seed+2)
    splits = dict(train=tr, development=dev, certification=cert, reporting=report)
    assert len(np.unique(np.concatenate(list(splits.values())))) == len(y)
    assert sum(map(len, splits.values())) == len(y)
    return splits


def select_on_development(old, new, x, y, coeffs):
    base = per_slice(predictions(old, x), y)
    weights = np.array(CONFIG['objective_weights'])
    candidates = []
    for coeff in coeffs:
        scores = per_slice(predictions(merge(old, new, coeff), x), y)
        margin = float(np.min(scores-base+CONFIG['epsilon']))
        utility = float(scores @ weights)
        feasible = margin >= -1e-12
        candidates.append(dict(coeff0=float(coeff[0]), coeff1=float(coeff[1]),
                               utility=utility, min_margin=margin, feasible=feasible))
    feasible = [c for c in candidates if c['feasible']]
    # Frozen tie rule: utility, worst margin, then less parameter movement.
    chosen = max(feasible, key=lambda c: (c['utility'], c['min_margin'],
                                           -c['coeff0']-c['coeff1'], -c['coeff0']))
    return chosen, candidates


def certify_one(old_pred, candidate_pred, y, epsilon, alpha):
    # One development-frozen candidate: intersection-union gate at alpha.
    # Distinct class slices need no independence for the false-release theorem.
    diffs = (candidate_pred == y).astype(float) - (old_pred == y).astype(float)
    exact_incumbent = False  # handled structurally from coefficient identity outside
    records = []
    for k in range(10):
        d = diffs[y == k]
        radius = np.sqrt(2*np.log(1/alpha)/len(d))
        lower = float(d.mean()-radius)
        records.append(dict(slice=k, n=len(d), mean_difference=float(d.mean()),
                            hoeffding_radius=float(radius), lower=lower,
                            passed=lower >= -epsilon))
    return all(r['passed'] for r in records), records


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'papers/base_upgrade/results')
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    dataset = load_digits()
    x, y = dataset.data.astype(np.float64)/16.0, dataset.target
    digest = hashlib.sha256(x.tobytes()+y.tobytes()).hexdigest()
    rows, slice_rows, cert_rows, search_rows, loss_rows = [], [], [], [], []
    for seed in CONFIG['seeds']:
        rng = np.random.default_rng(seed)
        splits = split_indices(y, seed)
        tr, dev, cert, report = (splits[k] for k in ['train','development','certification','reporting'])
        old, old_loss = train(initialize(rng), x[tr], y[tr], CONFIG['old_epochs'], rng)
        updated_ids = tr[y[tr] < 5]
        new, new_loss = train(old, x[updated_ids], y[updated_ids], CONFIG['continuation_epochs'], rng)
        scalar, scalar_search = select_on_development(old, new, x[dev], y[dev],
            [(v,v) for v in np.linspace(0,1,CONFIG['scalar_candidates'])])
        layer, layer_search = select_on_development(old, new, x[dev], y[dev],
            [(a,b) for a in np.linspace(0,1,CONFIG['layer_grid'])
                   for b in np.linspace(0,1,CONFIG['layer_grid'])])
        # Policy selection itself uses only development observations.
        selected_name, selected = max([('scalar',scalar),('layer',layer)],
             key=lambda z: (z[1]['utility'],z[1]['min_margin'],
                            -z[1]['coeff0']-z[1]['coeff1'],z[0]=='scalar'))
        coeff = (selected['coeff0'],selected['coeff1'])
        selected_model = merge(old,new,coeff)
        old_cert = predictions(old,x[cert])
        selected_cert = predictions(selected_model,x[cert])
        passed, cs = certify_one(old_cert,selected_cert,y[cert],CONFIG['epsilon'],CONFIG['family_error'])
        if coeff == (0.,0.):
            passed = True  # known identity, not inferred from predictions agreeing
        released = selected_model if passed else old
        models = dict(incumbent=old, updated=new,
                      scalar=merge(old,new,(scalar['coeff0'],scalar['coeff1'])),
                      layer=merge(old,new,(layer['coeff0'],layer['coeff1'])), released=released)
        old_report = predictions(old,x[report])
        base_scores = per_slice(old_report,y[report])
        saved = {**{k+'_ids':v for k,v in splits.items()}, 'labels':y,
                 'old_cert_prediction':old_cert, 'selected_cert_prediction':selected_cert}
        saved.update({f'old_parameter_{i}':p for i,p in enumerate(old)})
        saved.update({f'new_parameter_{i}':p for i,p in enumerate(new)})
        for name,params in models.items():
            pred = predictions(params,x[report])
            scores = per_slice(pred,y[report])
            saved[name+'_report_prediction'] = pred
            rows.append(dict(seed=seed,policy=name,accuracy=float(np.mean(pred==y[report])),
                weighted_accuracy=float(scores @ np.array(CONFIG['objective_weights'])),
                worst_slice_difference=float(np.min(scores-base_scores)),
                selected_policy=selected_name,selected_coeff0=coeff[0],selected_coeff1=coeff[1],
                certification_passed=passed,reporting_count=len(report)))
            for k in range(10):
                slice_rows.append(dict(seed=seed,policy=name,slice=k,n=int(np.sum(y[report]==k)),
                    accuracy=float(scores[k]),difference=float(scores[k]-base_scores[k])))
        cert_rows.extend(dict(seed=seed,**c) for c in cs)
        search_rows.extend(dict(seed=seed,policy='scalar',**c) for c in scalar_search)
        search_rows.extend(dict(seed=seed,policy='layer',**c) for c in layer_search)
        loss_rows.extend(dict(seed=seed,phase='incumbent',epoch=i+1,loss=v) for i,v in enumerate(old_loss))
        loss_rows.extend(dict(seed=seed,phase='continuation',epoch=i+1,loss=v) for i,v in enumerate(new_loss))
        np.savez_compressed(out/f'digits_seed_{seed}.npz',**saved)
        print(f'seed={seed} selected={selected_name} coefficients={coeff} certified={passed}',flush=True)
    for name,data in [('digits_summary.csv',rows),('digits_slices.csv',slice_rows),
                      ('digits_certification.csv',cert_rows),('digits_search.csv',search_rows),
                      ('digits_training_loss.csv',loss_rows)]:
        write_csv(out/name,data)
    aggregate = {}
    for policy in ['incumbent','updated','scalar','layer','released']:
        rr = [r for r in rows if r['policy']==policy]
        aggregate[policy] = {m: {'mean':float(np.mean([r[m] for r in rr])),
                                 'seed_sd':float(np.std([r[m] for r in rr],ddof=1))}
                   for m in ['accuracy','weighted_accuracy','worst_slice_difference']}
    manifest = dict(status='completed_public_data_integration_study',config=CONFIG,
        dataset='sklearn.datasets.load_digits; 1797 examples; 64 features; classes 0-9',
        dataset_sha256=digest,source='https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_digits.html',
        dataset_original='https://archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits',
        versions=dict(python=platform.python_version(),numpy=np.__version__,sklearn=sklearn.__version__),
        runtime_seconds=time.perf_counter()-start,aggregate=aggregate,
        certification_pass_count=sum(r['certification_passed'] for r in rows if r['policy']=='released'),
        caveats=['Not MNIST, multilingual translation, or a foundation-model result.',
                 'Five fixed split/training seeds; seed SD is descriptive, not an independent confidence interval.',
                 'Small certification sets may force incumbent fallback.',
                 'Scalar and layer searches each evaluate 121 development candidates.',
                 'No hyperparameter revision after inspecting certification/reporting results.'])
    (out/'digits_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest['aggregate'],indent=2))


if __name__ == '__main__':
    main()
