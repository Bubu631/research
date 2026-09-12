#!/usr/bin/env python3
"""Export the first three diagnostic alignments per pair; no model forwards.

Requires the cached public data and tokenizer files produced by public_postedit.
It neither regenerates translations nor selects examples based on their outcome.
"""
import csv
import hashlib
import json
from pathlib import Path
import tarfile

import numpy as np
from sacremoses import MosesDetokenizer
from transformers import MarianTokenizer

from public_postedit import CACHE, RELEASE, edit_mask

BASE=RELEASE/"papers/edit_localization/results"


def main():
    examples=[]
    for pair,directory in [("en-de",BASE),("en-zh",BASE/"public_en_zh")]:
        manifest=json.loads((directory/"public_manifest.json").read_text())
        with (directory/"public_selected_ids.csv").open() as handle:
            selected=[r for r in csv.DictReader(handle) if r["split"]=="diagnostic"][:3]
        archive=CACHE/"mlqe_pe"/f"{pair}-train.tar.gz"
        assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest["archive_sha256"]
        snapshot=CACHE/"huggingface"/("models--"+manifest["model_id"].replace("/","--"))/"snapshots"/manifest["model_revision"]
        tokenizer=MarianTokenizer.from_pretrained(snapshot,local_files_only=True)
        with tarfile.open(archive) as handle:
            columns={ext:handle.extractfile(f"{pair}-train/train.{ext}").read().decode().splitlines()
                     for ext in ["src","mt","pe"]}
        detok_src=MosesDetokenizer(lang="en")
        detok_tgt=MosesDetokenizer(lang=pair.split("-")[1])
        for rank,record in enumerate(selected,1):
            index=int(record["line"])-1
            raw={k:v[index] for k,v in columns.items()}
            digest=hashlib.sha256((raw["src"]+"\n"+raw["mt"]+"\n"+raw["pe"]).encode()).hexdigest()
            assert digest==record["raw_triple_sha256"]
            source=detok_src.detokenize(raw["src"].split())
            mt=detok_tgt.detokenize(raw["mt"].split())
            pe=detok_tgt.detokenize(raw["pe"].split())
            mt_ids=tokenizer(text_target=mt,add_special_tokens=False)["input_ids"]
            pe_ids=tokenizer(text_target=pe,add_special_tokens=False)["input_ids"]
            mask,distance,deletions=edit_mask(mt_ids,pe_ids)
            assert int(mask.sum())==int(record["edited_tokens"])
            assert deletions==int(record["deletions"])
            assert distance==int(record["levenshtein_distance"])
            tokens=pe_ids+[tokenizer.eos_token_id]
            full_mask=np.append(mask,False)
            positions=[dict(position=j+1,token_id=token,piece=tokenizer.convert_ids_to_tokens(token),
                            edited=bool(full_mask[j]),label="E" if full_mask[j] else "U",is_eos=j==len(pe_ids))
                       for j,token in enumerate(tokens)]
            examples.append(dict(pair=pair,diagnostic_order=rank,original_line=int(record["line"]),
                raw_triple_sha256=digest,source=source,archived_mt=mt,human_postedit=pe,
                raw_archive_text=raw,model_id=manifest["model_id"],model_revision=manifest["model_revision"],
                source_control_token=">>cmn_Hans<<" if pair=="en-zh" else None,
                pe_token_count_excluding_eos=len(pe_ids),loss_normalization_length=len(tokens),
                edited_tokens=int(mask.sum()),untouched_tokens_including_eos=int((~full_mask).sum()),
                levenshtein_distance=distance,deletions=deletions,pe_tokens=positions))
    result=dict(selection="First three diagnostic records in saved frozen record order, per language; no outcome-based choice",
        data_repository="https://github.com/sheffieldnlp/mlqe-pe",data_revision="2a670a1140416cf80507b5a829659383c878feb8",
        repository_declared_license="CC0-1.0",scope="Token alignment illustration only; no model forward, generated translation, or quality assessment",
        examples=examples)
    (BASE/"public_alignment_examples.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    doc=["# Deterministic public post-edit alignment examples\n\n",
         "These are the **first three diagnostic records in the saved experiment order for each language pair**. "
         "They were not chosen by edit type, bias result, likelihood change, or translation quality. "
         "This export loads cached data and tokenizer files only; it runs no translation model.\n\n",
         "Source: [MLQE-PE author repository](https://github.com/sheffieldnlp/mlqe-pe), pinned revision "
         "`2a670a1140416cf80507b5a829659383c878feb8`, whose repository license declares CC0-1.0; "
         "see [the dataset paper](https://aclanthology.org/2022.lrec-1.530.pdf). "
         "The archived MT belongs to the dataset's logging system. The human PE corrects that archived MT, "
         "not a newly generated Helsinki model output.\n\n",
         "`U` denotes a PE subword aligned to an equal archived-MT subword; `E` denotes an insertion or substitution. "
         "SentencePiece `▁` is a word-boundary marker. Minimum-cost backtracking ties prefer equal diagonal, "
         "substitution, deletion, then insertion. Deleted MT subwords have no PE-position gradient. "
         "The final `</s>` is always untouched. Both gradient component sums use the same total PE length "
         "including EOS, rather than separate edited/untouched lengths. These labels are mechanical edit "
         "alignment labels, not independent judgments that a token is correct.\n\n"]
    for ex in examples:
        doc.append(f"## {ex['pair']}, diagnostic record {ex['diagnostic_order']} (original line {ex['original_line']})\n\n")
        doc.append(f"**Source:** {ex['source']}\n\n**Archived MT:** {ex['archived_mt']}\n\n**Human PE:** {ex['human_postedit']}\n\n")
        doc.append("**PE subword labels, in target order:**\n\n```text\n"+
                   " · ".join(f"{token['label']}:{token['piece']}" for token in ex["pe_tokens"])+"\n```\n\n")
        doc.append(f"Edited positions: {ex['edited_tokens']}; untouched positions including EOS: {ex['untouched_tokens_including_eos']}; "
                   f"deleted MT subwords: {ex['deletions']}; Levenshtein distance: {ex['levenshtein_distance']}. "
                   f"Both loss components divide by {ex['loss_normalization_length']}.\n\n")
        if ex["source_control_token"]:
            doc.append("The model source additionally begins with `>>cmn_Hans<<`; it is excluded from source-length filtering and selection features.\n\n")
        doc.append(f"Raw triple SHA-256: `{ex['raw_triple_sha256']}`.\n\n")
    doc.append("The machine-readable export preserves raw archive strings, detokenized text, token IDs, masks, revisions and counts in "
               "[public_alignment_examples.json](../papers/edit_localization/results/public_alignment_examples.json). "
               "Rebuild after caching the main public experiment assets with `python experiments/public_alignment_examples.py`.\n")
    (RELEASE/"docs/public_alignment_examples.md").write_text("".join(doc))
    print(json.dumps([{k:e[k] for k in ["pair","diagnostic_order","original_line","edited_tokens","deletions"]}
                      for e in examples],indent=2))


if __name__=="__main__":
    main()
