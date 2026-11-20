# Phase 6: Visual quality evaluation (QP and preset)

**Status:** completed 2026-11-05 as an **automated, evidence-based analysis**, at the user's request (no further manual YUView inspection). The findings carry three labels:
- **[measured]:** computed from the YUV data or the encoder logs.
- **[user-confirmed]:** stated by the user. There is exactly one such statement (§4.1).
- **[preliminary interpretation]:** Claude's inspection of the generated images. These are not user-confirmed and are not a formal subjective test.

**Inputs:** verified reconstructions from the Phase 4B full run. Nothing was re-encoded and no existing result was modified (§8).

---

## 1. Samples and verification [measured]

| Sequence | Resolution / fps | Variants | Frames per file |
|---|---|---|---|
| BasketballPass | 416×240, 50 fps | QP 22 / 32 / 37 at `medium`; `faster` / `slower` at QP 32 | 500 (original file: 501 incl. copyright frame) |
| BQMall | 832×480, 60 fps | same | 600 (original: 601) |

Every reconstruction was re-verified by `scripts/prepare_visual.py` (log: `logs/phase6_01_prepare_samples.log`):
- file size = frames × frame size (10-bit 4:2:0, 16-bit little-endian)
- SHA256 recorded (`visual/sample_manifest.json`)
- PSNR recomputed over all frames, and equal to the stored Phase 4B values
- bitstream SHA256 equal to results.csv
- frame alignment offset 0
- original SHA256 equal to the manifest

For YUView, hard links with format-encoding names were created in `visual/yuview/`. No data was copied. A step-by-step guide is in `visual/YUVIEW_GUIDE.md`.

### 1.1 Frame selection (fixed rules, same frames for every variant)

| Sequence | Frame | Rule | Picture type (all presets) |
|---|---|---|---|
| BasketballPass | 15 | first IDR picture | IDR_W_RADL, TId 0 |
| BasketballPass | 133 | QP 32 / medium frame Y-PSNR closest to the sequence mean | STSA B, TId 4 |
| BasketballPass | 370 | lowest QP 37 / medium frame Y-PSNR (non-intra) | STSA B, TId 5 |
| BQMall | 31 | first IDR picture | IDR_W_RADL, TId 0 |
| BQMall | 441 | QP 32 / medium frame Y-PSNR closest to the sequence mean | STSA B, TId 4 |
| BQMall | 42 | lowest QP 37 / medium frame Y-PSNR (non-intra) | STSA B, TId 5 |

**Crop rule:** the window (104×80 for BasketballPass, 160×120 for BQMall) with the largest QP 37 / medium luma squared error in that frame. The same window is used for every variant (`visual/rendered/crops.json`).

---

## 2. Method

### 2.1 Display conversion (identical for every image)
- 10-bit → 8-bit by right shift of 2. The content is 8-bit precision padded to 10 bit (Phase 4A), so no information is lost.
- YCbCr BT.709 limited range → sRGB. This is an assumption, because the files carry no colour metadata; it affects all panels equally.
- Chroma upsampled by pixel repetition.
- Enlargement by pixel repetition (no smoothing, so coding artefacts are not hidden).
- Implementation: `scripts/render_visual_crops.py` (`to_rgb`), reused by `scripts/analyze_visual.py`.

### 2.2 Difference maps
- Value shown: |Y_rec − Y_orig| in 10-bit code values (luma only).
- Linear scale, fixed for every map: white = 0, black ≥ 64 (clipped). 64 code values are 16 in 8-bit terms. A colour bar is drawn in every figure.
- A difference map shows **where** the samples differ numerically. It does not show whether a difference is visible.

### 2.3 Objective metrics (per frame, full frame and crop; `visual/phase6/tables/frame_metrics.csv`)
- **PSNR:** Y, U and V PSNR (peak 1020, as in Phases 3–5). The frame values are identical to the stored per-frame values (all 30 checks pass).
- **Differences:** mean and maximum |dY|, and the share of luma pixels with |dY| > 16 and > 64.
- **SSIM-Y:** luma SSIM with an 8×8 uniform window, L = 1023. This is a simplified SSIM, not the Gaussian-window reference implementation.
- **Detail-retention ratio** = mean |Laplacian(rec)| / mean |Laplacian(orig)|. Values below 1 mean that high-frequency energy was removed, i.e. smoothing or blurring. Ringing or noise can raise it again, so it is not a pure blur measure.

