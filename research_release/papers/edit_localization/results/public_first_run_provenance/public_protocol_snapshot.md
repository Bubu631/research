# Public human post-edit gradient experiment: frozen protocol

Protocol frozen before any model forward pass: 2026-09-11. This is a finite-population mechanism experiment using real public human post-edits and a pretrained translation model, with deliberately injected selection. It is not a measurement of production complaints, full-model training, or translation-quality improvement.

## Assets and scope

- Dataset: author-released [MLQE-PE](https://github.com/sheffieldnlp/mlqe-pe), English–German post-editing **training** archive, 7,000 source/MT/human-PE triples. Git revision `2a670a1140416cf80507b5a829659383c878feb8`; archive SHA-256 `219cdfd4e1d89d47e6136651af5136e3942ee93b4c9c44354b232baa18c75731`. The repository's license is CC0-1.0. Cite [Fomicheva et al., MLQE-PE](https://arxiv.org/abs/2010.04480). The [WMT20 APE task](https://www.statmt.org/wmt20/ape-task.html) describes human revisions of neural translations of Wikipedia sentences.
- Model: [Helsinki-NLP/opus-mt-en-de](https://huggingface.co/Helsinki-NLP/opus-mt-en-de), revision `6183067f769a302e3861815543b9f312c71b0ca4`, CC-BY-4.0. Source and target SentencePiece tokenizers from this same snapshot. The model is not the system that generated the dataset's original MT. Potential overlap with pretrained model training data is unmeasured, so this is not a clean generalization benchmark.
- Initial candidate WMT16 APE was not used: the official distribution requires named/email download steps. This change was made before any model computation or outcome inspection. MLQE-PE provides a small, directly accessible author release.
- Local machine: Apple M1 Pro / 16 GB; use float32 MPS if supported, otherwise CPU. Record actual device, versions, parameter count, elapsed time, and hashes. Do not run an optimizer over base-model weights.

## Population and untouched/edited masks

1. Read the archive directly; match source, MT, PE by their original 1-based line number. Preserve original strings for hashing; Moses-detokenize English source and German MT/PE for model input.
2. Exclude empty records and records with fewer than 4 or more than 128 source or PE subword tokens, or over 128 MT subword tokens; no truncation. Deduplicate by SHA-256 of detokenized source + newline + PE, retaining the earliest row.
3. Rank eligible unique records by SHA-256 of `public-postedit-v1|` followed by the decimal original line number. Take the first 512. First 256 form a diagnostic/adaptation population; next 256 form a disjoint reporting/evaluation population. These are finite populations, not iid draws from a claimed traffic distribution. All eligible/excluded counts and selected IDs are saved.
4. Target-tokenize MT and PE without special tokens. Compute minimum-unit-cost Levenshtein alignment. Backtracking ties prefer equal diagonal, substitution diagonal, deletion, then insertion. A PE token is untouched only when aligned to an equal MT token; substitutions and insertions are edited. Deletions have no PE token and receive no separate gradient. Add EOS as untouched to both sequences. Record this limitation.

## Exact restricted gradients

Teacher-force the frozen model on source and PE. Introduce one **shared output-logit bias vector** `b` added at every PE position. At `b=0`, each token's gradient is `softmax(logits) − onehot(PE token)`. Compute `g_U` and `g_E` by summing that vector on untouched and edited positions respectively, each divided by the **total** target length including EOS. No per-component renormalization. Thus `g_alpha = alpha*g_U + g_E`, and `alpha=1` is the full PE NLL gradient. Store complete float32 per-example `g_U, g_E` and source IDs; all population analysis accumulates in float64. Check analytical gradients against autograd with respect to this bias on the first example; check gradient sums and EOS/mask accounting.

## Predeclared selection mechanisms and diagnostics

For each of the two 256-example populations separately, P is uniform. Define `e_i` as the fraction of edited PE subword tokens excluding EOS and `l_i=min(source_length/64,1)`:

- `edit`: `pi_i=0.10+0.80*e_i`.
- `length`: `pi_i=0.10+0.80*l_i`.
- `edit_length`: `pi_i=0.10+0.80*(e_i+l_i)/2`.

No fitting of these propensities: they are intentionally known synthetic observation probabilities. `Q_i=pi_i/sum(pi)`. Report all mechanisms, including reversals. For `alpha=0,0.05,...,1`, compute exact finite-population means under P/Q, absolute bias, relative bias `rho=||E_Q g_alpha−E_P g_alpha||/||E_P g_alpha||`, and oracle normalized-ratio IPW expectation `E_Q[(mean(pi)/pi)*g_alpha]`. The target is the matching localized population gradient, not a fixed alpha=1 target. Report both endpoints, `b_U`, `b_E`, all six coefficients of the numerator/denominator quadratics, their inner products, derivative signs, and decomposition of absolute-bias change. IPW identity is an algebraic check, not discovery of real complaint propensities.

For fixed target `mu_1`, report exact finite-sample bias, trace variance, and MSE of the unnormalized Hansen–Hurwitz mean of **64 iid Q draws** for unweighted and oracle ratio-IPW estimators at every alpha. Enumerated expectations are exact for this finite model; additionally run 500 seeded draws using sample-count covariance / Gram matrices, avoiding expensive dense repeated gradients. Monte Carlo seed 29117. The exact MSE is `||E estimate−mu_1||²+trace(Cov(single draw))/64`. Save replication-wise errors. No estimator/alpha is selected after viewing reporting results.

## Actual output-bias adaptation and held-out NLL

On the diagnostic population only, create one iid synthetic sample of 64 Q draws for each mechanism using fixed seeds 8101, 8102, 8103. For `alpha in {0,0.25,0.5,0.75,1}`, compute population-P, sampled-Q, and oracle ratio-IPW gradients. Take **one predeclared gradient-descent step** `b=-eta*g` for `eta in {1,10}`; all base weights remain frozen. Evaluate every adapter on the disjoint reporting population's full PE NLL. The unadapted NLL and every outcome, including degradations, are retained. This is genuine restricted-parameter optimization, but is not a claim about decoded BLEU/COMET, production utility, repeated optimization, or full fine-tuning. Use the identity `NLL(b)-NLL(0)=log(sum_v p_v exp(b_v))−b_y` at each teacher-forced position, which permits batched evaluation without re-running the transformer per adapter. Keep sample IDs and complete bias vectors.

## Reproducibility and output

Run `python research_release/experiments/public_postedit.py` from the project root with the local `.venv` activated. The script downloads only the pinned model assets and 1.1 MB data archive, caches them outside the release, writes all results under `papers/edit_localization/results/public_*`, figures under `figures/public_*`, and a machine-readable manifest including this protocol's SHA-256. No data/model upload or online submission occurs. Full raw text and pretrained weights are not required in the release; source URLs, revisions, raw hashes, original line numbers, and derived arrays suffice to recreate it.

## Definition correction recorded before the first model forward pass

2026-09-11: During independent manuscript integration review, the root reviewer noted that the manuscript's relative-bias definition divides by the **selected** mean norm, whereas the original protocol above wrote the **population** mean norm. To align definitions without suppressing the sensitivity analysis, compute both: primary `rho_Q=||E_Q g_alpha−E_P g_alpha||/||E_Q g_alpha||` and secondary `rho_P=||E_Q g_alpha−E_P g_alpha||/||E_P g_alpha||`. Store numerator and both denominator quadratics, derivatives, and both endpoint ratios. This is a pre-computation definition correction, not an outcome-dependent change. The total-length normalization in this experiment defines a sentence-uniform, within-sentence token-mean objective, distinct from unnormalized token-sum simulations.

Numerical implementation correction: the first-example gradient check stopped the initial run before any population analysis because mixed MPS-softmax / CPU-autograd computations differed by `1.24e-6`. All analytic output-bias softmax, NLL and autograd checks now use CPU float64 on fixed model logits; the transformer forward remains float32 MPS. Gradients are stored float32 and aggregate arithmetic float64. No outcomes were inspected before this numerical correction.
