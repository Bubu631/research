"""Generate every paper chart and numerical table from stored experiment summaries."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import ROOT

FIG=ROOT/'paper/figures';TAB=ROOT/'paper/tables'
FIG.mkdir(exist_ok=True);TAB.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
P={'ordinary_kg':'Ordinary KG','two_channel_kg':'Two-channel KG','balanced_mix':'Balanced mixture','validation_only':'Validation only','uniform':'Uniform ordinary','boundary':'Boundary heuristic','uncertainty':'Maximum variance','bias_blind_kg':'Bias-blind KG','uniform_blind':'Uniform, bias blind','two_channel_uniform':'Equal-action mixture'}
C={'ordinary_kg':'#176b87','two_channel_kg':'#bf5b32','balanced_mix':'#71578d','validation_only':'#74846c','uniform':'#777777'}
SC={'unweighted_uniform':'Uniform','unweighted_tilt_025':'Tilt 0.25','unweighted_tilt_05':'Tilt 0.50','weighted_tilt_05':'Weighted tilt','validation_tilt_025':'Biased validation'}
def save(fig,name):
    fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight');fig.savefig(FIG/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)
def table(name,headers,rows,align=None):
    align=align or 'l'+'r'*(len(headers)-1)
    lines=['\\begin{tabular}{'+align+'}','\\toprule',' & '.join(headers)+r' \\',r'\midrule']
    lines+=[' & '.join(map(str,row))+r' \\' for row in rows]
    lines +=[r'\bottomrule',r'\end{tabular}']
    (TAB/(name+'.tex')).write_text('\n'.join(lines)+'\n')
def main():
    sy=pd.read_csv(ROOT/'results/synthetic.csv');st=pd.read_csv(ROOT/'results/synthetic_stress.csv');re=pd.read_csv(ROOT/'results/replay.csv')
    s=sy[(sy.audit_cost==5)&(sy.budget==120)]
    fig,ax=plt.subplots(figsize=(6.8,2.65))
    for policy in ['uniform','ordinary_kg','balanced_mix','two_channel_kg']:
        d=s[s.policy==policy].sort_values('bias_sd')
        ax.errorbar(d.bias_sd,d.regret_mean,yerr=1.96*d.regret_mcse,label=P[policy],color=C[policy],marker='o',markersize=4,capsize=2)
    ax.set(xlabel='Persistent unit-specific offset SD',ylabel='Mean severity regret',xticks=[0,.15,.35,.7]);ax.legend(ncol=2,frameon=False,fontsize=8);fig.tight_layout();save(fig,'synthetic_bias')
    d=re[(re.audit_cost==5)&(re.budget==144)&(re.policy=='two_channel_kg')].set_index('scenario').loc[list(SC)]
    fig,ax=plt.subplots(figsize=(6.8,2.5));y=np.arange(len(d))
    ax.errorbar(d.regret_diff_ordinary_kg_mean,y,xerr=1.96*d.regret_diff_ordinary_kg_mcse,fmt='o',capsize=3,color=C['two_channel_kg'])
    ax.axvline(0,color='#777777',lw=.8);ax.set(yticks=y,yticklabels=list(SC.values()),xlabel='Regret: two-channel KG minus ordinary KG');ax.invert_yaxis();fig.tight_layout();save(fig,'replay_paired')
    fig,axs=plt.subplots(1,2,figsize=(6.8,2.5))
    for p in ['ordinary_kg','two_channel_kg','balanced_mix','validation_only']:
        d=re[(re.scenario=='unweighted_tilt_05')&(re.budget==144)&(re.policy==p)].sort_values('audit_cost')
        axs[0].plot(d.audit_cost,d.regret_mean,'o-',color=C[p],label=P[p],markersize=4)
    axs[0].set(xlabel='Validation packet cost',ylabel='Mean severity regret',xticks=[2,5,10]);axs[0].legend(frameon=False,fontsize=7)
    d=st[st.policy=='two_channel_kg'].copy();d=d.sort_values('regret_diff_ordinary_kg_mean')
    lab={'biased_validation':'Biased validation','heavy_tails':'Heavy-tailed packets','heteroscedastic':'Unequal noise','overestimated_bias':'Overestimated bias','shared_group_bias':'Shared group shift','target_drift':'Target drift','underestimated_bias':'Underestimated bias'}
    axs[1].barh([lab[x] for x in d.scenario],d.regret_diff_ordinary_kg_mean,color=np.where(d.regret_diff_ordinary_kg_mean>0,C['two_channel_kg'],C['ordinary_kg']))
    axs[1].axvline(0,color='black',lw=.6);axs[1].set_xlabel('Regret difference vs ordinary KG');axs[1].tick_params(axis='y',labelsize=7);fig.tight_layout(w_pad=2);save(fig,'cost_and_stress')
    rows=[]
    for beta,g in s.groupby('bias_sd'):
        z=g.set_index('policy');t=z.loc['two_channel_kg']
        rows.append([f'{beta:.2f}',f"{z.loc['ordinary_kg','regret_mean']:.4f}",f"{t.regret_mean:.4f}",f"{t.regret_diff_ordinary_kg_mean:+.4f}",f"[{t.regret_diff_ordinary_kg_lo:+.4f}, {t.regret_diff_ordinary_kg_hi:+.4f}]"])
    table('synthetic_main',['$\\beta$','Ord. KG','Two KG','$\\Delta$','95\\% paired interval'],rows)
    rows=[]
    order=['uniform','uniform_blind','uncertainty','boundary','ordinary_kg','bias_blind_kg','two_channel_uniform','balanced_mix','validation_only','two_channel_kg']
    d=re[(re.audit_cost==5)&(re.budget==144)]
    for p in order:
        z=d[d.policy==p].set_index('scenario');rows.append([P[p]]+[f"{z.loc[sc,'regret_mean']:.4f}" for sc in SC])
    table('replay_main',['Policy','Unif.','T.25','T.50','Wgt.','V.bias'],rows)
    rows=[]
    for sc,g in d.groupby('scenario',sort=False):
        z=g.set_index('policy');a=z.loc['ordinary_kg'];b=z.loc['two_channel_kg']
        rows.append([SC[sc],f'{a.regret_mean:.4f}',f'{b.regret_mean:.4f}',f'{a.mse_mean:.5f}',f'{b.mse_mean:.5f}',f'{b.validation_fraction_mean:.1%}'.replace('%',r'\%')])
    table('replay_mse',['Scenario','Ord. loss','Two loss','Ord. MSE','Two MSE','Val. cost'],rows)
    # Detailed tables include all declared settings; grouped by scenario to avoid over-wide grids.
    lines=[]
    for name,frame,keys in [('Gaussian',sy,['bias_sd','audit_cost','budget']),('Stress',st,['scenario']),('Replay',re,['scenario','audit_cost','budget'])]:
        for values,g in frame.groupby(keys,sort=False):
            if not isinstance(values,tuple):values=(values,)
            caption=name+': '+', '.join(f'{k}={v}' for k,v in zip(keys,values))
            caption=caption.replace('_',r'\_')
            lines +=[r'\begin{table}[htbp]',r'\centering',r'\small',r'\caption{'+caption+r'. MCSE describes simulation variation conditional on the experiment, not population uncertainty.}']
            lines +=[r'\begin{tabular}{lrrrrr}',r'\toprule',r'Policy & Regret & MCSE & Overlap & Coverage & Val. cost \\',r'\midrule']
            for p in order:
                a=g[g.policy==p].iloc[0]
                lines.append(f'{P[p]} & {a.regret_mean:.5f} & {a.regret_mcse:.5f} & {a.overlap_mean:.3f} & {a.coverage_mean:.3f} & {a.validation_fraction_mean:.3f}'+r' \\')
            lines +=[r'\bottomrule',r'\end{tabular}',r'\end{table}']
    (TAB/'full_grid.tex').write_text('\n'.join(lines)+'\n')
    compact=[r'\begin{landscape}']
    for name,frame,keys in [('Gaussian',sy,['bias_sd','audit_cost','budget']),('Stress',st,['scenario']),('Replay',re,['scenario','audit_cost','budget'])]:
        compact +=[r'\small',r'\Needspace{12\baselineskip}',r'\begin{longtable}{lrrrrrrrrrr}',r'\caption{'+name+r': all ten policy mean regrets. Full precision and uncertainty are in the CSV release.}\\',r'\toprule',r'Setting & U & UB & V & B & O & OB & E & M & A & T \\',r'\midrule',r'\endfirsthead',r'\toprule',r'Setting & U & UB & V & B & O & OB & E & M & A & T \\',r'\midrule',r'\endhead']
        for values,g in frame.groupby(keys,sort=False):
            if not isinstance(values,tuple):values=(values,)
            if name=='Gaussian':label=f'b={values[0]:.2f}, c={values[1]}, B={values[2]}'
            elif name=='Replay':label=SC[values[0]]+f', c={values[1]}, B={values[2]}'
            else:label=values[0].replace('_',' ')
            compact.append(label+' & '+' & '.join(f"{g.set_index('policy').loc[p,'regret_mean']:.4f}" for p in order)+r' \\')
        compact +=[r'\bottomrule',r'\end{longtable}']
    compact +=[r'\end{landscape}']
    (TAB/'compact_grid.tex').write_text('\n'.join(compact)+'\n')
    if (ROOT/'results/replay_budget_extension.csv').exists():
        ex=pd.read_csv(ROOT/'results/replay_budget_extension.csv');fig,ax=plt.subplots(figsize=(6.8,2.65))
        for p in ['ordinary_kg','two_channel_kg','balanced_mix','validation_only','uniform']:
            d=ex[ex.policy==p].sort_values('budget');ax.errorbar(d.budget,d.regret_mean,yerr=1.96*d.regret_mcse,fmt='o-',color=C[p],label=P[p],markersize=4,capsize=2)
        ax.set(xscale='log',xlabel='Additional budget (ordinary-packet equivalents)',ylabel='Mean severity regret',xticks=[48,144,480,1440]);ax.set_xticklabels(['48','144','480','1440']);ax.legend(ncol=2,fontsize=8,frameon=False);fig.tight_layout();save(fig,'budget_extension')
        table('budget_extension',['Budget','Ord. KG','Two KG','Balanced','Val. only','Uniform'],[[str(b)]+[f"{g.set_index('policy').loc[p,'regret_mean']:.4f}" for p in ['ordinary_kg','two_channel_kg','balanced_mix','validation_only','uniform']] for b,g in ex.groupby('budget')])
    print('Figures and tables regenerated from stored CSVs.')
if __name__=='__main__':main()
