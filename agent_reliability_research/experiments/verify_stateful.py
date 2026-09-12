"""Independent finite-difference, truth-boundary and audit integration checks."""
from pathlib import Path
import json
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'experiments'))
from src.stateful_env import (DependencyRepair, AuditOracle, cheap_verifier,
                             initial_policy, rollout, sample_task, reference_verifier,
                             environment_self_check)
from src.reward_audit import split_advantages, make_survival, cutoff_probabilities
from stateful_training import coefficients


def held_action_log_likelihood(weights, task, actions):
    env=DependencyRepair(task)
    value=0.
    for a in actions:
        logits=env.observation()@weights
        maximum=logits.max()
        log_normalizer=maximum+np.log(np.exp(logits-maximum).sum())
        value+=logits[a]-log_normalizer
        env.step(int(a))
    return value/len(actions)


def main():
    rng=np.random.default_rng(20260912991)
    weights=initial_policy()+rng.normal(0,.1,initial_policy().shape)
    task=sample_task(rng,12)
    final,actions,score=rollout(weights,task,rng.random(12))
    fd=np.zeros_like(weights)
    step=1e-5
    for i in range(weights.shape[0]):
        for j in range(weights.shape[1]):
            plus=weights.copy();minus=weights.copy()
            plus[i,j]+=step;minus[i,j]-=step
            fd[i,j]=(held_action_log_likelihood(plus,task,actions)-
                     held_action_log_likelihood(minus,task,actions))/(2*step)
    score_error=float(np.max(np.abs(score-fd)))
    assert score_error<1e-9
    boundary_cases=0
    max_error=0.
    max_queries=0
    for horizon in (12,24,48):
        finals=[]
        for _ in range(64):
            final,_,_=rollout(initial_policy(),sample_task(rng,horizon),rng.random(horizon))
            finals.append(final)
            true,proxy=reference_verifier(final),cheap_verifier(final)
            assert not true or proxy
            boundary_cases+=1
        for start in range(0,len(finals),8):
            group=finals[start:start+8]
            proxy=np.asarray([cheap_verifier(f) for f in group])
            truth=np.asarray([reference_verifier(f) for f in group])
            candidates=np.flatnonzero(proxy)
            target=split_advantages(truth)
            m=len(candidates)
            if not m:
                continue
            q=make_survival(m,.5*m,exponent=.5)
            stops=cutoff_probabilities(q)
            average=np.zeros(16)
            for k,prob in enumerate(stops):
                if not prob:
                    continue
                lo=0. if k==m else q[k]
                hi=1. if k==0 else q[k-1]
                u=(lo+hi)/2
                oracle=AuditOracle(group)
                value=coefficients('rr_completion',proxy,oracle,np.full(8,u))
                actual=[i for i,_ in oracle.records]
                assert actual==candidates[:k].tolist()
                assert len(actual)==k
                assert all(proxy[i] for i in actual)
                average+=prob*value
                max_queries=max(max_queries,len(actual))
            error=float(np.max(np.abs(average-target)))
            max_error=max(max_error,error)
            assert error<1e-12
            # Whole-group residual is independently enumerated at its two atoms.
            whole=[]
            for u in (.25,.75):
                oracle=AuditOracle(group)
                whole.append(coefficients('whole_group_residual',proxy,oracle,np.full(8,u)))
                assert len(oracle.records)==(m if u<.5 else 0)
            assert np.max(np.abs(np.mean(whole,axis=0)-target))<1e-12
    result=dict(status='passed',environment=environment_self_check(),
                score_finite_difference_max_error=score_error,
                generated_release_boundary_checks=boundary_cases,
                integrated_rr_all_cutoffs_max_error=max_error,
                maximum_reference_queries_per_group=max_queries,
                seed=20260912991,
                scope='No full training; exact cutoff expectation on actual generated releases and numerical likelihood derivatives.')
    (ROOT/'results/stateful_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
