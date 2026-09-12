# Repository portability and packaging audit

Checked on 2026-09-11. This is a static review plus temporary archive, dependency and path checks. It did not rerun model inference, alter frozen experiments, or claim that the still-running native-gradient extension had finished. Final publication archives must be rebuilt after the native extension and balanced digits manuscript integration are complete.

## Findings and corrections

1. **Nested gradient archives were not ignored by Git.** The original ignore rule matched the four English–German arrays but missed the four arrays under `results/public_en_zh/`. The rule was corrected to `papers/**/public_gradients_*.npz`. An isolated temporary Git repository verified that all eight current gradient archives are now ignored. The packaging script already separated all eight correctly by filename.
2. **CPU command wording was too broad.** `public_postedit.py` automatically selects MPS or CPU but does not accept `--device`. `full_parameter_postedit.py` accepts `--device cpu`. The README was corrected to identify the native extension specifically.
3. **The new balanced-study protocol used a workspace-specific command.** `../.venv/bin/python experiments/digits_balanced.py` assumes a virtual environment outside the repository. The paper's owner corrected the current instructions to use `python experiments/digits_balanced.py` after activating the README environment and added the comparison-generator command. A documentation-only correction note records this change; the executed protocol snapshot and its hash remain unchanged. The balanced study is a later descriptive continuation with reused holdouts.
4. **Output-manifest scope was too broad.** Initially, `package_release.py` selected every ZIP or PDF already in the output directory for `bundle_manifest.json` and `SHA256SUMS.txt`, which could include an unrelated older file. The corrected script enumerates only the six exact files it generates, preserving unrelated files. This correction was rechecked in the source.

## Checks completed

| Area | Check and result |
|---|---|
| Entry points | Current experiment scripts derive repository locations from their own source paths. The public model cache uses `PUBLIC_POSTEDIT_CACHE` or the repository's ignored `.cache/public_postedit` directory. No current entry point requires the private workspace name. |
| Commands | `make -n test reproduce-core reproduce-public reproduce-full papers` resolves to existing scripts and paper directories. The final Makefile also includes the balanced continuation and its comparison generator in `reproduce-core`, plus a separate `digits-balanced` target. The native run is followed by its report generator. The amended targets were checked again with `make -n`. |
| Python dependencies | Every directly imported external package is represented by `requirements-core.txt` or `requirements-models.txt`; model requirements include the core requirements. The recorded Python 3.13 environment reports `No broken requirements found` from `pip check`. A completely fresh environment installation was not performed in this audit. |
| Native prerequisites | The README explicitly requires `latexmk`, `pdflatex`, and BibTeX. These are separate from Python requirements. Earlier paper agents compiled and visually reviewed the manuscripts; the final archive build remains a separate check. |
| Relative links | All 12 relative Markdown links present at inspection resolved. External literature and venue links were checked separately in the reference audit and submission plan. |
| LaTeX source closure | All required local `input`, bibliography and figure references were included by the source-archive selection rule: 17 current source members for the edit paper and 14 for the upgrade paper. The explicitly optional, not-yet-generated native section was excluded from this interim count. |
| Private material | Filename and text scans, including JSON and CSV, found no private workspace absolute paths, WeChat identifiers, original attachments, interview skill material, or private-source references in the release tree. No symlinks were present. |
| Downloaded assets | Archive selection excludes `.cache`, `.venv`, Git internals and Python caches. No pretrained model weights, raw downloaded corpora, or native gradient bank were selected. The small digits checkpoint arrays are intentional experiment evidence. The six public text examples are intentional, attributed alignment illustrations. |
| Build noise and provenance | LaTeX auxiliary logs are excluded; `.bbl` files are retained intentionally for source-based submission. Run-start manifests are retained because completed manifests can hash them as part of provenance. They record a historical start state and do not override the final completed manifest or the packaging completion gate. |
| Large evidence | The code archive omits all eight per-record vocabulary-gradient NPZ files. The evidence archive restores them at matching repository-relative paths. At inspection the eight files totaled 390,920,894 bytes; the largest individual selected file was 58,590,154 bytes. |
| Archive integrity | A temporary code archive made using the actual selection and compression functions contained 187 files and was 90,435,292 bytes; CRC validation passed. Its uncompressed contents totaled 109,639,023 bytes. This is an interim measurement, not the final release checksum. |
| Destination containment | The package command rejects an output directory equal to or inside the source repository, preventing its generated ZIP files from recursively entering the bundle. It refuses packaging when the native experiment's final manifest is missing or incomplete. |

The retained first-run scripts and protocol snapshots contain their historical command conventions. They are provenance records, not the current reproduction entry points. The public protocol transparently records the later path correction and the final replay. Both current public experiment source snapshots and all previously executed numeric outputs were preserved during this audit.

## Final handoff checks

The repository owner should finish the pending native and balanced-study integration, update headline counts and status, then generate the final archives and checksums. Inspect the actual final archive size instead of extrapolating the temporary measurement. An extracted source archive should compile independently; the combined code and gradient-evidence archives should support the saved-array verification commands. The current packaging gate correctly prevents treating unfinished native results as a completed release.

Authorship, author review, public repository creation, release terms and venue-specific formatting are intentionally separate from this portability audit. No upload or publication occurred.
