#!/usr/bin/env python3
"""Check saved token artifact and independently reconstruct three fixed records."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/swe_gym"
OUT = DATA / "processed"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    manifest = json.loads((OUT / "token_artifact_manifest.json").read_text())
    p = Path(manifest["artifact_path"])
    assert sha(p) == manifest["artifact_sha256"]
    assert sha(ROOT / "experiments/swe_token_artifact.py") == manifest["script_sha256"]
    assert sha(ROOT / "docs/swe_token_protocol.md") == manifest["protocol_sha256"]
    assert sha(OUT / "token_lengths.jsonl") == manifest["length_table_sha256"]
    for name, expected in manifest["source_sha256"].items():
        source = DATA / name if name == "source_manifest.json" else OUT / name
        assert sha(source) == expected
    model = Tokenizer.from_file(str(DATA / "tokenizer_cache/tokenizer.json"))
    records = {r["record_id"]: r for r in map(json.loads, (OUT / "unique_records.jsonl").read_text().splitlines())}
    lengths = {r["record_id"]: r for r in map(json.loads, (OUT / "token_lengths.jsonl").read_text().splitlines())}
    assert len(lengths) == 6055
    groups = sorted([g for g in map(json.loads, (OUT / "heterogeneous_groups_g8.jsonl").read_text().splitlines()) if g["split"] == "heldout"], key=lambda g: g["group_id"])
    archive = np.load(p, allow_pickle=False)
    ids = list(archive["record_ids"])
    assert ids == [rid for g in groups for rid in g["record_ids"]]
    assert len(ids) == len(set(ids)) == 392
    assert archive["input_ids"].shape == archive["attention_mask"].shape == archive["score_mask"].shape
    assert archive["input_ids"].shape[1] <= 2048
    assert np.all(archive["score_mask"] <= archive["attention_mask"])
    assert np.all(archive["score_mask"][:, 0] == 0)
    assert np.array_equal(archive["score_mask"].sum(axis=1), archive["retained_target_tokens"])
    assert np.array_equal(archive["attention_mask"].sum(axis=1), archive["input_tokens"])
    assert np.all(archive["retained_context_tokens"] <= 1536)
    assert np.all((archive["retained_target_tokens"] > 0) & (archive["retained_target_tokens"] <= 512))
    assert np.array_equal(archive["group_record_rows"], np.arange(392).reshape(49, 8))
    for i, rid in enumerate(ids):
        assert archive["source_content_sha256"][i] == records[rid]["content_sha256"]
        n = int(archive["input_tokens"][i])
        c = int(archive["retained_context_tokens"][i])
        assert np.all(archive["score_mask"][i, :c] == 0)
        assert np.all(archive["score_mask"][i, c:n] == 1)
        assert np.all(archive["attention_mask"][i, n:] == 0)
        assert np.all(archive["input_ids"][i, n:] == manifest["pad_token_id"])
    samples = [0, len(ids)//2, len(ids)-1]
    for array_row in samples:
        rid = ids[array_row]
        source = records[rid]
        target_row = source["source_row"]
        count = 0
        messages = None
        for batch in pq.ParquetFile(ROOT / source["source_file"]).iter_batches(batch_size=16, columns=["messages"]):
            if count + batch.num_rows > target_row:
                messages = batch.to_pylist()[target_row-count]["messages"]
                break
            count += batch.num_rows
        assert messages is not None
        headers = []
        bodies = []
        positions = []
        for j, m in enumerate(messages):
            text = m.get("content") if isinstance(m.get("content"), str) else ""
            if m.get("tool_calls"):
                text = text + "\n<tool_calls>\n" + json.dumps(m["tool_calls"], sort_keys=True) + "\n</tool_calls>"
            headers.append(model.encode("\n### " + m["role"] + "\n", add_special_tokens=False).ids)
            bodies.append(model.encode(text, add_special_tokens=False).ids)
            if m["role"] == "assistant" and text.strip():
                positions.append(j)
        j = positions[-1]
        before = sum((headers[k] + bodies[k] for k in range(j)), []) + headers[j]
        moved = max(0, len(bodies[j])-512)
        context = (before + bodies[j][:moved])[-1536:]
        target = bodies[j][moved:]
        expected = context + target
        assert np.array_equal(archive["input_ids"][array_row, :len(expected)], expected)
        assert sum(map(len, headers)) + sum(map(len, bodies)) == lengths[rid]["full_transcript_tokens"]
        assert len(context) == int(archive["retained_context_tokens"][array_row])
        assert len(target) == int(archive["retained_target_tokens"][array_row])
    report = {"checks_passed": True, "all_records_metadata_checked": len(ids),
              "independent_reconstruction_record_ids": [ids[i] for i in samples],
              "artifact_sha256": manifest["artifact_sha256"], "checker_sha256": sha(Path(__file__))}
    (OUT / "token_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
