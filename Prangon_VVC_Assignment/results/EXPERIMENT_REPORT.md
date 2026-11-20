# VVC Experiment Report: Sadab Khan Prangon

**Assignment:** VVC encoding and decoding with VVenC and VVdeC, for Prof. Kiho Choi, Video Coding and Processing Lab, Kyung Hee University.

**Date of execution:** 2026-11-11. **Project folder:** `D:\Korea\Prangon_VVC_Assignment`.

**Who did what:** every command in this report was executed by Claude, an AI assistant, on this computer at the user's request. The commands, outputs and logs are recorded in `logs/`. Sadab Khan Prangon has **not yet** personally performed or verified any step; see section 9.

## 1. Execution summary

| Phase | Status | Evidence |
|---|---|---|
| 1. Environment check | Completed | `logs/00_setup_provenance.log`, `results/environment.txt` |
| 2. Build: Windows (MSVC 19.44) | Completed. VVenC 32/39 tests passed; 7 **not run** (blocked by Smart App Control); VVdeC conformance tests **skipped** (test bitstreams not included) | `logs/build/02_*`, `05_*`, `06_*` |
| 2. Build: Linux (GCC 13.3, WSL2) | Completed. VVenC 39/39 tests passed; VVdeC unit test passed | `logs/build/03_*`, `07_*`, `08_*`, `09_*` |
| 2. Smoke test (16 frames, both platforms) | **Passed** | `logs/04_smoke_test.log` |
| 3. Full experiment (16 configurations + 2 repeats) | **Completed: 18/18 runs OK**, none failed or interrupted | `results/results_raw.csv`, `logs/runs/*.log`, `logs/10_full_run_console.log` |
| 4. Windows vs Linux | Completed: identical in 3 of 3 checks | `results/crossplatform.json`, `logs/11_*`, `logs/14_*` |
| 5. Visual evaluation | Partly done: same-frame crops rendered by script. **Not done:** YUView inspection and screenshots by Sadab | `visual/` |
| 6. Analysis and charts | Completed | `results/summary.json`, `results/charts/*.png` |
| 7. PowerPoint update | Completed except one item that only Sadab can write (slide 7 observation) | `presentation/` |

## 2. Setup

```
Recorded: 2026-11-11 11:21:59 +06:00
Computer: FARIASR
CPU: 12th Gen Intel(R) Core(TM) i7-1260P (12 cores, 16 threads)
RAM: 15.7 GB
OS: Microsoft Windows 11 Home Single Language 10.0.26200
Power: battery status code 2 (2 = on AC power), charge 49%
Power plan: Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e  (Balanced)
Threads used (-t): 8; decode repeats: 3; run-order seed: 2026
vvencapp version 1.14.0
vvdecapp.exe version 3.2.1
```

- **Sequences:** BlowingBubbles 416×240, 50 fps, 500 frames; BQMall 832×480, 60 fps, 600 frames. Both are 10-bit 4:2:0. The inputs were copied from the provided dataset folder and their SHA-256 hashes were verified (`logs/00_setup_provenance.log`).
- **Encoder settings:** `vvencapp -c yuv420_10 -q {24,29,34,39} --preset {fast,medium} --qpa 0 -t 8`; all other options are defaults.
- **Decoder:** `vvdecapp -t 8`. Each bitstream was decoded 3 times and the median time kept.
- **Run order:** shuffled with a fixed seed (2026), on AC power with the Balanced power plan. WSL was stopped during the Windows runs.
- **PSNR:** peak 1020, mean of the per-frame PSNR. The encoder's value was checked against the independent `experiment/psnr_check.py`.

## 3. Measured results (all 18 runs)

