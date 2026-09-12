#!/usr/bin/env python3
"""One-time descriptive suffix correction for the preserved initial data run.

Fresh swe_gym_data.py runs already use the corrected separator expression.
No labels, features, probabilities, splits or group membership are modified.
"""
import json
import re
from pathlib import Path
from swe_gym_data import ROOT, OUT, sha_file, write_json, write_jsonl


def main():
    changes = {}
    for name in ["records.jsonl", "unique_records.jsonl", "proxy_predictions.jsonl"]:
        p = OUT / name
        rows = [json.loads(l) for l in p.read_text().splitlines()]
        updated = 0
        for r in rows:
            old = r["behavior_config"]
            new = re.sub(r"[-_]run_?\d+$", "", old)
            if old != new:
                r["behavior_config"] = new
                updated += 1
        if updated:
            before = sha_file(p)
            write_jsonl(p, rows)
            changes[name] = {"updated_descriptive_fields": updated,
                             "sha256_before": before, "sha256_after": sha_file(p)}
    if changes:
        p = OUT / "summary.json"
        summary = json.loads(p.read_text())
        summary["behavior_configs"] = {re.sub(r"[-_]run_?\d+$", "", k): v
                                      for k, v in summary["behavior_configs"].items()}
        summary["metadata_correction"] = {
            "reason": "Actual run IDs use a hyphen before run_1; normalize descriptive configuration suffix.",
            "scientific_values_unchanged": True,
            "initial_executed_script_sha256": summary["script_sha256"],
            "current_reproduction_script_sha256": sha_file(ROOT / "experiments/swe_gym_data.py"),
            "amended_protocol_sha256": sha_file(ROOT / "docs/swe_gym_data_protocol.md"),
            "correction_script_sha256": sha_file(Path(__file__)),
        }
        write_json(p, summary)
        write_json(OUT / "metadata_correction.json", {"changes": changes,
            "numeric_values_changed": False, "script_sha256": sha_file(Path(__file__))})
    print(json.dumps(changes, indent=2))


if __name__ == "__main__":
    main()
