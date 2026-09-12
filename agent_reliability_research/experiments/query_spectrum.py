"""Product-Bernoulli cube approximation obstruction for hard-cap means.
The high Boolean degree is an exact-unbiasedness statement. This spectral
calculation quantifies omitted energy under specified label distributions; it
is not a lower bound on estimator variance or a minimax training guarantee.
"""
import hashlib,json,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def transform(x,p):
    y=x.copy();h=1;q=1-p
    while h<len(y):
        v=y.reshape(-1,2*h);a=v[:,:h].copy();b=v[:,h:].copy()
        v[:,:h]=q*a+p*b;v[:,h:]=np.sqrt(p*q)*(b-a);h*=2
    return y
def run():
    t=time.perf_counter();rows=[]
    for g in range(2,17):
        codes=np.arange(2**g,dtype=np.uint32)
        r=((codes[:,None]>>np.arange(g))&1).astype(float)
        mean=r.mean(1);sd=np.sqrt(mean*(1-mean))
        a=np.divide(r-mean[:,None],sd[:,None],out=np.zeros_like(r),where=sd[:,None]>0)
        order=r.sum(1).astype(int)
        for p in [.05,.2,.5,.8,.95]:
          weights=p**order*(1-p)**(g-order)
          for name,value in [('unclipped_contrast',(a[:,0]-a[:,1])/g),('positive_coefficient',np.maximum(a[:,0],0))]:
            coef=transform(value,p);energy=np.bincount(order,weights=coef*coef,minlength=g+1)
            assert abs(energy.sum()-np.dot(weights,value*value))<1e-12
            for b in range(g+1):
                rows.append(dict(g=g,bernoulli_p=p,target=name,hard_cap=b,integrated_squared_bias_lower_bound=float(energy[b+1:].sum()),
                  target_second_moment=float(energy.sum()),degree_energy=energy.tolist()))
    out=ROOT/'results/query_spectrum.json';out.write_text(json.dumps(dict(status='complete',rows=rows,
       method='Exact product-Bernoulli orthogonal Fourier transform on complete Boolean cube; no data-fitted label distribution',
       source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),seconds=time.perf_counter()-t),indent=2))
    for x in rows:
        if x['hard_cap']==x['g']//2 and x['g'] in [4,8,16] and x['bernoulli_p'] in [.05,.5]:print(x['g'],x['bernoulli_p'],x['target'],x['integrated_squared_bias_lower_bound']/x['target_second_moment'])
if __name__=='__main__':run()
