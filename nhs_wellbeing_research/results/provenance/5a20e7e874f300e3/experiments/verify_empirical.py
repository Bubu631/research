"""Independent CSV-based verification; never overwrites empirical result files.

Prediction/selection/metrics/crossings are implemented here without importing the
analysis implementation. Original modules are loaded only for a separately
labelled, isolated end-to-end future-label perturbation test.
"""
from __future__ import annotations
import contextlib
import csv
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import importlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT/'data/processed/nhs_staff_survey_panel_2021_2025.csv'
VINTAGE = ROOT/'vintage_data/benchmark_vintage_panel.csv'
PHIS = (0., .3, .6, .85, .97, 1.)
NOISE_RATIOS = (0., 10., 30., 100., 300., 1000., 3000.)
METHODS = ('latest', 'equal_history', 'group_centred_equal', 'linear_trend',
           'geometric_history', 'group_mean_reversion', 'working_covariance')
CHECKS = []
MAX_ERRORS = {}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def near(label, actual, expected, tolerance=2e-10):
    a = np.asarray(actual, dtype=float)
    b = np.asarray(expected, dtype=float)
    assert a.shape == b.shape, (label, a.shape, b.shape)
    difference = float(np.max(abs(a-b))) if a.size else 0.
    assert np.isfinite(a).all() and np.isfinite(b).all(), label
    assert np.allclose(a, b, atol=tolerance, rtol=tolerance), (label, difference)
    MAX_ERRORS[label] = difference


def cohort(rows):
    """Reconstruct the inclusion rule using dictionaries rather than pivots."""
    by_code = {}
    for row in rows:
        if row['is_trust'] == '1':
            by_code.setdefault(row['org_code'], []).append(row)
    included, rejected = [], []
    for code, records in sorted(by_code.items()):
        records = [r for r in records if 2021 <= int(r['year']) <= 2025]
        records.sort(key=lambda r: int(r['year']))
        good = ([int(r['year']) for r in records] == list(range(2021, 2026))
                and all(r['burnout_score'] and r['burnout_n'] and
                        float(r['burnout_n']) > 0 and r['historically_comparable'] == '1'
                        for r in records)
                and len({r['benchmark_group'] for r in records}) == 1)
        (included if good else rejected).append(code)
    return included, rejected, by_code


def matrices(rows, codes, years, version=None):
    lookup = {}
    for row in rows:
        if (row['org_code'] in codes and int(row['year']) in years and
            (version is None or int(row['release_vintage']) == version)):
            key = (row['org_code'], int(row['year']))
            assert key not in lookup, key
            lookup[key] = row
    scores = np.array([[float(lookup[c, y]['burnout_score']) for y in years] for c in codes])
    counts = np.array([[float(lookup[c, y]['burnout_n']) for y in years] for c in codes])
    groups = np.array([lookup[c, years[-1]]['benchmark_group'] for c in codes])
    return scores, counts, groups


def group_centres(history, groups):
    result = np.zeros(history.shape)
    for group in sorted(set(groups)):
        ids = [i for i, value in enumerate(groups) if value == group]
        # Explicit reduction provides a separate extraction/computation path.
        means = [sum(float(history[i, t]) for i in ids)/len(ids)
                 for t in range(history.shape[1])]
        result[ids] = means
    return result


