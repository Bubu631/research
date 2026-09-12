> Authorship update (2026-09-12): the edit-localization paper lists Shengwei Zhang, Haoda Dai, Yifei Li and Yuheng Song, all University of Pennsylvania. The base-model upgrade paper now lists Shengwei Zhang (University of Pennsylvania), Tao Wu and Fei Qian (both Alibaba International Digital Commerce). Earlier single-author statements in this dated document describe previous versions; reviewer-eligibility or quota conclusions relying on those assumptions require reassessment. Scientific result records are unchanged.

# Edit localization research QA

Checks completed on 2026-09-11 for the corrected 21-page English manuscript, synthetic experiment, public output-bias study, and completed native-parameter extension.

## Scientific corrections

- Relative selection bias is analyzed with a general ratio-of-quadratics derivative; amplification is conditional.
- Localization-specific means are distinguished from one common full-gradient target.
- The MSE formula includes localization mismatch and integrand-dependent variance.
- Oracle IPW, unnormalized weights, population-normalized clipping, and finite-sample self-normalization are distinguished.
- The invalid universal weight-only variance floor and incompatible weight-independence assumption were removed.
- Randomized-audit identification explicitly requires its sampling independence and conditional outcome/gradient assumptions.
- No simulated production feedback or synthetic gradient is presented as an observed production measurement.

## Executed synthetic verification

The default experiment completed with 10,000 independent repeated datasets at each of five sample sizes. Four estimators and five retention coefficients reuse each dataset. Therefore one million output rows correspond to 50,000 independent datasets, not one million independent runs.

Seven independent unit tests passed, covering general derivatives via finite differences, exact change of measure, exhaustive sample enumeration for the MSE formula, dense-grid comparison of the analytic optimizer under arbitrary weights, uniform-selection controls, a zero-variance counterexample, and single-sample self-normalization.

Across 75 fixed-weight Monte Carlo comparisons, the maximum discrepancy from an exact MSE is 2.3305 Monte Carlo standard errors. This is a descriptive comparison, not a simultaneous coverage claim. Exact covariance traces independently checked for the aligned case are A = 35/6, B = 1/2, and C = 145/72.

## Public post-edit integration

The public experiment agent supplied completed English–German and English–Chinese studies and pinned provenance. All six reporting cases use the selected Q-mean denominator matching the primary theorem. The manuscript reports the English–German interior maximum and nonzero untouched-gradient biases, as well as all 180 restricted one-step adapters without claiming uniform superiority of weighting.

The underlying text and pretrained models are real. Selection mechanisms are declared synthetic functions. The restricted experiment introduces an output-logit bias; it does not train the base transformer. Any extension to native differentiable parameters must retain this parameterization distinction.

An independent implementation recomputed all six reporting curves and exact fixed-target MSE values directly from the released per-record gradient matrices. Maximum discrepancies were 1.23e-15 for relative bias and 1.09e-18 for MSE. Per-example adapter NLL summaries matched exactly, as did executed source and protocol hashes; the two record splits were disjoint. The checker is `experiments/verify_public_geometry.py`, with details in `docs/public_postedit_independent_audit.md`. A separate complete same-device replay reproduced all 30 numerical files byte for byte.

## Document verification

The final title is **When Edit Localization Amplifies Relative Selection Bias: Gradient Geometry, Target Mismatch, and Importance Weighting**. The abstract, introduction, native results, and scope statements explicitly distinguish higher relative bias from lower absolute bias under hard localization compared with full retention. No monotonic absolute-bias claim is made: the native absolute curves have shallow interior minima.

The complete 21-page manuscript was compiled and every page was rendered and visually inspected, including all equations, tables, figure labels, references, and appendix proofs. No text/figure clipping or overlap was observed. The final LaTeX log has no warnings, undefined references, or overfull/underfull boxes. Bibliography alignment avoids stretched word spacing around checkpoint hashes, and the AI-assistance statement remains together. Figure typography was enlarged for print readability, with the same numerical synthetic experiment rerun and its updated source hash saved. The bibliography has also undergone the separate primary-source audit in `docs/reference_audit.md`.

The confirmed author is Shengwei Zhang, University of Pennsylvania. The AI-use statement does not assert that completed human scientific review has occurred. Final human author review remains necessary before submission.

## Completed native extension

The 73,886,208-parameter English–German extension is integrated with a numerical table and vector figure. All three selected-mean relative curves decrease with increasing retention, while absolute bias is lower at hard localization than full retention. Both simple-corollary assumptions fail in these measured native gradients. The mixture dependence, finite-precision residuals, reused reporting population, and absence of native fine-tuning are explicit.

The independent Euclidean-Gram verifier was executed and passed, including every original artifact/source/protocol hash and exact reporting IDs. Maximum curve discrepancy is 7.22e-15; loss reconstruction and cross-implementation baseline discrepancies are 2.98e-7 and 1.73e-6. Details are in `docs/native_gradient_independent_audit.md` and `papers/edit_localization/results/full_parameter/independent_validation.json`. This checks calculations from the completed native run; it is not a second full-model execution or a rigorous bound on numerical gradient error.
