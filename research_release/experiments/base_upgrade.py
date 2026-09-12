#!/usr/bin/env python3
"""Reproducible synthetic studies for incumbent-anchored model selection.

All observations are generated from explicit bounded paired-score families.
No neural model, translation benchmark, or production trace is represented.
Binomial counts are sampled directly because they are exact sufficient
statistics for the Rademacher and two-point observations defined below.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta, binom, norm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "papers" / "base_upgrade" / "results"
FIG = ROOT / "papers" / "base_upgrade" / "figures"
ALPHA = 0.05
SEED = 20260911


def interval(k: int, n: int, level: float = 0.95) -> tuple[float, float]:
    """Equal-tailed exact Clopper--Pearson interval for a Bernoulli rate."""
    a = (1 - level) / 2
    return (float(beta.ppf(a, k, n-k+1)) if k else 0.0,
            float(beta.ppf(1-a, k+1, n-k)) if k < n else 1.0)


def mean_interval(values: np.ndarray) -> tuple[float, float, float]:
    mu = float(np.mean(values))
    half = float(1.96 * np.std(values, ddof=1) / np.sqrt(len(values)))
    return mu, mu-half, mu+half


def hoeffding_radius(width: np.ndarray | float, n: int, eta: float) -> np.ndarray:
    return np.asarray(width) * np.sqrt(np.log(1/eta) / (2*n))


def candidate_iut_pvalues(counts: np.ndarray, n: int, epsilon: float,
                         half_range: float = 0.2) -> np.ndarray:
    """Exact whole-candidate p-value: max of slice non-inferiority p-values.

    X in {-half_range,+half_range}; unsafe null includes E[X] <= -epsilon.
    The final dimension of counts indexes slices. No slice independence is
    required for validity, although some experiments generate independent slices.
    """
    p0 = (half_range-epsilon) / (2*half_range)
    return np.max(binom.sf(counts-1, n, p0), axis=-1)


def fixed_sequence(pvalues: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Certify a frozen order only up to its first non-rejection."""
    return np.cumprod(pvalues <= alpha, axis=-1).astype(bool)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def rate_row(exp: str, flags: np.ndarray, **kwargs) -> dict:
    k, n = int(np.sum(flags)), len(flags)
    lo, hi = interval(k, n)
    return {"experiment": exp, **kwargs, "trials": n, "events": k,
            "rate": k/n, "lower_95": lo, "upper_95": hi}


def gates(counts: np.ndarray, n: int, epsilon: float) -> dict[str, np.ndarray]:
    k = counts.shape[-1]
    mean = 0.4*counts/n - 0.2
    p0 = (0.2-epsilon)/0.4
    ps = binom.sf(counts-1, n, p0)
    # The no-harm gate rejects a slice only if its lower-tail harm test is
    # significant. This tests for harm; it does not certify non-inferiority.
    harm_ps = binom.cdf(counts, n, p0)
    return {
        "point": np.all(mean >= -epsilon, axis=-1),
        "no_detected_harm": np.all(harm_ps > ALPHA/k, axis=-1),
        "exact_iut": np.all(ps <= ALPHA, axis=-1),
        "simultaneous_exact": np.all(ps <= ALPHA/k, axis=-1),
        "hoeffding_iut": np.all(mean-hoeffding_radius(0.4,n,ALPHA) >= -epsilon,
                                axis=-1),
    }


def calibration(rng: np.random.Generator, trials: int) -> list[dict]:
    rows, raw, sufficient = [], [], {}
    for n in [128, 512, 2048]:
        for k in [1, 8, 32]:
            for scenario in ["one_harmful", "all_safe"]:
                # One harmful slice is 0.002 beyond tolerance. All other
                # slices in that scenario are easy, isolating false release.
                mu = np.full(k, 0.08 if scenario == "one_harmful" else 0.01)
                if scenario == "one_harmful":
                    mu[0] = -0.022
                counts = rng.binomial(n, (mu+0.2)/0.4, size=(trials,k))
                sufficient[f"n{n}_K{k}_{scenario}"]=counts.astype(np.uint16)
                for name, accepted in gates(counts,n,0.02).items():
                    rows.append(rate_row("calibration", accepted, n=n, slices=k,
                                         scenario=scenario, gate=name))
                    raw.append(np.packbits(accepted))
    # Raw Bernoulli outcomes suffice to reproduce every reported rate and CI.
    np.savez_compressed(OUT/"calibration_outcomes.npz", outcomes=np.stack(raw),
                        trials=trials)
    np.savez_compressed(OUT/"calibration_counts.npz",**sufficient)
    write_csv(OUT/"calibration.csv",rows)
    return rows


