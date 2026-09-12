# Independent PDF visual audit: pages 12–23

Reviewed on 11 September 2026. Scope: the twelve rendered pages numbered **12 through 23**, inspected individually at their supplied PNG resolution. Pages 1–11 were assigned to the lead analyst and are **not certified by this record**. This is visual inspection, separate from the earlier mathematical and numerical audit.

## Final frozen version: passed

The final 23-page PDF has SHA-256:

`051d8aefbc73aed35227fa2e9ab662cb07cb028dd0b2c917b232b1698156040d`

This hash was independently confirmed before the final review. The final renders are `tmp/nhs_pdf_qa/final-01.png` through `final-23.png` in the parent workspace. Within this reviewer's assigned range:

- Pages **16, 17, 18, 19, 22 and 23** changed and were individually visually inspected again.
- Pages **12, 13, 14, 15, 20 and 21** were independently compared with the previously inspected renders using an exact RGB pixel difference; every pixel was unchanged. Their original visual inspection therefore carries forward to this final PDF.
- The Figure 5 **175.5** annotation is now left of the dashed line and clear of all three legend entries. The overlap is resolved.
- The previously split NHS workbook reference now begins and ends on page 19. The preceding archived-workbook entry ends cleanly on page 18. The reference-entry page split is resolved.
- The revised text and all tables on pages 17, 19, 22 and 23 fit cleanly. The complete stress table remains readable on one page.

**Final result: no unresolved visual defects observed on pages 12–23.** This is not a claim to have independently reviewed pages 1–11.

The changed final page-image hashes are:

```text
16 753e71f0f59a0391b40a458096346aba6b4ff5f3a960f50312a02943813ac606
17 3dffb3c51f1a40f6b2623d05aeb1ae5fcf1d7b307d6d27b20985caf37b5a53d0
18 960e7a2838e2f2c96d14bba663c3e09cdea9e3e943b370d2b754f6d4ca6ef173
19 bda732c2ed67e153890ccb6212844c760f182c51e0290ba33dccb48106c206f9
22 1d79fc85c3a673328a1ebda40954e755b48d6cf3fa51e98118430b410414823f
23 b75f2c3b7346cfbf778c9b8ecaa43d71d53b6719e8ce101a9610e006ea2236c9
```

The remaining six hashes are unchanged from the initial render fingerprints recorded below. The rest of this document preserves the initial review and findings as an audit trail; its requested fixes have now been completed and verified.

## Initial version reviewed

At the start of inspection, `paper/main.pdf` had SHA-256:

`229adc65bad287d58ff1e4aff35c3fe3cd229e328d7f5da22140cbe841784376`

The supplied render directory was `tmp/nhs_pdf_qa/` in the parent workspace, with `page-12.png` through `page-23.png`. The PDF was updated while this audit was underway; the subsequent hash `b54465e9c8c2777daad879d7180ef211b23634684e96d4d6eed6acaaeaa02817` is **not automatically covered** by the initial visual observations. A final render must be checked after the reported changes.

## Initial observations by page

| Page | Content inspected | Visual finding |
|---:|---|---|
| 12 | Figure 1, empirical narrative and subsection transitions | Both panels and labels are readable; captions and text remain inside margins. No overlap. |
| 13 | Figure 2, Table 4, continued empirical narrative | Bars, legend and axis labels are legible. Table is complete on one page. No clipping. |
| 14 | Figure 3 and simulation design | Both panels, logarithmic ticks, labels and caption are legible. Section transition is clean. |
| 15 | Table 5, Figure 4, pooling narrative | Complete table; all three heatmaps, axis labels and colour scale are readable. No column collision. |
| 16 | Figure 5, conditional-rebound narrative, next section | The **175.5** annotation in the right panel overlaps the area occupied by the third legend's green line segment. Move the annotation to the left of the vertical dashed line, clear of the legend. Other text and page placement are sound. |
| 17 | Implications, limitations and data/code statement | Paragraph spacing, headings, continuation and margins are sound. |
| 18 | AI statement and references | References are legible. The final NHS workbook reference splits across the page boundary in the middle of its URL; keeping this bibliographic entry together would improve readability. |
| 19 | Reference continuation and Appendix A.1 | The first line continues the split URL from page 18. Appendix equations, integral and paragraph layout are otherwise intact. |
| 20 | Appendices A.2–A.4 | Display and inline equations are readable and within margins; no overlapping subscripts or broken symbols observed. |
| 21 | Appendices A.5–A.6 and Table 6 | Probability formula, rank-path discussion and complete empirical table are legible. |
| 22 | Table 7, stress section and Table 8 | Both tables are complete. The stress table uses compact but readable type; all five columns fit, with no row splitting or clipping. |
| 23 | Stress continuation and reproducibility appendix | Continuation, heading and final paragraphs are readable, with a normal final-page margin. |

No further actual layout defects were identified in this page range. In particular, Figures 1–4 do not need larger labels solely to satisfy this audit, and the pressure-test table does not need a page split.

## Initially requested fixes — now resolved

1. Move Figure 5's crossover annotation away from the right-panel legend. One suitable placement is just left of the dashed line, right-aligned and above the plotted curves.
2. Prefer keeping each reference entry together across pages, particularly the NHS workbook entry. This is a smaller readability issue than the figure overlap.

The lead analyst received both findings. This reviewer did not edit the manuscript or figures.

## Render fingerprints

These identify the exact supplied page images inspected, even if the working PDF changes:

```text
12 c941c4ee1f1ac58afd85e585c6bd5d460fa710cf34983e73e038570865fb5391
13 56c9299f365c39207464e0ad990c2fcd7ffe878c159d153e09e57aabfddc8dd8
14 7c656ccec849b09bbb0071c45ed9a0c532c8507355cc925334abfbbcd107d7e3
15 4ba608ec39944de9e75faef4f5ce9df52de2731f48e7ea921eff69a30c3c6e2f
16 8f7918ecfb2dd674e4fd94671ce4ec26506b1f65fa4fdc23b66a6c1ea677b1b5
17 9ca067543729aa7b944025f1e08b21b5d1aa2e09bd1c3896aceed0e88040e9a0
18 003337e761eee262c54ec6f3f1bd878850415f53e18cefc1fa1a2037c74db960
19 8ecacb636a2d58ffa3511b91ef9ec00ad6c5925cc085977fed494afe9ef233e6
20 75b9c9f50563e59979c4b6448e944a76d082ed6aa84c2d627c476abb8a13c7f0
21 5331cfaa6195e220049bac8f71585f14768ae65ef223c09547392d6bf7afbfb8
22 7cd3664c17ad88dde36d7c0432e7bd3db4e43a6dee5c8bf813a52dd874ccfc38
23 2684b824e815e6d5f145fea8e7a6751cde4b571a97f013f2a5cdff14f176b4a0
```
