# Phase 7: Final results audit

**Date:** 2026-11-05.

**Scope:** every derived report was read and its key numerical claims were recomputed from the primary result files:
- `report/preliminary_results_report.md`: the Phase 4B full run, including the supplementary AC section §9
- `report/phase5_linux_build_report.md`
- `report/phase6_visual_evaluation_report.md`
- `report/phase6_summary_for_prof_kiho.md`
- the new Q&A document

The primary data were only read; none was modified.

**Method:** `scripts/audit_claims.py` recomputes each claim from the primary files below and records PASS or FAIL together with the recomputed values.
- `results/full/results.csv`, `config_summary.csv`, `timing_variability.csv`, `analysis_summary.json`
- `results/supp_ac/`
- `results/phase5_linux/`
- `visual/phase6/`

**Result files:**

| File | Contents |
|---|---|
| `results/audit/claims_audit_pre_correction.md` | first run: 24/26 PASS |
| `results/audit/claims_audit.md` | after corrections: **28/28 PASS**, including two claims added during the audit |
| `logs/phase7_01_claims_audit.log`, `logs/phase7_02_claims_audit_post_correction.log` | audit logs |

Copies of the reports as they were before the audit are kept in `report/_pre_audit/`.

---

## 1. The apparent inconsistency (Phase 4B vs Phase 6)

**Observation:**
- **Phase 4B:** `slower` improves Y-PSNR by about 0.24–0.38 dB and reduces size by 1.5–4.3%.
- **Phase 6:** `slower` gives +0.84–0.98 dB and 13–15% smaller files.

**Finding:** this is **not a contradiction**. The two statements use a different reference preset and a different set of sequences. Both are sequence-level values (mean of per-frame PSNR over all frames; total bitstream bytes) at QP 32.

| Statement | Reference → target | Sequences | Level | Recomputed values |
|---|---|---|---|---|
| Phase 4B | **medium** → slower | all 4 | sequence | +0.3747 / +0.2963 / +0.3280 / +0.2389 dB; 2.20 / 1.51 / 4.31 / 3.59% smaller |
| Phase 4B (also stated) | **faster** → slower | all 4 | sequence | +0.843 / +0.955 / +0.979 / +0.687 dB; 13.10 / 7.35 / 14.65 / 15.27% smaller |
| Phase 6 | **faster** → slower | BasketballPass, BQMall | sequence | +0.843 / +0.979 dB; 13.10 / 14.65% smaller |
| Phase 6 | faster → slower | 6 selected frames | **frame** | 0.24 – 1.31 dB |

The sequence order in the four-value rows is BasketballPass / BlowingBubbles / BQMall / BasketballDrive.

The Phase 6 sequence-level numbers are a subset of the Phase 4B `faster` → `slower` numbers and agree exactly.

**Correction made:** the Phase 6 summary now states both comparisons explicitly and labels each one sequence-level or frame-level:
- `faster` → `slower`: +0.84 / +0.98 dB, 13.1% / 14.6%
- `medium` → `slower`: +0.37 / +0.33 dB, 2.2% / 4.3%

In checking this, the Phase 4B upper bound "+0.38 dB" was found to be imprecise. The measured maximum is 0.3747 dB, so it was corrected to **+0.37 dB** (§2, item 2).

---

## 2. Corrections made (original wording preserved in `report/_pre_audit/`)

| # | Report | Before | After | Evidence |
|---|---|---|---|---|
| 1 | preliminary_results_report.md §3.2 | `faster` → `medium` costs "7.7–9.1×" the time | **7.7–9.5×** | BlowingBubbles 9.51× (config_summary.csv, encoder-reported medians) |
| 2 | preliminary_results_report.md §3.2 | `medium` → `slower` "+0.24 to +0.38 dB" | **+0.24 to +0.37 dB** | max 0.3747 dB (BasketballPass) |
| 3 | preliminary_results_report.md §3.1 | 240p decoding "1,400–2,900 fps" | **1,400–3,100 fps** | BlowingBubbles QP 37: 3,067 fps; BasketballPass QP 37: 2,924 fps |
| 4 | phase6_summary_for_prof_kiho.md | "IDR at QP 27 vs the top temporal layer at QP 42 for `-q 32`" (no sequence given) | IDR at slice QP **27 (BasketballPass) or 29 (BQMall)**; top layer QP **41–42** | encoder logs via visual/phase6/analysis.json |
| 5 | phase6_visual_evaluation_report.md §4.1 | "the IDR picture is coded at slice QP 27" | made sequence-specific (BasketballPass 27, BQMall 29) | same |
| 6 | phase6_summary_for_prof_kiho.md | sequence-level preset gain given only for `faster` → `slower` | `faster` → `slower` and `medium` → `slower` both stated; sequence vs frame level labelled; link to the Phase 4B figure | §1 |
| 7 | phase6_summary_for_prof_kiho.md | mechanism of preset-dependent slice QPs stated as fact | labelled a **hypothesis** from static source reading. Measured part kept: medium and slower have identical slice QPs. | visual/phase6/analysis.json |
| 8 | scripts/audit_claims.py (the audit itself) | the first check of the +0.38 dB claim accepted either 0.37 or 0.38 | tightened to the exact rounded values; this is what exposed item 2 | – |

