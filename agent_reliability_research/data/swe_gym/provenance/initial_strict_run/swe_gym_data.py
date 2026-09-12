#!/usr/bin/env python3
"""Fetch and audit public SWE-Gym trajectories without executing their code.

Run from any directory: python /path/to/experiments/swe_gym_data.py [--fetch] [--parse]
Raw Parquet files are a local cache, not a redistributable release artifact.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "swe_gym"
RAW = DATA / "raw"
OUT = DATA / "processed"
DATASET = "SWE-Gym/OpenHands-Sampled-Trajectories"
REVISION = "baf3a4e4bff514d48ddc08a93a2ade5c126212c7"
FILES = [f"data/train.raw-{i:05d}-of-00003.parquet" for i in range(3)]
MAX_BYTES = 360_000_000


def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(p, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        for row in rows:
            f.write(canonical(row) + "\n")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def fetch():
    import requests

    RAW.mkdir(parents=True, exist_ok=True)
    api_url = f"https://huggingface.co/api/datasets/{DATASET}?blobs=true"
    response = requests.get(api_url, timeout=60)
    response.raise_for_status()
    info = response.json()
    # The immutable requested revision must be the revision whose file list was checked.
    if info["sha"] != REVISION:
        raise RuntimeError("Upstream main changed. Inspect the pinned revision before fetching.")
    sources = {x["rfilename"]: x for x in info["siblings"]}
    assert all(name in sources for name in FILES)
    write_json(RAW / "huggingface_metadata.json", info)
    card_url = f"https://huggingface.co/datasets/{DATASET}/raw/{REVISION}/README.md"
    card = requests.get(card_url, timeout=60)
    card.raise_for_status()
    (RAW / "dataset_card.md").write_bytes(card.content)
    files = []
    total = 0
    for name in FILES:
        target = RAW / Path(name).name
        url = f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/{name}"
        expected = sources[name].get("lfs", {}).get("sha256")
        cached = target.exists() and (expected is None or sha_file(target) == expected)
        if not cached:
            part = target.with_suffix(".part")
            with requests.get(url, timeout=(30, 120), stream=True) as r:
                r.raise_for_status()
                size = 0
                with part.open("wb") as f:
                    for chunk in r.iter_content(2**20):
                        size += len(chunk)
                        if size + total > MAX_BYTES:
                            raise RuntimeError("Download exceeded bounded data allowance")
                        f.write(chunk)
            part.replace(target)
        actual = sha_file(target)
        if expected and actual != expected:
            raise RuntimeError(f"SHA mismatch for {target.name}")
        total += target.stat().st_size
        files.append({"path": str(target.relative_to(ROOT)), "url": url,
                      "sha256": actual, "expected_lfs_sha256": expected,
                      "bytes": target.stat().st_size, "accessed_at_utc": now(),
                      "reused_local_cache": cached})
        print(f"Verified {target.name}: {target.stat().st_size:,} bytes", flush=True)
    write_json(DATA / "source_manifest.json", {
        "dataset": DATASET, "revision": REVISION, "metadata_url": api_url,
        "dataset_card_url": card_url, "dataset_card_sha256": sha_file(RAW / "dataset_card.md"),
        "licence": info.get("cardData", {}).get("license"),
        "licence_note": "No explicit dataset licence in official card/API when accessed; code licences do not automatically cover the dataset.",
        "download_bytes": total, "files": files,
    })


def task_split(instance):
    b = int(hashlib.sha256(("swe-gym-audit-v1|" + instance).encode()).hexdigest()[:8], 16) % 100
    return "train" if b < 60 else "calibration" if b < 80 else "heldout"


def features(messages):
    roles = collections.Counter(m.get("role", "unknown") for m in messages)
    roletext = collections.defaultdict(list)
    tool_calls = 0
    for m in messages:
        text = m.get("content") or ""
        # Tool-call arguments are model actions and must not disappear from length/features.
        calls = m.get("tool_calls") or []
        if calls:
            text += "\n" + canonical(calls)
        tool_calls += len(calls)
        roletext[m.get("role", "unknown")].append(text)
    text = {k: "\n".join(v) for k, v in roletext.items()}
    tooltext = text.get("tool", "")
    assistant = text.get("assistant", "")
    counts = {"message_count": len(messages), "assistant_turns": roles["assistant"],
              "tool_messages": roles["tool"], "tool_calls": tool_calls,
              "assistant_chars": len(assistant), "tool_chars": len(tooltext),
              "all_chars": sum(len(t) for t in text.values()),
              "all_utf8_bytes": sum(len(t.encode()) for t in text.values()),
              "test_command_mentions": len(re.findall(r"\b(?:pytest|unittest|tox|nosetests)\b", assistant, re.I)),
              "visible_pass_mentions": len(re.findall(r"\b(?:passed|passes|passing)\b", tooltext, re.I)),
              "visible_fail_mentions": len(re.findall(r"\b(?:failed|failures|failing)\b", tooltext, re.I)),
              "visible_error_mentions": len(re.findall(r"\b(?:error|exception|traceback)\b", tooltext, re.I))}
    return counts, {"log1p_" + k: math.log1p(v) for k, v in counts.items()}


def percentile_summary(xs):
    import numpy as np
    return {str(q): float(np.percentile(xs, q)) for q in [0, 25, 50, 75, 90, 95, 99, 100]} if xs else {}


def parse():
    import pyarrow.parquet as pq

    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    reports = collections.Counter()
    test_output_keys = collections.Counter()
    for name in FILES:
        p = RAW / Path(name).name
        if not p.exists():
            raise FileNotFoundError(f"Run --fetch first: {p}")
        shard_row = 0
        for batch in pq.ParquetFile(p).iter_batches(batch_size=8):
            for z in batch.to_pylist():
                messages = z["messages"]
                test = z.get("test_result") or {}
                report = test.get("report") or {}
                test_output_keys.update(test.keys())
                for k, v in report.items():
                    if v:
                        reports[k] += 1
                counts, x = features(messages)
                initial = []
                for m in messages:
                    if m.get("role") == "assistant":
                        break
                    initial.append(m)
                identity = digest({"messages": messages, "git_patch": test.get("git_patch")})
                timings = [float(v) for v in re.findall(r"\bin\s+([\d]+(?:\.[\d]+)?)s\b", test.get("test_output") or "")]
                row = {"record_id": f"{Path(name).stem}:{shard_row}",
                       "source_file": str(p.relative_to(ROOT)), "source_row": shard_row,
                       "instance_id": z["instance_id"], "run_id": z["run_id"],
                       "behavior_config": re.sub(r"_run_?\d+$", "", z["run_id"]),
                       "initial_prompt_sha256": digest(initial), "content_sha256": identity,
                       "resolved": bool(z["resolved"]), "split": task_split(z["instance_id"]),
                       "report": report, "counts": counts, "features": x,
                       "runner_reported_seconds": timings,
                       "eligible_evaluation": not any(report.get(k, False) for k in ["error_eval", "failed_apply_patch", "test_timeout"])}
                rows.append(row)
                shard_row += 1
        print(f"Parsed {p.name}: {shard_row:,} rows", flush=True)
    by_hash = collections.defaultdict(list)
    for r in rows:
        by_hash[r["content_sha256"]].append(r)
    duplicate_map = []
    unique = []
    conflicts = []
    for h, rr in by_hash.items():
        labels = {r["resolved"] for r in rr}
        if len(labels) > 1:
            conflicts.append({"content_sha256": h, "records": [r["record_id"] for r in rr]})
            for r in rr:
                r["label_conflict"] = True
                r["eligible_evaluation"] = False
        else:
            rr[0]["label_conflict"] = False
        unique.append(rr[0])
        for r in rr[1:]:
            duplicate_map.append({"removed": r["record_id"], "retained": rr[0]["record_id"], "sha256": h})
    write_jsonl(OUT / "records.jsonl", rows)
    write_jsonl(OUT / "unique_records.jsonl", unique)
    write_jsonl(OUT / "duplicates.jsonl", duplicate_map)
    write_json(OUT / "label_conflicts.json", conflicts)
    taskrows = collections.defaultdict(list)
    configrows = collections.defaultdict(list)
    for r in unique:
        taskrows[r["instance_id"]].append(r)
        configrows[r["behavior_config"]].append(r)
    write_jsonl(OUT / "task_splits.jsonl", [{"instance_id": k, "split": task_split(k),
                   "unique_records": len(v)} for k, v in sorted(taskrows.items())])
    blocks = collections.defaultdict(list)
    for r in unique:
        if r["eligible_evaluation"]:
            blocks[(r["instance_id"], r["behavior_config"], r["initial_prompt_sha256"])].append(r)
    group_stats = {}
    for g in [4, 8]:
        groups = []
        dropped = 0
        for key, records in sorted(blocks.items()):
            records = sorted(records, key=lambda r: r["content_sha256"])
            dropped += len(records) % g
            for offset in range(0, len(records) - g + 1, g):
                members = records[offset:offset+g]
                groups.append({"group_id": digest([g, key, offset])[:24], "group_size": g,
                               "instance_id": key[0], "behavior_config": key[1],
                               "initial_prompt_sha256": key[2], "split": members[0]["split"],
                               "record_ids": [r["record_id"] for r in members],
                               "success_count": sum(r["resolved"] for r in members)})
        write_jsonl(OUT / f"groups_g{g}.jsonl", groups)
        group_stats[g] = {"groups": len(groups), "mixed_groups": sum(0 < r["success_count"] < g for r in groups),
                          "by_split": {s: {"groups": sum(r["split"] == s for r in groups),
                              "mixed_groups": sum(r["split"] == s and 0 < r["success_count"] < g for r in groups)}
                              for s in ["train", "calibration", "heldout"]}, "incomplete_records": dropped}
    summary = {"raw_rows": len(rows), "unique_rows": len(unique), "duplicates_removed": len(duplicate_map),
               "label_conflicting_hashes": len(conflicts), "tasks": len(taskrows),
               "run_ids": dict(collections.Counter(r["run_id"] for r in rows)),
               "behavior_configs": {k: {"records": len(v), "tasks": len({r['instance_id'] for r in v})} for k, v in configrows.items()},
               "records_per_task": percentile_summary([len(v) for v in taskrows.values()]),
               "records_per_eligible_task_config_prompt": percentile_summary([len(v) for v in blocks.values()]),
               "groups": group_stats, "report_flags": dict(reports), "test_result_fields": dict(test_output_keys),
               "eligible_unique_rows": sum(r["eligible_evaluation"] for r in unique),
               "counts_quantiles": {k: percentile_summary([r["counts"][k] for r in unique]) for k in unique[0]["counts"]},
               "runner_timing": {"rows_with_textual_seconds": sum(bool(r["runner_reported_seconds"]) for r in rows),
                                 "individual_text_values_quantiles": percentile_summary([t for r in rows for t in r["runner_reported_seconds"]]),
                                 "interpretation": "Free-text runner output; not complete verifier or rollout wall-clock costs."},
               "script_sha256": sha_file(Path(__file__)),
               "protocol_sha256": sha_file(ROOT / "docs/swe_gym_data_protocol.md"),
               "runtime": {k: importlib.metadata.version(k) for k in ["pyarrow", "numpy", "scikit-learn", "requests"]},
               "created_at_utc": now()}
    write_json(OUT / "summary.json", summary)
    print(json.dumps({k: summary[k] for k in ["raw_rows", "unique_rows", "tasks", "groups", "runner_timing"]}, indent=2), flush=True)


def fit_proxy():
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    rows = [json.loads(line) for line in (OUT / "unique_records.jsonl").read_text().splitlines()]
    eligible = [r for r in rows if r["eligible_evaluation"]]
    keys = sorted(eligible[0]["features"])
    x = np.array([[r["features"][k] for k in keys] for r in eligible])
    y = np.array([r["resolved"] for r in eligible], dtype=int)
    train = np.array([r["split"] == "train" for r in eligible])
    model = make_pipeline(StandardScaler(), LogisticRegression(C=1., max_iter=2000, solver="lbfgs"))
    model.fit(x[train], y[train])
    pred = model.predict_proba(x)[:, 1]
    write_jsonl(OUT / "proxy_predictions.jsonl", [{"record_id": r["record_id"], "instance_id": r["instance_id"],
         "behavior_config": r["behavior_config"], "split": r["split"], "resolved": int(y[i]),
         "proxy_probability": float(pred[i])} for i, r in enumerate(eligible)])
    metrics = {}
    for split in ["train", "calibration", "heldout"]:
        use = np.array([r["split"] == split for r in eligible])
        metrics[split] = {"records": int(use.sum()), "tasks": len({r["instance_id"] for r in eligible if r["split"] == split}),
                         "success_rate": float(y[use].mean()),
                         "auc": float(roc_auc_score(y[use], pred[use])) if len(set(y[use])) > 1 else None,
                         "brier": float(brier_score_loss(y[use], pred[use])),
                         "log_loss": float(log_loss(y[use], pred[use], labels=[0, 1]))}
    scale, clf = model.steps[0][1], model.steps[1][1]
    write_json(OUT / "proxy_model.json", {"feature_names": keys, "scaler_mean": scale.mean_.tolist(),
       "scaler_scale": scale.scale_.tolist(), "coef": clf.coef_[0].tolist(), "intercept": float(clf.intercept_[0]),
       "configuration": {"C": 1, "max_iter": 2000, "solver": "lbfgs", "fit_split": "train"},
       "converged_iterations": clf.n_iter_.tolist(), "metrics": metrics,
       "note": "Message-only proxy, no final evaluator or identity features; this is a diagnostic baseline, not an audit method."})
    print(json.dumps(metrics, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--parse", action="store_true")
    parser.add_argument("--fit-proxy", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.print_help()
        return
    if args.fetch:
        fetch()
    if args.parse:
        parse()
    if args.fit_proxy:
        fit_proxy()


if __name__ == "__main__":
    main()
