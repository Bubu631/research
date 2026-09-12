#!/usr/bin/env python3
"""Frozen public post-edit experiment; see docs/public_postedit_protocol.md.

All gradients are exact for a shared output-logit bias, not for full weights.
The archived MT system and pretrained gradient-evaluation model are distinct.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import tarfile
import time

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
import numpy as np
import requests
import torch
from huggingface_hub import snapshot_download
from sacremoses import MosesDetokenizer
from transformers import MarianMTModel, MarianTokenizer

RELEASE = Path(__file__).resolve().parents[1]
OUT = RELEASE / "papers/edit_localization/results"
FIG = RELEASE / "papers/edit_localization/figures"
CACHE = Path(os.environ.get("PUBLIC_POSTEDIT_CACHE",str(RELEASE/".cache/public_postedit"))).expanduser()
PAIR = "en-de"
DATA_REV = "2a670a1140416cf80507b5a829659383c878feb8"
MODEL = "Helsinki-NLP/opus-mt-en-de"
MODEL_REV = "6183067f769a302e3861815543b9f312c71b0ca4"
DATA_SHA = "219cdfd4e1d89d47e6136651af5136e3942ee93b4c9c44354b232baa18c75731"
ALPHAS = np.linspace(0, 1, 21)
ADAPT_ALPHAS = [0., .25, .5, .75, 1.]
MECHANISMS = ["edit", "length", "edit_length"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for part in iter(lambda: f.read(2**20), b""):
            h.update(part)
    return h.hexdigest()


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fetch(url, path):
    if not path.exists():
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
    return path


def edit_mask(mt, pe):
    """PE token mask: equal diagonal > substitute > delete > insert ties."""
    m, n = len(mt), len(pe)
    cost = np.empty((m + 1, n + 1), dtype=np.int16)
    cost[:, 0] = np.arange(m + 1)
    cost[0, :] = np.arange(n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost[i, j] = min(cost[i-1, j-1] + (mt[i-1] != pe[j-1]),
                             cost[i-1, j] + 1, cost[i, j-1] + 1)
    edited = np.zeros(n, dtype=bool)
    i, j, deleted = m, n, 0
    while i or j:
        if i and j and mt[i-1] == pe[j-1] and cost[i, j] == cost[i-1, j-1]:
            i, j = i-1, j-1
        elif i and j and cost[i, j] == cost[i-1, j-1] + 1:
            edited[j-1] = True
            i, j = i-1, j-1
        elif i and cost[i, j] == cost[i-1, j] + 1:
            i, deleted = i-1, deleted+1
        else:
            assert j and cost[i, j] == cost[i, j-1]+1
            edited[j-1] = True
            j -= 1
    return edited, int(cost[m, n]), deleted


def load_assets():
    cache = CACHE / "mlqe_pe"
    data_url = f"https://raw.githubusercontent.com/sheffieldnlp/mlqe-pe/{DATA_REV}/data/post-editing/train/{PAIR}-train.tar.gz"
    archive = fetch(data_url, cache / f"{PAIR}-train.tar.gz")
    assert sha(archive) == DATA_SHA
    for name in ["LICENSE", "README.md"]:
        fetch(f"https://raw.githubusercontent.com/sheffieldnlp/mlqe-pe/{DATA_REV}/{name}", cache / name)
    snapshot = Path(snapshot_download(MODEL, revision=MODEL_REV,
        allow_patterns=["README.md", "config.json", "generation_config.json", "pytorch_model.bin",
                        "source.spm", "target.spm", "tokenizer_config.json", "vocab.json"],
        cache_dir=str(CACHE / "huggingface")))
    with tarfile.open(archive) as f:
        columns = {ext: f.extractfile(f"{PAIR}-train/train.{ext}").read().decode("utf-8").splitlines()
                   for ext in ["src", "mt", "pe"]}
    assert len({len(v) for v in columns.values()}) == 1
    return snapshot, columns, {"data_url": data_url, "data_revision": DATA_REV,
        "archive_sha256": sha(archive), "data_license": "CC0-1.0",
        "license_sha256": sha(cache / "LICENSE"), "model_id": MODEL,
        "model_revision": MODEL_REV, "model_license": "CC-BY-4.0" if PAIR=="en-de" else "Apache-2.0",
        "model_files_sha256": {p.name: sha(p) for p in snapshot.iterdir() if p.is_file()}}


def population(columns, tokenizer):
    en, de = MosesDetokenizer(lang="en"), MosesDetokenizer(lang=PAIR.split("-")[1])
    eligible, rejected, seen = [], [], set()
    for k, (src, mt, pe) in enumerate(zip(columns["src"], columns["mt"], columns["pe"]), 1):
        raw_hash = hashlib.sha256((src + "\n" + mt + "\n" + pe).encode()).hexdigest()
        src, mt, pe = en.detokenize(src.split()), de.detokenize(mt.split()), de.detokenize(pe.split())
        sid = tokenizer(src, add_special_tokens=False)["input_ids"]
        mid = tokenizer(text_target=mt, add_special_tokens=False)["input_ids"]
        pid = tokenizer(text_target=pe, add_special_tokens=False)["input_ids"]
        fingerprint = hashlib.sha256((src + "\n" + pe).encode()).hexdigest()
        reason = None
        if not src.strip() or not mt.strip() or not pe.strip():
            reason = "empty"
        elif not (4 <= len(sid) <= 128 and 4 <= len(pid) <= 128 and len(mid) <= 128):
            reason = "length"
        elif fingerprint in seen:
            reason = "duplicate_source_pe"
        if reason:
            rejected.append({"line": k, "reason": reason})
            continue
        seen.add(fingerprint)
        model_source_ids = tokenizer(">>cmn_Hans<< "+src,add_special_tokens=False)["input_ids"] if PAIR=="en-zh" else sid
        eligible.append({"line": k, "raw_triple_sha256": raw_hash, "src": src, "pe": pe,
            "source_ids": model_source_ids + [tokenizer.eos_token_id], "pe_ids": pid + [tokenizer.eos_token_id],
            "mt_ids": mid, "pe_plain_ids": pid, "source_length": len(sid),
            "mt_length": len(mid), "pe_length": len(pid),
            "rank_hash": hashlib.sha256(f"public-postedit-v1|{k}".encode()).hexdigest()})
    eligible.sort(key=lambda r: r["rank_hash"])
    assert len(eligible) >= 512
    selected = eligible[:512]
    rows = []
    for i, record in enumerate(selected):
        mask, distance, deleted = edit_mask(record["mt_ids"], record["pe_plain_ids"])
        record["mask"] = np.append(mask, False)
        record["split"] = "diagnostic" if i < 256 else "reporting"
        record["edit_fraction"] = float(mask.mean())
        row = {k: record[k] for k in ["line", "raw_triple_sha256", "rank_hash", "split",
                                      "source_length", "mt_length", "pe_length", "edit_fraction"]}
        row.update(edited_tokens=int(mask.sum()), untouched_tokens=int((~mask).sum())+1,
                   levenshtein_distance=distance, deletions=deleted)
        rows.append(row)
    write_csv(OUT / "public_selected_ids.csv", rows)
    write_csv(OUT / "public_excluded_ids.csv", rejected)
    return selected, {"input_count": len(columns["src"]), "eligible_count": len(eligible),
        "excluded_counts": {reason: sum(r["reason"] == reason for r in rejected)
                            for reason in sorted({r["reason"] for r in rejected})},
        "selected": 512, "diagnostic": 256, "reporting": 256,
        "split_overlap": len(set(r["line"] for r in selected[:256]) & set(r["line"] for r in selected[256:]))}


def logits_for(record, model, device):
    src = torch.tensor([record["source_ids"]], device=device)
    target = torch.tensor([record["pe_ids"]], device=device)
    with torch.no_grad():
        logits = model(input_ids=src, attention_mask=torch.ones_like(src),
                       labels=target, use_cache=False).logits[0]
    return logits, target[0]


def gradients(selected, model, device):
    n, v = len(selected), model.config.vocab_size
    U, E = np.zeros((n, v), np.float32), np.zeros((n, v), np.float32)
    nll, max_sum_error, checks = [], 0., {}
    start = time.perf_counter()
    for i, record in enumerate(selected):
        logits, target = logits_for(record, model, device)
        # MPS softmax and CPU log-softmax disagree at ~1e-6 on some tails.
        # Evaluate this analytic block consistently in CPU float64, then store float32.
        logits, target = logits.cpu().double(), target.cpu()
        with torch.no_grad():
            probability = logits.softmax(-1)
            gradient = probability.clone()
            gradient[torch.arange(len(target)), target] -= 1
            mask = torch.tensor(record["mask"])
            u = gradient[~mask].sum(0) / len(target)
            e = gradient[mask].sum(0) / len(target)
            U[i], E[i] = u.cpu().numpy(), e.cpu().numpy()
            value = torch.nn.functional.cross_entropy(logits, target).item()
            nll.append(value)
            max_sum_error = max(max_sum_error, abs(float(U[i].sum())), abs(float(E[i].sum())))
        if i == 0:
            log_cpu, tgt_cpu = logits.detach().cpu(), target.cpu()
            b = torch.zeros(v, requires_grad=True,dtype=torch.float64)
            loss = torch.nn.functional.cross_entropy(log_cpu+b, tgt_cpu, reduction="none")
            weights = torch.tensor(np.where(record["mask"], 1., .37), dtype=torch.float64)
            (loss * weights).mean().backward()
            error = float(np.max(np.abs(b.grad.numpy() - (.37*U[i]+E[i]))))
            assert error < 1e-7, error
            checks["analytical_vs_autograd_max_abs"] = error
        if (i+1) % 32 == 0:
            print(f"Gradients {i+1}/{n}; elapsed {time.perf_counter()-start:.1f}s", flush=True)
    assert max_sum_error < 1e-5, max_sum_error
    checks["max_gradient_coordinate_sum_abs"] = max_sum_error
    for label, sl in [("diagnostic", slice(0, 256)), ("reporting", slice(256, 512))]:
        # Separate arrays stay comfortably below GitHub's 100 MB per-file limit.
        for component, array in [("U", U[sl]), ("E", E[sl])]:
            np.savez_compressed(OUT / f"public_gradients_{label}_{component}.npz", gradient=array,
                original_line=np.array([r["line"] for r in selected[sl]]))
    np.save(OUT / "public_base_nll.npy", nll)
    return U, E, np.asarray(nll), checks


def propensity(records, mechanism):
    e = np.asarray([r["edit_fraction"] for r in records])
    length = np.minimum(np.asarray([r["source_length"] for r in records]) / 64., 1.)
    return .1+.8*{"edit": e, "length": length, "edit_length": (e+length)/2}[mechanism]


def analyze(U, E, selected):
    coefficients, curves, risks, mc = [], [], [], []
    mean_vectors = {}
    for split, sl in [("diagnostic", slice(0, 256)), ("reporting", slice(256, 512))]:
        u, e = U[sl].astype(np.float64), E[sl].astype(np.float64)
        n, _ = u.shape
        mu_u, mu_e = u.mean(0), e.mean(0)
        target = mu_u+mu_e
        target_norm2 = float(target@target)
        # Finite n-by-n Gram matrices preserve all coordinates exactly up to roundoff.
        uu, ee, ue = u@u.T, e@e.T, u@e.T
        target_u, target_e = u@target, e@target
        rng = np.random.default_rng(29117)
        for mechanism in MECHANISMS:
            pi = propensity(selected[sl], mechanism)
            q = pi / pi.sum()
            weights = pi.mean()/pi
            q_u,q_e=q@u,q@e
            b_u, b_e = q_u-mu_u, q_e-mu_e
            a,b,c = float(b_u@b_u),float(2*b_u@b_e),float(b_e@b_e)
            d,h,f = float(q_u@q_u),float(2*q_u@q_e),float(q_e@q_e)
            dp,hp,fp = float(mu_u@mu_u),float(2*mu_u@mu_e),float(mu_e@mu_e)
            coeff = dict(split=split, mechanism=mechanism, n=n, pi_min=float(pi.min()),
                pi_max=float(pi.max()), pi_mean=float(pi.mean()),
                numerator_alpha2=a, numerator_alpha1=b, numerator_alpha0=c,
                denominator_alpha2=d, denominator_alpha1=h, denominator_alpha0=f,
                denominator_P_alpha2=dp, denominator_P_alpha1=hp, denominator_P_alpha0=fp,
                b_U_norm=float(np.linalg.norm(b_u)), b_E_norm=float(np.linalg.norm(b_e)),
                b_U_dot_b_E=b/2, mu_U_dot_mu_E=hp/2, Q_U_dot_Q_E=h/2,
                b_U_relative=float(np.linalg.norm(b_u)/np.linalg.norm(mu_u)),
                b_E_relative=float(np.linalg.norm(b_e)/np.linalg.norm(mu_e)),
                derivative_alpha2=a*h-b*d, derivative_alpha1=2*(a*f-c*d),
                derivative_alpha0=b*f-c*h,
                derivative_P_alpha2=a*hp-b*dp, derivative_P_alpha1=2*(a*fp-c*dp),
                derivative_P_alpha0=b*fp-c*hp,
                rho_Q_0=float(np.linalg.norm(b_e)/np.linalg.norm(q_e)),
                rho_Q_1=float(np.linalg.norm(b_u+b_e)/np.linalg.norm(q_u+q_e)),
                rho_P_0=float(np.linalg.norm(b_e)/np.linalg.norm(mu_e)),
                rho_P_1=float(np.linalg.norm(b_u+b_e)/np.linalg.norm(mu_u+mu_e)))
            coefficients.append(coeff)
            for key, vector in [("mu_U",mu_u),("mu_E",mu_e),("b_U",b_u),("b_E",b_e)]:
                mean_vectors[f"{split}_{mechanism}_{key}"] = vector
            counts = rng.multinomial(64, q, size=500)
            for alpha in ALPHAS:
                g = alpha*u+e
                mu = alpha*mu_u+mu_e
                bias = alpha*b_u+b_e
                ipw_mu = (q*weights)@g
                ratio = np.linalg.norm(bias)/np.linalg.norm(q@g)
                ratio_p = np.linalg.norm(bias)/np.linalg.norm(mu)
                derivative = ((a*h-b*d)*alpha**2+2*(a*f-c*d)*alpha+b*f-c*h)
                derivative_p = ((a*hp-b*dp)*alpha**2+2*(a*fp-c*dp)*alpha+b*fp-c*hp)
                curves.append(dict(split=split, mechanism=mechanism, alpha=float(alpha),
                    P_gradient_norm=float(np.linalg.norm(mu)), Q_gradient_norm=float(np.linalg.norm(q@g)),
                    absolute_bias=float(np.linalg.norm(bias)), rho_Q=float(ratio),rho_P=float(ratio_p),
                    oracle_ipw_bias=float(np.linalg.norm(ipw_mu-mu)),
                    rho_Q_squared_derivative_numerator=float(derivative),
                    rho_P_squared_derivative_numerator=float(derivative_p)))
                gram = alpha**2*uu+ee+alpha*(ue+ue.T)
                g_target = alpha*target_u+target_e
                for method, w in [("unweighted",np.ones(n)),("oracle_ipw",weights)]:
                    mean = (q*w)@g
                    bias2 = float(np.sum((mean-target)**2))
                    tracevar = float((q*w*w)@np.diag(gram)-mean@mean)
                    countweights = counts/64*w
                    squared_error = np.einsum("ij,jk,ik->i",countweights,gram,countweights,optimize=True)
                    squared_error += target_norm2 - 2*(countweights@g_target)
                    if squared_error.min() < -1e-10:
                        raise ArithmeticError("Negative squared norm from Gram computation")
                    risks.append(dict(split=split, mechanism=mechanism, alpha=float(alpha), method=method,
                        sample_size=64, target="full_alpha1_population_gradient", squared_bias=bias2,
                        trace_variance=tracevar/64, exact_mse=bias2+tracevar/64,
                        mc_mean_squared_error=float(squared_error.mean()),
                        mc_standard_error=float(squared_error.std(ddof=1)/np.sqrt(len(squared_error)))))
                    for r,value in enumerate(squared_error):
                        mc.append(dict(split=split,mechanism=mechanism,alpha=float(alpha),
                                       method=method,replicate=r,squared_error=float(value)))
            print(f"Analyzed {split}/{mechanism}: rhoQ0={coeff['rho_Q_0']:.6g}, rhoQ1={coeff['rho_Q_1']:.6g}",flush=True)
    write_csv(OUT / "public_coefficients.csv", coefficients)
    write_csv(OUT / "public_bias_curves.csv", curves)
    write_csv(OUT / "public_fixed_target_risk.csv", risks)
    write_csv(OUT / "public_monte_carlo.csv", mc)
    np.savez_compressed(OUT / "public_population_means.npz", **mean_vectors)
    return coefficients, curves, risks


def adapters(U, E, selected):
    rows, biases, samples = [], [], []
    u,e = U[:256].astype(np.float64),E[:256].astype(np.float64)
    for k,mechanism in enumerate(MECHANISMS):
        pi = propensity(selected[:256],mechanism)
        q,w = pi/pi.sum(),pi.mean()/pi
        indices = np.random.default_rng(8101+k).choice(256,size=64,p=q)
        for j,i in enumerate(indices):
            samples.append(dict(mechanism=mechanism,seed=8101+k,draw=j,original_line=selected[i]["line"]))
        for alpha in ADAPT_ALPHAS:
            g=alpha*u+e
            estimates={"population_P":g.mean(0),"sampled_Q":g[indices].mean(0),
                       "oracle_ipw":(g[indices]*w[indices,None]).mean(0)}
            for method,gradient in estimates.items():
                for eta in [1.,10.]:
                    identifier=len(rows)
                    rows.append(dict(adapter_id=identifier,mechanism=mechanism,alpha=alpha,
                                     method=method,step_size=eta,gradient_norm=float(np.linalg.norm(gradient))))
                    biases.append((-eta*gradient).astype(np.float32))
    biases=np.stack(biases)
    write_csv(OUT / "public_adapter_samples.csv",samples)
    np.savez_compressed(OUT / "public_adapters.npz",bias=biases)
    return rows,biases


def evaluate_adapters(records,model,device,biases,rows,base_nll):
    differences=np.zeros((len(records),len(rows)),dtype=np.float64)
    b=torch.tensor(biases,dtype=torch.float64)
    exp_b=torch.exp(b)
    for i,record in enumerate(records):
        logits,target=logits_for(record,model,device)
        logits,target=logits.cpu().double(),target.cpu()
        with torch.no_grad():
            p=logits.softmax(-1)
            # Exact likelihood ratio for fixed teacher-forced hidden states.
            normalization=torch.log(p@exp_b.T)
            delta=normalization-b[:,target].T
            differences[i]=delta.mean(0).cpu().numpy()
        if (i+1)%64==0:
            print(f"Adapter evaluation {i+1}/{len(records)} ({len(rows)} fixed adapters)",flush=True)
    nll=base_nll[:,None]+differences
    for j,row in enumerate(rows):
        row.update(reporting_examples=len(records),baseline_mean_nll=float(base_nll.mean()),
            adapted_mean_nll=float(nll[:,j].mean()),nll_change=float(differences[:,j].mean()),
            nll_change_se=float(differences[:,j].std(ddof=1)/np.sqrt(len(records))))
    write_csv(OUT/"public_adapter_nll.csv",rows)
    np.savez_compressed(OUT/"public_adapter_per_example_nll.npz",baseline=base_nll,
                       delta_nll=differences,original_line=np.array([r["line"] for r in records]))
    return rows


def figures(curves, risks, adapter_rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False})
    colors={"edit":"#a6532b","length":"#2b6886","edit_length":"#6a568f"}
    fig,axes=plt.subplots(1,2,figsize=(9,3.3),layout="constrained")
    for mech in MECHANISMS:
        data=[r for r in curves if r["split"]=="reporting" and r["mechanism"]==mech]
        axes[0].plot([r["alpha"] for r in data],[r["rho_Q"] for r in data],label=mech,color=colors[mech])
        axes[1].plot([r["alpha"] for r in data],[r["absolute_bias"] for r in data],label=mech,color=colors[mech])
    for ax,title in zip(axes,["Relative bias (selected Q mean denominator)","Absolute gradient bias"]):
        ax.set(xlabel=r"Untouched-token weight $\alpha$",ylabel=title)
        ax.grid(alpha=.2)
    axes[0].legend(frameon=False)
    fig.suptitle("Real Marian output-bias gradients; human post-edits; synthetic selection")
    for ext in ["pdf","png"]:fig.savefig(FIG/f"public_gradient_bias.{ext}",dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(10,3),layout="constrained")
    for ax,mech in zip(axes,MECHANISMS):
        for method,style in [("unweighted","-"),("oracle_ipw","--")]:
            data=[r for r in risks if r["split"]=="reporting" and r["mechanism"]==mech and r["method"]==method]
            ax.plot([r["alpha"] for r in data],[r["exact_mse"] for r in data],style,label=method)
        ax.set(title=mech,xlabel=r"$\alpha$",ylabel="MSE to full P gradient")
        ax.grid(alpha=.2)
    axes[0].legend(frameon=False)
    fig.suptitle("Exact finite-population risk, 64 synthetic Q draws")
    for ext in ["pdf","png"]:fig.savefig(FIG/f"public_fixed_target_risk.{ext}",dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(10,3),layout="constrained")
    for ax,mech in zip(axes,MECHANISMS):
        for method in ["population_P","sampled_Q","oracle_ipw"]:
            data=[r for r in adapter_rows if r["mechanism"]==mech and r["method"]==method and r["step_size"]==10.]
            ax.plot([r["alpha"] for r in data],[r["nll_change"] for r in data],"o-",label=method,markersize=3)
        ax.axhline(0,color="gray",lw=.6)
        ax.set(title=mech,xlabel=r"$\alpha$",ylabel="Held-out NLL change (nats/token)")
        ax.grid(alpha=.2)
    axes[0].legend(frameon=False,fontsize=8)
    fig.suptitle("One output-bias gradient step (eta=10); no base-weight fine-tuning")
    for ext in ["pdf","png"]:fig.savefig(FIG/f"public_adapter_nll.{ext}",dpi=180)
    plt.close(fig)


def main():
    global PAIR,MODEL,MODEL_REV,DATA_SHA,OUT,FIG
    parser=argparse.ArgumentParser()
    parser.add_argument("--reuse-gradients",action="store_true")
    parser.add_argument("--pair",choices=["en-de","en-zh"],default="en-de")
    args=parser.parse_args()
    PAIR=args.pair
    if PAIR=="en-zh":
        MODEL="Helsinki-NLP/opus-mt-en-zh"
        MODEL_REV="408d9bc410a388e1d9aef112a2daba955b945255"
        DATA_SHA="9aee7f258d9a7050a6f46851ff37c6cfe4efd074a57fd692af832f2d8c864d5c"
        OUT=OUT/"public_en_zh";FIG=FIG/"public_en_zh"
    started=time.perf_counter()
    OUT.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
    (OUT/f"public_executed_script_{PAIR.replace('-','_')}.py").write_bytes(Path(__file__).read_bytes())
    torch.set_num_threads(4);torch.manual_seed(1701);np.random.seed(1701)
    device="mps" if torch.backends.mps.is_available() else "cpu"
    protocol=RELEASE/"docs/public_postedit_protocol.md"
    (OUT/"public_protocol_snapshot.md").write_bytes(protocol.read_bytes())
    print(f"Frozen protocol sha256={sha(protocol)}; device={device}",flush=True)
    snapshot,columns,manifest=load_assets()
    tokenizer=MarianTokenizer.from_pretrained(snapshot,local_files_only=True)
    selected,pop=population(columns,tokenizer)
    manifest.update(population=pop,protocol_sha256=sha(protocol),script_sha256=sha(__file__),language_pair=PAIR,
        device=device,platform=platform.platform(),machine=platform.machine(),
        versions={p:importlib.metadata.version(p) for p in ["torch","transformers","sentencepiece",
                    "sacremoses","numpy","scipy","matplotlib","huggingface-hub","requests"]},
        run_started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        scope="Real public human post-edits; separate frozen MT evaluation model; shared output-bias gradients; synthetic selection")
    write_json(OUT/"public_manifest_in_progress.json",manifest)
    model=MarianMTModel.from_pretrained(snapshot,local_files_only=True).to(device).eval()
    for p in model.parameters():p.requires_grad_(False)
    manifest["model_parameter_count"]=sum(p.numel() for p in model.parameters())
    print(f"Loaded {manifest['model_parameter_count']:,} parameters; selected {len(selected)} examples",flush=True)
    t=time.perf_counter()
    if args.reuse_gradients:
        U=np.concatenate([np.load(OUT/f"public_gradients_{s}_U.npz")["gradient"] for s in ["diagnostic","reporting"]])
        E=np.concatenate([np.load(OUT/f"public_gradients_{s}_E.npz")["gradient"] for s in ["diagnostic","reporting"]])
        nll=np.load(OUT/"public_base_nll.npy")
        checks={"reused_saved_gradients":True}
    else:
        U,E,nll,checks=gradients(selected,model,device)
    manifest["gradient_wall_seconds"]=time.perf_counter()-t
    manifest["checks"]=checks
    coefficients,curves,risks=analyze(U,E,selected)
    rows,biases=adapters(U,E,selected)
    rows=evaluate_adapters(selected[256:],model,device,biases,rows,nll[256:])
    figures(curves,risks,rows)
    manifest["total_wall_seconds"]=time.perf_counter()-started
    manifest["max_oracle_ipw_population_bias"]=max(r["oracle_ipw_bias"] for r in curves)
    manifest["output_sha256"]={p.name:sha(p) for p in sorted(OUT.glob("public_*"))
                               if p.is_file() and "manifest" not in p.name}
    manifest["completed"]=True
    write_json(OUT/"public_manifest.json",manifest)
    print(json.dumps({"complete":True,"seconds":manifest["total_wall_seconds"],
        "reporting_endpoints":[r for r in coefficients if r["split"]=="reporting"]},indent=2),flush=True)


if __name__=="__main__":
    main()
