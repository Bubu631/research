"""Independent theory diagnostics for repeat-versus-validation selection.

No study data, fitted parameters, or main experiment implementation are imported.
This verifies algebra and constructs counterexamples; it does not certify novelty.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]


def kg(gap, innovation_sd):
    gap = abs(float(gap))
    if innovation_sd <= 0:
        return 0.
    x = gap/innovation_sd
    return float(innovation_sd*norm.pdf(x)-gap*norm.sf(x))


def update_covariance(covariance, loading, noise):
    cross = covariance@loading
    return covariance-np.outer(cross, cross)/(loading@cross+noise)


def check_topk_formula():
    rng = np.random.default_rng(2026091115)
    errors = []
    for _ in range(60):
        m = rng.normal(size=7)
        k = int(rng.integers(1, 7))
        i = int(rng.integers(7))
        sd = float(np.exp(rng.uniform(-2, .5)))
        competitor = np.partition(np.delete(m, i), k-1)[k-1]
        before = np.partition(m, k-1)[:k].sum()
        def improvement(z):
            changed = m.copy()
            changed[i] += sd*z
            return (before-np.partition(changed, k-1)[:k].sum())*norm.pdf(z)
        kink = (competitor-m[i])/sd
        value, _ = quad(improvement, -12, 12,
                        points=[kink] if -12 < kink < 12 else None,
                        epsabs=1e-11, limit=150)
        errors.append(abs(value-kg(m[i]-competitor, sd)))
    assert max(errors) < 1e-9
    return dict(cases=len(errors), maximum_absolute_error=max(errors),
                normal_integral_range=[-12, 12],
                assumptions='Only one posterior target mean changes; all other means stay fixed')


def check_repeat_floor():
    tau2, beta2, noise = .35**2, .30**2, .6
    initial = np.diag([tau2, beta2])
    repeat = np.ones(2)
    exact_floor = tau2*beta2/(tau2+beta2)
    rows = []
    for n in [1, 10, 100, 10000, 100000000]:
        post = update_covariance(initial, repeat, noise/n)
        formula = tau2-tau2**2/(tau2+beta2+noise/n)
        assert abs(post[0, 0]-formula) < 1e-14
        rows.append(dict(repeat_count=n, target_posterior_variance=float(post[0, 0]),
                         excess_above_floor=float(post[0, 0]-exact_floor)))
    # Once the exact biased signal is observed, further repetitions carry no
    # additional target information, whereas a clean audit can still inform it.
    limiting = update_covariance(initial, repeat, 0.)
    covariance_with_repeat = float((limiting@repeat)[0])
    audit = np.array([1., 0.])
    repeat_sd = abs(covariance_with_repeat)/np.sqrt(repeat@limiting@repeat+noise)
    audit_noise = .2
    audit_sd = abs((limiting@audit)[0])/np.sqrt(audit@limiting@audit+audit_noise)
    assert abs(covariance_with_repeat) < 1e-14
    assert audit_sd > 0
    # Independent population-level calculation for the two-unit Bayes regret.
    tau, beta = np.sqrt(tau2), np.sqrt(beta2)
    regret_floor = tau/np.sqrt(np.pi)*(1-tau/np.sqrt(tau2+beta2))
    rng = np.random.default_rng(2026091116)
    reps = 400000
    theta = rng.normal(0, tau, (reps, 2))
    bias = rng.normal(0, beta, (reps, 2))
    signal = theta+bias
    chosen = np.argmin(signal, axis=1)
    regret = theta[np.arange(reps), chosen]-theta.min(axis=1)
    mcse = float(regret.std(ddof=1)/np.sqrt(reps))
    z = float((regret.mean()-regret_floor)/mcse)
    assert abs(z) < 6
    return dict(tau2=tau2, beta2=beta2, repeat_noise_variance=noise,
                target_variance_floor=exact_floor, rows=rows,
                covariance_with_repeat_at_limit=covariance_with_repeat,
                repeat_innovation_sd_at_limit=float(repeat_sd),
                audit_innovation_sd_at_limit=float(audit_sd),
                two_unit_bayes_regret_floor=float(regret_floor),
                independent_monte_carlo=dict(seed=2026091116, reps=reps,
                    regret_mean=float(regret.mean()), mcse=mcse, z=z),
                scope='Static independent unit-specific biases; not common group shifts or a changing latent target')


def check_shared_group_bias():
    rng = np.random.default_rng(2026091117)
    theta = rng.normal(size=(200, 12))
    arbitrary_decisions = [np.array([0, 2]), np.array([5]), np.array([8, 10])]
    groups = [np.arange(0, 4), np.arange(4, 8), np.arange(8, 12)]
    quotas = [2, 1, 2]
    bias = rng.normal(0, 5, size=(200, 3))
    changed = theta.copy()
    for g, ids in enumerate(groups):
        changed[:, ids] += bias[:, [g]]
    def constrained_loss(x):
        chosen_sum = sum(x[:, ids].sum(axis=1) for ids in arbitrary_decisions)
        oracle_sum = sum(np.sort(x[:, ids], axis=1)[:, :k].sum(axis=1)
                         for ids, k in zip(groups, quotas))
        return (chosen_sum-oracle_sum)/sum(quotas)
    delta = float(np.max(abs(constrained_loss(theta)-constrained_loss(changed))))
    assert delta < 1e-14
    oracle_old = [np.argsort(theta[:, ids], axis=1)[:, :k] for ids, k in zip(groups, quotas)]
    oracle_new = [np.argsort(changed[:, ids], axis=1)[:, :k] for ids, k in zip(groups, quotas)]
    assert all(np.array_equal(a, b) for a, b in zip(oracle_old, oracle_new))
    # Perfectly correlated posterior uncertainty shifts both candidates equally:
    # the target-level uncertainty is positive but ranking VOI is zero.
    independent_shortcut = kg(0., 1.)
    correct_shared_value = 0.
    return dict(panels=200, quotas=quotas, max_regret_invariance_error=delta,
                all_oracle_memberships_unchanged=True,
                perfectly_correlated_two_unit_example=dict(
                    posterior_covariance=[[1., 1.], [1., 1.]],
                    erroneous_independent_formula=independent_shortcut,
                    exact_joint_kg=correct_shared_value))


def check_cost_ratio_counterexample():
    # Known comparison target zero versus theta~N(0,1). Two actions both measure
    # theta, with noise variances 1 and .1 and costs 1 and 2. Total budget is 2.
    cheap_sd = 1/np.sqrt(2.)
    expensive_sd = 1/np.sqrt(1.1)
    cheap_kg = kg(0., cheap_sd)
    expensive_kg = kg(0., expensive_sd)
    two_cheap_expected_gain = kg(0., np.sqrt(2/3))
    assert cheap_kg > expensive_kg/2
    assert expensive_kg > two_cheap_expected_gain
    return dict(total_budget=2, costs=[1, 2], observation_noise_variances=[1., .1],
                first_action_kg=[cheap_kg, expensive_kg],
                first_action_kg_per_cost=[cheap_kg, expensive_kg/2],
                ratio_policy_first_action='cheap',
                ratio_policy_total_expected_gain=two_cheap_expected_gain,
                one_expensive_action_expected_gain=expensive_kg,
                ratio_policy_expected_value_gap=expensive_kg-two_cheap_expected_gain,
                interpretation='Concrete finite-budget counterexample; cost-normalised myopia is not globally optimal')


def check_uncertainty_and_audit_bias():
    high_var = np.array([[1., -.99], [-.99, 1.]])
    low_var = np.diag([.25, 0.])
    h = np.ones(2)
    noise = .1
    s = [abs((p@h)[0])/np.sqrt(h@p@h+noise) for p in [high_var, low_var]]
    values = [kg(.1, x) for x in s]
    assert high_var[0, 0] > low_var[0, 0] and values[0] < values[1]
    # Both channels may have their own persistent biases. Exact observations of
    # theta+b and theta+d do not fully reveal theta under these Gaussian priors.
    tau2, beta2, audit_bias2 = .1225, .09, .04
    prior = np.diag([tau2, beta2, audit_bias2])
    loading = np.array([[1., 1., 0.], [1., 0., 1.]])
    posterior = prior-prior@loading.T@np.linalg.solve(loading@prior@loading.T, loading@prior)
    floor = 1/(1/tau2+1/beta2+1/audit_bias2)
    assert abs(posterior[0, 0]-floor) < 1e-14
    return dict(boundary_gap=.1, target_variances=[1., .25],
                repeat_target_mean_innovation_sds=list(map(float, s)),
                repeat_kg=values,
                two_independently_biased_channels_target_variance_floor=float(floor),
                interpretation='Total uncertainty differs from actionable information; independent persistent audit bias does not average away')


def main():
    result = dict(status='all checks passed',
        claims='Algebra checks and counterexamples, not novelty or NHS external validation',
        topk_knowledge_gradient=check_topk_formula(),
        repeat_only_floor=check_repeat_floor(),
        benchmark_shared_bias=check_shared_group_bias(),
        budget_counterexample=check_cost_ratio_counterexample(),
        uncertainty_and_audit_bias=check_uncertainty_and_audit_bias(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    output = ROOT/'results/theory_verification.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
