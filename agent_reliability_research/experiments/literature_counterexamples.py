"""Exact checks supporting the independent literature audit, not paper replications.

No model, benchmark, or data from the cited papers is used.  Each example is an
explicit finite construction, enumerated with rational arithmetic.
"""
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_upstream_credit():
    # a0 determines R; a1 has no effect. Branch only after observing a0.
    p, q = F(1, 4), F(1, 2)
    true_pg = p * (1 - p)
    backbone_pg = F(0)
    propagated_pg = F(0)
    for a0, a1, a1_sibling in product((0, 1), repeat=3):
        prob = (p if a0 else 1-p) * (q if a1 else 1-q) * (q if a1_sibling else 1-q)
        r, sibling_r = F(a0), F(a0)
        score = F(a0) - p
        backbone_pg += prob * score * r
        propagated_pg += prob * score * (r-sibling_r)
    assert true_pg == backbone_pg and propagated_pg == 0
    return dict(true_logit_gradient=str(true_pg),
                backbone_gradient=str(backbone_pg),
                local_advantage_propagated_upstream=str(propagated_pg),
                scope="Local zero-mean contrasts alone need not carry an earlier action's mediated effect.")


def check_positive_weight_cancellation():
    # 1D token contributions. Both weights satisfy the CrEST-style numerical
    # envelope [1, 1+0.3*0.28]; this does not instantiate its teacher model.
    g = [F(1), -F(99, 100)]
    weights = [F(1), F(271, 250)]
    base = sum(g)
    weighted = sum(w*x for w, x in zip(weights, g))
    perturbation = abs(weighted-base)
    absolute_bound = F(21, 250)*sum(abs(x) for x in g)
    invalid_relative_bound = F(21, 250)*abs(base)
    assert base > 0 > weighted
    assert perturbation <= absolute_bound
    assert perturbation > invalid_relative_bound
    return dict(base_gradient=str(base), weighted_gradient=str(weighted),
                perturbation=str(perturbation), absolute_bound=str(absolute_bound),
                invalid_relative_bound=str(invalid_relative_bound),
                scope="Positive bounded scalar weights alone do not preserve aggregate direction.")


def check_minimal_is_not_minimum():
    # Success can arise from {a} or jointly from {b,c}; an inclusion-minimal
    # successful set need not have minimum cardinality or be unique.
    universe = ('a', 'b', 'c')
    success = lambda x: 'a' in x or {'b', 'c'}.issubset(x)
    sets = [frozenset(v for v, keep in zip(universe, bits) if keep)
            for bits in product((0, 1), repeat=3)]
    minimal = [x for x in sets if success(x) and
               all(not success(x-{v}) for v in x)]
    assert set(minimal) == {frozenset({'a'}), frozenset({'b', 'c'})}
    return dict(one_minimal_success_sets=sorted([sorted(x) for x in minimal]),
                minimum_cardinality=min(map(len, minimal)),
                scope="A minimized successful edit subset is not a unique causal attribution.")


if __name__ == '__main__':
    report = dict(description=__doc__.strip(), arithmetic="exact fractions; exhaustive enumeration",
                  upstream_credit=check_upstream_credit(),
                  positive_weight_cancellation=check_positive_weight_cancellation(),
                  minimality=check_minimal_is_not_minimum())
    dest = ROOT/'results'/'literature_counterexamples.json'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
