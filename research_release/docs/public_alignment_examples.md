# Deterministic public post-edit alignment examples

These are the **first three diagnostic records in the saved experiment order for each language pair**. They were not chosen by edit type, bias result, likelihood change, or translation quality. This export loads cached data and tokenizer files only; it runs no translation model.

Source: [MLQE-PE author repository](https://github.com/sheffieldnlp/mlqe-pe), pinned revision `2a670a1140416cf80507b5a829659383c878feb8`, whose repository license declares CC0-1.0; see [the dataset paper](https://aclanthology.org/2022.lrec-1.530.pdf). The archived MT belongs to the dataset's logging system. The human PE corrects that archived MT, not a newly generated Helsinki model output.

`U` denotes a PE subword aligned to an equal archived-MT subword; `E` denotes an insertion or substitution. SentencePiece `▁` is a word-boundary marker. Minimum-cost backtracking ties prefer equal diagonal, substitution, deletion, then insertion. Deleted MT subwords have no PE-position gradient. The final `</s>` is always untouched. Both gradient component sums use the same total PE length including EOS, rather than separate edited/untouched lengths. These labels are mechanical edit alignment labels, not independent judgments that a token is correct.

## en-de, diagnostic record 1 (original line 4207)

**Source:** His averages jumped from .262 / .371 / .532 and .904 OPS to .274 / .381 / .576 and .958 OPS.

**Archived MT:** Seine Durchschnittswerte sprangen von .262 / .371 / .532 und .904 OPS auf .274 / .381 / .576 und .958 OPS.

**Human PE:** Seine Durchschnittswerte sprangen von .262 / .371 / .532 und .904 OPS auf .274 / .381 / .576 und .958 OPS.

**PE subword labels, in target order:**

```text
U:▁Seine · U:▁Durchschnitt · U:swerte · U:▁sprang · U:en · U:▁von · U:▁ · U:. · U:26 · U:2 · U:▁/ · U:▁ · U:. · U:37 · U:1 · U:▁/ · U:▁ · U:. · U:53 · U:2 · U:▁und · U:▁ · U:. · U:90 · U:4 · U:▁OP · U:S · U:▁auf · U:▁ · U:. · U:27 · U:4 · U:▁/ · U:▁ · U:. · U:38 · U:1 · U:▁/ · U:▁ · U:. · U:5 · U:76 · U:▁und · U:▁ · U:. · U:95 · U:8 · U:▁OP · U:S · U:. · U:</s>
```

Edited positions: 0; untouched positions including EOS: 51; deleted MT subwords: 0; Levenshtein distance: 0. Both loss components divide by 51.

Raw triple SHA-256: `11112c311b9af993d8b43672799690e9b294e8b4183d5432a49c229a054f4cfe`.

## en-de, diagnostic record 2 (original line 149)

**Source:** Blue Riband would overwhelm any possible carcinotron design, while also providing enough accuracy to directly guide interceptors.

**Archived MT:** Blue Riband würde jedes mögliche Karzinotron-Design überwältigen und gleichzeitig genügend Genauigkeit bieten, um Abfanggeräte direkt zu steuern.

**Human PE:** Blue Riband würde jedes mögliche Carzinotron-Design besiegen und gleichzeitig genügend Genauigkeit bieten, um Abfanggeräte direkt zu steuern.

**PE subword labels, in target order:**

```text
U:▁Blue · U:▁Ri · U:band · U:▁würde · U:▁jedes · U:▁mögliche · E:▁Car · U:z · U:ino · U:tron · U:- · U:Design · E:▁besiegen · U:▁und · U:▁gleichzeitig · U:▁genügend · U:▁Genauigkeit · U:▁bieten · U:, · U:▁um · U:▁Ab · U:fang · U:geräte · U:▁direkt · U:▁zu · U:▁steuern · U:. · U:</s>
```

Edited positions: 2; untouched positions including EOS: 26; deleted MT subwords: 3; Levenshtein distance: 5. Both loss components divide by 28.

Raw triple SHA-256: `29b97fc90f4604351054fa7e92d0f778114ed3bcd5239bee772f254efe9ba3a3`.

## en-de, diagnostic record 3 (original line 5037)

**Source:** Against the Hokies, he had five receptions for 105 yards and three touchdowns.

**Archived MT:** Gegen die Hokies hatte er fünf Empfänge für 105 Meter und drei Touchdowns.

**Human PE:** Gegen die Hokies hatte er fünf Receptions auf 105 Yards und drei Touchdowns.

**PE subword labels, in target order:**

```text
U:▁Gegen · U:▁die · U:▁Ho · U:ki · U:es · U:▁hatte · U:▁er · U:▁fünf · E:▁Re · E:ception · E:s · E:▁auf · U:▁105 · E:▁Y · E:ard · E:s · U:▁und · U:▁drei · U:▁Touch · U:down · U:s · U:. · U:</s>
```

Edited positions: 7; untouched positions including EOS: 16; deleted MT subwords: 0; Levenshtein distance: 7. Both loss components divide by 23.

Raw triple SHA-256: `3f9bc90fb022e881f0df544670b33d6ffdd289ebad6bae22534b659d2e1b6a30`.

## en-zh, diagnostic record 1 (original line 4207)

**Source:** Webber collided with the Lotus of Heikki Kovalainen, flipping his Red Bull car into a somersault before landing and crashing into a tyre barrier.

**Archived MT:** Webber 与 Heikki Kovalainen 的 Lotus 相撞 ， 他的红牛车在降落和撞上轮胎屏障之前 ， 撞上了一个木头。

**Human PE:** Webber 与 Heikki Kovalainen 的 Lotus 相撞 ， 他的 Red Bull 在落地前翻了一个筋斗 ， 撞上了轮胎护栏。

**PE subword labels, in target order:**

```text
U:▁We · U:b · U:ber · U:▁ · U:与 · U:▁He · U:ik · U:ki · U:▁ · U:Ko · U:val · U:ain · U:en · U:▁ · U:的 · U:▁Lo · U:t · U:us · U:▁ · U:相 · U:撞 · U:▁ · U:, · U:▁他的 · E:▁Re · E:d · E:▁B · E:ull · E:▁在 · E:落 · E:地 · E:前 · E:翻 · E:了一个 · E:筋 · E:斗 · U:▁ · U:, · U:▁ · U:撞 · E:上了 · E:轮胎 · E:护 · E:栏 · U:。 · U:</s>
```

Edited positions: 16; untouched positions including EOS: 30; deleted MT subwords: 0; Levenshtein distance: 16. Both loss components divide by 46.

The model source additionally begins with `>>cmn_Hans<<`; it is excluded from source-length filtering and selection features.

Raw triple SHA-256: `c36a474d7fd331be8bf8acf565e4fbe4df52c5c8f994e825046b2fac3e8ec129`.

## en-zh, diagnostic record 2 (original line 149)

**Source:** When Richard refuses, Hurley secretly walks to the Black Rock and defuses the remaining dynamite.

**Archived MT:** 当理查德拒绝时, 赫利秘密地走到布莱克岩, 并拆除剩余的炸药.

**Human PE:** 当理查德拒绝时 ， 赫利悄悄地走向黑岩 ， 并拆除剩余的炸药。

**PE subword labels, in target order:**

```text
U:▁当 · U:理查德 · U:拒绝 · U:时 · E:▁ · U:, · U:▁ · U:赫 · U:利 · E:悄悄 · U:地 · E:走向 · E:黑 · E:岩 · E:▁ · U:, · U:▁ · U:并 · U:拆除 · U:剩余的 · U:炸药 · E:。 · U:</s>
```

Edited positions: 7; untouched positions including EOS: 16; deleted MT subwords: 0; Levenshtein distance: 7. Both loss components divide by 23.

The model source additionally begins with `>>cmn_Hans<<`; it is excluded from source-length filtering and selection features.

Raw triple SHA-256: `7bae7dabe78e0ab95b2bee3250a50468a72d110855fd8629138ce50453504074`.

## en-zh, diagnostic record 3 (original line 5037)

**Source:** The two friends both admired each other for their great feats and rebellions, and also of each other's brilliance.

**Archived MT:** 这两个朋友都钦佩对方的伟大成就和反叛 ， 也钦佩对方的辉煌。

**Human PE:** 这两个朋友都钦佩对方的伟大成就和反叛 ， 也钦佩对方的光彩。

**PE subword labels, in target order:**

```text
U:▁这两个 · U:朋友 · U:都 · U:钦 · U:佩 · U:对方 · U:的 · U:伟大 · U:成就 · U:和 · U:反叛 · U:▁ · U:, · U:▁ · U:也 · U:钦 · U:佩 · U:对方 · U:的 · E:光 · E:彩 · U:。 · U:</s>
```

Edited positions: 2; untouched positions including EOS: 21; deleted MT subwords: 0; Levenshtein distance: 2. Both loss components divide by 23.

The model source additionally begins with `>>cmn_Hans<<`; it is excluded from source-length filtering and selection features.

Raw triple SHA-256: `d662b4278c3e20a250c547f941db58f25b1cd632f21ab309a68ea3ba1ba89f0a`.

The machine-readable export preserves raw archive strings, detokenized text, token IDs, masks, revisions and counts in [public_alignment_examples.json](../papers/edit_localization/results/public_alignment_examples.json). Rebuild after caching the main public experiment assets with `python experiments/public_alignment_examples.py`.