def adaptive_selection(rng: np.random.Generator, trials: int) -> list[dict]:
    rows = []
    stored = {}
    n, epsilon = 2048, 0.02
    # Every candidate is slightly unsafe. Candidate score vectors are
    # independent conditional on the frozen library; the incumbent is exact.
    probability = (0.2-epsilon-0.0005)/0.4
    p0 = (0.2-epsilon)/0.4
    for j in [1,5,20,100]:
        counts = rng.binomial(n,probability,size=(trials,j))
        ps = binom.sf(counts-1,n,p0)
        dev = rng.binomial(n,probability,size=(trials,j))
        stored[f"J{j}_certification_counts"]=counts.astype(np.uint16)
        stored[f"J{j}_development_counts"]=dev.astype(np.uint16)
        dev_choice = np.argmax(dev,axis=1)
        decisions = {
            "reuse_uncorrected": np.any(ps <= ALPHA,axis=1),
            "bonferroni_candidates": np.any(ps <= ALPHA/j,axis=1),
            "fixed_sequence": np.any(fixed_sequence(ps),axis=1),
            "independent_development": ps[np.arange(trials),dev_choice] <= ALPHA,
        }
        for name, flags in decisions.items():
            rows.append(rate_row("adaptive_selection",flags,n=n,candidates=j,gate=name))
            stored[f"J{j}_{name}"] = np.packbits(flags)
    np.savez_compressed(OUT/"adaptive_outcomes.npz",trials=trials,**stored)
    write_csv(OUT/"adaptive_selection.csv",rows)
    return rows


def correlated_calibration(rng: np.random.Generator, trials: int) -> list[dict]:
    """Shared-uniform observations preserve real cross-slice dependence.

    A fixed fraction of each slice's n examples uses common latent uniforms;
    all remaining uniforms are independent. Thresholding a common uniform at
    each slice's success probability retains correct binomial marginals.
    """
    rows,packed,sufficient=[],[],{}
    n,k=512,32
    for rho in [0.0,0.5,1.0]:
        shared=int(n*rho)
        for scenario in ["one_harmful","all_safe"]:
            if scenario == "one_harmful":
                low,high=(.2-.022)/.4,(.2+.08)/.4
                joint=rng.multinomial(shared,[low,high-low,1-high],size=trials)
                common=np.repeat((joint[:,0]+joint[:,1])[:,None],k,axis=1)
                common[:,0]=joint[:,0]
                probs=np.full(k,high); probs[0]=low
            else:
                probs=np.full(k,(.2+.01)/.4)
                common=np.repeat(rng.binomial(shared,probs[0],trials)[:,None],k,axis=1)
            counts=common+rng.binomial(n-shared,probs,size=(trials,k))
            sufficient[f"rho{rho}_{scenario}"]=counts.astype(np.uint16)
            for name,accepted in gates(counts,n,.02).items():
                rows.append(rate_row("correlated_calibration",accepted,n=n,slices=k,
                                     shared_fraction=rho,scenario=scenario,gate=name))
                packed.append(np.packbits(accepted))
    write_csv(OUT/"correlated_calibration.csv",rows)
    np.savez_compressed(OUT/"correlated_outcomes.npz",outcomes=np.stack(packed),trials=trials)
    np.savez_compressed(OUT/"correlated_counts.npz",**sufficient)
    return rows


def geometry(slices: int = 8) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    mus = np.tile([0.10,0.04],(slices,1))
    mus[0] = [-0.08,0.02]
    grid = np.linspace(0,1,21)
    scalar = np.column_stack([grid,grid])
    block = np.array([(a,b) for a in grid for b in grid])
    return mus,scalar,block