### 2.4 Preset investigation over all frames
- Per-picture slice QP, bits, temporal ID and Y-PSNR were taken from the encoder logs (`logs/runs/full/*_enc.log`).
- The encoder's per-picture Y-PSNR equals the independent per-frame PSNR for every frame (maximum difference 0.0).

---

## 3. Figures

All figures are in `visual/phase6/figures/`.

**Comparison figures:** each has four rows:
1. full frame, crop marked
2. full-frame |dY| map
3. enlarged crop
4. enlarged-crop |dY| map

Each panel is labelled with frame Y-PSNR, SSIM, mean |dY| and detail ratio.

| Set | Figures |
|---|---|
| QP comparison (medium) | `BasketballPass_qp_frame015/133/370_*.png`, `BQMall_qp_frame031/441/042_*.png` |
| Preset comparison (QP 32) | `BasketballPass_preset_frame015/133/370_*.png`, `BQMall_preset_frame031/441/042_*.png` |
| Metric charts | `selected_frames_ssim.png`, `selected_frames_detail_ratio.png`, `preset_per_frame_psnr_delta.png` (all frames) |

- Earlier simple strips (crop only and full frame, without difference maps) are in `visual/rendered/`.
- Suggested presentation figures are copied to `visual/phase6/presentation_candidates/`.

**Image inspection by Claude:**
- All 12 crop strips in `visual/rendered/`, and one full-frame strip.
- The composite figures `BasketballPass_qp_frame133`, `BasketballPass_preset_frame370` and `BQMall_qp_frame042`.
- The three metric charts.

The other nine composite figures were generated by the same code from the same crops but were not individually opened.

---

## 4. QP comparison (preset medium)

### 4.1 Results

| Sequence | Frame | Y-PSNR QP 22 / 32 / 37 (dB) | SSIM-Y QP 22 / 32 / 37 | Detail ratio QP 22 / 32 / 37 | Pixels with \|dY\|>16, QP 22 / 32 / 37 |
|---|---|---|---|---|---|
| BasketballPass | 15 (IDR) | 45.44 / 38.85 / 35.60 | 0.989 / 0.953 / 0.913 | 0.924 / 0.797 / 0.665 | 0.8 / 13.2 / 25.8 % |
| BasketballPass | 133 | 40.79 / 33.28 / 30.55 | 0.976 / 0.908 / 0.845 | 0.842 / 0.638 / 0.469 | 7.4 / 28.7 / 40.0 % |
| BasketballPass | 370 | 37.62 / 30.41 / 27.68 | 0.965 / 0.862 / 0.780 | 0.787 / 0.524 / 0.387 | 17.1 / 44.3 / 55.3 % |
| BQMall | 31 (IDR) | 41.53 / 36.74 / 33.61 | 0.979 / 0.957 / 0.929 | 0.851 / 0.776 / 0.702 | 5.7 / 20.9 / 31.0 % |
| BQMall | 441 | 40.67 / 35.17 / 32.55 | 0.975 / 0.943 / 0.912 | 0.685 / 0.570 / 0.499 | 7.9 / 22.4 / 30.6 % |
| BQMall | 42 | 38.28 / 32.31 / 29.58 | 0.969 / 0.917 / 0.864 | 0.809 / 0.698 / 0.591 | 14.7 / 33.6 / 42.5 % |

Sequence-level sizes: BasketballPass 1,430,459 / 325,445 / 166,829 B; BQMall 3,246,923 / 760,913 / 397,582 B.

- **[measured]** In all six frames, every metric worsens monotonically from QP 22 to QP 32 to QP 37: PSNR, SSIM, the detail-retention ratio (on both full frame and crop) and the share of large differences.
  - The QP 22 → 37 frame PSNR drop is 9.8–10.2 dB (BasketballPass) and 7.9–8.7 dB (BQMall).
  - The sequence bitstream shrinks 8.2–8.6×.
