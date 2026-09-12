#!/usr/bin/env python3
"""Verify saved public experiment provenance and the recorded deterministic replay.

No downloads or pretrained-model dependencies. A different platform can produce
slightly different numerical arrays; byte equality reports the executed replay,
not a hardware-independent numerical guarantee.
"""
import hashlib
import json
from pathlib import Path

RELEASE = Path(__file__).resolve().parents[1]
BASE = RELEASE / "papers/edit_localization/results"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for part in iter(lambda: handle.read(2**20), b""):
            h.update(part)
    return h.hexdigest()


def main():
    report = {"scope": "Recorded same-device deterministic replay; all original numerical configurations retained",
              "runs": {}}
    for pair, directory in [("en-de", BASE), ("en-zh", BASE/"public_en_zh")]:
        old_directory = directory/"public_first_run_provenance"
        if not old_directory.exists():
            raise FileNotFoundError(f"Original provenance missing for {pair}: {old_directory}")
        current = json.loads((directory/"public_manifest.json").read_text())
        old = json.loads((old_directory/"public_manifest.json").read_text())
        source = f"public_executed_script_{pair.replace('-','_')}.py"
        for manifest, folder in [(current,directory),(old,old_directory)]:
            assert manifest["completed"]
            assert digest(folder/source) == manifest["script_sha256"]
            assert digest(folder/"public_protocol_snapshot.md") == manifest["protocol_sha256"]
        comparisons = []
        for name, first_digest in old["output_sha256"].items():
            if Path(name).suffix not in [".csv", ".npz", ".npy"]:
                continue
            actual = digest(directory/name)
            assert actual == current["output_sha256"][name], name
            comparisons.append({"file": name,"first_sha256":first_digest,"replay_sha256":actual,
                                "byte_identical": first_digest == actual})
        report["runs"][pair] = {"first_run_started_utc":old["run_started_utc"],
            "replay_started_utc":current["run_started_utc"],
            "first_seconds":old["total_wall_seconds"],"replay_seconds":current["total_wall_seconds"],
            "first_script_sha256":old["script_sha256"],"replay_script_sha256":current["script_sha256"],
            "first_protocol_sha256":old["protocol_sha256"],"replay_protocol_sha256":current["protocol_sha256"],
            "provenance_snapshots_match_manifests":True,
            "numeric_file_count":len(comparisons),
            "all_numeric_files_byte_identical":all(row["byte_identical"] for row in comparisons),
            "files":comparisons}
    destination=BASE/"public_replay_validation.json"
    destination.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({p:{k:v for k,v in row.items() if k!="files"} for p,row in report["runs"].items()},indent=2))


if __name__ == "__main__":
    main()