def utility_selection(rng: np.random.Generator, trials: int) -> list[dict]:
    rows, raw, sufficient = [], [], {}
    mus,scalar,block = geometry()
    dense_grid=np.linspace(0,1,len(block))
    scalar_dense=np.column_stack([dense_grid,dense_grid])
    epsilon = 0.01
    for n in [128,512,2048]:
        # A development split selects ONE candidate. A fresh certification
        # split tests that candidate. No retry after certification failure.
        devcounts=rng.binomial(n,0.5,size=(trials,8,2))
        calcounts=rng.binomial(n,0.5,size=(trials,8,2))
        sufficient[f"n{n}_development_counts"]=devcounts.astype(np.uint16)
        sufficient[f"n{n}_certification_counts"]=calcounts.astype(np.uint16)
        dev = mus + 0.06*(2*devcounts/n-1)
        cal = mus + 0.06*(2*calcounts/n-1)
        for family,library in [("scalar",scalar),("scalar_dense",scalar_dense),("block",block)]:
            # Known structural bounds: each observed coefficient lies in
            # [-0.2,0.2], so X(lambda) has width 0.4*||lambda||_1.
            radius = hoeffding_radius(0.4*library.sum(axis=1),n,ALPHA)
            # Candidate search anticipates certificate width and adds a fixed
            # design buffer; this is a disclosed heuristic, not a theorem.
            buffer = 0.12*np.linalg.norm(library,axis=1)/np.sqrt(n)
            selected = []
            for start in range(0,trials,256):
                d = np.einsum("tkl,jl->tkj",dev[start:start+256],library)
                feasible = np.all(d-radius-buffer >= -epsilon,axis=1)
                feasible[:,0] = True
                objective = d.mean(axis=1)
                objective[~feasible] = -np.inf
                selected.extend(np.argmax(objective,axis=1).tolist())
            selected = np.asarray(selected)
            lam = library[selected]
            calmean = np.einsum("tkl,tl->tk",cal,lam)
            lower = calmean-radius[selected,None]
            passed = np.all(lower >= -epsilon,axis=1)
            identity = np.all(lam == 0,axis=1)
            passed[identity] = True
            deployed = lam.copy()
            deployed[~passed] = 0
            truth = deployed @ mus.T
            gain = truth.mean(axis=1)
            unsafe = np.any(truth < -epsilon-1e-12,axis=1)
            retained = gain / float(np.mean(mus.sum(axis=1)))
            oracle_d = library @ mus.T
            oracle_ok = np.all(oracle_d >= -epsilon-1e-12,axis=1)
            oracle_idx = np.argmax(np.where(oracle_ok,oracle_d.mean(axis=1),-np.inf))
            oracle_gain = float(oracle_d[oracle_idx].mean())
            avg,lo,hi = mean_interval(gain)
            lowrisk,highrisk = interval(int(unsafe.sum()),trials)
            rows.append({"experiment":"utility_selection","n_development":n,
                         "n_certification":n,"slices":8,"family":family,
                         "library_size":len(library),"trials":trials,
                         "gain_mean":avg,"gain_lower_95":lo,"gain_upper_95":hi,
                         "retained_gain_mean":float(retained.mean()),
                         "fallback_rate":float(np.mean(np.all(deployed == 0,axis=1))),
                         "certification_failure_rate":float(np.mean(~passed)),
                         "unsafe_count":int(unsafe.sum()),"unsafe_rate":float(unsafe.mean()),
                         "unsafe_lower_95":lowrisk,"unsafe_upper_95":highrisk,
                         "oracle_grid_gain":oracle_gain,
                         "oracle_lambda1":float(library[oracle_idx,0]),
                         "oracle_lambda2":float(library[oracle_idx,1]),
                         "selected_lambda1_mean":float(lam[:,0].mean()),
                         "selected_lambda2_mean":float(lam[:,1].mean()),
                         "deployed_lambda1_mean":float(deployed[:,0].mean()),
                         "deployed_lambda2_mean":float(deployed[:,1].mean())})
            for i in range(trials):
                raw.append({"n":n,"family":family,"trial":i,
                            "selected_lambda1":float(lam[i,0]),
                            "selected_lambda2":float(lam[i,1]),
                            "certified":bool(passed[i]),
                            "deployed_lambda1":float(deployed[i,0]),
                            "deployed_lambda2":float(deployed[i,1]),
                            "gain":float(gain[i]),"unsafe":bool(unsafe[i])})
    write_csv(OUT/"utility_selection.csv",rows)
    write_csv(OUT/"utility_trials.csv",raw)
    np.savez_compressed(OUT/"utility_counts.npz",**sufficient)
    return rows


