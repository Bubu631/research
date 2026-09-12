#!/usr/bin/env python3
"""Verify recorded hashes; compact bundles can omit regenerable large arrays."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-large", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checks, missing = [], []
    def check(path, expected):
        if not path.exists():
            if not args.require_large and path.name.startswith("public_gradients_"):
                missing.append(str(path.relative_to(ROOT)))
                return
            raise FileNotFoundError(path)
        actual = sha(path)
        if actual != expected:
            raise AssertionError(f"Hash mismatch: {path}")
        checks.append(str(path.relative_to(ROOT)))
    a = ROOT/"papers/edit_localization/results"
    b = ROOT/"papers/base_upgrade/results"
    summary = json.loads((a/"summary.json").read_text())
    check(ROOT/"experiments/edit_localization.py", summary["experiment_sha256"])
    base = json.loads((b/"manifest.json").read_text())
    check(ROOT/"experiments/base_upgrade.py", base["script_sha256"])
    for name, expected in base["outputs"].items():
        check(b/name, expected)
    balanced = b/"digits_balanced"
    balanced_manifest = json.loads((balanced/"digits_manifest.json").read_text())
    if not balanced_manifest["status"].startswith("completed_"):
        raise AssertionError("Incomplete balanced digits path")
    for name, expected in balanced_manifest["output_sha256"].items():
        check(balanced/name, expected)
    for directory, pair in [(a,"en_de"), (a/"public_en_zh","en_zh")]:
        manifest = json.loads((directory/"public_manifest.json").read_text())
        if manifest.get("completed") is not True:
            raise AssertionError(f"Incomplete public study: {pair}")
        check(directory/f"public_executed_script_{pair}.py",manifest["script_sha256"])
        check(directory/"public_protocol_snapshot.md",manifest["protocol_sha256"])
        for name, expected in manifest["output_sha256"].items():
            check(directory/name, expected)
        first = directory/"public_first_run_provenance"
        original = json.loads((first/"public_manifest.json").read_text())
        check(first/f"public_executed_script_{pair}.py", original["script_sha256"])
        check(first/"public_protocol_snapshot.md", original["protocol_sha256"])
    native = a/"full_parameter"
    manifest = json.loads((native/"manifest.json").read_text())
    if manifest.get("completed") is not True:
        raise AssertionError("Incomplete native-parameter study")
    check(native/"executed_script.py", manifest["script_sha256"])
    check(native/"executed_helper_script.py", manifest["helper_script_sha256"])
    check(native/"protocol_snapshot.md", manifest["protocol_sha256"])
    for name, expected in manifest["outputs"].items():
        check(native/name, expected)
    result = dict(status="passed", hash_checks=len(checks), verified=checks,
                  intentionally_absent_large_arrays=missing,
                  scope="Integrity of recorded files; this does not itself prove scientific claims or rerun training.")
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
