# Canonical token artifact for the frozen Qwen diagnostic

Specified on 2026-09-12 before token-length inspection or model forward passes.

The target is an explicitly truncated, fixed empirical surrogate on archived trajectories. It is not the original model's native chat format, an on-policy gradient, a full-trajectory gradient, or an evaluation of new code executions.

## Population and source boundaries

Process all 6,055 unique frozen source rows for a separate token-length table. The forward-pass artifact contains **every heldout group** in the already-frozen `heterogeneous_groups_g8.jsonl`, sorted by `group_id`; members retain their frozen within-group order. There are 49 such groups and 392 distinct records. Do not select on labels, proxy probability, mixedness, apparent code quality, or sequence length.

Input text comes only from each record's original `messages`. Do not serialize `resolved`, `test_result`, final evaluation output, final patch outside the messages, task identity, logging model, or proxy probability. Source-content hashes and indices remain metadata, never input tokens. The dataset-level tool-schema field is not injected into this surrogate either.

## Exact serialization and tokenization

For message `m`, let its role header be `"\n### " + m["role"] + "\n"`.

Its body starts with `m["content"]` when that field is a string, otherwise the empty string. If `m["tool_calls"]` is nonempty, append the following exact string:

```python
"\n<tool_calls>\n" + json.dumps(m["tool_calls"], sort_keys=True) + "\n</tool_calls>"
```

Use Python's default `json.dumps` settings for the remaining options: `ensure_ascii=True`, default comma/colon spacing, and no key filtering. This preserves function names, argument strings and call IDs, including an assistant whose content is null but whose action is in tool calls. Null/empty tool-call fields add nothing. Preserve content whitespace; a body is considered empty for target selection when `body.strip()` is empty.

Use `Qwen/Qwen2.5-Coder-1.5B-Instruct`, revision `2e1fd397ee46e1388853d2af2c993145b0f1098a`, via the downloaded, hashed `tokenizer.json` and the `tokenizers` library directly. Tokenize **each role header and each body separately** with `add_special_tokens=False`, and concatenate the token-ID blocks. This blockwise BPE boundary rule is part of the definition; it need not equal a single tokenizer call on the concatenated display string. No native chat template, BOS, EOS or other additional special token is inserted. Literal special-token spellings occurring in archived text retain the tokenizer's documented ordinary encoding behavior.

The full-transcript length is the sum of those actual token block lengths over all original messages, including messages after the selected target. It is a token count for this defined serialization, not a character-based approximation or a claim about original logging-model token counts.

## Target and truncation

Choose the **last assistant message with a nonempty body**. Concatenate the headers and bodies of every preceding original message, then the chosen assistant's header, to obtain context token IDs `C`. The chosen assistant body token IDs are `T`. Messages after this target are excluded from the model input, since they would be future feedback.

If `len(T)>512`, move `T[:-512]` to the end of `C` and retain `T[-512:]` as the target. Then retain only the final 1,536 context token IDs. Concatenate context and target, producing at most 2,048 tokens. The target's role header is context and is not scored. For a shorter target, keep its entire body; the context limit remains 1,536 rather than expanding to fill spare target capacity. This rule includes tool-call parameters even when textual assistant content is null.

If a trajectory has no nonempty assistant body or its target encodes to zero tokens, flag it. Do not substitute a label-selected record. Abort artifact creation for any such required heldout member; the all-record audit must still disclose the count. Also require at least one context token so that the first scored token has a predecessor.

## Array conventions and scoring

Save right-padded `input_ids:int32`, `attention_mask:uint8` and `score_mask:uint8`. Padding uses the tokenizer's actual ID for `<|endoftext|>`, verified at runtime, and has attention and score masks zero. `score_mask[j]=1` means **input token j is a target token to be predicted**, so a causal-LM shifted loss uses `logits[:, :-1]`, `input_ids[:, 1:]`, and `score_mask[:, 1:]`. The context contributes conditioning only.

Also save record IDs, group IDs, the group-to-record-row index matrix, source content hashes, unpadded lengths, context/target lengths, chosen message positions, original target lengths, counts of target-prefix tokens moved to context, context tokens dropped, and trailing messages excluded. No labels or proxy probabilities are required in this token archive; they remain in the independently frozen group index.

The requested local cache path is `/Users/shengweizhang/.cache/shengwei-agent-audit/swe_tokens.npz`. A project manifest records the artifact hash, tokenizer hash/revision, source and group-index hashes, script/protocol hashes, runtime versions, validation checks, and precise schema. The builder accepts an output path for portable reproduction. The raw-source/previously frozen numeric files are not changed.