def paired_variance(rng: np.random.Generator, trials: int) -> list[dict]:
    # score_old = 0.5 + 0.20 U; score_new = 0.5 + 0.20 U + 0.01 + 0.02 V,
    # U,V independent Rademacher. All scores are in [0,1].
    n=256
    u_old = 2*rng.binomial(n,.5,trials)/n-1
    u_new_ind = 2*rng.binomial(n,.5,trials)/n-1
    v = 2*rng.binomial(n,.5,trials)/n-1
    paired = .01+.02*v
    unpaired = .01+.20*(u_new_ind-u_old)+.02*v
    rows=[]
    for name,observed,theory in [("paired",paired,.02**2/n),
                                  ("independent",unpaired,(2*.20**2+.02**2)/n)]:
        rows.append({"method":name,"n":n,"trials":trials,
                     "empirical_variance":float(np.var(observed,ddof=1)),
                     "theoretical_variance":theory})
    write_csv(OUT/"paired_variance.csv",rows)
    return rows


def figures(calrows: list[dict], adrows: list[dict], utrows: list[dict]) -> None:
    plt.rcParams.update({"font.size":11,"axes.spines.top":False,
                         "axes.spines.right":False,"savefig.bbox":"tight",
                         "font.family":"DejaVu Sans","pdf.fonttype":42})
    colors={"point":"#8C6D31","no_detected_harm":"#BB4F49",
            "exact_iut":"#216A9C","simultaneous_exact":"#7A65A3",
            "hoeffding_iut":"#238273"}
    labels={"point":"Point estimate","no_detected_harm":"No detected harm",
            "exact_iut":"Exact IUT","simultaneous_exact":"Simultaneous exact",
            "hoeffding_iut":"Hoeffding IUT"}
    fig,axes=plt.subplots(1,2,figsize=(10,3.2),sharex=True)
    for ax,scenario,title in zip(axes,["one_harmful","all_safe"],
                                 ["One harmful slice","All slices safe"]):
        for name in colors:
            r=[x for x in calrows if x["n"]==512 and x["scenario"]==scenario
               and x["gate"]==name]
            ys=np.array([x["rate"] for x in r])
            ax.errorbar([x["slices"] for x in r],ys,
                        yerr=np.array([[x["rate"]-x["lower_95"] for x in r],
                                       [x["upper_95"]-x["rate"] for x in r]]),
                        label=labels[name],color=colors[name],marker="o",capsize=2)
        ax.set(title=title,xlabel="Number of slices K",ylim=(-.025,1.025))
        ax.set_xscale("log",base=2)
        ax.set_xticks([1,8,32],["1","8","32"])
        ax.minorticks_off()
        ax.grid(alpha=.18)
    axes[0].set_ylabel("Probability of release")
    axes[0].axhline(ALPHA,color="#333333",ls="--",lw=1)
    handles,labs=axes[1].get_legend_handles_labels()
    fig.legend(handles,labs,loc="lower center",ncol=3,bbox_to_anchor=(.5,-.13),frameon=False)
    fig.tight_layout()
    fig.savefig(FIG/"gate_calibration.pdf")
    fig.savefig(FIG/"gate_calibration.png",dpi=180)
    plt.close(fig)

    fig,ax=plt.subplots(figsize=(6.8,3.6))
    acols=["#BB4F49","#216A9C","#238273","#7A65A3"]
    names=["reuse_uncorrected","bonferroni_candidates","fixed_sequence","independent_development"]
    labs=["Reuse, no candidate correction","Bonferroni over candidates",
          "Frozen fixed sequence","Independent development choice"]
    for name,lab,col in zip(names,labs,acols):
        r=[x for x in adrows if x["gate"]==name]
        ax.errorbar([x["candidates"] for x in r],[x["rate"] for x in r],
                    yerr=np.array([[x["rate"]-x["lower_95"] for x in r],
                                   [x["upper_95"]-x["rate"] for x in r]]),
                    color=col,label=lab,marker="o",capsize=2)
    ax.set(xlabel="Number of frozen candidates J",ylabel="False release probability",
           xscale="log",ylim=(-.02,1.02))
    ax.set_xticks([1,5,20,100],["1","5","20","100"])
    ax.minorticks_off()
    ax.axhline(ALPHA,color="#333",ls="--",lw=1,label="Target 0.05")
    ax.legend(frameon=False,fontsize=9,loc="upper left")
    ax.grid(alpha=.18)
    fig.tight_layout()
    fig.savefig(FIG/"adaptive_selection.pdf")
    fig.savefig(FIG/"adaptive_selection.png",dpi=180)
    plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(10,3.5))
    mus,_,_=geometry()
    x=np.linspace(0,1,301)
    xx,yy=np.meshgrid(x,x)
    gg=np.stack([xx,yy],axis=-1)
    gain=gg@mus.mean(axis=0)
    frag=gg@mus[0]
    im=axes[0].pcolormesh(xx,yy,gain,cmap="Blues",shading="auto",rasterized=True)
    axes[0].contour(xx,yy,frag,levels=[-.01],colors=["#BB4F49"],linewidths=2)
    axes[0].plot(x,x,color="#6A5D9E",ls="--",label="Scalar path")
    axes[0].scatter([1/6,.375],[1/6,1],c=["#6A5D9E","#BB4F49"],s=45,zorder=4)
    axes[0].text(.10,.60,"Feasible",color="#21364A")
    axes[0].text(.52,.30,"Fragile slice\nregresses",color="#923C35")
    axes[0].set(xlabel=r"Block coefficient $\lambda_1$",ylabel=r"Block coefficient $\lambda_2$",
                title="Known population geometry")
    axes[0].legend(frameon=False,fontsize=9.5,loc="lower right")
    fig.colorbar(im,ax=axes[0],label="Aggregate gain",fraction=.046)
    for family,color,label in [("scalar","#9A91B8","Scalar (21)"),
                               ("scalar_dense","#6A5D9E","Scalar (441)"),
                               ("block","#216A9C","Block (441)")]:
        r=[z for z in utrows if z["family"]==family]
        axes[1].errorbar([z["n_certification"] for z in r],[z["gain_mean"] for z in r],
                         yerr=np.array([[z["gain_mean"]-z["gain_lower_95"] for z in r],
                                        [z["gain_upper_95"]-z["gain_mean"] for z in r]]),
                         color=color,marker="o",label=label,capsize=3)
        if family != "scalar":
            axes[1].axhline(r[0]["oracle_grid_gain"],color=color,ls=":",alpha=.7,
                           label=label+" oracle")
    axes[1].set(xlabel="Examples per slice in each split",ylabel="Mean deployed aggregate gain",
                xscale="log",ylim=(0,.072),title="Certification and fallback")
    axes[1].set_xticks([128,512,2048],["128","512","2048"])
    axes[1].minorticks_off()
    axes[1].legend(frameon=False,fontsize=9.5)
    axes[1].grid(alpha=.18)
    fig.tight_layout()
    fig.savefig(FIG/"geometry_utility.pdf")
    fig.savefig(FIG/"geometry_utility.png",dpi=180)
    plt.close(fig)


