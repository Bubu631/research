"""Actual CPU softmax-policy training in a constructed dependency tool task.

Run a bounded smoke only:
  python experiments/stateful_training.py --smoke

Full same-rollout study (requires an explicit invocation):
  python experiments/stateful_training.py --updates 300 --seeds 10 --eval-episodes 256

This is not an LLM, SWE-bench, or measured expensive-verifier speedup experiment.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.reward_audit import completion, make_survival, sequential_audit, split_advantages
from src.stateful_env import (ACTION_NAMES, FEATURE_NAMES, AuditOracle, cheap_verifier,
                             environment_self_check, initial_policy, reference_verifier,
                             ReleaseTask, replay, rollout, sample_task)

POLICIES = ('full', 'proxy', 'whole_group_residual', 'rr_completion',
            'naive_reward_ht', 'partial_replacement')


class FixedUniform:
    """Pair the first audit uniform across methods without variable RNG use."""
    def __init__(self, value):
        self.value = float(value)

    def random(self):
        return self.value


def coefficients(method, proxy, oracle, audit_uniforms, fraction=.5,
                 completion_probability=.55, exponent=.5):
    """No unpurchased reference labels are present in this interface.

    Every method exploits the valid logical implication cheap=0 => reference=0.
    M cheap-positive candidates remain; expected purchased labels are fraction*M
    for all four partial methods.  The target still normalizes all G labels.
    """
    proxy = np.asarray(proxy, dtype=np.int8)
    candidates = np.flatnonzero(proxy)
    m = len(candidates)
    p = proxy.astype(float)*completion_probability
    if method == 'proxy':
        return split_advantages(proxy)
    if not m:
        return split_advantages(np.zeros_like(proxy))
    if method == 'full':
        reward = np.zeros_like(proxy)
        for i in candidates:
            reward[i] = oracle(int(i))
        return split_advantages(reward)
    if method == 'whole_group_residual':
        baseline = completion(p)
        if audit_uniforms[0] < fraction:
            reward = np.zeros_like(proxy)
            for i in candidates:
                reward[i] = oracle(int(i))
            return baseline+(split_advantages(reward)-baseline)/fraction
        return baseline
    if method == 'rr_completion':
        survival = make_survival(m, fraction*m, exponent=exponent)
        result, _ = sequential_audit(p, oracle, candidates, survival,
                                     FixedUniform(audit_uniforms[0]))
        return result
    if method in ('naive_reward_ht', 'partial_replacement'):
        # Inclusions are independent across candidates, known before their label.
        reward = np.zeros(len(proxy), dtype=float) if method == 'naive_reward_ht' else proxy.astype(float)
        for i in candidates:
            if audit_uniforms[i] < fraction:
                label = oracle(int(i))
                reward[i] = label/fraction if method == 'naive_reward_ht' else label
        return split_advantages(reward)
    raise ValueError(method)


def seed_rng(seed, horizon, stream):
    return np.random.default_rng(np.random.SeedSequence([2026091207, seed, horizon, stream]))


def evaluation_bank(seed, horizon, episodes):
    rng = seed_rng(seed, horizon, 9001)
    tasks = [sample_task(rng, horizon) for _ in range(episodes)]
    uniforms = rng.random((episodes, horizon))
    return tasks, uniforms


def evaluate(weights, bank):
    tasks, uniforms = bank
    true, proxy = [], []
    for task, random_actions in zip(tasks, uniforms):
        final, _, _ = rollout(weights, task, random_actions, need_score=False)
        true.append(reference_verifier(final))
        proxy.append(cheap_verifier(final))
    return np.asarray(true, np.int8), np.asarray(proxy, np.int8)


def run_one(args, method, horizon, seed, out):
    train_rng = seed_rng(seed, horizon, 1001)
    audit_rng = seed_rng(seed, horizon, 2001)
    weights = initial_policy(args.initial_preference)
    bank = evaluation_bank(seed, horizon, args.eval_episodes)
    actions_bank, changed_bank, proxy_bank = [], [], []
    query_mask_bank, bought_bank, coefficient_bank, weight_bank = [], [], [], [weights.copy()]
    train_rows, eval_rows, eval_true_bank, eval_proxy_bank = [], [], [], []
    total_queries = 0
    cumulative_candidate_labels = 0
    timings = dict(rollout_seconds=0., estimation_seconds=0., optimization_seconds=0.,
                   reporting_seconds=0., offline_diagnostic_seconds=0.)

    def reporting(update):
        started = time.perf_counter()
        true, proxy = evaluate(weights, bank)
        timings['reporting_seconds'] += time.perf_counter()-started
        eval_true_bank.append(true)
        eval_proxy_bank.append(proxy)
        eval_rows.append(dict(method=method, horizon=horizon, seed=seed,
                              update=update, generated_training_trajectories=update*args.group_size,
                              training_actions=update*args.group_size*horizon,
                              purchased_reference_queries=total_queries,
                              purchased_invariant_checks=total_queries*horizon,
                              candidate_reference_labels=cumulative_candidate_labels,
                              evaluation_episodes=len(true), reference_success=float(true.mean()),
                              cheap_success=float(proxy.mean()),
                              cheap_false_acceptance=float(np.mean((proxy==1)&(true==0))),
                              reporting_reference_queries=len(true)))

    reporting(0)
    for update in range(1, args.updates+1):
        started = time.perf_counter()
        tasks = [sample_task(train_rng, horizon) for _ in range(args.group_size)]
        uniforms = train_rng.random((args.group_size, horizon))
        finals, actions, scores = [], [], []
        for task, random_actions in zip(tasks, uniforms):
            final, action, score = rollout(weights, task, random_actions)
            finals.append(final)
            actions.append(action)
            scores.append(score)
        proxy = np.asarray([cheap_verifier(f) for f in finals], dtype=np.int8)
        timings['rollout_seconds'] += time.perf_counter()-started
        # This independent stream consumes exactly G uniforms under every method.
        audit_uniforms = audit_rng.random(args.group_size)
        oracle = AuditOracle(finals)
        started = time.perf_counter()
        phi = coefficients(method, proxy, oracle, audit_uniforms,
                           args.audit_fraction, args.completion_probability,
                           args.survival_exponent)
        timings['estimation_seconds'] += time.perf_counter()-started
        started = time.perf_counter()
        advantage = phi[:args.group_size]+phi[args.group_size:]
        gradient = np.einsum('g,gda->da', advantage, np.asarray(scores))/args.group_size
        grad_norm = float(np.linalg.norm(gradient))
        factor = min(1., args.max_grad_norm/max(grad_norm, 1e-15))
        weights += args.learning_rate*factor*gradient
        timings['optimization_seconds'] += time.perf_counter()-started
        bought = np.full(args.group_size, -1, dtype=np.int8)
        for i, label in oracle.records:
            bought[i] = label
        total_queries += len(oracle.records)
        cumulative_candidate_labels += int(proxy.sum())
        actions_bank.append(actions)
        changed_bank.append([t.changed_component for t in tasks])
        proxy_bank.append(proxy)
        query_mask_bank.append(bought >= 0)
        bought_bank.append(bought)
        coefficient_bank.append(phi)
        weight_bank.append(weights.copy())
        train_rows.append(dict(method=method, horizon=horizon, seed=seed, update=update,
                               cheap_success=float(proxy.mean()),
                               candidate_labels=int(proxy.sum()),
                               expected_queries=(int(proxy.sum()) if method=='full' else
                                                 0. if method=='proxy' else args.audit_fraction*int(proxy.sum())),
                               purchased_queries=len(oracle.records), cumulative_queries=total_queries,
                               coefficient_norm=float(np.linalg.norm(phi)),
                               gradient_norm=grad_norm, gradient_clip_factor=factor))
        if update % args.eval_every == 0 or update == args.updates:
            reporting(update)

    # Offline diagnostics occur only after the entire optimization run has ended.
    # They cannot supply labels to any update, stopping rule, or predictor fit.
    started = time.perf_counter()
    true_bank = np.empty((args.updates, args.group_size), dtype=np.int8)
    for u in range(args.updates):
        for g in range(args.group_size):
            required = [0]*(horizon//4)
            required[changed_bank[u][g]] = 1
            task = ReleaseTask(tuple(required), changed_bank[u][g])
            final = replay(task, actions_bank[u][g])
            true_bank[u, g] = reference_verifier(final)
            assert cheap_verifier(final) == proxy_bank[u][g]
            if bought_bank[u][g] >= 0:
                assert true_bank[u, g] == bought_bank[u][g]
    timings['offline_diagnostic_seconds'] = time.perf_counter()-started
    for u, row in enumerate(train_rows):
        row['offline_reference_success'] = float(true_bank[u].mean())
        row['offline_false_acceptance'] = float(np.mean((np.asarray(proxy_bank[u])==1)&(true_bank[u]==0)))
        row['offline_diagnostic_queries'] = args.group_size
    stem = f'{method}_h{horizon}_s{seed}'
    np.savez_compressed(out/'trajectories'/f'{stem}.npz',
                        actions=np.asarray(actions_bank, np.int8),
                        changed_component=np.asarray(changed_bank, np.int16),
                        cheap_rewards=np.asarray(proxy_bank, np.int8),
                        reference_rewards_offline=true_bank,
                        purchased_mask=np.asarray(query_mask_bank, bool),
                        purchased_labels=np.asarray(bought_bank, np.int8),
                        split_coefficients=np.asarray(coefficient_bank),
                        policy_weights=np.asarray(weight_bank),
                        reporting_reference=np.asarray(eval_true_bank, np.int8),
                        reporting_cheap=np.asarray(eval_proxy_bank, np.int8))
    # A readable exact action trace; all other traces are in the NPZ bank.
    example = dict(method=method, horizon=horizon, seed=seed,
                   changed_component=int(changed_bank[0][0]),
                   actions=[ACTION_NAMES[int(a)] for a in actions_bank[0][0]],
                   cheap_reward=int(proxy_bank[0][0]),
                   reference_reward_obtained_after_training=int(true_bank[0,0]),
                   bought_during_training=bool(query_mask_bank[0][0]))
    (out/'trajectories'/f'{stem}_example.json').write_text(json.dumps(example, indent=2)+'\n')
    accounting = dict(method=method, horizon=horizon, seed=seed, updates=args.updates,
                       purchased_reference_queries=total_queries,
                       reporting_reference_queries=args.eval_episodes*len(eval_rows),
                       offline_diagnostic_reference_queries=args.updates*args.group_size,
                       training_cheap_verifier_calls=args.updates*args.group_size,
                       reporting_cheap_verifier_calls=args.eval_episodes*len(eval_rows),
                       offline_diagnostic_cheap_verifier_calls=args.updates*args.group_size,
                       timings=timings)
    print(f'{stem}: eval {eval_rows[0]["reference_success"]:.3f} -> '
          f'{eval_rows[-1]["reference_success"]:.3f}, train queries={total_queries}', flush=True)
    return train_rows, eval_rows, accounting


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def summarize(eval_rows):
    out = []
    keys = sorted({(r['horizon'], r['method'], r['update']) for r in eval_rows})
    for h, method, u in keys:
        rows = [r for r in eval_rows if (r['horizon'],r['method'],r['update'])==(h,method,u)]
        values = np.asarray([r['reference_success'] for r in rows])
        proxy = np.asarray([r['cheap_success'] for r in rows])
        out.append(dict(horizon=h, method=method, update=u, seeds=len(rows),
                        reference_success_mean=float(values.mean()),
                        reference_success_seed_se=float(values.std(ddof=1)/np.sqrt(len(rows))) if len(rows)>1 else '',
                        cheap_success_mean=float(proxy.mean()),
                        mean_purchased_queries=float(np.mean([r['purchased_reference_queries'] for r in rows]))))
    return out


def paired_endpoint(eval_rows, updates):
    final = {(r['horizon'],r['method'],r['seed']):r for r in eval_rows if r['update']==updates}
    rows = []
    for h in sorted({r['horizon'] for r in eval_rows}):
        for method in POLICIES:
            for baseline in ('full', 'whole_group_residual', 'proxy'):
                if method == baseline:
                    continue
                seeds = sorted(s for hh,m,s in final if hh==h and m==method and (h,baseline,s) in final)
                d = np.asarray([final[h,method,s]['reference_success']-final[h,baseline,s]['reference_success'] for s in seeds])
                rows.append(dict(horizon=h, method=method, baseline=baseline,
                                 updates=updates, paired_seeds=len(seeds),
                                 success_difference=float(d.mean()),
                                 paired_seed_se=float(d.std(ddof=1)/np.sqrt(len(d))) if len(d)>1 else '',
                                 comparison='same rollout count; different purchased-query counts'))
    return rows


def matched_query_view(eval_rows):
    """Compare observed checkpoints only; no interpolation or same-budget claim.

    Each partial method's final mean purchased budget defines a reference point.
    Select each other method's latest observed checkpoint at or below that budget,
    seed by seed, and report its ACTUAL query and rollout counts. Proxy has zero
    paid labels and remains rollout-capped, so it is explicitly identified.
    """
    out = []
    for h in sorted({r['horizon'] for r in eval_rows}):
        hrows = [r for r in eval_rows if r['horizon']==h]
        final_update = max(r['update'] for r in hrows)
        anchors = [r for r in hrows if r['method']=='rr_completion' and r['update']==final_update]
        budget = float(np.mean([r['purchased_reference_queries'] for r in anchors]))
        for method in POLICIES:
            for seed in sorted({r['seed'] for r in hrows}):
                available = [r for r in hrows if r['method']==method and r['seed']==seed and r['purchased_reference_queries']<=budget]
                r = max(available, key=lambda rr:rr['update'])
                out.append(dict(horizon=h, method=method, seed=seed,
                                shared_query_ceiling=budget, update=r['update'],
                                actual_queries=r['purchased_reference_queries'],
                                actual_training_trajectories=r['generated_training_trajectories'],
                                reference_success=r['reference_success'],
                                comparison='observed checkpoint under ceiling; unequal residual budget; no interpolation',
                                zero_query_proxy=method=='proxy'))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--updates', type=int, default=300)
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizons', nargs='+', type=int, default=[12,24,48])
    parser.add_argument('--policies', nargs='+', choices=POLICIES, default=list(POLICIES))
    parser.add_argument('--eval-episodes', type=int, default=256)
    parser.add_argument('--eval-every', type=int, default=25)
    parser.add_argument('--group-size', type=int, default=8)
    parser.add_argument('--audit-fraction', type=float, default=.5)
    parser.add_argument('--completion-probability', type=float, default=.55)
    parser.add_argument('--survival-exponent', type=float, default=.5)
    parser.add_argument('--initial-preference', type=float, default=.9)
    parser.add_argument('--learning-rate', type=float, default=.5)
    parser.add_argument('--max-grad-norm', type=float, default=1.)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.smoke:
        args.updates, args.seeds, args.eval_episodes, args.eval_every = 5, 1, 64, 5
    if min(args.updates,args.seeds,args.eval_episodes,args.eval_every) < 1 or args.group_size < 2:
        parser.error('Counts must be positive and group size must be at least 2.')
    if not .005 <= args.audit_fraction <= 1 or not 0 <= args.completion_probability <= 1:
        parser.error('Invalid audit fraction or completion probability.')
    if args.learning_rate <= 0 or args.max_grad_norm <= 0:
        parser.error('Learning rate and gradient norm cap must be positive.')
    out = args.output or ROOT/'results'/('stateful_smoke' if args.smoke else 'stateful_training')
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f'Refusing to overwrite a populated output directory: {out}')
    out.mkdir(parents=True, exist_ok=True)
    (out/'trajectories').mkdir()
    start = time.perf_counter()
    metadata = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                    runtime=dict(python=sys.version, executable=sys.executable,
                                 numpy=np.__version__, platform=platform.platform()),
                    study='constructed stateful tool dependency-repair policy training',
                    no_llm_or_public_benchmark=True, parameters={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
                    feature_names=FEATURE_NAMES, action_names=ACTION_NAMES,
                    environment_checks=environment_self_check(),
                    notes=['Softmax policy; one on-policy SGD update, averaged action scores; no replay PPO epochs.',
                           'Query count is a resource unit. No artificial sleep or measured expensive-verifier speedup.',
                           'Cheap negatives imply reference negatives and are inferred free under every method.',
                           'Evaluation and offline diagnostic checks are separately accounted and never train the policy.'],
                    source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in [Path(__file__),ROOT/'src/stateful_env.py',ROOT/'src/reward_audit.py',ROOT/'docs/stateful_protocol.md']})
    (out/'manifest.json').write_text(json.dumps(metadata, indent=2)+'\n')
    for relpath in metadata['source_sha256']:
        copied = out/'executed_source'/relpath
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/relpath, copied)
    training, evaluation, accounting = [], [], []
    for h in args.horizons:
        for seed in range(args.seeds):
            for method in args.policies:
                tr, ev, ac = run_one(args, method, h, seed, out)
                training.extend(tr); evaluation.extend(ev); accounting.append(ac)
    write_csv(out/'training.csv', training)
    write_csv(out/'evaluation.csv', evaluation)
    write_csv(out/'summary.csv', summarize(evaluation))
    if set(args.policies) == set(POLICIES):
        write_csv(out/'paired_endpoint.csv', paired_endpoint(evaluation, args.updates))
        write_csv(out/'query_ceiling_view.csv', matched_query_view(evaluation))
    metadata.update(completed_utc=datetime.now(timezone.utc).isoformat(),
                    wall_seconds=time.perf_counter()-start, runs=accounting,
                    numeric_sha256={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted(out.glob('*.csv'))})
    (out/'manifest.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(dict(output=str(out), wall_seconds=metadata['wall_seconds'], runs=len(accounting))))


if __name__ == '__main__':
    main()
