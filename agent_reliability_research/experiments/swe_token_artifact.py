#!/usr/bin/env python3
"""Tokenize frozen SWE history without executing code or loading an LLM."""
from __future__ import annotations
import argparse
import collections
import hashlib
import importlib.metadata
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/swe_gym"
OUT = DATA / "processed"
TOKENIZER = DATA / "tokenizer_cache/tokenizer.json"
DEFAULT_OUTPUT = Path.home() / ".cache/shengwei-agent-audit/swe_tokens.npz"


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonl(p):
    return [json.loads(line) for line in p.read_text().splitlines()]


def header(m):
    return "\n### " + m["role"] + "\n"


def body(m):
    value = m.get("content")
    result = value if isinstance(value, str) else ""
    if m.get("tool_calls"):
        result += "\n<tool_calls>\n" + json.dumps(m["tool_calls"], sort_keys=True) + "\n</tool_calls>"
    return result


def self_test():
    action = [{"function": {"name": "run", "arguments": "{\"x\":1}"}, "id": "example"}]
    assert body({"content": None, "tool_calls": action}) == "\n<tool_calls>\n" + json.dumps(action, sort_keys=True) + "\n</tool_calls>"
    assert body({"content": "hello", "tool_calls": None}) == "hello"
    assert body({"content": None, "tool_calls": []}) == ""
    assert body({"content": " \n", "tool_calls": None}).strip() == ""
    assert header({"role": "assistant"}) == "\n### assistant\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    self_test()
    import numpy as np
    import pyarrow.parquet as pq
    from tokenizers import Tokenizer

    start = time.perf_counter()
    tokenizer = Tokenizer.from_file(str(TOKENIZER))
    tokenizer_meta = json.loads((TOKENIZER.parent / "manifest.json").read_text())
    assert sha(TOKENIZER) == tokenizer_meta["sha256"]
    pad = tokenizer.token_to_id("<|endoftext|>")
    assert isinstance(pad, int)
    original = jsonl(OUT / "unique_records.jsonl")
    records = {r["record_id"]: r for r in original}
    groups = sorted([g for g in jsonl(OUT / "heterogeneous_groups_g8.jsonl") if g["split"] == "heldout"], key=lambda g: g["group_id"])
    chosen_ids = [rid for g in groups for rid in g["record_ids"]]
    assert len(chosen_ids) == len(set(chosen_ids)) == 392
    assert len(groups) == 49
    needed = set(chosen_ids)
    headers = {}
    lengths = []
    chosen = {}
    examples = {}
    total_seen = 0
    for source_file in sorted({r["source_file"] for r in original}):
        source = ROOT / source_file
        row_index = 0
        for batch in pq.ParquetFile(source).iter_batches(batch_size=16, columns=["messages"]):
            rows = batch.to_pylist()
            # Batch text encoding uses the same separate-body boundary semantics.
            all_bodies = [body(m) for row in rows for m in row["messages"]]
            encoded = tokenizer.encode_batch(all_bodies, add_special_tokens=False)
            cursor = 0
            for z in rows:
                rid = f"{source.stem}:{row_index}"
                row_index += 1
                total_seen += 1
                source_record = records[rid]
                messages = z["messages"]
                bodies = all_bodies[cursor:cursor+len(messages)]
                body_ids = [e.ids for e in encoded[cursor:cursor+len(messages)]]
                cursor += len(messages)
                header_ids = []
                for m in messages:
                    h = header(m)
                    if h not in headers:
                        headers[h] = tokenizer.encode(h, add_special_tokens=False).ids
                    header_ids.append(headers[h])
                target_positions = [i for i, m in enumerate(messages) if m["role"] == "assistant" and bodies[i].strip()]
                full_count = sum(len(a) + len(b) for a, b in zip(header_ids, body_ids))
                result = {"record_id": rid, "source_content_sha256": source_record["content_sha256"],
                          "full_transcript_tokens": full_count, "message_count": len(messages),
                          "assistant_message_count": sum(m["role"] == "assistant" for m in messages),
                          "has_nonempty_assistant_target": bool(target_positions),
                          "in_frozen_heldout_g8_artifact": rid in needed}
                if target_positions:
                    pos = target_positions[-1]
                    target = body_ids[pos]
                    prefix = [token for i in range(pos) for block in [header_ids[i], body_ids[i]] for token in block]
                    prefix.extend(header_ids[pos])
                    original_context_len = len(prefix)
                    original_target_len = len(target)
                    moved = max(0, len(target) - 512)
                    if moved:
                        prefix.extend(target[:moved])
                        target = target[moved:]
                    dropped = max(0, len(prefix) - 1536)
                    prefix = prefix[-1536:]
                    ids = prefix + target
                    mask = [0] * len(prefix) + [1] * len(target)
                    result.update({"target_message_index": pos, "original_context_tokens": original_context_len,
                       "original_target_tokens": original_target_len, "target_prefix_tokens_moved_to_context": moved,
                       "context_tokens_dropped": dropped, "retained_context_tokens": len(prefix),
                       "retained_target_tokens": len(target), "input_tokens": len(ids),
                       "trailing_messages_excluded": len(messages)-pos-1,
                       "target_content_is_null": messages[pos].get("content") is None,
                       "target_has_tool_calls": bool(messages[pos].get("tool_calls")),
                       "has_score_tokens": bool(target)})
                    kind = ("null_content_with_tool_calls" if result["target_content_is_null"] and result["target_has_tool_calls"]
                            else "text_with_tool_calls" if result["target_has_tool_calls"] else "text_only")
                    if kind not in examples:
                        examples[kind] = {k: result[k] for k in ["record_id", "target_message_index", "target_content_is_null", "target_has_tool_calls", "original_target_tokens", "retained_target_tokens"]}
                    if rid in needed:
                        assert target and prefix and len(ids) <= 2048
                        assert len(target) <= 512 and len(prefix) <= 1536
                        assert mask[0] == 0 and sum(mask) == len(target)
                        chosen[rid] = (ids, mask, result)
                elif rid in needed:
                    raise RuntimeError(f"Required heldout record lacks a nonempty assistant target: {rid}")
                lengths.append(result)
            if total_seen % 320 == 0:
                print(f"Tokenized {total_seen}/6055 records; {time.perf_counter()-start:.1f}s", flush=True)
        print(f"Completed {source.name}: {row_index} records", flush=True)
    assert total_seen == len(lengths) == 6055
    assert set(chosen) == needed
    width = max(len(chosen[rid][0]) for rid in chosen_ids)
    inputs = np.full((len(chosen_ids), width), pad, dtype=np.int32)
    attention = np.zeros_like(inputs, dtype=np.uint8)
    scores = np.zeros_like(inputs, dtype=np.uint8)
    for i, rid in enumerate(chosen_ids):
        ids, mask, result = chosen[rid]
        inputs[i, :len(ids)] = ids
        attention[i, :len(ids)] = 1
        scores[i, :len(ids)] = mask
    assert np.all(scores <= attention)
    assert np.all(scores[:, 0] == 0)
    assert np.all(np.sum(scores, axis=1) > 0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["target_message_index", "original_context_tokens", "original_target_tokens",
              "target_prefix_tokens_moved_to_context", "context_tokens_dropped", "retained_context_tokens",
              "retained_target_tokens", "input_tokens", "trailing_messages_excluded", "full_transcript_tokens"]
    numeric_metadata = {field: np.array([chosen[rid][2][field] for rid in chosen_ids], dtype=np.int32) for field in fields}
    np.savez_compressed(args.output, input_ids=inputs, attention_mask=attention, score_mask=scores,
        record_ids=np.array(chosen_ids), group_ids=np.array([g["group_id"] for g in groups]),
        group_record_rows=np.arange(len(chosen_ids), dtype=np.int32).reshape(len(groups), 8),
        source_content_sha256=np.array([records[rid]["content_sha256"] for rid in chosen_ids]),
        **numeric_metadata)
    length_file = OUT / "token_lengths.jsonl"
    with length_file.open("w") as f:
        for r in lengths:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    # Verify the actual persisted archive, with no object arrays/pickle required.
    with np.load(args.output, allow_pickle=False) as persisted:
        assert np.array_equal(inputs, persisted["input_ids"])
        assert np.array_equal(scores, persisted["score_mask"])
        assert list(persisted["record_ids"]) == chosen_ids
        schema = {k: {"shape": list(persisted[k].shape), "dtype": str(persisted[k].dtype)} for k in persisted.files}
    quantiles = lambda values: {str(q): float(np.percentile(values, q)) for q in [0, 25, 50, 75, 90, 95, 99, 100]}
    report = {"artifact_path": str(args.output.resolve()), "artifact_sha256": sha(args.output),
       "artifact_bytes": args.output.stat().st_size, "records_in_length_table": len(lengths),
       "heldout_g8_groups": len(groups), "heldout_records": len(chosen_ids), "no_target_records": sum(not r["has_nonempty_assistant_target"] for r in lengths),
       "zero_encoded_target_records": sum(r.get("has_nonempty_assistant_target", False) and not r.get("has_score_tokens", False) for r in lengths),
       "pad_token": "<|endoftext|>", "pad_token_id": pad,
       "tokenizer": tokenizer_meta, "schema": schema,
       "source_sha256": {"unique_records.jsonl": sha(OUT / "unique_records.jsonl"),
                         "heterogeneous_groups_g8.jsonl": sha(OUT / "heterogeneous_groups_g8.jsonl"),
                         "source_manifest.json": sha(DATA / "source_manifest.json")},
       "length_table_sha256": sha(length_file), "script_sha256": sha(Path(__file__)),
       "protocol_sha256": sha(ROOT / "docs/swe_token_protocol.md"),
       "runtime": {k: importlib.metadata.version(k) for k in ["numpy", "pyarrow", "tokenizers"]},
       "elapsed_seconds": time.perf_counter()-start, "full_transcript_token_quantiles": quantiles([r["full_transcript_tokens"] for r in lengths]),
       "heldout_input_token_quantiles": quantiles([chosen[rid][2]["input_tokens"] for rid in chosen_ids]),
       "heldout_score_token_quantiles": quantiles([chosen[rid][2]["retained_target_tokens"] for rid in chosen_ids]),
       "heldout_context_truncated_records": sum(chosen[rid][2]["context_tokens_dropped"] > 0 for rid in chosen_ids),
       "heldout_target_prefix_moved_records": sum(chosen[rid][2]["target_prefix_tokens_moved_to_context"] > 0 for rid in chosen_ids),
       "serialization_case_checks": examples,
       "checks": {"synthetic_null_content_tool_call_fixture": True, "all_frozen_heldout_groups_included": True,
                  "score_only_target_token_positions": True, "persisted_arrays_identical": True,
                  "no_labels_or_test_result_in_serialized_inputs": True},
       "interpretation": "Blockwise-BPE, bounded-context final-assistant-action surrogate on fixed heterogeneous historical groups; not native chat or on-policy trajectories."}
    (OUT / "token_artifact_manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["artifact_path", "artifact_sha256", "artifact_bytes", "heldout_records", "no_target_records", "elapsed_seconds", "full_transcript_token_quantiles"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
