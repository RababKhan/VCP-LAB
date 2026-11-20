# YUView comparison workflow (Phase 6)

YUView: `tools/YUView/YUView.exe` (v2.14). All files to open are in `visual/yuview/`. These are hard links to the verified files in `dataset/` and `recon/full/`, so no data was copied. Their names encode the format so YUView can detect it: `<Sequence>_<variant>_<W>x<H>_<fps>fps_10bit_420.yuv`.

## 1. Load files
- Drag the `.yuv` files from `visual/yuview/` into the **Playlist** panel, or use File > Open.
- For each loaded file, check its **Properties** panel:
  - Width × height: 416 × 240 (BasketballPass) or 832 × 480 (BQMall)
  - Frame rate: 50 (BasketballPass) or 60 (BQMall)
  - YUV format: 4:2:0, 10 bit, little-endian (planar YUV, 16-bit samples)
  - Frame count: 501 / 601 for the originals (the last frame is the copyright card), 500 / 600 for the reconstructions
- If the detected format differs, set these fields by hand.

## 2. Frame alignment
- Frame index *i* in a reconstruction is frame *i* of the original. This was verified numerically: best offset = 0 for every file.
- Do **not** set a start offset.
- YUView counts frames from 0, as do the frame indices in this study.

## 3. Compare
- **Single view:** select one playlist item. Move between frames with the frame slider or frame number box, or with the arrow keys.
- **Side-by-side / split view:** switch the view to the split (two-pane) mode. Then select the original for one pane and the reconstruction for the other.
  - In split view both panes show the same frame index, and zoom/pan are synchronised by default.
  - Comparison mode shows one image with a movable divider.
- **Switching original ↔ reconstruction:** in single view, click the two playlist items alternately at the same frame. Flicker comparison is the most sensitive way to see small differences.
- **Zoom:** mouse wheel; pan by dragging. Use the same zoom for every variant. Suggested: 3–4×, at the crop positions in `visual/rendered/crops.json`.
- **Difference image (optional):** create a difference item from two selected playlist items. This shows where the errors are, not how visible they are.
- **Screenshot:** YUView can save the current view as an image (File menu). Name screenshots `<seq>_f<frame>_<variant>.png` and save them in `visual/screenshots_yuview/`.

## 4. What to compare (same frames for every variant)

| Sequence | Frame | Why this frame (fixed rule) | Crop (x, y, w, h) |
|---|---|---|---|
| BasketballPass | 15 | first IDR (intra) picture | 232, 88, 104, 80 |
| BasketballPass | 133 | QP 32 / medium frame PSNR closest to the sequence mean | 176, 88, 104, 80 |
| BasketballPass | 370 | lowest QP 37 / medium frame PSNR | 312, 104, 104, 80 |
| BQMall | 31 | first IDR (intra) picture | 504, 240, 160, 120 |
| BQMall | 441 | QP 32 / medium frame PSNR closest to the sequence mean | 376, 200, 160, 120 |
| BQMall | 42 | lowest QP 37 / medium frame PSNR | 56, 232, 160, 120 |

- **QP set:** Original vs QP 22 / 32 / 37 (medium).
- **Preset set:** Original vs faster / medium / slower (QP 32).
- **Look for:** loss of fine detail, blurring, blocking, ringing near sharp edges, texture loss, and motion artefacts. For motion artefacts, also play a few frames around the chosen frame.

Record what you actually see in `visual/visual_evaluation_record.csv`, column `user_confirmed_observation`. Write "no visible difference" where that is the case.
