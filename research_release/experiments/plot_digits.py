"""Render the public digits result figure from saved per-seed CSVs."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]/'papers/base_upgrade'


def main():
    with (ROOT/'results/digits_summary.csv').open() as f:
        rows=list(csv.DictReader(f))
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.6))
    policies=['incumbent','updated','scalar','layer','released']
    labels=['Incumbent','Continued','Scalar','Layer','Released']
    colors=['#67727e','#cd7847','#458aa2','#716698','#67727e']
    for i,policy in enumerate(policies):
        values=[float(r['weighted_accuracy']) for r in rows if r['policy']==policy]
        axes[0].scatter(np.full(len(values),i)+np.linspace(-.1,.1,len(values)),
                        values,color=colors[i],s=23,alpha=.85)
        axes[0].plot([i-.22,i+.22],[np.mean(values)]*2,color=colors[i],lw=2)
    axes[0].set_xticks(range(5),labels,rotation=25,ha='right')
    axes[0].set_ylabel('Reporting weighted accuracy')
    axes[0].set_title('Public digits: all 5 fixed seeds')
    axes[0].grid(axis='y',alpha=.2)
    with (ROOT/'results/digits_certification.csv').open() as f:
        cert=list(csv.DictReader(f))
    for seed in [1701,1702,1703,1704,1705]:
        selected=[r for r in cert if int(r['seed'])==seed]
        axes[1].plot(range(10),[float(r['lower']) for r in selected],
                     marker='.',alpha=.7,label=str(seed))
    axes[1].axhline(-.03,color='#333333',ls='--',label='Tolerance boundary')
    axes[1].set(xlabel='Digit slice',ylabel='Paired Hoeffding lower bound',
                title='All frozen candidates fail certification')
    axes[1].legend(fontsize=7,ncol=3,loc='upper center',
                    bbox_to_anchor=(0.5,-0.24),frameon=False)
    axes[1].grid(alpha=.2)
    fig.tight_layout()
    (ROOT/'figures').mkdir(exist_ok=True)
    fig.savefig(ROOT/'figures/digits_integration.pdf',bbox_inches='tight')
    fig.savefig(ROOT/'figures/digits_integration.png',dpi=160,bbox_inches='tight')
    plt.close(fig)


if __name__=='__main__':
    main()
