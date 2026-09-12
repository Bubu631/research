"""Exact finite-group checks for the feasibility memo; no RL training claims.

Run from repository: python experiments/verify_theory_feasibility.py
Only this script's JSON is written. Exact finite sums, not Monte Carlo, establish
numerical checks; the memo supplies the mathematical arguments.
"""
from pathlib import Path
from itertools import product
from math import comb
from datetime import datetime, timezone
import hashlib
import json
import numpy as np
from scipy.optimize import brentq, minimize

ROOT = Path(__file__).resolve().parents[1]


def group_advantage(r):
    r = np.asarray(r, float)
    sd = r.std(ddof=0)
    return np.zeros_like(r) if sd < 1e-14 else (r-r.mean())/sd


def group_update(r, score):
    return float(np.dot(group_advantage(r), score)/len(r))


def boolean_degree_checks():
    rows = []
    for G in range(2, 13):
        scores = np.sin(np.arange(G)+.17)
        centered = scores-scores.mean()
        rewards = np.asarray([[int(mask >> j & 1) for j in range(G)] for mask in range(1 << G)])
        values = np.asarray([group_update(r, scores) for r in rewards])
        coefficient = values.copy()
        for j in range(G):
            for mask in range(1 << G):
                if mask >> j & 1:
                    coefficient[mask] -= coefficient[mask ^ (1 << j)]
        analytic = np.zeros_like(coefficient)
        for mask in range(1, (1 << G)-1):
            ids = [j for j in range(G) if mask >> j & 1]
            L = len(ids)
            diff = sum((-1)**(L-j)*comb(L-1, j-1)/np.sqrt(j*(G-j)) for j in range(1, L+1))
            analytic[mask] = centered[ids].sum()*diff
        error = float(np.max(np.abs(coefficient-analytic)))
        degree = max(mask.bit_count() for mask in range(1 << G) if abs(coefficient[mask]) > 1e-9)
        target = G-1 if G % 2 == 0 else G-2
        assert degree == target, (G, degree, target)
        assert error < 1e-10, (G, error)
        rows.append(dict(group_size=G, computed_degree=degree, theorem_degree=target,
                         maximum_mobius_formula_error=error,
                         full_interaction_coefficient=float(coefficient[-1])))
    return rows


def completions(p, score):
    G = len(p)
    rewards = np.asarray(list(product([0, 1], repeat=G)))
    probability = np.prod(np.where(rewards, p, 1-p), axis=1)
    target = np.asarray([group_update(r, score) for r in rewards])
    values = np.empty((len(rewards), G+1))
    for i, r in enumerate(rewards):
        for k in range(G+1):
            use = (rewards[:, :k] == r[:k]).all(axis=1)
            values[i, k] = np.dot(probability[use], target[use])/probability[use].sum()
    return rewards, probability, target, values


def roulette_checks():
    G = 5
    model_p = np.asarray([.12, .33, .45, .67, .86])
    scores = np.asarray([-.7, .2, 1.1, -.4, .8])
    rewards, prob, target, values = completions(model_p, scores)
    max_error = 0.
    for i, r in enumerate(rewards):
        # Continuation for query j depends only on labels at indices < j.
        q = np.r_[.73, [.27+.38*r[j-1]+.015*j for j in range(1, G)]]
        Q = np.r_[1., np.cumprod(q)]
        stop_probability = np.r_[Q[:-1]-Q[1:], Q[-1]]
        estimates = np.r_[values[i, 0], values[i, 0]+np.cumsum(np.diff(values[i])/Q[1:])]
        mean = float(stop_probability@estimates)
        max_error = max(max_error, abs(mean-target[i]))
        assert abs(mean-target[i]) < 1e-12
    # Separate exact variance test for deterministic survival and a correct model.
    Q = np.asarray([.84, .67, .48, .31, .17])
    stop_probability = np.r_[1-Q[0], Q[:-1]-Q[1:], Q[-1]]
    delta = np.diff(values, axis=1)
    estimate = np.column_stack([values[:, 0], values[:, 0, None]+np.cumsum(delta/Q, axis=1)])
    exact_var = float(np.sum(prob[:, None]*stop_probability[None, :]*estimate**2) - (prob@target)**2)
    increments = np.sum(prob[:, None]*delta**2, axis=0)
    formula_var = float(np.sum(increments/Q))
    cross = delta.T@(prob[:, None]*delta)
    off_diagonal = cross-np.diag(np.diag(cross))
    assert abs(exact_var-formula_var) < 1e-12
    assert np.max(np.abs(off_diagonal)) < 1e-12
    return dict(group_size=G, all_reward_configurations=2**G,
                pointwise_unbiasedness_max_error=max_error,
                note='Pointwise RR check holds regardless of whether model probabilities match the reward law.',
                exact_variance_under_correct_model=exact_var,
                sum_increment_variance_over_survival=formula_var,
                orthogonality_max_error=float(np.max(np.abs(off_diagonal))),
                deterministic_survival=Q.tolist(), expected_queries=float(Q.sum()))


