#!/usr/bin/env python3
"""Construct explicitly heterogeneous historical groups; never on-policy samples."""
from __future__ import annotations
import collections
import json
from pathlib import Path
from swe_gym_data import ROOT, OUT, digest, sha_file, write_json, write_jsonl, now


def main():
    records = [json.loads(l) for l in (OUT / "unique_records.jsonl").read_text().splitlines()]
    predictions = {r["record_id"]: r for r in
                   map(json.loads, (OUT / "proxy_predictions.jsonl").read_text().splitlines())}
    blocks = collections.defaultdict(list)
    for r in records:
        if r["eligible_evaluation"]:
            blocks[(r["instance_id"], r["initial_prompt_sha256"])].append(r)
    stats = {}
    for size in [4, 8]:
        groups = []
        used = set()
        for key, rr in sorted(blocks.items()):
            rr = sorted(rr, key=lambda r: r["content_sha256"])
            for offset in range(0, len(rr) - size + 1, size):
                members = rr[offset:offset+size]
                ids = [r["record_id"] for r in members]
                assert not used.intersection(ids)
                used.update(ids)
                assert len({r["instance_id"] for r in members}) == 1
                assert len({r["split"] for r in members}) == 1
                assert len({r["initial_prompt_sha256"] for r in members}) == 1
                assert all(r["eligible_evaluation"] for r in members)
                groups.append({"group_id": digest(["heterogeneous-historical-v1", size, key, offset])[:24],
                    "population": "heterogeneous_historical_replay_not_on_policy",
                    "group_size": size, "instance_id": key[0], "initial_prompt_sha256": key[1],
                    "split": members[0]["split"], "record_ids": ids,
                    "run_ids": [r["run_id"] for r in members],
                    "behavior_configs": [r["behavior_config"] for r in members],
                    "behavior_models": [r["run_id"].split("_maxiter_")[0] for r in members],
                    "labels": [int(r["resolved"]) for r in members],
                    "proxy_probabilities": [predictions[r["record_id"]]["proxy_probability"] for r in members],
                    "success_count": sum(r["resolved"] for r in members)})
        write_jsonl(OUT / f"heterogeneous_groups_g{size}.jsonl", groups)
        stats[size] = {"groups": len(groups), "records": len(used),
                      "mixed_groups": sum(0 < r["success_count"] < size for r in groups),
                      "groups_with_multiple_behavior_models": sum(len(set(r["behavior_models"])) > 1 for r in groups),
                      "groups_with_multiple_behavior_configs": sum(len(set(r["behavior_configs"])) > 1 for r in groups),
                      "incomplete_records": sum(len(rr) % size for rr in blocks.values()),
                      "by_split": {s: {"groups": sum(r["split"] == s for r in groups),
                           "mixed_groups": sum(r["split"] == s and 0 < r["success_count"] < size for r in groups),
                           "tasks": len({r["instance_id"] for r in groups if r["split"] == s})}
                           for s in ["train", "calibration", "heldout"]}}
    result = {"protocol_amendment": "availability-driven after strict G4/G8 groups were found empty",
              "interpretation": "fixed empirical group target; heterogeneous historical logging; no on-policy claim",
              "groups": stats, "source_sha256": {p.name: sha_file(p) for p in [
                  OUT / "unique_records.jsonl", OUT / "proxy_predictions.jsonl", ROOT / "docs/swe_gym_data_protocol.md"]},
              "script_sha256": sha_file(Path(__file__)), "created_at_utc": now()}
    write_json(OUT / "heterogeneous_group_summary.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
