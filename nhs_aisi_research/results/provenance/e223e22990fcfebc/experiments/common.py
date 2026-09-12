"""Shared utilities for the AISI information-allocation extension."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import shutil
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_csv(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)

def manifest(path, details):
    value = dict(details, recorded_at_utc=datetime.now(timezone.utc).isoformat(),
                 python=platform.python_version(), numpy=np.__version__, platform=platform.platform())
    sources = {str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'experiments').glob('*.py'))}
    protocol = ROOT/'docs/analysis_protocol.md'
    sig = hashlib.sha256(json.dumps([sources, sha(protocol)], sort_keys=True).encode()).hexdigest()[:16]
    snap = ROOT/'results/provenance'/sig
    for rel in sources:
        dest=snap/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
    (snap/'docs').mkdir(exist_ok=True);shutil.copyfile(protocol,snap/'docs/analysis_protocol.md')
    value.update(source_sha256=sources,protocol_sha256=sha(protocol),source_snapshot=str(snap.relative_to(ROOT)))
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def selected(mean, groups, fraction=.2):
    """Fixed number of lowest means per group; deterministic index ties."""
    result = np.zeros(mean.shape,dtype=bool)
    for group in np.unique(groups):
        ids=np.flatnonzero(groups==group);k=max(1,int(len(ids)*fraction))
        chosen=np.argsort(mean[:,ids],axis=1,kind='stable')[:,:k]
        np.put_along_axis(result,ids[chosen],True,axis=1)
    return result

def thresholds(mean, groups, fraction=.2):
    """The alternative cutoff when one posterior coordinate changes."""
    out=np.empty_like(mean)
    for group in np.unique(groups):
        ids=np.flatnonzero(groups==group);k=max(1,int(len(ids)*fraction))
        if k==len(ids):
            out[:,ids]=np.inf;continue
        values=mean[:,ids];order=np.argsort(values,axis=1,kind='stable')
        lower=np.take_along_axis(values,order[:,k-1:k],axis=1)
        upper=np.take_along_axis(values,order[:,k:k+1],axis=1)
        mask=np.zeros_like(values,dtype=bool);np.put_along_axis(mask,order[:,:k],True,axis=1)
        out[:,ids]=np.where(mask,upper,lower)
    return out

def performance(mean, variance, truth, groups, fraction=.2):
    chosen=selected(mean,groups,fraction);oracle=selected(truth,groups,fraction)
    k=chosen.sum(axis=1)
    return dict(regret=((chosen-oracle.astype(float))*truth).sum(axis=1)/k,
                overlap=(chosen&oracle).sum(axis=1)/k,
                mse=((mean-truth)**2).mean(axis=1),
                coverage=(np.abs(mean-truth)<=1.959963984540054*np.sqrt(variance)).mean(axis=1),
                selected_size=k)

def summarise(x):
    x=np.asarray(x,dtype=float)
    se=float(x.std(ddof=1)/np.sqrt(len(x))) if len(x)>1 else 0.
    return {'mean':float(x.mean()),'mcse':se,'lo':float(x.mean()-1.96*se),'hi':float(x.mean()+1.96*se)}