def pava_solution(a, c, budget):
    blocks = []
    for j in range(len(a)):
        blocks.append(([j], a[j], c[j]))
        while len(blocks) >= 2 and blocks[-2][1]/blocks[-2][2] < blocks[-1][1]/blocks[-1][2]:
            b2 = blocks.pop(); b1 = blocks.pop()
            blocks.append((b1[0]+b2[0], b1[1]+b2[1], b1[2]+b2[2]))
    def q(lam):
        result = np.empty_like(a)
        for ids, sa, sc in blocks:
            result[ids] = min(1., np.sqrt(sa/(lam*sc)))
        return result
    upper = 1.
    while c@q(upper) > budget:
        upper *= 2
    lam = brentq(lambda x: c@q(x)-budget, 1e-15, upper, xtol=1e-13)
    return q(lam)


def allocation_checks():
    rng = np.random.default_rng(202609121)
    max_objective_gap = 0.
    for _ in range(20):
        n = 6
        a = rng.uniform(.2, 2., n); c = rng.uniform(.5, 3., n)
        budget = .4*c.sum()
        Q = pava_solution(a, c, budget)
        cons = [dict(type='ineq', fun=lambda x: x[:-1]-x[1:]),
                dict(type='ineq', fun=lambda x: budget-c@x)]
        fit = minimize(lambda x: float((a/x).sum()), np.full(n, .35),
                       jac=lambda x: -a/x**2, bounds=[(1e-6, 1.)]*n,
                       constraints=cons, method='SLSQP',
                       options={'ftol':1e-10, 'maxiter':1000})
        # SLSQP occasionally reports a line-search code at an otherwise precise optimum.
        assert np.max(np.maximum(0., fit.x[1:]-fit.x[:-1])) < 1e-7
        assert c@fit.x <= budget+1e-7
        gap = abs((a/Q).sum()-fit.fun)
        max_objective_gap = max(max_objective_gap, float(gap))
        assert gap < 1e-6, (gap, fit.message)
        assert np.max(Q[1:]-Q[:-1]) <= 1e-12
        assert abs(c@Q-budget) < 1e-10
    return dict(cases=20, maximum_objective_gap_vs_independent_SLSQP=max_objective_gap,
                scope='Fixed query order, deterministic survival and costs, supplied positive increment second moments.')


def counterexamples():
    r = np.asarray([1., 0.]); score = np.asarray([1., -1.]); q = .5
    oracle = group_update(r, score)
    ht_then_normalize = (1-q)*group_update([0., 0.], score)+q*group_update([1/q, 0.], score)
    # Unbiased scalar advantage A=0 from noisy +/-1, ratio2, upper clip1.2.
    clipped_oracle = 0.
    clip_after_estimate = .5*min(2., 1.2)+.5*min(-2., -1.2)
    assert oracle == 1. and ht_then_normalize == .5
    assert abs(clip_after_estimate+.4) < 1e-12
    # Positive affine correction cannot change exact group-standardized advantages.
    rr = np.asarray([1., 0., 1., 0.]); corrected=(rr-.15)/(1-.15-.2)
    affine_error=float(np.max(np.abs(group_advantage(rr)-group_advantage(corrected))))
    assert affine_error < 1e-12
    return dict(ht_rewards_then_normalize=dict(oracle_update=oracle, expected_update=ht_then_normalize),
                unbiased_advantage_then_clip=dict(oracle_objective=clipped_oracle, expected_objective=clip_after_estimate),
                affine_flip_correction_normalization_max_difference=affine_error)


def main():
    result=dict(status='passed', computed_at_utc=datetime.now(timezone.utc).isoformat(),
                binary_grpo_degree=boolean_degree_checks(), adaptive_roulette=roulette_checks(),
                fixed_survival_pava=allocation_checks(), counterexamples=counterexamples(),
                seed=202609121, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='Finite exact enumeration and optimization checks; no empirical RL performance or novelty claim.')
    output=ROOT/'results/theory_feasibility_checks.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