def forecast(history, count, groups, method, phi=None, ratio=None):
    """Independent formulas: least squares and direct linear solves, not pinv."""
    length = history.shape[1]
    centre = group_centres(history, groups)
    residual = history-centre
    if method == 'latest':
        return history[:, -1].copy()
    if method == 'equal_history':
        return np.array([sum(row)/length for row in history])
    if method == 'group_centred_equal':
        return centre[:, -1]+np.array([sum(row)/length for row in residual])
    if method == 'linear_trend':
        design = np.column_stack((np.ones(length), np.arange(length)))
        coefficients = np.linalg.lstsq(design, history.T, rcond=None)[0]
        return np.array([1., float(length)])@coefficients
    if method == 'geometric_history':
        coefficients = np.array([phi**(length-t-1) for t in range(length)])
        return history@coefficients/sum(coefficients)
    if method == 'group_mean_reversion':
        return centre[:, -1]+phi*residual[:, -1]
    assert method == 'working_covariance'
    if phi == 1. and ratio == 0.:
        # Covariance is the all-ones rank-one matrix; its Moore-Penrose result
        # predicts the mean centred state exactly.
        return centre[:, -1]+residual.mean(axis=1)
    kernel = np.array([[phi**abs(i-j) for j in range(length)] for i in range(length)])
    cross = np.array([phi**(length-t) for t in range(length)])
    result = []
    for i in range(len(history)):
        matrix = kernel+np.diag(ratio/count[i])
        solution = np.linalg.solve(matrix, cross)
        result.append(float(centre[i, -1]+np.dot(solution, residual[i])))
    return np.asarray(result)


def candidates():
    return ([(m, None, None) for m in METHODS[:4]]+
            [('geometric_history', p, None) for p in PHIS]+
            [('group_mean_reversion', p, None) for p in PHIS]+
            [('working_covariance', p, r) for p in PHIS for r in NOISE_RATIOS])


def select(history, counts, groups, target):
    rows, selected = [], {}
    for order, (method, phi, ratio) in enumerate(candidates()):
        prediction = forecast(history, counts, groups, method, phi, ratio)
        mse = sum(float(d)**2 for d in prediction-target)/len(target)
        row = dict(candidate_order=order, method=method, phi=phi, ratio=ratio,
                   development_mse=mse)
        rows.append(row)
        if method not in selected or mse < selected[method]['development_mse']-1e-14:
            selected[method] = row
    return rows, selected


def bottom(values, groups, fraction):
    chosen = set()
    for group in sorted(set(groups)):
        ids = [i for i, g in enumerate(groups) if g == group]
        k = max(1, int(len(ids)*fraction))
        chosen.update(sorted(ids, key=lambda i: (values[i], i))[:k])
    return chosen


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    result = np.zeros(len(values))
    start = 0
    while start < len(order):
        stop = start+1
        while stop < len(order) and values[order[stop]] == values[order[start]]:
            stop += 1
        result[order[start:stop]] = (start+1+stop)/2
        start = stop
    return result


def metrics(target, pred, groups):
    errors = [float(p)-float(y) for p, y in zip(pred, target)]
    actual_ranks, predicted_ranks = ranks(target), ranks(pred)
    actual_ranks -= actual_ranks.mean()
    predicted_ranks -= predicted_ranks.mean()
    result = dict(rmse=(sum(e*e for e in errors)/len(errors))**.5,
                  mae=sum(abs(e) for e in errors)/len(errors),
                  spearman=float(np.dot(actual_ranks, predicted_ranks)/
                                 np.sqrt(np.dot(actual_ranks, actual_ranks)*
                                         np.dot(predicted_ranks, predicted_ranks))))
    for fraction in (.1, .2, .3):
        actual, predicted = bottom(target, groups, fraction), bottom(pred, groups, fraction)
        result[f'observed_overlap_{fraction:.1f}'] = len(actual & predicted)/len(actual)
    return result