No measurement in any primary result file was changed. All 28 recomputed claims now PASS.

---

## 3. Claims checked and found correct (selection; full list in `results/audit/claims_audit.md`)
- **Verification:** 65/65 runs ok; 32/32 repeats byte-identical; independent PSNR = encoder PSNR (max |Δ| 0.0000 dB).
- **QP sweep:** bitrate ÷1.91–2.35 per +5 QP (median 2.06); Y-PSNR −1.45 to −3.93 dB per +5 QP; QP 22 takes 2.7–3.7× as long as QP 37.
- **Encode vs decode:** encoding 133–333× slower than decoding (preset medium); 1080p decoding 134–220 fps.
- **Preset time ratios vs medium:** faster 0.11–0.13×; fast 0.27–0.30×; slow 3.25–3.71×; slower 14.4–17.1×.
- **Other Phase 4B claims:** BlowingBubbles `fast` 0.58% smaller than `medium` with −0.44 dB; encode CV median 2.4%; battery interval 14:27:34–15:31:17 with 11 exposed runs.
- **Supplementary AC differences:** −18.71 / −2.39 / +0.87 / −2.82%; all AC-valid and bitstream-identical.
- **Phase 5:** Windows = Linux bitstream, reconstruction and PSNR for the 16-frame smoke test.
- **Phase 6:** QP 22 → 37 frame drops of 9.8–10.2 dB (BasketballPass) and 7.9–8.7 dB (BQMall); BasketballPass `medium` < `faster` in 67 frames, all with more bits spent by `faster`; average slice-QP offsets of I pictures −2.7 to −3.6 and B pictures +5.7 to +8.6.

---

## 4. Evidence categories used in the deliverables
- **Sequence-level metrics:** mean of per-frame PSNR over all frames and total bytes. Phase 4B tables and charts, slides 8–10.
- **Frame-level metrics:** six selected frames (Phase 6, slide 11), and the all-frames per-picture analysis of presets (Phase 6 §5.2).
- **Measured results:** everything computed from the YUV files, bitstreams and logs.
- **Preliminary visual interpretation:** Claude's inspection of rendered crops (Phase 6 §4.1 and §5.1). It is labelled and is not presented as a confirmed observation.
- **User-confirmed observation:** exactly one, for BasketballPass frame 133: "QP22 appeared clearest and QP37 appeared blurriest" (slide 11, Phase 6 report).
- **Hypotheses:** labelled wherever they occur:
  - the cause of the BQMall `faster` AC timing difference (battery turbo limits)
  - the cause of the "originals slower than repeats" effect (time of session)
  - preset-dependent slice QPs via MCTF / BIM / GOP-QPA
  - learned fast encoding as future work

---

## 5. Unresolved limitations (not fixable without new experiments)
1. **No BD-rate.** Presets were compared at a single QP (32). Preset efficiency is therefore not established.
2. **Timing on one laptop:** hybrid CPU; one sample for BQMall and BasketballDrive; a 64-minute battery period. Four affected configurations were re-measured on AC once, in a different session.
3. **8-bit-precision content** in a 10-bit container.
4. **Linux via WSL2**, not native. Cross-platform identity was verified for one 16-frame configuration only.
5. **Visual evaluation is not a formal subjective study.** One user-confirmed observation; the rest is automated metrics plus preliminary interpretation. Enlarged still frames only; no playback.
6. **Simplified metrics:** SSIM uses an 8×8 uniform window; the detail ratio is a Laplacian proxy; no VMAF, XPSNR or blocking/ringing metric.
7. **Thermal sensor:** the ACPI thermal zone is not a core sensor (plateau at 91.9 °C).
8. **Hypervisor now active** on Windows. Future Windows timing is not comparable with the recorded runs.
9. **VVdeC conformance tests** (JVET bitstreams) were not run on either platform.
10. **Source-code reasoning** about preset QP adaptation was not instrumented.

