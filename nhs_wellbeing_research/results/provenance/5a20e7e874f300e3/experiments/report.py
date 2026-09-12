"""Generate manuscript figures and tables from executed result files."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import ROOT, gaussian_weights, save_csv, pair_crossings, static_shrinkage
from empirical import select_within

FIG=ROOT/'paper/figures';TABLE=ROOT/'paper/tables'
FIG.mkdir(parents=True,exist_ok=True);TABLE.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
                     'axes.labelsize':9,'legend.fontsize':8,'pdf.fonttype':42,
                     'axes.spines.top':False,'axes.spines.right':False,
                     'savefig.bbox':'tight'})
COLORS=['#183b56','#cf6a32','#357d72','#8b6c98','#718096']
LABEL={'latest':'Latest score','equal_history':'Equal history',
       'group_centred_equal':'Group-centred history','linear_trend':'Linear trend',
       'geometric_history':'Tuned geometric history','group_mean_reversion':'Group mean reversion',
       'working_covariance':'Working covariance',
       'raw':'Current score','geometric_history_sim':'Geometric history',
       'gaussian_posterior':'Gaussian posterior',
       'independent_error_posterior':'Assumed white error'}

def latex_escape(s):
    return str(s).replace('&',r'\&').replace('_',r'\_').replace('%',r'\%')

def table(path,headers,rows,alignment=None):
    align=alignment or 'l'+'r'*(len(headers)-1)
    lines=[r'\begin{tabular}{'+align+'}',r'\toprule',
           ' & '.join(headers)+r' \\',r'\midrule']
    lines+=[' & '.join(map(str,row))+r' \\' for row in rows]
    lines += [r'\bottomrule',r'\end{tabular}']
    (TABLE/path).write_text('\n'.join(lines)+'\n')

def save(fig,name):
    fig.savefig(FIG/f'{name}.pdf')
    fig.savefig(FIG/f'{name}.png',dpi=180)
    plt.close(fig)

def empirical_reports():
    prefixes=['harmonised']+(['vintage'] if (ROOT/'results/vintage/test_metrics.csv').exists() else [])
    fig,axes=plt.subplots(1,len(prefixes),figsize=(6.5,3.5),squeeze=False)
    for col,prefix in enumerate(prefixes):
        base=ROOT/'results'/prefix
        metrics=pd.read_csv(base/'test_metrics.csv');boot=pd.read_csv(base/'paired_bootstrap.csv')
        config=json.loads((base/'selected_hyperparameters.json').read_text())
        rows=[]
        for _,r in metrics.iterrows():
            b=boot[boot.method==r.method].iloc[0]
            rows.append([LABEL[r.method],f'{r.rmse:.4f}',f'{r.mae:.4f}',
                         f'{100*r["observed_overlap_0.2"]:.1f}',
                         f'[{b.rmse_difference_lo:+.4f}, {b.rmse_difference_hi:+.4f}]'])
        table(f'{prefix}_metrics.tex',['Rule','RMSE','MAE',r'Overlap (\%)',r'$\Delta$RMSE 95\% interval'],rows)
        ax=axes[0,col];sub=boot[boot.method!='latest'].iloc[::-1]
        yy=np.arange(len(sub));xx=sub.rmse_difference.to_numpy()
        ax.errorbar(xx,yy,xerr=np.vstack([xx-sub.rmse_difference_lo,sub.rmse_difference_hi-xx]),
                    fmt='o',color=COLORS[0],capsize=3,markersize=4)
        ax.axvline(0,color='0.5',lw=.8,ls='--')
        ax.set_yticks(yy,[LABEL[m] for m in sub.method]);ax.set_xlabel('RMSE difference from latest score')
        ax.set_title('2025-reweighted histories' if prefix=='harmonised' else 'Archived historical vintages')
        ax.grid(axis='x',alpha=.15)
        hp=[]
        for method,c in config.items():
            hp.append([LABEL[method],('--' if c['phi'] is None else f"{c['phi']:.2f}"),
                       ('--' if c['ratio'] is None else f"{c['ratio']:.0f}"),f"{c['development_mse']:.5f}"])
        table(f'{prefix}_tuning.tex',['Rule',r'$\phi$',r'$\lambda$','2024 MSE'],hp)
    fig.tight_layout(w_pad=2);save(fig,'temporal_prediction')

    follow=pd.read_csv(ROOT/'results/harmonised/observational_followup.csv')
    fig,ax=plt.subplots(figsize=(6.5,3));xx=np.arange(len(follow));width=.24
    for j,(column,label) in enumerate([('observed_selected_change','Selected units: observed change'),
                                      ('corresponding_group_change','Corresponding benchmark-group change'),
                                      ('group_centred_change','Difference from group change')]):
        ax.bar(xx+(j-1)*width,follow[column],width,color=COLORS[j],label=label)
    ax.axhline(0,color='0.4',lw=.8);ax.set_xticks(xx,[f'{a}–{b}' for a,b in zip(follow.selection_year,follow.followup_year)])
    ax.set_ylabel('Change in burnout sub-score (0–10)');ax.set_ylim(-.08,.34)
    ax.legend(frameon=False,loc='upper left',fontsize=7.5)
    fig.tight_layout();save(fig,'observed_followup')
    table('followup.tex',['Selection','Follow-up','Selected',r'$\Delta Y_S$',r'$\Delta\mu_S$','Difference'],
          [[int(r.selection_year),int(r.followup_year),int(r.selected_units),
            f'{r.observed_selected_change:+.4f}',f'{r.corresponding_group_change:+.4f}',f'{r.group_centred_change:+.4f}']
           for _,r in follow.iterrows()])

    sensitivity=pd.read_csv(ROOT/'results/harmonised/rank_sensitivity.csv')
    thresholds=pd.read_csv(ROOT/'results/harmonised/rank_thresholds.csv')
    membership=pd.read_csv(ROOT/'results/harmonised/rank_membership.csv')
    fig,(ax,bx)=plt.subplots(1,2,figsize=(6.5,2.8))
    current=membership[membership.ratio==0].copy()
    z=current.centred_score.to_numpy();nn=current.burnout_n.to_numpy();gg=current.benchmark_group.to_numpy()
    raw=set(select_within(z,gg,.2));breaks={0.,3000.}
    for g in np.unique(gg):
        ids=gg==g;breaks.update(v for v,_,_ in pair_crossings(z[ids],nn[ids],3000.))
    breaks=sorted(breaks);counts=[]
    for lo,hi in zip(breaks[:-1],breaks[1:]):
        chosen=set(select_within(static_shrinkage(z,nn,(lo+hi)/2),gg,.2))
        counts.append(len(raw&chosen))
    counts.append(counts[-1]);ax.step(breaks,counts,where='post',color=COLORS[0])
    ax.plot(sensitivity.ratio,sensitivity.retained_from_raw,'o',color=COLORS[0]);ax.set_xscale('symlog',linthresh=10)
    ax.set_ylim(30,37);ax.set_yticks(range(30,38,2));ax.set_xlabel(r'Working variance ratio $\lambda$')
    ax.set_ylabel('Original selected units retained / 36');ax.grid(alpha=.15)
    sizes=membership[membership.ratio==0].burnout_n.to_numpy()
    bx.hist(sizes,bins=np.geomspace(sizes.min(),sizes.max(),13),color=COLORS[2],edgecolor='white')
    bx.set_xscale('log');bx.set_xlabel('Valid burnout respondents in 2025');bx.set_ylabel('Reporting units')
    fig.tight_layout();save(fig,'rank_sensitivity')
    short={'Acute Specialist Trusts':'Acute specialist','Acute&Acute Community Trusts':'Acute / acute-community',
           'Ambulance Trusts':'Ambulance','Community Trusts':'Community','MH&LD, MH, LD&Community Trusts':'Mental health / related'}
    table('rank_thresholds.tex',['Benchmark group','$M$','$k$',r'First boundary $\lambda$'],
          [[short.get(r.benchmark_group,latex_escape(r.benchmark_group)),int(r.units),int(r.k),
            ('None at finite '+r'$\lambda$' if pd.isna(r.first_membership_crossing) else f'{r.first_membership_crossing:,.2f}')]
           for _,r in thresholds.iterrows()])
    cohort=pd.read_csv(ROOT/'results/harmonised/analysis_cohort.csv');latest=cohort[cohort.year==2025]
    rows=[]
    for group,g in latest.groupby('benchmark_group'):
        rows.append([short.get(group,latex_escape(group)),len(g),f'{g.burnout_n.min():,.0f}',
                     f'{g.burnout_n.median():,.1f}',f'{g.burnout_n.max():,.0f}'])
    table('cohort.tex',['Benchmark group','Units','Minimum $n$','Median $n$','Maximum $n$'],rows)

def simulation_reports():
    sim=pd.read_csv(ROOT/'results/simulation.csv')
    focus=sim[(sim.fraction==.2)&(sim.sigma2==6.25)&(sim.psi==0)]
    methods=['equal_history','geometric_history','gaussian_posterior']
    phis=sorted(focus.phi.unique());los=sorted(focus.n_lo.unique())
    values=[]
    for method in methods:
        matrix=np.empty((len(los),len(phis)))
        for a,lo in enumerate(los):
            for b,phi in enumerate(phis):
                cell=focus[(focus.n_lo==lo)&(focus.phi==phi)]
                matrix[a,b]=cell[cell.method==method].latent_regret_mean.iloc[0]-cell[cell.method=='raw'].latent_regret_mean.iloc[0]
        values.append(matrix)
    bound=max(abs(a).max() for a in values)
    fig,axes=plt.subplots(1,3,figsize=(6.5,2.7),sharey=True)
    for ax,method,matrix in zip(axes,methods,values):
        im=ax.imshow(matrix,aspect='auto',cmap='RdBu_r',vmin=-bound,vmax=bound)
        ax.set_xticks(range(len(phis)),[str(p) for p in phis],rotation=45)
        ax.set_xlabel(r'Latent persistence $\phi$')
        ax.set_title('Equal history' if method=='equal_history' else ('Geometric history' if method=='geometric_history' else 'Gaussian posterior'))
        ax.set_yticks(range(len(los)),['20–120','40–250','150–600','800–3000'])
    axes[0].set_ylabel('Nominal size range')
    fig.subplots_adjust(left=.12,right=.84,bottom=.24,top=.84,wspace=.18)
    cax=fig.add_axes([.87,.24,.022,.60]);fig.colorbar(im,cax=cax,label='Regret difference from raw')
    save(fig,'simulation_regret')
    ref=focus[focus.phi==.85];rows=[]
    for lo in los:
        subset=ref[ref.n_lo==lo];hi=int(subset.n_hi.iloc[0]);row=[f'{lo}--{hi}']
        for method in ['raw','geometric_history','gaussian_posterior']:
            r=subset[subset.method==method].iloc[0];row += [f'{100*r.hit_mean:.1f}',f'{r.latent_regret_mean:.4f}']
        rows.append(row)
    table('simulation_reference.tex',['Size range',r'Raw hit\%','Regret',r'Geom. hit\%','Regret',r'Gauss. hit\%','Regret'],rows)

    refall=sim[(sim.fraction==.2)&(sim.method=='raw')]
    fig,(ax,bx)=plt.subplots(1,2,figsize=(6.5,2.8))
    for j,psi in enumerate([0.,.5]):
        q=refall[refall.psi==psi]
        ax.errorbar(q.predicted_rebound_mean,q.rebound_mean,yerr=1.96*q.rebound_residual_mcse,
                    fmt='o',markersize=3,alpha=.65,color=COLORS[j],label=fr'Error correlation $\psi={psi}$')
    lim=max(refall.predicted_rebound_mean.max(),refall.rebound_mean.max())*1.05
    ax.plot([0,lim],[0,lim],color='0.4',lw=.8);ax.set_xlabel('Mean conditional prediction');ax.set_ylabel('Mean simulated selected change')
    ax.legend(frameon=False,fontsize=7)
    n=np.geomspace(10,10000,200);tau2=.35**2;sigma2=6.25;phi=.85
    w=phi**np.arange(5);w/=w.sum();C=phi**np.abs(np.arange(5)[:,None]-np.arange(5)[None,:]);c=phi**np.arange(5)
    D=tau2*(1-2*w@c+w@C@w);crit=sigma2*(1-w@w)/D
    _,_,postvar,_=gaussian_weights(n,tau2,sigma2,phi,0.,5)
    bx.loglog(n,sigma2/n,label='Current score',color=COLORS[0]);bx.loglog(n,D+sigma2/n*(w@w),label='Fixed geometric',color=COLORS[1])
    bx.loglog(n,postvar,label='Gaussian posterior',color=COLORS[2]);bx.axvline(crit,color='0.4',lw=.8,ls='--')
    bx.text(crit*1.06,.2,f'{crit:.1f}',fontsize=8);bx.set_xlabel('Equal nominal sample size n');bx.set_ylabel('Current-state MSE');bx.legend(frameon=False,fontsize=7)
    fig.tight_layout();save(fig,'rebound_and_pooling')
    save_csv(ROOT/'results/pooling_curve.csv',[dict(n=float(a),raw_mse=float(b),geometric_mse=float(c),posterior_mse=float(d))
              for a,b,c,d in zip(n,sigma2/n,D+sigma2/n*(w@w),postvar)])

    stress=pd.read_csv(ROOT/'results/simulation_stress.csv');stress=stress[(stress.fraction==.2)&stress.method.isin(['raw','geometric_history','gaussian_posterior','independent_error_posterior'])]
    desc={0:'Heavy-tailed error',1:'Common decline',2:'Persistent response bias',3:'Strong error correlation'}
    table('stress.tex',['Stress','Rule','Latent regret','Observed change','Predicted change'],
          [[desc[int(r.cell_id)],(r'Geometric history (known $\phi$)' if r.method=='geometric_history' else LABEL.get(r.method,r.method)),f'{r.latent_regret_mean:.4f}',f'{r.rebound_mean:+.4f}',f'{r.predicted_rebound_mean:+.4f}']
           for _,r in stress.iterrows()],alignment='llrrr')

def main():
    empirical_reports();simulation_reports()
    harmonised=pd.read_csv(ROOT/'results/harmonised/test_metrics.csv').set_index('method')
    vintage=pd.read_csv(ROOT/'results/vintage/test_metrics.csv').set_index('method')
    follow=pd.read_csv(ROOT/'results/harmonised/observational_followup.csv').iloc[-1]
    values={'RawHrmse':f'{harmonised.loc["latest","rmse"]:.4f}',
            'RawVrmse':f'{vintage.loc["latest","rmse"]:.4f}',
            'MeanVrmse':f'{vintage.loc["group_mean_reversion","rmse"]:.4f}',
            'CovVrmse':f'{vintage.loc["working_covariance","rmse"]:.4f}',
            'SelectedChange':f'{follow.observed_selected_change:.4f}',
            'PeerChange':f'{follow.corresponding_group_change:.4f}',
            'AdjustedChange':f'{follow.group_centred_change:.4f}'}
    (TABLE/'numbers.tex').write_text(''.join('\\newcommand{\\'+name+'}{'+value+'}\n' for name,value in values.items()))
    print('Generated manuscript figures and tables from saved results.')

if __name__=='__main__':main()
