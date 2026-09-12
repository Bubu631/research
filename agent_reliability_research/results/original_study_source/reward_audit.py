"""Finite-group reward auditing. No language-model or environment dependencies.

The target is the full-label normalized, sign-split advantage vector. The
randomization corrects this vector, not individual rewards passed through a
subsequent nonlinear normalizer. All probabilities must precede hidden labels.
"""
from __future__ import annotations
import numpy as np


def split_advantages(rewards, epsilon=0.0):
    r = np.asarray(rewards, dtype=np.float64)
    mean = r.mean(axis=-1, keepdims=True)
    sd = r.std(axis=-1, keepdims=True)
    a = np.divide(r - mean, sd + epsilon, out=np.zeros_like(r), where=sd > 0)
    return np.concatenate((np.maximum(a, 0), np.minimum(a, 0)), axis=-1)


def count_distribution(probabilities):
    out = np.array([1.0])
    for p in probabilities:
        nxt = np.zeros(len(out)+1)
        nxt[:-1] += out*(1-p)
        nxt[1:] += out*p
        out = nxt
    return out


def completion(probabilities, epsilon=0.0):
    """Exact independent-Bernoulli completion, O(G^3), zero random sampling.

    Degenerate probabilities are allowed for already observed labels. The model
    is a variance-reduction device; its correctness is not assumed by auditing.
    """
    p = np.asarray(probabilities, dtype=np.float64)
    if p.ndim != 1 or len(p) < 2 or np.any((p < 0) | (p > 1)):
        raise ValueError('Need G>=2 probabilities in [0,1].')
    g = len(p)
    k = np.arange(g, dtype=np.float64)
    mu_pos = (k+1)/g
    mu_neg = k/g
    dp = np.sqrt(mu_pos*(1-mu_pos))
    dn = np.sqrt(mu_neg*(1-mu_neg))
    vp = np.divide(1-mu_pos, dp+epsilon, out=np.zeros(g), where=dp > 0)
    vn = np.divide(-mu_neg, dn+epsilon, out=np.zeros(g), where=dn > 0)
    pos, neg = np.zeros(g), np.zeros(g)
    for i in range(g):
        d = count_distribution(np.delete(p, i))
        pos[i] = p[i]*np.dot(d, vp)
        neg[i] = (1-p[i])*np.dot(d, vn)
    return np.r_[pos, neg]


def query_order(probabilities, costs=None, mode='uncertainty'):
    p = np.asarray(probabilities, dtype=np.float64)
    cost = np.ones_like(p) if costs is None else np.asarray(costs)
    if mode == 'uncertainty':
        score = p*(1-p)/cost
    elif mode == 'index':
        score = -np.arange(len(p))
    else:
        raise ValueError(mode)
    return np.argsort(-score, kind='stable')


def completion_path(probabilities, labels, order, epsilon=0.0):
    """Offline evaluation helper. Online users should call sequential_audit."""
    p = np.asarray(probabilities, dtype=np.float64).copy()
    r = np.asarray(labels)
    out = [completion(p, epsilon)]
    for i in order:
        p[i] = r[i]
        out.append(completion(p, epsilon))
    return np.stack(out)


def make_survival(size, budget, exponent=0.0, floor=0.005, costs=None):
    """A predictable, monotone survival schedule with specified expected cost."""
    c = np.ones(size) if costs is None else np.asarray(costs, dtype=np.float64)
    if not (np.all(c > 0) and floor*c.sum() <= budget <= c.sum()):
        raise ValueError('Budget must lie between floor*total and total cost.')
    shape = np.arange(1, size+1, dtype=float)**(-exponent)
    lo, hi = 0., max(1., 1/shape[-1])
    for _ in range(80):
        mid = (lo+hi)/2
        q = np.clip(mid*shape, floor, 1)
        if q@c < budget:
            lo = mid
        else:
            hi = mid
    return np.clip((lo+hi)/2*shape, floor, 1)


def cutoff_probabilities(survival):
    q = np.asarray(survival, dtype=np.float64)
    if np.any(q <= 0) or q[0] > 1 or np.any(np.diff(q)>1e-12):
        raise ValueError('Survival must be positive, <=1, nonincreasing.')
    return np.r_[1-q[0], q[:-1]-q[1:], q[-1]]


def all_prefix_estimates(path, survival):
    q = np.asarray(survival)
    return np.vstack((path[0], path[0]+np.cumsum(np.diff(path,axis=0)/q[:,None],axis=0)))


def sequential_audit(probabilities, oracle_query, order, survival, rng, epsilon=0.0):
    """Online interface. oracle_query(i) is called only when label i is bought.

    A single uniform random variable implements nested inclusion. Order and
    survival are supplied before any label is queried. Auditing has an expected
    budget, not a deterministic per-group cap.
    """
    q = np.asarray(survival, dtype=np.float64)
    cutoff_probabilities(q)
    p = np.asarray(probabilities, dtype=np.float64).copy()
    previous = completion(p, epsilon)
    estimate = previous.copy()
    u = rng.random()
    queried = []
    for k, i in enumerate(order):
        if u >= q[k]:
            break
        label = oracle_query(int(i))
        if label not in (0, 1):
            raise ValueError('Reference verifier must return a binary label.')
        queried.append(int(i))
        p[i] = label
        current = completion(p, epsilon)
        estimate += (current-previous)/q[k]
        previous = current
    return estimate, queried


def clipped_surrogate(coefficients, ratios, clip=0.2):
    c, r = np.asarray(coefficients), np.asarray(ratios)
    g = len(r)
    bounded = np.clip(r,1-clip,1+clip)
    return (c[:g]@np.minimum(r,bounded) + c[g:]@np.maximum(r,bounded))/g


def clipped_ratio_derivative(coefficients, ratios, clip=0.2):
    """Derivative w.r.t ratios away from clipping kinks."""
    c, r = np.asarray(coefficients), np.asarray(ratios)
    g = len(r)
    return (c[:g]*(r<1+clip) + c[g:]*(r>1-clip))/g
