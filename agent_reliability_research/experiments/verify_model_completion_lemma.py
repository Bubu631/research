"""Independent exact-enumeration check of the count-compressed moment lemma.

This file is independent of src/reward_audit.py and never imports it.
"""
from pathlib import Path
from itertools import product
from datetime import datetime, timezone
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def count_pmf(p):
    value = np.array([1.])
    for x in p:
        value = np.convolve(value, [1-x, x])
    return value


def split_binary(labels):
    labels = np.asarray(labels)
    g = labels.shape[-1]
    k = labels.sum(axis=-1, keepdims=True)
    denom = np.sqrt(k*(g-k))
    a = np.zeros(labels.shape)
    np.divide(g*labels-k, denom, out=a, where=denom>0)
    return np.c_[np.maximum(a, 0), np.minimum(a, 0)]


def moment_by_counts(p):
    G = len(p)
    plus = np.zeros(G+1); minus = np.zeros(G+1)
    k = np.arange(1, G)
    plus[k] = np.sqrt((G-k)/k)
    minus[k] = -np.sqrt(k/(G-k))
    result = []
    for count in range(G+1):
        prefix = count_pmf(p[:count]); rem = p[count:]
        future = count_pmf(rem)
        other = [count_pmf(np.delete(rem, j)) for j in range(len(rem))]
        M = 0.
        for s, mass in enumerate(prefix):
            idx = s+np.arange(len(future))
            a = future@plus[idx]; b = future@minus[idx]
            square = s*a*a+(count-s)*b*b
            for j, prob in enumerate(rem):
                idx = s+np.arange(len(other[j]))
                pa = prob*(other[j]@plus[idx+1])
                na = (1-prob)*(other[j]@minus[idx])
                square += pa*pa+na*na
            M += mass*square
        result.append(M)
    return np.asarray(result)


def moment_by_all_patterns(p):
    G = len(p)
    r = np.asarray(list(product([0,1], repeat=G)), dtype=np.int8)
    prob = np.prod(np.where(r, p, 1-p), axis=1)
    phi = split_binary(r)
    result = []
    code = np.zeros(len(r), dtype=int)
    for k in range(G+1):
        if k:
            code = 2*code+r[:, k-1]
        mass = np.bincount(code, weights=prob, minlength=2**k)
        total = np.zeros((2**k, 2*G))
        for j in range(2*G):
            total[:,j] = np.bincount(code, weights=prob*phi[:,j], minlength=2**k)
        M = (np.divide((total*total).sum(axis=1), mass,
                       out=np.zeros_like(mass), where=mass>0)).sum()
        result.append(M)
    return np.asarray(result)


def main():
    rng = np.random.default_rng(202609122)
    rows=[]
    for G in list(range(2,9))+[16]:
        p = rng.uniform(.04,.96,G)
        direct=moment_by_all_patterns(p); count=moment_by_counts(p)
        error=float(np.max(abs(direct-count)))
        endpoint=G*(1-np.prod(p)-np.prod(1-p))
        assert error<1e-10,(G,error)
        assert abs(count[-1]-endpoint)<1e-10
        assert np.min(np.diff(count)) >= -1e-12
        rows.append(dict(group_size=G,enumerated_labels=2**G,
                         maximum_moment_error=error,minimum_increment=float(np.min(np.diff(count))),
                         endpoint_error=float(abs(count[-1]-endpoint))))
    value=dict(status='passed',recorded_at_utc=datetime.now(timezone.utc).isoformat(),
               rows=rows,seed=202609122,
               source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               scope='Independent Bernoulli completion; fixed order; unweighted coefficient Euclidean norm; epsilon=0.')
    (ROOT/'results/model_completion_lemma_checks.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value,indent=2))


if __name__=='__main__':main()