- **[measured]** The detail-retention ratio falls to 0.39–0.70 at QP 37. Between a third and two thirds of the original high-frequency energy is gone. The largest losses are in the moving-content frames (BasketballPass 370: 0.387; 133: 0.469), the smallest in the intra frames.
- **[measured]** Inter frames lose more than intra frames at the same `-q`. For example, BasketballPass frame 15 (IDR) has 35.60 dB at QP 37, frame 370 has 27.68 dB. This matches the hierarchical slice QPs: the IDR picture is coded at slice QP 27 for `-q 32`, a TId 5 picture at QP 42 (encoder log).
- **[user-confirmed]** BasketballPass frame 133: "QP22 appeared clearest and QP37 appeared blurriest." The metrics for this frame rank the same way: SSIM 0.976 > 0.908 > 0.845, detail ratio 0.842 > 0.638 > 0.469.
- **[preliminary interpretation]**, from the enlarged crops; not user-confirmed:
  - **QP 22:** close to the original at 3–4× enlargement.
  - **QP 32:** fine textures are smoothed (wood grain, knitwear). Thin structures disappear (a thin vertical line and a small grey object on the wall in BasketballPass frame 370). Lettering on moving players is softened.
  - **QP 37:** strong blurring and smearing of moving objects: the ball and shorts number in BasketballPass frame 133, the moving woman in BQMall frame 42. Faces are blurred (BQMall frame 31). There are blotchy, smeared patches in motion regions.
  - **Not observed:** clear ringing at edges and regular block-grid artefacts. Their absence is not proven, because no dedicated ringing or blocking metric was computed.

---

## 5. Preset comparison (QP 32)

### 5.1 Selected frames

| Sequence | Frame | Y-PSNR faster / medium / slower (dB) | SSIM-Y faster / medium / slower | Slice QP faster / medium / slower | Picture bits faster / medium / slower |
|---|---|---|---|---|---|
| BasketballPass | 15 (IDR) | 38.10 / 38.85 / 39.00 | 0.949 / 0.953 / 0.955 | **28** / 27 / 27 | 53,984 / 51,752 / 51,224 |
| BasketballPass | 133 | 32.75 / 33.28 / 33.87 | 0.898 / 0.908 / 0.915 | 40 / 40 / 40 | 3,216 / 2,800 / 3,016 |
| BasketballPass | 370 | **30.55** / 30.41 / 30.79 | **0.864** / 0.862 / 0.870 | **41** / 42 / 42 | 3,000 / 2,776 / 2,744 |
| BQMall | 31 (IDR) | 36.48 / 36.74 / 36.90 | 0.955 / 0.957 / 0.958 | 29 / 29 / 29 | 229,960 / 202,312 / 201,216 |
| BQMall | 441 | 34.78 / 35.17 / 35.48 | 0.938 / 0.943 / 0.945 | 40 / 40 / 40 | 5,584 / 4,944 / 4,648 |
| BQMall | 42 | 31.51 / 32.31 / 32.82 | 0.904 / 0.917 / 0.922 | 42 / 42 / 42 | 3,432 / 3,400 / 3,128 |

Sequence-level values:

| | BasketballPass faster / medium / slower | BQMall faster / medium / slower |
|---|---|---|
| Y-PSNR (dB) | 32.84 / 33.30 / 33.68 | 34.51 / 35.16 / 35.49 |
| Bytes | 366,257 / 325,445 / 318,273 | 853,056 / 760,913 / 728,106 |

- **[measured]** In 5 of the 6 frames, PSNR and SSIM rank faster < medium < slower.
  - The faster → slower spread per frame is 0.24–1.31 dB. This is an order of magnitude smaller than the 7.9–10.2 dB spread of the QP comparison.
  - The exception is BasketballPass frame 370 (§5.2).
- **[measured]** The detail-retention ratio does **not** rank consistently with the presets. For example, BasketballPass 133: faster 0.599, medium 0.638, slower 0.613; BQMall 31: faster 0.789 is the highest. The differences are small (≤ 0.04), and the ratio also responds to artefact energy. It is therefore not used to rank presets.
- **[preliminary interpretation]**, from the enlarged crops; not user-confirmed:
  - **Intra frames (BasketballPass 15, BQMall 31):** `faster`, `medium` and `slower` are hard to tell apart at 3–4× enlargement.
  - **Motion frames:** `faster` shows somewhat more smearing or colour distortion (the ball in BasketballPass 133; the arm region in BQMall 42). `medium` and `slower` look very similar; any difference is small or uncertain.
  - These are numerical differences of 0.15–0.59 dB between medium and slower, with **no clearly visible difference** in the inspected crops.

