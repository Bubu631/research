> Authorship update (2026-09-12): the edit-localization paper lists Shengwei Zhang, Haoda Dai, Yifei Li and Yuheng Song, all University of Pennsylvania. The base-model upgrade paper now lists Shengwei Zhang (University of Pennsylvania), Tao Wu and Fei Qian (both Alibaba International Digital Commerce). Earlier single-author statements in this dated document describe previous versions; reviewer-eligibility or quota conclusions relying on those assumptions require reassessment. Scientific result records are unchanged.

# Final release audit

Both final research manuscripts contain **21 pages**. Every page was rendered and inspected; the parent additionally checked the final title/abstract and native-gradient figure page.

The complete source dependencies of each paper were copied into separate clean directories and compiled with `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`. Both clean builds passed with **zero LaTeX warnings, overfull boxes, or underfull boxes**. Extracted PDF text matched the reviewed PDFs exactly, and every source/table/figure file in the archive dependency closure matched the corresponding clean-build input byte for byte.

The scientific verification results are in `validation_results.md`; exact final PDF hashes and machine-readable audit fields are in `final_release_audit.json`. The package builder also checks ZIP CRCs and emits `bundle_manifest.json` and `SHA256SUMS.txt` beside the archives.

Private interview materials, original attachments, model/data caches, and the 4.73 GB native gradient bank are excluded from the public-code archives. Large per-record vocabulary gradients have a separate evidence archive; the compact code archive retains manuscript figures, tables, summaries, smaller checkpoints and metadata. Run-start manifests and the failed initial native attempt are deliberately preserved as provenance; completed manifests identify final execution status.

This audit establishes the recorded results and manuscript artifacts, not conference acceptance. Both papers have the confirmed author Shengwei Zhang and affiliation University of Pennsylvania. Scientific author review, publication license, conference formatting, and public submission remain separate outstanding steps.

## Display-date-only revision

The user-requested display dates are **August 13, 2026** for edit localization and **August 28, 2026** for base upgrade. The actual checks and experiment timestamps remain unchanged or record their real execution time; they were not backdated. Author and affiliation are unchanged.

Both rebuilt PDFs remain 21 pages. Full-page raster comparisons identify changes only in each first-page date area; all other 40 pages are pixel-identical to the previously reviewed PDFs. The two revised title pages were visually inspected. The extracted text and LaTeX source are identical except for the requested date substitutions. All 141 scientific/protocol/result files checked before and after this revision have identical hashes, and all 89 existing recorded-file integrity checks pass. No scientific experiment was rerun for this date-only edit. Both source ZIPs were extracted into fresh directories and compiled without LaTeX warnings or box warnings; their extracted PDF text matches the final PDFs. See `display_date_update_audit.json` for current hashes and the actual check timestamp.
