# Frozen 32-dimensional logit-bias score: independent audit

Audited and repaired on 2026-09-12 before the parent runs the model. No pretrained forward pass, new trajectory, reference-test execution or policy optimization was performed by this audit.

## Mathematical target and precision

For predictable target positions J, fixed base logits z_(t−1), and vocabulary-by-32 matrix B, the diagnostic adds eta through `z_eta = float32(z_frozen_fp16) + B eta`. At eta=0 its mean log-probability score is

`g = |J|^(-1) Σ_(t∈J) [B[y_t,:] − softmax(z_(t−1))^T B]`.

The sign is for log probability, the negative of the NLL derivative. Target positions index the token being predicted, so using `hidden[target_position−1]` is correct. The helper computes score sums and positive NLL sums, with normalization after summation. The model's half-precision hidden/head forward is frozen; float32 softmax and bias accumulation then define the numerical diagnostic. Exporting those numbers into a float64 NumPy array does not recover double precision. It is not a native model-bias parameter, a full-parameter score, or the gradient that a float32 model would necessarily produce.

The Qwen local configuration identifies Qwen2ForCausalLM, vocabulary size 151,936, tied word embeddings, and a 32,768-position context. The original configuration declares bfloat16; the experiment explicitly loads float16 and records that choice. Nonfinite logits/results now fail rather than enter a bank. The direct backbone-plus-head extraction is intentionally restricted to this pinned Qwen2 checkpoint, not an arbitrary architecture passed through the same CLI.

## Material issues fixed before execution

1. **Unsafe cache reuse.** The original cache checked only record IDs. Identical IDs with changed tokens, masks, models or script could silently mix gradients. The cache now contains and strictly compares token SHA256, complete pinned model-file fingerprint, script hash, basis hash/seed/dimension, numerical/library versions, device, dtype, requested record count and smoke/full scope. It verifies cached shapes, finite values, target counts and record ordering.
2. **Smoke/full overlap.** They now use different partial caches. A full run does not reuse smoke scores. Explicit `--fresh` archives prior cache/output/manifest instead of silently destroying them. Source snapshots are retained under their fingerprint.
3. **Non-atomic partial writes.** Compressed NPZ and JSON now write to a temporary file, flush/fsync and atomically replace the target. An interrupted write cannot truncate the existing valid cache.
4. **Implicit mask assumptions.** Attention must be a contiguous prefix followed by right padding. Score masks must be binary, inside attention, nonempty, and exclude position zero. Shapes, integer token range and unique record IDs are checked before model execution. This prevents `sum(attention)` from silently truncating left-padded/holey arrays or scored padding. The cropped model input receives an explicit all-one attention mask.
5. **Unproved model revision.** The old manifest wrote a constant revision for any local model path. The runner now checks the actual local weight size and SHA256 against the official revision, and verifies Git blob identities for config/tokenizer files. Other model metadata files are hashed into the fingerprint. Weights are hashed once per invocation, not per record. The token artifact is hashed again at completion to detect mutation during a run.

Mask shape validation does not establish that canonicalization correctly distinguishes assistant/action text from user/tool text. That is the responsibility of the separate input-artifact audit. Nor does the added-bias diagnostic correct the policy under which historical trajectories were generated; its inferential target is the declared frozen empirical historical surrogate.

## Primary checkpoint provenance

Official model: [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct), revision `2e1fd397ee46e1388853d2af2c993145b0f1098a`.

The [official revision API](https://huggingface.co/api/models/Qwen/Qwen2.5-Coder-1.5B-Instruct/revision/2e1fd397ee46e1388853d2af2c993145b0f1098a?blobs=true) was retrieved on 2026-09-12; its response is saved as `results/frozen_gradient_reference_metadata.json`. It specifies `model.safetensors` as 3,087,467,144 bytes with LFS SHA256 `c1b9b30e907950516ba3c646bdf570d8084c25a6410a0cdca80cf04b11bc13a8`. The actual local file matches. Config and tokenizer Git blob hashes also match. This verification is read-only and does not instantiate the model.

## Executed independent CPU checks

`experiments/verify_frozen_gradient.py` uses a 23-token-vocabulary, 32-dimensional-bias, 11-position random fixture. Its frozen logits are quantized to float16 then cast to float32; no model output is invented or attributed to Qwen.

* Conventional shifted-token masked log-softmax with autograd agrees with the analytic float64 helper to `5.55e-17`.
* The actual float32 score differs from that double-precision reference by at most `1.03e-8`.
* Central finite differences over all 32 coordinates agree to `3.77e-11`.
* An intentionally wrong token shift changes the score by `0.04917`, so the fixture is sensitive to the shift error.
* All six invalid-mask cases are rejected. Cache checks reject changed tokens/model/source, smoke/full mixing, reordered IDs and oversized prefixes, while valid resume and atomic temporary-file cleanup pass.

Results and exact script hashes: `results/frozen_gradient_verification.json`. Executed with CPU torch 2.14.0 and NumPy 2.5.3 in the cache-local Python environment. These finite checks do not establish MPS reproducibility or the numerical accuracy of the whole fp16 pretrained forward; the parent still needs the model smoke, nonfinite diagnostics and real token-artifact audit.

Command: `/Users/shengweizhang/.cache/shengwei-agent-audit/venv/bin/python agent_reliability_research/experiments/verify_frozen_gradient.py`.
