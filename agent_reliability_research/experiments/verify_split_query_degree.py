#!/usr/bin/env python3
"""Independent full-Boolean-cube check of sign-split coefficient degree."""
import hashlib,json,math,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def forward_difference(g,n):
    return sum((-1)**(n-j)*math.comb(n,j)/math.sqrt((j+1)*(g-j-1)) for j in range(n+1))

def main():
    start=time.time();rows=[]
    for g in range(2,13):
        masks=np.arange(1<<g,dtype=np.int64)
        labels=((masks[:,None]>>np.arange(g))&1).astype(float)
        means=labels.mean(axis=1);sd=np.sqrt(means*(1-means))
        value=np.divide(labels[:,0]-means,sd,out=np.zeros(len(masks)),where=sd>0)
        coefficient=np.maximum(value,0)
        for i in range(g):
            chosen=(masks&(1<<i))!=0
            coefficient[chosen]-=coefficient[masks[chosen]^(1<<i)]
        degree=max(mask.bit_count() for mask,c in zip(masks.tolist(),coefficient) if abs(c)>1e-10)
        expected=g if g%2==0 else g-1
        assert degree==expected,(g,degree)
        full=-(g-1)*forward_difference(g,g-2)
        assert abs(coefficient[-1]-full)<1e-10
        below=None
        if g%2:
            # Remove coordinate g-1; the retained subset still contains i=0.
            mask=(1<<(g-1))-1
            below=-(g-2)*forward_difference(g,g-3)
            assert abs(coefficient[mask]-below)<1e-10
            assert abs(below)>1e-10
        rows.append(dict(g=g,degree=degree,full_coefficient=float(coefficient[-1]),
            full_formula=full,one_below_formula=below))
    result=dict(status='passed',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        runtime_seconds=time.time()-start,scope='epsilon=0, population SD, allsame set to zero',checks=rows)
    (ROOT/'results/split_query_degree_checks.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