| Run | Sequence | QP | Preset | Encode time (s) | Decode time, median (s) | Bitstream (bytes) | Bitrate (kbps) | Y-PSNR (dB) | U / V-PSNR (dB) | Own-check Δ (dB) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R07 | BQMall | 24 | fast | 76.441 | 1.348 | 2,531,387 | 2025.11 | 39.0939 | 43.32 / 44.67 | 0.0000 | OK |
| R06 | BQMall | 29 | fast | 57.167 | 1.535 | 1,208,276 | 966.62 | 36.4110 | 41.48 / 42.42 | 0.0000 | OK |
| R02 | BQMall | 34 | fast | 34.882 | 1.087 | 601,320 | 481.06 | 33.6498 | 39.64 / 40.36 | 0.0000 | OK |
| R09 | BQMall | 39 | fast | 24.469 | 1.154 | 312,709 | 250.17 | 31.0090 | 37.92 / 38.50 | 0.0000 | OK |
| R14 | BQMall | 24 | medium | 233.052 | 1.380 | 2,376,924 | 1901.54 | 39.3636 | 43.57 / 44.99 | 0.0000 | OK |
| R15 | BQMall | 29 | medium | 150.545 | 1.421 | 1,149,316 | 919.45 | 36.7734 | 41.83 / 42.85 | 0.0000 | OK |
| R05 | BQMall | 34 | medium | 141.172 | 1.466 | 582,799 | 466.24 | 34.0773 | 40.01 / 40.74 | 0.0000 | OK |
| R01 | BQMall | 39 | medium | 84.718 | 2.772 | 308,911 | 247.13 | 31.4765 | 38.37 / 38.90 | 0.0000 | OK |
| R11 | BlowingBubbles | 24 | fast | 28.096 | 0.419 | 1,051,208 | 840.97 | 36.0044 | 40.16 / 41.17 | 0.0000 | OK |
| R10 | BlowingBubbles | 29 | fast | 19.975 | 0.353 | 487,898 | 390.32 | 32.8871 | 37.90 / 38.71 | 0.0000 | OK |
| R04 | BlowingBubbles | 34 | fast | 23.982 | 0.615 | 233,927 | 187.14 | 30.1374 | 35.89 / 36.60 | 0.0000 | OK |
| R17 (repeat of R04) | BlowingBubbles | 34 | fast | 13.236 | 0.338 | 233,927 | 187.14 | 30.1374 | 35.89 / 36.60 | 0.0000 | OK |
| R12 | BlowingBubbles | 39 | fast | 11.385 | 0.364 | 111,140 | 88.91 | 27.6509 | 34.30 / 34.96 | 0.0000 | OK |
| R03 | BlowingBubbles | 24 | medium | 122.094 | 0.716 | 1,016,655 | 813.32 | 36.3690 | 40.40 / 41.42 | 0.0000 | OK |
| R13 | BlowingBubbles | 29 | medium | 79.964 | 0.417 | 485,230 | 388.18 | 33.3299 | 38.17 / 38.97 | 0.0000 | OK |
| R16 | BlowingBubbles | 34 | medium | 48.579 | 0.359 | 235,433 | 188.35 | 30.5371 | 36.15 / 36.77 | 0.0000 | OK |
| R18 (repeat of R16) | BlowingBubbles | 34 | medium | 47.576 | 0.378 | 235,433 | 188.35 | 30.5371 | 36.15 / 36.77 | 0.0000 | OK |
| R08 | BlowingBubbles | 39 | medium | 43.913 | 0.399 | 112,934 | 90.35 | 27.9715 | 34.47 / 35.15 | 0.0000 | OK |

## 4. Analysis

### 4.1 Effect of QP (charts: `results/charts/qp_vs_bitrate.png`, `qp_vs_ypsnr.png`, `bitstream_size.png`)

- For each +5 QP step (12 steps in total), the bitrate was divided by **1.89–2.15** (median 2.08), and Y-PSNR fell by **2.49–3.12 dB** (median 2.69).
- BlowingBubbles, fast: from QP 24 to QP 39 the bitrate was divided by 9.46 and Y-PSNR fell by 8.35 dB.
- BlowingBubbles, medium: from QP 24 to QP 39 the bitrate was divided by 9.00 and Y-PSNR fell by 8.40 dB.
- BQMall, fast: from QP 24 to QP 39 the bitrate was divided by 8.10 and Y-PSNR fell by 8.08 dB.
- BQMall, medium: from QP 24 to QP 39 the bitrate was divided by 7.69 and Y-PSNR fell by 7.89 dB.

