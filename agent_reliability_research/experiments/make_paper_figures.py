"""Regenerate scientific figures exclusively from completed result artifacts."""
import csv,json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':240})
def read(path):return list(csv.DictReader((ROOT/path).open()))
colors=['#176b95','#db7926','#b14343']
fig,ax=plt.subplots(1,2,figsize=(9,3.1),layout='constrained')
g=np.arange(2,17);ax[0].plot(g,g-1-(g%2),'o-',label='Unclipped aggregate',color=colors[0]);ax[0].plot(g,g-(g%2),'s--',label='Each sign-split coefficient',color=colors[1])
ax[0].set(xlabel='Group size G',ylabel='Exact Boolean degree',xticks=[2,4,8,12,16],title='(a) Hard-cap unbiasedness');ax[0].legend(frameon=False,fontsize=8)
rows=json.loads((ROOT/'results/query_spectrum.json').read_text())['rows']
for p,col in zip([.05,.2,.5],colors):
 a=[x for x in rows if x['target']=='unclipped_contrast' and x['bernoulli_p']==p and x['hard_cap']==x['g']//2]
 ax[1].semilogy([x['g'] for x in a],[x['integrated_squared_bias_lower_bound']/x['target_second_moment'] for x in a],'o-',ms=3,label=f'p = {p}',color=col)
ax[1].set(xlabel='Group size G',ylabel='Relative high-order energy',title='(b) Approximation obstruction at cap floor(G/2)');ax[1].legend(frameon=False)
fig.savefig(OUT/'query_degree.png');plt.close(fig)
rows=read('results/estimation_corrected/summary.csv')
fig,axs=plt.subplots(1,3,figsize=(9,2.8),layout='constrained')
for ax,reg,col in zip(axs,['calibrated','overconfident','shifted'],colors):
 for q in [.25,.5,.75]:
  chosen=[x for x in rows if x['regime']==reg and float(x['budget'])==q and x['method']=='rr_development']
  ratios=[]
  for x in chosen:
   base=next(y for y in rows if y['setting']==x['setting'] and y['budget']==x['budget'] and y['method']=='whole_group_cv')
   ratios.append(float(x['gradient_mse'])/float(base['gradient_mse']))
  ax.scatter(np.full(len(ratios),q)+np.linspace(-.016,.016,len(ratios)),ratios,s=13,alpha=.7,color=col)
 qs=np.array([.25,.5,.75]);charged=(1/np.minimum(1,qs+.25)-1)/(1/qs-1)
 ax.plot(qs,np.ones(3),'--',color='#666666',lw=1,label='Whole-group: marginal cost')
 ax.plot(qs,charged,'ks-',ms=4,label='Whole-group: calibration cost included')
 ax.set(title=reg.capitalize(),xlabel='Evaluation audit fraction',ylim=(-.05,1.2),xticks=qs)
axs[0].set_ylabel('MSE / same-fraction whole-group MSE');axs[1].legend(frameon=False,fontsize=6.5,loc='lower left')
fig.savefig(OUT/'calibration_cost.png');plt.close(fig)
rows=read('results/model_only/summary.csv');fig,ax=plt.subplots(figsize=(7,3.4),layout='constrained')
for j,(reg,col) in enumerate(zip(['calibrated','overconfident','shifted'],colors)):
 ratio=[]
 for x in rows:
  if x['regime']!=reg or x['method']!='rr_model':continue
  b=next(y for y in rows if y['setting']==x['setting'] and y['budget_fraction']==x['budget_fraction'] and y['method']=='whole_group_cv')
  ratio.append(float(x['gradient_mse'])/float(b['gradient_mse']))
 ax.scatter(j+np.linspace(-.22,.22,len(ratio)),ratio,s=16,alpha=.72,color=col)
 ax.plot([j-.27,j+.27],[np.median(ratio)]*2,color=col,lw=2.5)
ax.axhline(1,color='#333333',ls='--',lw=1);ax.set(xticks=range(3),xticklabels=['Calibrated','Overconfident','Shifted'],yscale='log',ylabel='Projected MSE ratio to whole-group',title='Model-derived schedule: all 135 setting-budget comparisons')
fig.savefig(OUT/'model_schedule.png');plt.close(fig)
rows=read('results/stateful_training/summary.csv');fig,axs=plt.subplots(1,3,figsize=(9,3),layout='constrained')
methods=[('full','Complete labels','#2a8468','-'),('whole_group_residual','Whole-group','#222222','--'),('rr_completion','Sequential','#176b95','-'),('partial_replacement','Partial replacement','#9873ad','-'),('naive_reward_ht','Reward HT + norm','#db7926','-'),('proxy','Proxy only','#b14343',':')]
for ax,h in zip(axs,[12,24,48]):
 for method,label,c,ls in methods:
  a=[r for r in rows if int(r['horizon'])==h and r['method']==method];a.sort(key=lambda x:int(x['update']))
  x=np.array([int(r['update']) for r in a]);y=np.array([float(r['reference_success_mean']) for r in a]);se=np.array([float(r['reference_success_seed_se']) for r in a])
  ax.plot(x,y,label=label,color=c,ls=ls,lw=1.5);ax.fill_between(x,y-se,y+se,color=c,alpha=.09)
 ax.set(title=f'Horizon {h}',xlabel='Policy updates',ylim=(0,1),xticks=[0,100,200,300])
axs[0].set_ylabel('Reference success');axs[-1].legend(frameon=False,fontsize=6.5,loc='upper left')
fig.savefig(OUT/'stateful_training.png');plt.close(fig)
manifest={'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'figures':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.png')},'source':'completed saved experiments only'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