def verify_variant(name, dev_history, dev_n, test_history, test_n, groups, dev_target, test, codes):
    directory = ROOT/'results'/name
    grid, selected = select(dev_history, dev_n, groups, dev_target)
    saved_grid = read(directory/'development_grid.csv')
    assert len(grid) == len(saved_grid) == 58
    for expected, recorded in zip(grid, saved_grid):
        assert int(recorded['candidate_order']) == expected['candidate_order']
        assert recorded['method'] == expected['method']
        for key in ('phi', 'ratio'):
            assert (None if recorded[key] == '' else float(recorded[key])) == expected[key]
    near(name+'/58 development MSE', [r['development_mse'] for r in saved_grid],
         [r['development_mse'] for r in grid])
    saved_selected = json.loads((directory/'selected_hyperparameters.json').read_text())
    for method, chosen in selected.items():
        for key in ('candidate_order', 'method', 'phi', 'ratio'):
            assert chosen[key] == saved_selected[method][key], (name, method, key)
        near(name+'/'+method+'/selected MSE', chosen['development_mse'],
             saved_selected[method]['development_mse'])
    predictions = {m: forecast(test_history, test_n, groups, m, c['phi'], c['ratio'])
                   for m, c in selected.items()}
    saved_predictions = read(directory/'frozen_2025_predictions.csv')
    assert [r['org_code'] for r in saved_predictions] == codes
    near(name+'/2024 values', [r['observed_2024'] for r in saved_predictions], test_history[:, -1])
    near(name+'/2025 outcomes', [r['observed_2025'] for r in saved_predictions], test)
    saved_metrics = {r['method']: r for r in read(directory/'test_metrics.csv')}
    output_metrics = {}
    for method, prediction in predictions.items():
        near(name+'/'+method+'/190 predictions', [r[method] for r in saved_predictions], prediction)
        computed = metrics(test, prediction, groups)
        output_metrics[method] = computed
        near(name+'/'+method+'/all metrics', [saved_metrics[method][k] for k in computed], list(computed.values()))
    group_rows = read(directory/'group_test_metrics.csv')
    assert len(group_rows) == 35
    for row in group_rows:
        ids = np.array([i for i, group in enumerate(groups) if group == row['benchmark_group']])
        assert int(row['units']) == len(ids)
        computed = metrics(test[ids], predictions[row['method']][ids], groups[ids])
        near(name+'/'+row['benchmark_group']+'/'+row['method'], [row[k] for k in computed], list(computed.values()))
    for row in read(directory/'paired_bootstrap.csv'):
        assert int(row['resampling_clusters']) == 189 and int(row['bootstrap_repetitions']) == 5000
        for metric in ('rmse', 'mae'):
            expected = output_metrics[row['method']][metric]-output_metrics['latest'][metric]
            near(name+'/'+row['method']+'/bootstrap point '+metric, row[metric+'_difference'], expected)
    CHECKS.append(name+': independent 58-row grid, seven settings, 1,330 predictions, 42 global metrics and 210 group metrics passed')
    return selected, predictions, output_metrics


