"""Constructed stateful dependency-repair tools; not an LLM benchmark.

A release has a chain of n components. Editing source i changes its version.
A build records the *current built* prefix from its parent, so rebuilding only
the edited component leaves downstream cached artifacts stale. Attestation and
publication retain immutable artifact fingerprints. The reference checker
executes all release invariants; a deliberately incomplete cheap check only
checks the local version of each published component.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

ACTION_NAMES = ('noop', 'edit_to_spec', 'build', 'attest', 'publish')
FEATURE_NAMES = ('intercept', 'phase_edit', 'phase_build', 'phase_attest',
                 'phase_publish', 'source_version', 'requested_version',
                 'artifact_local_matches_request', 'published_local_matches_request',
                 'attestation_matches_current_artifact', 'publication_matches_current_artifact',
                 'recorded_parent_matches_current_parent_artifact',
                 'component_position', 'remaining_horizon', 'size_scaled')


@dataclass(frozen=True)
class ReleaseTask:
    required: tuple[int, ...]
    changed_component: int


@dataclass(frozen=True)
class FinalRelease:
    task: ReleaseTask
    source: tuple[int, ...]
    artifacts: tuple[tuple[int, ...], ...]
    attestations: tuple[tuple[int, ...], ...]
    published: tuple[tuple[int, ...], ...]


def sample_task(rng, horizon):
    if horizon % 4 or horizon < 12:
        raise ValueError('Horizon must be a multiple of 4 and at least 12.')
    n = horizon//4
    # Upstream changes affect several downstream components. This is a fixed
    # declared task distribution, not selection based on policy outcomes.
    changed = int(rng.integers(0, max(1, (n+1)//2)))
    required = [0]*n
    required[changed] = 1
    return ReleaseTask(tuple(required), changed)


class DependencyRepair:
    def __init__(self, task):
        self.task = task
        self.n = len(task.required)
        self.horizon = 4*self.n
        self.step_number = 0
        self.source = [0]*self.n
        self.artifacts = [tuple([0]*(i+1)) for i in range(self.n)]
        self.attestations = self.artifacts.copy()
        self.published = self.artifacts.copy()

    def observation(self):
        if self.step_number >= self.horizon:
            raise RuntimeError('Episode has terminated.')
        i = self.step_number % self.n
        phase = self.step_number//self.n
        f = np.zeros(len(FEATURE_NAMES), dtype=np.float64)
        f[0] = 1
        f[1+phase] = 1
        # These are ordinary inspectable workspace metadata. No reference
        # checker or terminal label is consulted to construct observations.
        f[5] = self.source[i]
        f[6] = self.task.required[i]
        f[7] = self.artifacts[i][-1] == self.task.required[i]
        f[8] = self.published[i][-1] == self.task.required[i]
        f[9] = self.attestations[i] == self.artifacts[i]
        f[10] = self.published[i] == self.artifacts[i]
        f[11] = i == 0 or self.artifacts[i][:-1] == self.artifacts[i-1]
        f[12] = i/max(1, self.n-1)
        f[13] = (self.horizon-self.step_number)/self.horizon
        f[14] = self.n/12
        return f

    def step(self, action):
        if not (0 <= action < len(ACTION_NAMES)) or self.step_number >= self.horizon:
            raise ValueError('Invalid action or terminated episode.')
        i = self.step_number % self.n
        if action == 1:
            self.source[i] = self.task.required[i]
        elif action == 2:
            prefix = () if i == 0 else self.artifacts[i-1]
            self.artifacts[i] = prefix+(self.source[i],)
        elif action == 3:
            self.attestations[i] = self.artifacts[i]
        elif action == 4:
            self.published[i] = self.artifacts[i]
        self.step_number += 1

    def terminal_snapshot(self):
        if self.step_number != self.horizon:
            raise RuntimeError('Snapshot requested before termination.')
        return FinalRelease(self.task, tuple(self.source), tuple(self.artifacts),
                            tuple(self.attestations), tuple(self.published))


def cheap_verifier(final):
    """Incomplete release check; it omits dependencies and attestation."""
    return int(all(p[-1] == v for p, v in zip(final.published, final.task.required)))


def reference_verifier(final):
    """Execute every invariant; no early exit or reuse of the cheap label."""
    checks = []
    for i, version in enumerate(final.task.required):
        expected = final.task.required[:i+1]
        checks.extend((final.source[i] == version,
                       final.artifacts[i] == expected,
                       final.published[i] == expected,
                       final.attestations[i] == expected))
    return int(all(checks))


def initial_policy(preferred_probability=.9):
    if not 0 < preferred_probability < 1:
        raise ValueError('Initialization probability must lie in (0,1).')
    weights = np.zeros((len(FEATURE_NAMES), len(ACTION_NAMES)))
    logit = np.log((len(ACTION_NAMES)-1)*preferred_probability/(1-preferred_probability))
    for phase in range(4):
        weights[1+phase, 1+phase] = logit
    return weights


def rollout(weights, task, uniforms, need_score=True):
    env = DependencyRepair(task)
    if len(uniforms) != env.horizon:
        raise ValueError('Need exactly one action uniform per environment step.')
    actions = np.empty(env.horizon, dtype=np.int8)
    score = np.zeros_like(weights)
    for t, u in enumerate(uniforms):
        features = env.observation()
        logits = features@weights
        p = np.exp(logits-logits.max())
        p /= p.sum()
        a = min(int(np.searchsorted(np.cumsum(p), u)), len(p)-1)
        actions[t] = a
        if need_score:
            centered = -p
            centered[a] += 1
            score += np.outer(features, centered)
        env.step(a)
    # The policy target uses average action-token score per trajectory.
    return env.terminal_snapshot(), actions, score/env.horizon


def replay(task, actions):
    env = DependencyRepair(task)
    for a in actions:
        env.step(int(a))
    return env.terminal_snapshot()


class AuditOracle:
    """Only purchased labels enter the estimator; every call is logged."""
    def __init__(self, finals):
        self._finals = finals
        self.records = []
        self._bought = set()

    def __call__(self, index):
        if index in self._bought:
            raise RuntimeError('Duplicate reference query in a group.')
        label = reference_verifier(self._finals[index])
        self._bought.add(index)
        self.records.append((int(index), int(label)))
        return label


def environment_self_check():
    # Exact minimal failure examples, including a same-local-version stale
    # dependency that the cheap checker accepts.
    task = ReleaseTask((1, 0, 0), 0)
    correct = [1]*3+[2]*3+[3]*3+[4]*3
    full = replay(task, correct)
    assert cheap_verifier(full) == reference_verifier(full) == 1
    stale_actions = correct.copy()
    stale_actions[4] = 0
    stale = replay(task, stale_actions)
    assert cheap_verifier(stale) == 1 and reference_verifier(stale) == 0
    no_attestation = correct.copy()
    no_attestation[6] = 0
    missed = replay(task, no_attestation)
    assert cheap_verifier(missed) == 1 and reference_verifier(missed) == 0
    no_edit = correct.copy()
    no_edit[0] = 0
    missed_edit = replay(task, no_edit)
    assert cheap_verifier(missed_edit) == reference_verifier(missed_edit) == 0
    return dict(correct_release=True, dependency_omission_detected=True,
                attestation_omission_detected=True, local_failure_detected=True)
