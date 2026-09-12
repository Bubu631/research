# Third-paper release package checks

This file specifies the release procedure. It is not evidence that a package has already passed. The executed outcome is recorded separately in `output/release/nhs_wellbeing_package_validation.json` when the manuscript owner declares the PDF final and the builder runs successfully.

## Execution guard

The release builder must not be run while the PDF, tables, figures, data or final result files are still changing. After explicit PDF finalisation and after the final independent empirical audit is current, run from this repository:

Packaging additionally needs Poppler (`pdftoppm`), a TeX installation and the Python packages pypdf and Pillow. The executed packaging environment used pypdf 6.18.1 and Pillow 12.3.0; these are separate from the scientific computation dependencies and optional documentation-extraction environment.

```bash
python artifact_tools/build_release.py --finalized
```

The default invocation refuses to create an archive. Packaging does not rerun scientific experiments, submit to a venue, upload to arXiv, or create a remote repository. The PDF-authoring skill marker and final visual inspection belong to the surrounding artifact workflow and are performed before this compile/release operation.

When the PDF is frozen before the repository documentation, `--finalized --source-only` builds and validates just the standalone source package. The later complete build reuses that validation only if both source-ZIP bytes and canonical PDF bytes are identical; otherwise it performs a new clean compile.

## Artifacts

The builder writes only third-paper files under the parent workspace's `output/release/` directory:

- `nhs_wellbeing_source.zip`: a flat, independently compilable TeX source tree containing `main.tex`, `main.bbl`, `references.bib`, PDF figures and generated TeX tables.
- `nhs_wellbeing_research.zip`: a single `nhs_wellbeing_research/` directory with public code, documentation, required source manifests, processed CSVs, final results, final referenced provenance snapshots, manuscript source and PDF. The verified static workbook, when present, is included under `artifacts/nhs_wellbeing_results.xlsx`.
- `nhs_wellbeing_paper.pdf`: an exact copy of the final canonical `paper/main.pdf`.
- `nhs_wellbeing_manifest.json`: per-artifact and per-member sizes/hashes, exclusion inventory, builder hash and actual packaging timestamp.
- `nhs_wellbeing_package_validation.json`: the executed compile, syntax, hash, content and path checks.
- `nhs_wellbeing_source_validation.json`: the standalone source compile check when performed before complete code packaging; its checksum is included in the final checksum list.
- `nhs_wellbeing_SHA256SUMS.txt`: independent checksums for this paper's release files.

The first two papers' packages and their existing shared manifests/checksum file are never changed. Deterministic ZIP header dates are an archive reproducibility convention; original analysis and data-acquisition timestamps remain in their provenance records.

## Mandatory acceptance checks

1. The latest empirical independent audit has status `passed`, its verifier hash matches the current script, and every protected input/result hash matches the current repository.
2. Every source hash and protocol hash recorded in the final simulation, empirical and reporting manifests agrees with the retained referenced source snapshot. Reporting-manifest input and generated-figure/table hashes also match the current files. Distinct executed scientific and final reporting snapshots are both retained when appropriate.
3. The source archive is freshly extracted into an empty temporary directory and compiled with `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`. No existing compiled PDF is carried in that archive. The final build has no TeX errors, undefined citations/references or overfull/underfull warnings.
4. The rebuilt PDF has the same page count and identical normalised text on every page as the canonical final PDF. Every page is also rendered at 72 dpi; canonical and rebuilt images must be pixel-identical. This verifies packaging fidelity and supplements, rather than substitutes for, the final editorial visual review.
5. Every included Python file parses successfully. The code archive must contain all required scripts, manifests, processed inputs, result tables and declared Makefile script targets. Local Markdown links are classified as included or generated/downloaded/external for explicit review.
6. ZIP members are byte-checked against their inventory and pass ZIP CRC validation. Absolute or parent-traversal member paths are disallowed. No symlink is followed or shipped.
7. A public-component allowlist and targeted credential/private-transfer scan exclude unrelated workspace contents, the private source outline and known sensitive markers. This scan is a bounded check, not a claim to detect every conceivable private phrase.
8. If the static workbook is included, its saved validation and workbook hashes must agree and all scientific-source hashes must still match. Its generated values are not recalculated by the packager.
9. All included repository inputs and unrelated existing release artifacts are hashed before/after assembly to detect concurrent edits. Artifacts are copied into final names only after the complete acceptance sequence passes.

## Deliberate exclusions and restoration

The public code archive excludes `data/raw`, third-party full-text extraction, raw archived vintage XLSX/ZIP/PDF/HTML/GZIP payloads, previews, dependency directories, symbolic links, cache/TeX auxiliary files, and `results/initial_runs`. Earlier provenance snapshots unreferenced by any final executed-result manifest are also excluded. Those local historical copies include superseded intermediate representations and are not the final public evidence package.

Official source download scripts, historical benchmark recovery scripts, manifests, technical source links and all necessary derived CSVs are retained. Read the repository README and Makefile for the ordered restoration workflow. Downloaded originals are deliberately not needed to read the paper, inspect the final saved results or rerun the empirical analysis from included processed CSVs. Cell-level source validation and full re-parsing require restoration of the official raw assets first. The workbook renderer additionally uses the documented optional JavaScript artifact-tool dependency; the scientific Python calculations do not depend on that renderer.
