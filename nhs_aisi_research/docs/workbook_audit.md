# Supporting workbook verification

Checked on 11 September 2026. `results/nhs_aisi_results.xlsx` is a transparent supplement to the frozen scientific CSVs. It contains ten worksheets: a comparison summary, eight complete source grids, and a field dictionary. The exploratory budget extension is a separate **Exploratory** sheet; NHS assumptions are separate from the BRFSS replay.

The openpyxl builder retains all supplied result rows, including adverse and null findings. Across 53 settings, 477 linked formulas calculate both policies' regret, paired differences, approximate Monte Carlo intervals, validation cost shares and descriptive relative changes. Intervals use the supplied within-panel difference standard error; independent-policy standard errors are never combined. Relative changes have an explicit zero-baseline guard.

Validation included:

- Checking the SHA-256 of each of eight source CSVs against the build manifest.
- Comparing **186,830 source data cells** against the saved workbook, including numeric values, booleans and identifiers.
- Comparing all **477 saved formulas and cached values** against independently computed expectations after artifact-tool recalculation.
- Temporarily setting one linked baseline to zero to verify the relative-change guard, then restoring it before the final export.
- Scanning the saved workbook for formula-error cells and checking sheet structure, frozen panes and the direction-colour rule.
- Rendering and visually reviewing every worksheet, with a separate view of the comparison formulas and intervals. A widened exploratory-stage column was re-rendered after correction.

The final file passed these checks. Exact workbook and verifier hashes and check time are recorded in `results/workbook_validation.json`; source hashes and expected formulas are in `results/workbook_manifest.json`. The two JSON files are machine-readable evidence, rather than assertions that a native Microsoft Excel application was tested. Native Excel was not used.

The public builder requires openpyxl 3.1.5. `python artifact_tools/verify_results.py --formulas-only` verifies an openpyxl rebuild before formula recalculation; the same command without the flag also verifies cached values after a spreadsheet engine saves the file. The optional artifact-tool release-QA script is `artifact_tools/recalculate_results.mjs`. Scientific experiments and result CSVs were not modified by this workbook workflow.