### 5.2 Investigation: when does a slower preset have lower PSNR than a faster one? [measured]
Counted over all frames of each sequence (QP 32, `scripts/analyze_visual.py` → `visual/phase6/analysis.json`).

| Sequence | Comparison | Frames where the slower preset is lower | Of these: faster preset had a lower slice QP | same slice QP | faster preset spent more bits | Median / max deficit |
|---|---|---|---|---|---|---|
| BasketballPass (500) | medium < faster | 67 (13.4%) | 59 | 8 | **67 (all)** | 0.22 / 0.92 dB |
| | slower < medium | 4 (0.8%) | 0 | 4 | **4 (all)** | 0.07 / 0.63 dB |
| | slower < faster | 18 (3.6%) | 17 | 1 | **18 (all)** | 0.22 / 0.64 dB |
| BQMall (600) | medium < faster | 1 (0.2%) | 1 | 0 | **1** | 0.19 dB |
| | slower < medium | 3 (0.5%) | 0 | 3 | **3 (all)** | 0.04 / 0.19 dB |
| | slower < faster | 0 | – | – | – | – |

**Findings:**
1. **[measured]** In every frame where a slower preset had a lower PSNR than a faster one, the faster preset had spent **more bits on that picture**. So none of these cases is a "better quality for fewer bits" result for the faster preset. They are local rate–distortion trade-offs. At sequence level, the slower presets give both higher PSNR and fewer bytes (§5.1).
2. **[measured]** The presets do not always use the same slice QP for the same picture.
   - `faster` and `medium` differ in slice QP in 138 of 500 pictures (BasketballPass) and 60 of 600 (BQMall).
   - `medium` and `slower` differ in **0** pictures in both sequences.
   - Most cases where `faster` beats `medium` (59 of 67 in BasketballPass) are pictures that `faster` coded at a lower slice QP. Frame 370 is one of them: QP 41 vs 42.
   - So the comparison "at QP 32" is not an identical-QP comparison at picture level. `-q 32` sets the base QP, and the encoder adapts the picture QPs.
3. **[measured]** An equal slice QP does not guarantee the ranking, but the bits always explain the exception.
   - Deficits also occur at equal slice QP: 8 of the 67 BasketballPass `medium` < `faster` frames, and all 4 + 3 `slower` < `medium` frames.
   - In every one of them the faster preset spent more bits on that picture.
   - Among the selected frames, those with an equal slice QP in all three presets (BasketballPass 133; BQMall 31, 441 and 42) rank faster < medium < slower in PSNR. BasketballPass 15 and 370 had a different slice QP for `faster`.
4. **Source-code observation [measured]** (read, not traced at run time):
   - With QPA disabled (`--qpa 0`), VVenC enables GOP-wise QP adaptation (`m_GOPQPA = 1`; `vvencCfg.cpp`, lines 1555–1558). This adjusts a GOP's QP by ±1 based on spatial visual activity and noise levels (`EncGOP.cpp`, lines 1807–1822).
   - All presets enable block-importance mapping (BIM) with MCTF. BIM produces a picture-level QP offset (`EncGOP.cpp`, line 107).
   - The presets differ in MCTF and motion-search settings: `faster` uses MCTFSpeed 4 and SearchRange 128; `medium` and `slower` both use MCTFSpeed 2 and SearchRange 384.
5. **[interpretation, consistent with the data but not proven]** The preset-dependent slice QPs most likely come from these analysis stages producing different QP offsets for `faster`. This is consistent with `medium` and `slower`, which share MCTF settings, having identical slice QPs in every picture. It was not verified by instrumenting the encoder.

`preset_per_frame_psnr_delta.png` plots the per-frame differences:
- `slower − medium` is positive in almost every frame (mostly about +0.1 to +0.6 dB).
- `faster − medium` is mostly negative (about −0.5 to −1 dB). It approaches zero or turns positive in BasketballPass frames of roughly 255–375, where `faster` coded several pictures at lower slice QPs.

---

## 6. Visual quality vs PSNR