def verify_static(y, n, groups, codes):
    """Decimal roots; interval constancy proves coverage between all crossings."""
    centre = group_centres(y, groups)
    z = y[:, -1]-centre[:, -1]
    counts = n[:, -1]
    with localcontext() as context:
        context.prec = 60
        zz = [Decimal(float(value)) for value in z]
        nn = [Decimal(float(value)) for value in counts]
        upper = Decimal(3000)
        all_roots = {Decimal(0), upper}
        thresholds = {}
        for group in sorted(set(groups)):
            ids = [i for i, g in enumerate(groups) if g == group]
            k = max(1, int(len(ids)*.2))
            initial = set(sorted(ids, key=lambda i: (zz[i], i))[:k])
            crossings = []
            possible_first = []
            for position, i in enumerate(ids):
                for j in ids[position+1:]:
                    denominator = zz[i]*nn[i]-zz[j]*nn[j]
                    if denominator == 0:
                        continue
                    root = nn[i]*nn[j]*(zz[j]-zz[i])/denominator
                    if 0 < root <= upper:
                        crossings.append(root)
                        all_roots.add(root)
                    if root >= 0 and ((i in initial) != (j in initial)):
                        # Their rational curves can cross at most once; a
                        # nonnegative root exchanges initial selected/excluded.
                        possible_first.append(root)
            thresholds[group] = dict(units=len(ids), k=k, count=len(crossings),
                                     first=min(possible_first) if possible_first else None)
        endpoints = sorted(all_roots)
        probes = set(endpoints+[Decimal(str(v)) for v in NOISE_RATIOS])
        probes.update((a+b)/2 for a, b in zip(endpoints[:-1], endpoints[1:]))

        def picked(ratio):
            scores = [zz[i]*nn[i]/(nn[i]+ratio) for i in range(len(codes))]
            return bottom(scores, groups, .2)

        selected_sets = [picked(probe) for probe in sorted(probes)]
        union = set.union(*selected_sets)
        intersection = set.intersection(*selected_sets)
        raw = picked(Decimal(0))
        for row in read(ROOT/'results/harmonised/rank_thresholds.csv'):
            expected = thresholds[row['benchmark_group']]
            assert int(row['units']) == expected['units'] and int(row['k']) == expected['k']
            assert int(row['pair_crossings_0_3000']) == expected['count']
            if expected['first'] is None:
                assert row['first_membership_crossing'] == ''
            else:
                near('crossing/'+row['benchmark_group'], float(row['first_membership_crossing']), float(expected['first']), 1e-8)
            assert (row['stable_through_3000'] == 'True') == (expected['first'] is None or expected['first'] > upper)
        for row in read(ROOT/'results/harmonised/rank_envelope.csv'):
            i = codes.index(row['org_code'])
            assert int(row['raw_selected']) == int(i in raw)
            assert int(row['selected_somewhere_0_3000']) == int(i in union)
            assert int(row['selected_everywhere_0_3000']) == int(i in intersection)
        for row in read(ROOT/'results/harmonised/rank_sensitivity.csv'):
            choice = picked(Decimal(row['ratio']))
            assert int(row['selected']) == len(choice)
            assert int(row['retained_from_raw']) == len(choice & raw)
            assert int(row['changed_members']) == len(raw-choice)
            near('static ratio '+row['ratio'], row['overlap_with_raw'], len(choice & raw)/len(raw))
        for row in read(ROOT/'results/harmonised/rank_membership.csv'):
            i = codes.index(row['org_code'])
            ratio = Decimal(row['ratio'])
            near('static cell '+row['org_code']+'/'+row['ratio'], row['working_posterior_score'], float(zz[i]*nn[i]/(nn[i]+ratio)))
            assert int(row['selected']) == int(i in picked(ratio))
    CHECKS.append('Static sensitivity: Decimal crossing enumeration, all interval probes, 190 membership envelopes and 1,330 grid membership rows passed')
    return dict(unique_crossings_inside_interval=len(endpoints)-2,
                probes=len(probes), selected_everywhere=len(intersection), selected_somewhere=len(union),
                selected_raw=len(raw), thresholds={g: (None if r['first'] is None else float(r['first'])) for g, r in thresholds.items()})


def verify_followup(y, groups):
    means = group_centres(y, groups)
    rows = read(ROOT/'results/harmonised/observational_followup.csv')
    for t, row in enumerate(rows):
        ids = sorted(bottom(y[:, t], groups, .2))
        raw_change = y[ids, t+1]-y[ids, t]
        group_change = means[ids, t+1]-means[ids, t]
        expected = dict(baseline_mean=y[ids, t].mean(), followup_mean=y[ids, t+1].mean(),
                        observed_selected_change=raw_change.mean(), corresponding_group_change=group_change.mean(),
                        group_centred_change=(raw_change-group_change).mean(),
                        retained_in_next_observed_bottom=len(set(ids) & bottom(y[:, t+1], groups, .2))/len(ids))
        assert int(row['selection_year']) == 2021+t and int(row['selected_units']) == len(ids)
        near('follow-up '+str(t), [row[k] for k in expected], list(expected.values()))
    CHECKS.append('All four observational follow-up rows independently reproduced; no causal interpretation')