---

## 6. Deliverables produced in Phase 7

| Deliverable | File |
|---|---|
| Editable presentation (15 slides: 14 content + references) | `presentation/VVC_Experimental_Evaluation_Prof_Kiho.pptx` |
| PDF version (exported by Microsoft PowerPoint) | `presentation/VVC_Experimental_Evaluation_Prof_Kiho.pdf` |
| Speaker notes (also inside the .pptx) | `presentation/speaker_notes.md` |
| Likely questions and answers | `report/phase7_professor_QA.md` |
| This audit report | `report/phase7_final_audit_report.md` |
| Slide renders used for visual QA | `presentation/render/slide-01.png` … `slide-15.png` |
| Build and export scripts | `presentation/build_deck.py`, `presentation/export_with_powerpoint.ps1`, `scripts/make_deck_assets.py` |

**Deck build and checks:**
- All numbers on the slides are read from the result files at build time; none is typed by hand.
- The figures are the verified Phase 4B charts and YUV-rendered crops and thumbnails. No stock images are used.
- The deck passed the OOXML validator ("All validations PASSED").
- No leftover placeholder text was found.
- Every slide carries speaker notes.
- All 15 slides were rendered by PowerPoint and inspected. Overlap and clipping problems found in the first render (slides 1, 3, 5, 6, 10, 12, 13) were fixed and re-checked.

**Preservation check (SHA256 fingerprints, identical to the values recorded in earlier phases):**
- `results/full` `44eb11e4…2c47` (136 files)
- `results/supp_ac` `a496a22a…b485`
- `results/smoke` `9331bb27…19ff`

**Environment change in this phase:** `python-pptx` 1.0.2, `defusedxml`, `lxml` and `XlsxWriter` (installed as a python-pptx dependency) were installed into the project's own `.venv` (log: `logs/phase7_03_pip_python_pptx.log`). Nothing was installed system-wide.

Nothing was sent to the professor or anyone else.

---

## Addendum: Phase 8 (final presentation preparation, 2026-11-05)

**Title slide:**
- Name: Rabab Khan Rongon
- Degree: M.Sc. in Computer Science and Engineering (Major: Artificial Intelligence)
- University: Military Institute of Science and Technology (MIST), Bangladesh

**Structure:** the 15-slide structure is unchanged.

**Accuracy fixes in the deck:**
- **Citations:**
  - [1], [5], [6] and [8] are now cited where they are used.
  - Slide 14 wrongly cited "[4], [6]" for JVET common test conditions; it now cites only [4] (BD-rate).
- **References verified online (DOIs added):**
  - [2] IEEE TCSVT vol. 31, no. 10, pp. 3736-3764, Oct. 2021, doi:10.1109/TCSVT.2021.3101953
  - [3] ICMEW 2021, Shenzhen, doi:10.1109/ICMEW53276.2021.9455944
- **Slide 7:** the FFmpeg cross-check is now attributed to the Phase 3 smoke test only.
- **Slide 8:** the message now states the exact range 1.45-3.93 dB (it was previously rounded to 1.5-3.9).
- **Slide 11:**
  - The message no longer states preliminary visual impressions as general facts. It now states only the observer-confirmed BasketballPass result and the PSNR/SSIM agreement.
  - The BQMall row is labelled "automated metrics + preliminary interpretation".
- **Slide 14:** the future-research block is now titled "directions, not completed work". Its research question uses the measured 14-17x slower-preset time cost.

**Speaker notes:**
- Rewritten in short, simple sentences for a non-native speaker.
- All numbers are inserted from the result files at build time.
- Length: 1,493 words, about 12-14 minutes.

**New deliverables:**
- 5-minute deck `presentation/VVC_Experimental_Evaluation_Prof_Kiho_5min.pptx` / `.pdf`: slides 1, 6, 8, 10, 11, 12 and 14, renumbered, with their own 505-word notes.
- `presentation/five_minute_outline.md`
- `presentation/speaker_notes_5min.md`
- `report/phase8_top10_QA.md`: the 10 most important questions, plus a section on how the assignment connects to possible future research.

**Checks:**
- Both decks pass the OOXML validator.
- All 15 + 7 slides were rendered with Microsoft PowerPoint and inspected.
- No leftover placeholder text.
- Audit re-run: 28/28 PASS.
- Fingerprints of `results/full`, `results/supp_ac`, `results/smoke` and `results/phase5_linux` are unchanged.
- No experimental result or raw data was modified.
- Nothing was sent to anyone.