### 4.2 medium compared with fast at the same QP (charts: `encode_time.png`, `decode_time.png`)

| Sequence | QP | Encode time fast / medium (s) | Time ratio | Size change | Y-PSNR gain (dB) |
|---|---|---|---|---|---|
| BlowingBubbles | 24 | 28.10 (R11) / 122.09 (R03) | ×4.35 | -3.3 % | +0.36 |
| BlowingBubbles | 29 | 19.98 (R10) / 79.96 (R13) | ×4.00 | -0.5 % | +0.44 |
| BlowingBubbles | 34 | 23.98 (R04) / 48.58 (R16) | ×2.03 | +0.6 % | +0.40 |
| BlowingBubbles | 39 | 11.38 (R12) / 43.91 (R08) | ×3.86 | +1.6 % | +0.32 |
| BQMall | 24 | 76.44 (R07) / 233.05 (R14) | ×3.05 | -6.1 % | +0.27 |
| BQMall | 29 | 57.17 (R06) / 150.54 (R15) | ×2.63 | -4.9 % | +0.36 |
| BQMall | 34 | 34.88 (R02) / 141.17 (R05) | ×4.05 | -3.1 % | +0.43 |
| BQMall | 39 | 24.47 (R09) / 84.72 (R01) | ×3.46 | -1.2 % | +0.47 |

- medium took ×2.0–4.3 the encoding time of fast, and gave +0.27 to +0.47 dB Y-PSNR.
- The bitstream size changed by -6.1 % to +1.6 %. At one QP, medium therefore gives higher quality but not always a smaller file. These single-QP comparisons cannot measure compression efficiency; that needs BD-rate over the RD curves.
- The lowest time ratio (×2.03, BlowingBubbles QP 34) uses run R04. R04's repeat, R17, was 45 % faster (see 4.3). With R17 instead, the ratio would be ×3.67. Both values are reported, and R04 has not been replaced.
- Encoding took 21–192 times longer than decoding. The decode time includes writing the decoded YUV file to disk (about 720 MB for BQMall). Single decodes of BQMall occasionally took 5–6 s instead of about 1.3 s; the median of 3 limits, but does not remove, this disk effect.

### 4.3 Timing repeatability

- R17 repeated R04 (fast): 23.982 s, then 13.236 s, a difference of **44.8 %**. The bitstreams were identical: True.
- R18 repeated R16 (medium): 48.579 s, then 47.576 s, a difference of **2.1 %**. The bitstreams were identical: True.
- **Interpretation:** encoding time on this laptop can vary by tens of percent between runs. Only large differences (the factor of 2–4 between presets, the factor of 21–192 between encode and decode) are interpreted. Small differences, such as the non-monotonic fast-preset times for BlowingBubbles, are not interpreted.

## 5. Validation

- Runs with status OK: 16/16 main runs and 2/2 repeats. No run failed, was interrupted or was discarded.
- Decoded frame count equals the expected frame count in every run: True.
- The independent PSNR check matched the encoder's Y/U/V PSNR to within **0.0000 dB** in all runs.
- Bitrate from the file size and the encoder-reported bitrate differ by at most 0.0002 %.
- Repeated encodes produced byte-identical bitstreams.
- The smoke test (16 frames) passed on both platforms before the full run started.

## 6. Windows vs Linux verification

| Configuration | Size | Bitstream SHA-256 | Frames | Decoded-video SHA-256 | PSNR |
|---|---|---|---|---|---|
| BlowingBubbles QP 34 fast, 500 frames (Windows run R04) | same (233,927 B) | identical | same | identical | same |
| BQMall QP 29 medium, 600 frames (Windows run R15) | same (1,149,316 B) | identical | same | identical | same |
| BlowingBubbles QP 34 fast, 16 frames (smoke test) | – | identical | 16 | identical | same |