def verify_cluster_mapping(primary_rows, codes):
    meta = {r['org_code']: r for r in primary_rows if r['year'] == '2025' and r['org_code'] in codes}
    legal = [meta[code]['legal_org_code'] for code in codes]
    members = {entity: [i for i, value in enumerate(legal) if value == entity] for entity in set(legal)}
    duplicates = {entity: [codes[i] for i in ids] for entity, ids in members.items() if len(ids) > 1}
    assert duplicates == {'R1F': ['R1F1', 'R1F2']} and len(members) == 189
    ordered = sorted(members)
    # Independent explicit resampling of entity blocks checks the row-average
    # weighting algebra. It does not attempt to recreate all 5,000 draws.
    rng = np.random.default_rng(260911)
    artificial = np.arange(len(codes), dtype=float)**2
    for _ in range(37):
        drawn = rng.choice(ordered, len(ordered), replace=True)
        expanded = [i for entity in drawn for i in members[entity]]
        multiplicities = {entity: int(np.sum(drawn == entity)) for entity in ordered}
        weights = np.array([multiplicities[entity] for entity in legal])
        near('cluster expansion '+str(_), artificial[expanded].mean(), np.dot(weights, artificial)/weights.sum())
        assert weights[codes.index('R1F1')] == weights[codes.index('R1F2')]
    CHECKS.append('Source legal_org_code confirms 189 clusters; 37 explicit entity-block draws verify equal paired weights and realised-row denominator')
    return dict(clusters=189, non_singleton_clusters=duplicates, explicit_resampling_checks=37,
                interval_repetition='Saved 5,000-draw quantiles not independently rerun',
                interpretation='Paired legal-entity bootstrap conditional on fitted predictions, selected settings and retrospective cohort; unknown inter-entity dependence is not covered')


def future_label_perturbation():
    """Original pipeline ONLY in scratch, for a distinct metamorphic check."""
    sys.path.insert(0, str(ROOT/'experiments'))
    empirical = importlib.import_module('empirical')
    vintage = importlib.import_module('vintage_empirical')
    import pandas as pd
    output = {}
    old_argv = sys.argv[:]
    old_values = [(module, module.ROOT, module.save_manifest, module.bootstrap_differences)
                  for module in (empirical, vintage)]
    try:
        with tempfile.TemporaryDirectory(prefix='nhs_independent_audit_') as temporary:
            temporary = Path(temporary)
            for changed in (False, True):
                scratch = temporary/('perturbed' if changed else 'baseline')
                destination = scratch/'data/processed'/PRIMARY.name
                destination.parent.mkdir(parents=True)
                data = pd.read_csv(PRIMARY, dtype={'org_code': str})
                if changed:
                    mask = (data.year == 2025) & data.burnout_score.notna()
                    data.loc[mask, 'burnout_score'] = 10-data.loc[mask, 'burnout_score']
                    data.loc[mask, 'burnout_n'] *= 7
                data.to_csv(destination, index=False)
                (scratch/'vintage_data').mkdir()
                shutil.copyfile(VINTAGE, scratch/'vintage_data'/VINTAGE.name)
                for module in (empirical, vintage):
                    module.ROOT = scratch
                    module.save_manifest = lambda path, details: None
                    module.bootstrap_differences = lambda *args, **kwargs: [{'audit_skipped_bootstrap': True}]
                sys.argv = ['empirical.py', '--panel', str(destination)]
                with contextlib.redirect_stdout(io.StringIO()):
                    empirical.main()
                    vintage.main()
            for name in ('harmonised', 'vintage'):
                left, right = [temporary/state/'results'/name for state in ('baseline', 'perturbed')]
                for filename in ('development_grid.csv', 'selected_hyperparameters.json'):
                    assert (left/filename).read_bytes() == (right/filename).read_bytes(), (name, filename)
                a, b = read(left/'frozen_2025_predictions.csv'), read(right/'frozen_2025_predictions.csv')
                for method in METHODS:
                    assert [row[method] for row in a] == [row[method] for row in b], (name, method)
                assert [row['observed_2025'] for row in a] != [row['observed_2025'] for row in b]
                output[name] = dict(development_grid_identical=True, selected_settings_identical=True,
                                    all_1330_predictions_identical=True, targets_actually_changed=True)
    finally:
        sys.argv = old_argv
        for module, old_root, old_manifest, old_bootstrap in old_values:
            module.ROOT, module.save_manifest, module.bootstrap_differences = old_root, old_manifest, old_bootstrap
    CHECKS.append('Both original pipelines executed in isolated temporary directories: replace 2025 score by 10-score and multiply 2025 counts by seven; all development settings/predictions unchanged')
    return output


