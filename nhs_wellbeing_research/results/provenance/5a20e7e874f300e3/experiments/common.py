"""Numerical definitions shared by reproducible analyses."""
from __future__ import annotations
import csv
import hashlib
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save_csv(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        raise ValueError('Cannot infer columns of empty table')
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

def save_manifest(path, details):
    details = dict(details)
    details['recorded_at_utc'] = datetime.now(timezone.utc).isoformat()
    details['python'] = platform.python_version()
    details['numpy'] = np.__version__
    details['platform'] = platform.platform()
    details['source_sha256'] = {str(p.relative_to(ROOT)): file_hash(p)
                              for p in sorted((ROOT/'experiments').glob('*.py'))}
    protocol = ROOT/'docs/analysis_protocol.md'
    details['protocol_sha256'] = file_hash(protocol)
    signature=hashlib.sha256(json.dumps({'sources':details['source_sha256'],
                                       'protocol':details['protocol_sha256']},sort_keys=True).encode()).hexdigest()[:16]
    snapshot=ROOT/'results/provenance'/signature
    for relative in details['source_sha256']:
        target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/relative,target)
    target=snapshot/'docs/analysis_protocol.md';target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(protocol,target)
    details['source_snapshot_dir']=str(snapshot.relative_to(ROOT))
    Path(path).write_text(json.dumps(details, indent=2, allow_nan=False)+'\n')

def ar_covariance(length, coefficient):
    indices = np.arange(length)
    return coefficient ** np.abs(indices[:, None]-indices[None, :])

def gaussian_weights(n, tau2, sigma2, phi, psi=0.0, length=5):
    """Current latent-state and next-observation weights, oldest wave first."""
    n = np.asarray(n, dtype=float)
    v = sigma2 / n
    latent = tau2 * ar_covariance(length, phi)
    error = ar_covariance(length, psi)
    covariance = latent[None, :, :] + v[:, None, None]*error
    cross_state = np.broadcast_to(latent[-1], (len(n), length))
    cross_next = phi*cross_state + psi*v[:, None]*error[-1]
    # pinv handles phi=1 and sigma2=0 without inserting artificial noise.
    inverse = np.linalg.pinv(covariance, rcond=1e-12)
    state_weights = np.einsum('nt,ntj->nj', cross_state, inverse)
    next_weights = np.einsum('nt,ntj->nj', cross_next, inverse)
    posterior_var = np.maximum(0.0, tau2-np.sum(state_weights*cross_state,axis=1))
    next_var = np.maximum(0.0, tau2+v-np.sum(next_weights*cross_next,axis=1))
    return state_weights, next_weights, posterior_var, next_var

def bottom_indices(values, k):
    # Stable sorting is deterministic when scores are tied.
    return np.argsort(values, axis=-1, kind='stable')[..., :k]

def row_selected_mean(values, indices):
    return np.take_along_axis(values, indices, axis=1).mean(axis=1)

def overlap_rows(first, second, size):
    mask = np.zeros((len(first), size), dtype=bool)
    np.put_along_axis(mask, second, True, axis=1)
    return np.take_along_axis(mask, first, axis=1).mean(axis=1)

def summarise(x):
    x = np.asarray(x)
    return {'mean': float(x.mean()), 'mcse': float(x.std(ddof=1)/np.sqrt(len(x))),
            'p10': float(np.quantile(x, .1)), 'p90': float(np.quantile(x, .9))}

def static_shrinkage(z, n, ratio):
    return np.asarray(z) / (1 + ratio/np.asarray(n))

def pair_crossings(z, n, upper=3000.0):
    """Exact crossings of centred posterior means z_i/(1+lambda/n_i)."""
    z = np.asarray(z); n = np.asarray(n); result = []
    for i in range(len(z)):
        for j in range(i+1, len(z)):
            a = z[i]-z[j]
            b = z[i]/n[j]-z[j]/n[i]
            if b != 0:
                value = -a/b
                if 0 < value <= upper:
                    result.append((float(value), i, j))
    return sorted(result)

def first_membership_crossing(z, n, k):
    """First boundary crossing for the raw bottom-k set; infinity if none."""
    selected = set(bottom_indices(np.asarray(z), k).tolist())
    first = float('inf')
    for i in selected:
        for j in range(len(z)):
            if j in selected:
                continue
            a = z[i]-z[j]
            b = z[i]/n[j]-z[j]/n[i]
            # The selected score starts below the excluded score.
            if b > 0:
                root = -a/b
                if root >= 0:
                    first = min(first, float(root))
    return first