- **Result:** the MSVC (Windows) and GCC (Linux, WSL2) builds produced byte-identical bitstreams and decoded videos in 3 of 3 checks. Only these 3 configurations were compared across platforms.
- **Not compared:** speed. The Linux runs ran in WSL2 and read their input from `/mnt/d`.

## 7. Visual evaluation

- **BQMall, frame 432 (0-based), crop x,y,w,h = [280, 296, 208, 120]:** frame Y-PSNR 39.53 → 36.91 → 34.06 → 31.29 dB for QP 24 → 39 (medium). Images: `visual/BQMall_f432_qp_strip.png`.
- **BlowingBubbles, frame 365 (0-based), crop x,y,w,h = [312, 176, 104, 60]:** frame Y-PSNR 36.31 → 33.41 → 30.58 → 28.06 dB for QP 24 → 39 (medium). Images: `visual/BlowingBubbles_f365_qp_strip.png`.
- **Selection rule (decided before viewing):** the frame with the median QP-39 Y-PSNR, and the most detailed crop of that frame.
- **Rendering:** the images are script renderings of the decoded YUV files (BT.709, 10-bit to 8-bit, for display only). They are **not YUView screenshots**. A YUView inspection by Sadab has **not yet been done**; see section 9.
- **Note on the BQMall crop:** it contains a moving hand, so the original itself shows motion blur.

## 8. Failed, skipped and unverified items

| Item | Status | Reason |
|---|---|---|
| 7 VVenC unit tests on Windows (vvenclibtest, vvenc_unit_test) | Not run | Windows Smart App Control blocked the unsigned test programs. No security setting was changed. All 39 passed on Linux. |
| 252 VVdeC conformance tests (both platforms) | Skipped | They need JVET conformance bitstreams that are not in the source repository |
| YUView screenshots and visual observation | Not done | They need a person to use the YUView window; instructions are in section 9 |
| Linux timing | Not used | WSL2 with input on `/mnt/d`, not comparable |
| R04 encode time | Kept, flagged | Its repeat R17 was 45 % faster |

## 9. Record: automated steps and steps for Sadab

**Automated by Claude (AI assistant), 2026-11-11:**
- source download
- Windows and Linux builds
- unit tests
- smoke test
- all 18 runs
- Linux cross-platform runs
- PSNR checks
- analysis and charts
- frame rendering
- deck update

**Performed or verified by Sadab:** none recorded yet.

**Sadab should do these steps himself before presenting:**
1. Open `visual/yuview/` in YUView 2.14 (`tools/YUView/YUView.exe`):
   - Load `BQMall_original_...yuv` and `BQMall_QP24/29/34/39_medium_...yuv`.
   - Check the format in Properties: 832×480, YUV 4:2:0, 10-bit, 60 fps.
   - Go to frame 432 (YUView counts from 0), use split view and zoom into the area x 280–488, y 296–416 (the crop on slide 7).
   - Take screenshots (Win+Shift+S) and save them in `visual/yuview_screenshots/`.
2. Write one or two sentences about what he actually saw. Replace the bracket text on slide 7 and in the slide-7 notes.
3. Re-run at least one configuration himself and compare its SHA-256 with `results/results_raw.csv`. For example:
   ```
   vvenc\bin\release-static\vvencapp.exe -i dataset\BlowingBubbles_416_240_50_10_420.yuv -s 416x240 -c yuv420_10 --fps 50 -f 500 -q 34 --preset fast --qpa 0 -t 8 -o out\check.266
   ```
   then `Get-FileHash out\check.266`. The expected SHA-256 is that of R04.
4. Read this report and the speaker notes so that he can explain every number.
5. Be open with Prof. Choi about how the experiment was run, including the use of an AI assistant.