def main():
    protected = [PRIMARY, VINTAGE, ROOT/'experiments/empirical.py', ROOT/'experiments/vintage_empirical.py',
                 ROOT/'experiments/common.py']
    protected += sorted((ROOT/'results/harmonised').glob('*'))+sorted((ROOT/'results/vintage').glob('*'))
    before = {str(p.relative_to(ROOT)): digest(p) for p in protected if p.is_file()}
    primary, archived = read(PRIMARY), read(VINTAGE)
    codes, excluded, _ = cohort(primary)
    assert len(codes) == 190
    y, n, groups = matrices(primary, codes, list(range(2021, 2026)))
    a, an, ag = matrices(archived, codes, [2021, 2022, 2023], 2023)
    b, bn, bg = matrices(archived, codes, [2021, 2022, 2023, 2024], 2024)
    assert np.array_equal(groups, ag) and np.array_equal(groups, bg)
    computed = {}
    for name, args in [('harmonised', (y[:, :3], n[:, :3], y[:, :4], n[:, :4], groups, y[:, 3], y[:, 4], codes)),
                       ('vintage', (a, an, b, bn, groups, b[:, -1], y[:, -1], codes))]:
        selected, _, point_metrics = verify_variant(name, *args)
        computed[name] = dict(selected=selected, point_metrics=point_metrics)
    static = verify_static(y, n, groups, codes)
    verify_followup(y, groups)
    clusters = verify_cluster_mapping(primary, codes)
    perturbation = future_label_perturbation()
    after = {str(p.relative_to(ROOT)): digest(p) for p in protected if p.is_file()}
    assert before == after, 'Protected source or empirical output changed during audit'
    manifest = dict(status='passed', completed_at_utc=datetime.now(timezone.utc).isoformat(),
                    independent_implementation=True, units=190, excluded_reporting_codes=excluded,
                    checks=CHECKS, maximum_absolute_difference=max(MAX_ERRORS.values()),
                    numeric_check_count=len(MAX_ERRORS), numeric_check_max_errors=MAX_ERRORS,
                    empirical=computed, static=static, bootstrap=clusters, future_label_perturbation=perturbation,
                    protected_files_unchanged=True, input_and_result_sha256=before,
                    verifier_sha256=digest(__file__), numpy_version=np.__version__,
                    limitations=[
                        'Future-label perturbation is separate from independent formula recomputation and intentionally exercises original modules.',
                        'No future score or sample count enters tuning or prediction conditional on the fixed cohort; current complete-case/cohort rules still depend on eventual 2025 availability.',
                        'Harmonised historical measurements incorporate 2025 revisions and occupational weights; only vintage arm uses archived historical predictor measurements.',
                        'Original forecasting logic was audited now; original before-outcome chronology cannot be proved solely from a local timestamp.',
                        'No causal intervention effects, latent-state truth, effective sample sizes or individual-level uncertainty are identified.',
                        'Static envelope is conditional on fixed group centring and the specified model/ratio interval; it is not universal ranking certainty.',
                        'Bootstrap quantiles were inspected but not all independently rerun; point contrasts and entity-block weighting were independently verified.'])
    destination = ROOT/'results/empirical_independent_audit.json'
    destination.write_text(json.dumps(manifest, indent=2, allow_nan=False)+'\n')
    print(json.dumps({key: manifest[key] for key in ('status', 'units', 'numeric_check_count',
                      'maximum_absolute_difference', 'protected_files_unchanged')}, indent=2))


if __name__ == '__main__':
    main()