| Situation | PSNR difference | Visibility | Basis |
|---|---|---|---|
| QP 22 vs QP 37 (same preset) | 7.9–10.2 dB per frame | clearly visible | **user-confirmed** for BasketballPass frame 133; preliminary interpretation for the other frames |
| QP 22 vs QP 32 | 4.8–7.5 dB per frame | visible as texture and fine-detail loss in enlarged crops | preliminary interpretation |
| faster vs medium vs slower (QP 32) | 0.24–1.31 dB per frame (0.84–0.98 dB sequence-level faster → slower) | small; mostly in motion regions for `faster`; medium vs slower not clearly distinguishable | preliminary interpretation |
| Intra pictures across presets | 0.42–0.90 dB | not clearly distinguishable at 3–4× enlargement | preliminary interpretation |

**Cases where a numerical difference is not clearly visible [preliminary interpretation]:**
- medium vs slower in every inspected frame (0.15–0.59 dB)
- all three presets in the two intra frames
- BasketballPass frame 370 across presets: PSNR 30.41–30.79 dB, and the PSNR ranking itself is not monotonic

In these cases the difference maps still show widespread non-zero differences (§2.2), and |dY| > 16 occurs in 43–44% of pixels for all three presets in frame 370. A numerical difference is therefore present, but it is not necessarily visible.

**Agreement between metrics [measured]:** in all six frames, PSNR and SSIM rank the variants identically, in both the QP set and the preset set. They also agree on the frame-370 exception: `faster` is slightly above `medium` in both. The simple detail ratio agrees for QP but not for presets.

---

## 7. Limitations
1. **No formal subjective test.** There was one user-confirmed statement, for one frame. All other visual statements are Claude's preliminary inspection of rendered images. That is not a calibrated viewer, a standard viewing setup (e.g. ITU-R BT.500), or a MOS.
2. **Enlarged crops, not normal viewing.** Differences seen at 3–4× pixel repetition may be invisible at 1× on a normal display, and frame-by-frame viewing does not show temporal artefacts such as flicker. No video playback was assessed.
3. **Six frames, two sequences, three QPs, three presets.** The QPs are those of the approved plan; QP 27 was not part of the visual set. The crop rule targets the worst QP 37 region, which favours visible degradation.
4. **Display conversion assumptions:** BT.709 limited range, nearest-neighbour chroma upsampling and 8-bit display. A different matrix (e.g. BT.601) changes colours slightly but equally for all variants.
5. **Metrics:** SSIM uses an 8×8 uniform window (not the reference Gaussian SSIM). The detail ratio is a simple Laplacian-energy proxy. No dedicated blocking or ringing metric and no perceptual metric (VMAF, XPSNR) were computed.
6. **Per-picture QP adaptation** (§5.2) means that "QP 32" is a base QP. Frame-level preset comparisons partly compare different slice QPs.
7. **Source-code reasoning in §5.2 is static.** The causal chain from MCTF/BIM settings to the slice QP was not instrumented.
8. **YUView screenshots were not produced.** The figures are rendered from the YUV data by the project scripts. The YUView workflow is documented (`visual/YUVIEW_GUIDE.md`) and the files are prepared for it.

---

## 8. Reproducibility and data preservation
```
.venv\Scripts\python.exe scripts\prepare_visual.py          # verify samples, YUView links, frame selection
.venv\Scripts\python.exe scripts\render_visual_crops.py     # simple crop / full-frame strips
.venv\Scripts\python.exe scripts\make_visual_record.py      # v1 record (preliminary notes)
.venv\Scripts\python.exe scripts\analyze_visual.py          # metrics, difference maps, composite figures, preset investigation
.venv\Scripts\python.exe scripts\make_visual_record_v2.py   # v2 record with evidence labels
```

**Outputs:**
- `visual/sample_manifest.*` and `visual/frame_selection.json`
- `visual/rendered/`
- `visual/phase6/` (`figures/`, `tables/frame_metrics.csv|.md`, `analysis.json`, `visual_evaluation_record_v2.csv`, `presentation_candidates/`)
- `visual/visual_evaluation_record.csv` (v1, unchanged). A superseded buggy v1 draft was kept in `visual/_superseded/`.
- Logs: `logs/phase6_*`

**Preservation:** `results/full/` fingerprint `44eb11e4…2c47` (136 files) is unchanged. Reconstructions and originals were only read; the YUView hard links do not modify them.