def latex_tables(calrows: list[dict], adrows: list[dict], utrows: list[dict], varrows: list[dict], corrrows: list[dict]) -> None:
    lines=[r"\begin{tabular}{lrrr}",r"\toprule",
           r"Rule & $K=1$ & $K=8$ & $K=32$ \\",r"\midrule"]
    names=[("point","Point estimate"),("no_detected_harm","No detected harm"),
           ("exact_iut","Exact IUT"),("simultaneous_exact","Simultaneous exact"),
           ("hoeffding_iut","Hoeffding IUT")]
    for name,label in names:
        r=[x for x in calrows if x["n"]==512 and x["scenario"]=="one_harmful" and x["gate"]==name]
        lines.append(label+" & "+" & ".join(f'{100*x["rate"]:.2f}' for x in r)+r" \\")
    lines.extend([r"\bottomrule",r"\end{tabular}"])
    (OUT/"calibration_table.tex").write_text("\n".join(lines)+"\n")
    lines=[r"\begin{tabular}{llrrrr}",r"\toprule",
           r"$n$ & Family & Gain & Retained (\%) & Fallback (\%) & Harmful releases \\",r"\midrule"]
    for r in utrows:
        family_label={"scalar":"Scalar (21)","scalar_dense":"Scalar (441)","block":"Block (441)"}[r["family"]]
        lines.append(f'{r["n_certification"]} & {family_label} & {r["gain_mean"]:.4f} & '
                     f'{100*r["retained_gain_mean"]:.1f} & {100*r["fallback_rate"]:.2f} & '
                     f'{r["unsafe_count"]}/{r["trials"]}'+r" \\")
    lines.extend([r"\bottomrule",r"\end{tabular}"])
    (OUT/"utility_table.tex").write_text("\n".join(lines)+"\n")
    lookup=lambda rows,**keys: next(x for x in rows if all(x[k]==v for k,v in keys.items()))
    lines=[r"\begin{tabular}{rrrrrr}",r"\toprule",
           r"$n$ & $K$ & Harm: IUT & Harm: Hoeffding & Safe: IUT & Safe: simultaneous \\",r"\midrule"]
    for n in [128,512,2048]:
        for k in [1,8,32]:
            values=[lookup(calrows,n=n,slices=k,scenario=scenario,gate=gate)["rate"]
                    for scenario,gate in [("one_harmful","exact_iut"),("one_harmful","hoeffding_iut"),
                                          ("all_safe","exact_iut"),("all_safe","simultaneous_exact")]]
            lines.append(f"{n} & {k} & "+" & ".join(f"{100*v:.2f}" for v in values)+r" \\")
    lines.extend([r"\bottomrule",r"\end{tabular}"])
    (OUT/"sample_size_table.tex").write_text("\n".join(lines)+"\n")
    lines=[r"\begin{tabular}{lrrrr}",r"\toprule",
           r"Shared fraction & Harm: no detection & Harm: IUT & Safe: IUT & Safe: simultaneous \\",r"\midrule"]
    for rho in [0.0,0.5,1.0]:
        values=[lookup(corrrows,shared_fraction=rho,scenario=scenario,gate=gate)["rate"]
                for scenario,gate in [("one_harmful","no_detected_harm"),("one_harmful","exact_iut"),
                                      ("all_safe","exact_iut"),("all_safe","simultaneous_exact")]]
        lines.append(f"{rho:.1f} & "+" & ".join(f"{100*v:.2f}" for v in values)+r" \\")
    lines.extend([r"\bottomrule",r"\end{tabular}"])
    (OUT/"correlation_table.tex").write_text("\n".join(lines)+"\n")
    noharm=lookup(calrows,n=512,slices=32,scenario="one_harmful",gate="no_detected_harm")
    iut=lookup(calrows,n=512,slices=32,scenario="one_harmful",gate="exact_iut")
    reuse=lookup(adrows,candidates=100,gate="reuse_uncorrected")
    corrected=lookup(adrows,candidates=100,gate="bonferroni_candidates")
    block=lookup(utrows,n_certification=2048,family="block")
    scalar=lookup(utrows,n_certification=2048,family="scalar_dense")
    macros={"NoharmRate":f'{100*noharm["rate"]:.1f}',"IutRate":f'{100*iut["rate"]:.1f}',
            "ReuseRate":f'{100*reuse["rate"]:.1f}',"CorrectedRate":f'{100*corrected["rate"]:.1f}',
            "BlockGain":f'{block["gain_mean"]:.4f}',"ScalarGain":f'{scalar["gain_mean"]:.4f}',
            "BlockRatio":f'{block["gain_mean"]/scalar["gain_mean"]:.2f}',
            "CalTrials":str(noharm["trials"]),"SearchTrials":str(block["trials"]),
            "VarianceRatio":f'{varrows[1]["empirical_variance"]/varrows[0]["empirical_variance"]:.1f}',
            "ZeroHarmUpper":f'{100*block["unsafe_upper_95"]:.3f}'}
    (OUT/"numbers.tex").write_text("\n".join("\\newcommand{\\"+k+"}{"+v+"}" for k,v in macros.items())+"\n")


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--calibration-trials",type=int,default=20000)
    parser.add_argument("--search-trials",type=int,default=4000)
    parser.add_argument("--seed",type=int,default=SEED)
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(parents=True,exist_ok=True)
    children=np.random.SeedSequence(args.seed).spawn(5)
    cal=calibration(np.random.default_rng(children[0]),args.calibration_trials)
    ad=adaptive_selection(np.random.default_rng(children[1]),args.calibration_trials)
    ut=utility_selection(np.random.default_rng(children[2]),args.search_trials)
    va=paired_variance(np.random.default_rng(children[3]),args.calibration_trials)
    co=correlated_calibration(np.random.default_rng(children[4]),args.calibration_trials)
    figures(cal,ad,ut); latex_tables(cal,ad,ut,va,co)
    manifest={"study":"base_upgrade_synthetic","seed":args.seed,
              "calibration_trials":args.calibration_trials,"search_trials":args.search_trials,
              "alpha":ALPHA,"python":platform.python_version(),"numpy":np.__version__,
              "synthetic_only":True,"score_family":"bounded paired scores; exact binomial sufficient statistics",
              "split_policy":"independent development and certification; no retries after rejection",
              "confidence_intervals":"exact Clopper-Pearson for rates; normal Monte Carlo mean intervals for utility",
              "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "outputs":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir())
                         if p.is_file() and p.name!="manifest.json" and not p.name.startswith("digits")}}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"results":str(OUT),"figures":str(FIG),"seed":args.seed,
                      "calibration_trials":args.calibration_trials,"search_trials":args.search_trials}))


if __name__ == "__main__":
    main()
