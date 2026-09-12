# Recorded validation results

Checks below were actually executed on 2026-09-11 in the recorded environment. They validate specific implementation and artifact properties; they do not establish conference acceptance or universal empirical performance.

## Mathematics and code

`python -m unittest discover -s tests -v`: **21 tests passed** with the optional model dependencies installed. Checks include exact null probabilities, candidate multiplicity, fixed-sequence stopping, exact incumbent identity, structural score bounds, disjoint splits, neural-network finite differences, the relative-bias derivative, change of measure, exhaustive finite-sample MSE, the retention optimizer, counterexamples, Levenshtein ties, EOS normalization, and Gram calculations checked against direct vector norms.

The public output-bias experiments were replayed in both language directions. All **30 numeric artifacts** matched the respective first execution byte for byte, including gradients, Monte Carlo outputs, adapters, and per-example NLL. This is a same-environment replay result; it is not a guarantee of byte identity across arbitrary hardware. See `papers/edit_localization/results/public_replay_validation.json`.

An independent script reconstructed the six public reporting settings from saved per-record gradients. Maximum discrepancies were **1.23e-15** for relative bias and **1.09e-18** for fixed-target MSE; summaries of saved adapter NLL matched exactly. See `docs/public_postedit_independent_audit.md`.

Both public digits training paths retain all five seeds. `summarize_digits_paths.py` independently recomputed reporting metrics and certification bounds from saved predictions, regenerated tensor predictions from checkpoints, checked exact fallback, and verified balanced-run provenance hashes. Reconstructed incumbents and split IDs matched the original path exactly. The later balanced path is descriptive because it reuses the earlier holdouts.

The native-parameter run completed over 73,886,208 parameters and 256 records in 2,212 seconds. The independent baseline NLL implementation agrees to a maximum absolute difference of **1.73e-6**; edited plus untouched loss reconstruction differs by at most **2.99e-7**. All three derivative polynomials are negative on [0,1] with no interior roots. The mixture identity has a maximum relative norm residual of about **7.1e-5**, which is disclosed as finite-precision behavior; these native gradients are not claimed to satisfy exact machine-zero identities. A second full native-gradient run was not performed.

The separate `verify_native_geometry.py` reconstructed eight Euclidean vectors from the stored Gram matrix and recomputed norms and directional derivatives, with maximum curve discrepancy **7.22e-15**. It also checked record IDs, original source/protocol/output hashes, and baseline losses. These checks verify analysis of the recorded gradients; the mixture residual is not a rigorous numerical-error bound.

## Bibliography and repository

All 31 bibliography entries were checked against primary sources; conflicting author orders were resolved using official paper title pages. See `docs/reference_audit.md`.

The repository audit checked dependency availability, relative links, LaTeX dependency closure, Git ignores for all eight large gradient archives, and exclusion of private interview materials, original attachments, model weights, and local caches from publication archives. See `docs/repository_audit.md`.

The original-file integrity verifier passed **89 hash comparisons**, including the optional large gradient files and executed source/protocol snapshots. Final clean archive builds are recorded in the final release audit. Run `python experiments/verify_artifact_integrity.py --require-large` after restoring the optional gradient evidence archive to check the original recorded file hashes.

## Display-date-only revision

The user-requested display dates are **August 13, 2026** for edit localization and **August 28, 2026** for base upgrade. The actual checks and experiment timestamps remain unchanged or record their real execution time; they were not backdated. Author and affiliation are unchanged.

Both rebuilt PDFs remain 21 pages. Full-page raster comparisons identify changes only in each first-page date area; all other 40 pages are pixel-identical to the previously reviewed PDFs. The two revised title pages were visually inspected. The extracted text and LaTeX source are identical except for the requested date substitutions. All 141 scientific/protocol/result files checked before and after this revision have identical hashes, and all 89 existing recorded-file integrity checks pass. No scientific experiment was rerun for this date-only edit. Both source ZIPs were extracted into fresh directories and compiled without LaTeX warnings or box warnings; their extracted PDF text matches the final PDFs. See `display_date_update_audit.json` for current hashes and the actual check timestamp.
