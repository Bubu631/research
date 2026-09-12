#!/usr/bin/env python3
"""Independent saved-data integrity checks; uses only Python's standard library."""
from __future__ import annotations
import collections
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/swe_gym"
OUT = DATA / "processed"


def read_jsonl(p):
    return [json.loads(l) for l in p.read_text().splitlines()]


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda: f.read(1 << 20), b""):
            h.update(x)
    return h.hexdigest()


def main():
    source = json.loads((DATA / "source_manifest.json").read_text())
    for item in source["files"]:
        p = ROOT / item["path"]
        assert p.stat().st_size == item["bytes"]
        assert sha(p) == item["sha256"] == item["expected_lfs_sha256"]
    original = DATA / "provenance/initial_strict_run"
    original_summary = json.loads((original / "summary.json").read_text())
    assert sha(original / "swe_gym_data.py") == original_summary["script_sha256"]
    assert sha(original / "swe_gym_data_protocol.md") == original_summary["protocol_sha256"]
    current_summary = json.loads((OUT / "summary.json").read_text())
    correction = current_summary.get("metadata_correction")
    if correction:
        assert sha(ROOT / "experiments/swe_gym_data.py") == correction["current_reproduction_script_sha256"]
        assert sha(ROOT / "docs/swe_gym_data_protocol.md") == correction["amended_protocol_sha256"]
    records = read_jsonl(OUT / "unique_records.jsonl")
    by_id = {r["record_id"]: r for r in records}
    assert len(records) == len(by_id) == 6055
    assert len({r["content_sha256"] for r in records}) == len(records)
    task_splits = collections.defaultdict(set)
    strict_blocks = collections.Counter()
    for r in records:
        task_splits[r["instance_id"]].add(r["split"])
        b = int(hashlib.sha256(("swe-gym-audit-v1|" + r["instance_id"]).encode()).hexdigest()[:8], 16) % 100
        expected = "train" if b < 60 else "calibration" if b < 80 else "heldout"
        assert r["split"] == expected
        if r["eligible_evaluation"]:
            strict_blocks[(r["instance_id"], re.sub(r"[-_]run_?\d+$", "", r["run_id"]), r["initial_prompt_sha256"])] += 1
    assert all(len(v) == 1 for v in task_splits.values())
    assert max(strict_blocks.values()) == 2
    proxy = {r["record_id"]: r for r in read_jsonl(OUT / "proxy_predictions.jsonl")}
    model = json.loads((OUT / "proxy_model.json").read_text())
    max_proxy_error = 0.
    for rid, row in proxy.items():
        r = by_id[rid]
        z = model["intercept"] + sum(c * (r["features"][k] - m) / s
            for k, m, s, c in zip(model["feature_names"], model["scaler_mean"], model["scaler_scale"], model["coef"]))
        prediction = 1 / (1 + math.exp(-z))
        max_proxy_error = max(max_proxy_error, abs(prediction - row["proxy_probability"]))
        assert row["resolved"] == int(r["resolved"])
    assert max_proxy_error < 1e-12
    group_stats = {}
    for g in [4, 8]:
        assert (OUT / f"groups_g{g}.jsonl").read_text() == ""
        groups = read_jsonl(OUT / f"heterogeneous_groups_g{g}.jsonl")
        used = set()
        for group in groups:
            rr = [by_id[rid] for rid in group["record_ids"]]
            assert len(rr) == len(set(group["record_ids"])) == g
            assert not used.intersection(group["record_ids"])
            used.update(group["record_ids"])
            assert len({r["instance_id"] for r in rr}) == 1
            assert len({r["initial_prompt_sha256"] for r in rr}) == 1
            assert len({r["split"] for r in rr}) == 1
            assert [r["content_sha256"] for r in rr] == sorted(r["content_sha256"] for r in rr)
            assert group["labels"] == [int(r["resolved"]) for r in rr]
            assert group["run_ids"] == [r["run_id"] for r in rr]
            assert group["success_count"] == sum(group["labels"])
            assert group["proxy_probabilities"] == [proxy[r["record_id"]]["proxy_probability"] for r in rr]
            assert all(r["eligible_evaluation"] for r in rr)
        group_stats[g] = {"groups": len(groups), "members": len(used)}
    historical_summary = json.loads((OUT / "heterogeneous_group_summary.json").read_text())
    for name, expected in historical_summary["source_sha256"].items():
        p = ROOT / "docs" / name if name.endswith(".md") else OUT / name
        assert sha(p) == expected
    result = {"checks_passed": True, "files_sha_verified": len(source["files"]),
              "records": len(records), "tasks": len(task_splits),
              "strict_block_max_size": max(strict_blocks.values()),
              "proxy_max_absolute_reconstruction_error": max_proxy_error,
              "historical_groups": group_stats, "checker_sha256": sha(Path(__file__))}
    (OUT / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
