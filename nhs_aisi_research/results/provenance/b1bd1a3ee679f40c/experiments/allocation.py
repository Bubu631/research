"""Existing Gaussian knowledge-gradient specialised to two measurement channels.

No global budget optimality is asserted for cost-normalised one-step gains.
State stores independent 2x2 target/persistent-offset posteriors per unit.
"""
from dataclasses import dataclass
import numpy as np
from scipy.special import ndtr
from common import thresholds, selected

@dataclass
class Belief:
    mean: np.ndarray
    bias_mean: np.ndarray
    target_var: np.ndarray
    bias_var: np.ndarray
    cross: np.ndarray
    ordinary_n: np.ndarray
    validation_n: np.ndarray

    @classmethod
    def prior(cls, reps, units, mu=5.,tau=.35,beta=.35):
        shape=(reps,units)
        return cls(np.broadcast_to(mu,shape).copy().astype(float),np.zeros(shape),
                   np.broadcast_to(np.asarray(tau,dtype=float)**2,shape).copy(),
                   np.broadcast_to(np.asarray(beta,dtype=float)**2,shape).copy(),np.zeros(shape),
                   np.zeros(shape),np.zeros(shape))

    def update_all_ordinary(self, observation, noise_var, n):
        a=self.target_var+self.cross;b=self.bias_var+self.cross
        den=self.target_var+self.bias_var+2*self.cross+noise_var
        residual=observation-self.mean-self.bias_mean
        self.mean += a/den*residual;self.bias_mean += b/den*residual
        self.target_var -= a*a/den;self.bias_var -= b*b/den;self.cross -= a*b/den
        self.target_var=np.maximum(self.target_var,0);self.bias_var=np.maximum(self.bias_var,0)
        self.ordinary_n += n

    def update(self, rows, units, channel, observation, noise_var, n):
        v=self.target_var[rows,units];q=self.bias_var[rows,units];c=self.cross[rows,units]
        ordinary=channel==0
        a=np.where(ordinary,v+c,v);b=np.where(ordinary,q+c,c)
        den=np.where(ordinary,v+q+2*c,v)+noise_var
        residual=observation-self.mean[rows,units]-np.where(ordinary,self.bias_mean[rows,units],0)
        self.mean[rows,units]+=a/den*residual
        self.bias_mean[rows,units]+=b/den*residual
        self.target_var[rows,units]=np.maximum(0,v-a*a/den)
        self.bias_var[rows,units]=np.maximum(0,q-b*b/den)
        self.cross[rows,units]=c-a*b/den
        self.ordinary_n[rows,units]+=np.where(ordinary,n,0)
        self.validation_n[rows,units]+=np.where(ordinary,0,n)

    def innovation_sd(self, ordinary_noise, validation_noise):
        a=self.target_var+self.cross
        regular=np.abs(a)/np.sqrt(np.maximum(self.target_var+self.bias_var+2*self.cross+ordinary_noise,1e-30))
        audit=self.target_var/np.sqrt(np.maximum(self.target_var+validation_noise,1e-30))
        return np.stack([regular,audit],axis=2)

    def ordinary_uncertainty_floor(self):
        denominator=self.target_var+self.bias_var+2*self.cross
        decrease=np.divide((self.target_var+self.cross)**2,denominator,
                           out=np.zeros_like(denominator),where=denominator>1e-30)
        return np.maximum(0,self.target_var-decrease)

def gaussian_improvement(gap, sd):
    """E[(s Z - |gap|)+]; cancellation-safe nonnegative evaluation."""
    distance=np.abs(gap);ratio=np.divide(distance,sd,out=np.full_like(sd,np.inf),where=sd>1e-30)
    with np.errstate(invalid='ignore'):
        value=sd*np.exp(-.5*ratio**2)/np.sqrt(2*np.pi)-distance*ndtr(-ratio)
    return np.where((sd>1e-30)&np.isfinite(distance),np.maximum(value,0),0)

def choose_actions(belief, policy, groups, remaining, costs, ordinary_noise,
                   validation_noise, rng, fraction=.2):
    """Return a unit and channel for each active independent replication."""
    reps,units=belief.mean.shape
    affordable=np.asarray(costs)[None,None,:]<=remaining[:,None,None]
    if policy in {'uniform','two_channel_uniform','validation_only'}:
        score=rng.random((reps,units,2))
        if policy=='uniform':score[:,:,1]=-np.inf
        elif policy=='validation_only':score[:,:,0]=-np.inf
    elif policy=='uncertainty':
        score=np.full((reps,units,2),-np.inf);score[:,:,0]=belief.target_var
    elif policy=='boundary':
        cutoff=thresholds(belief.mean,groups,fraction)
        # Fixed-budget boundary heuristic, not the fixed-confidence LUCB algorithm.
        priority=2*np.sqrt(belief.target_var)-np.abs(belief.mean-cutoff)
        score=np.full((reps,units,2),-np.inf);score[:,:,0]=priority
    else:
        cut=thresholds(belief.mean,groups,fraction)
        sd=belief.innovation_sd(ordinary_noise,validation_noise)
        gain=gaussian_improvement((belief.mean-cut)[:,:,None],sd)
        score=gain/np.asarray(costs)[None,None,:]
        if policy in {'ordinary_kg','bias_blind_kg'}:score[:,:,1]=-np.inf
        elif policy not in {'two_channel_kg','two_channel_kg_terminal'}:raise ValueError(policy)
        if policy=='two_channel_kg_terminal':
            # When only one minimum-cost action remains, total KG is the exact objective.
            last=remaining<2*np.min(costs)
            score[last]=gain[last]
    score=np.where(affordable,score,-np.inf)
    flat=score.reshape(reps,-1);best=np.argmax(flat,axis=1)
    available=np.isfinite(flat[np.arange(reps),best])
    return best//2,best%2,available
