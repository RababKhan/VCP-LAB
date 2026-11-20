# VVC Experiment Report v2 (expanded): Sadab Khan Prangon

**Assignment:** VVC encoding and decoding with VVenC 1.14.0 and VVdeC 3.2.1, for Prof. Kiho Choi, Video Coding and Processing Lab, Kyung Hee University.

**Who did what:** Claude, an AI assistant, executed every build, run and analysis in this report on this computer, at the user's request, on 2026-11-11. The commands and raw outputs are in `logs/`. **Sadab Khan Prangon has not yet personally performed or verified any step**; see section 14.

**Relation to the first report:** `results/EXPERIMENT_REPORT.md` and all phase-1 data are kept unchanged. This report adds phases 1–7 of the extension.

## 1. Summary

- **Matrix:** 4 sequences × 4 QPs (24, 29, 34, 39) × 4 presets (faster, fast, medium, slow) = **64/64 configurations measured**.
- **Runs:** 94 encoder runs: 93 OK, 1 flagged, 0 failed.
  - The flagged run is B022: the laptop switched to battery during that run. Its timing is excluded, and it was re-measured as C001.
  - The PSNR check matched the encoder in every run (max difference 0.0000 dB).
  - The decoded frame count was correct in every run (True).
  - Every repeated configuration produced an identical bitstream (True).
- **QP:** each +5 QP divided the bitrate by 1.88–2.18 (median 2.06) and lowered Y-PSNR by 1.50–3.77 dB (median 2.66). This covers all 48 QP steps.
- **BD-rate against medium (Y-PSNR, PCHIP):**
  - faster: **+25.1 to +33.6 %**
  - fast: **+10.6 to +15.0 %**
  - slow: **-6.9 to -4.9 %**
  - All 24 comparisons passed the validity checks.
- **Encoding time against medium (geometric mean over QPs):**
  - faster: ×0.10–0.13
  - fast: ×0.27–0.32
  - slow: ×2.94–3.50
- **Timing reliability:** the 9 configurations repeated under the phase-2 controls varied by a CV of 0.2–2.7 % (phase-2 runs only; the CV including phase-1 runs is in `timing_reliability.csv`). The earlier 45 % difference (R04 vs R17) is explained in section 4.
- **Windows vs Linux:** 5/5 new checks identical in every compared field, plus 3/3 earlier checks.

## 2. Phase 1: audit of the first 18 runs

- **614 automated checks, 0 failed** (`analysis/audit_phase1.py`, `results/audit_phase1.json`, `logs/20_audit_phase1.log`).
- **What was checked:**
  - input SHA-256 against the provenance log
  - every encoder argument, the input file and the exit codes
  - the encode time and the encoder summary values against the logs
  - bitstream size and SHA-256 against the files
  - the bitrate, recomputed
  - 3 decodes per run: exit code, frame count and logged times
  - reconstruction size
  - the logged independent PSNR
- **Result:** no stored value differs from the raw files.

## 3. Data and setup

| Sequence | Resolution | fps | Frames used | Input SHA-256 (verified against the provided file) |
|---|---|---|---|---|
| BasketballPass | 416×240 | 50 | 500 (10 s) | `de0dcc61e9ba4d22…` |
| BlowingBubbles | 416×240 | 50 | 500 (10 s) | `ffe4039fc7cfc034…` |
| BQMall | 832×480 | 60 | 600 (10 s) | `02490741eed0ef8d…` |
| BasketballDrive | 1920×1080 | 50 | 500 (10 s) | `1c4cecebc10efb18…` |

- **Format:** all four files contain 501 (or 601) complete 10-bit 4:2:0 frames; the frame count was checked from the file size before the runs.
- **Encoder:** `vvencapp -c yuv420_10 --qpa 0 -t 8 -q {24,29,34,39} --preset {faster,fast,medium,slow}`; all other options are defaults. The build is the same Windows MSVC build as in phase 1.
- **Decoder, phase 2:**
  - one decode with an output file, for the frame count, the independent PSNR and the decoded-video SHA-256
  - 3 decodes **without** an output file for timing; the median is kept
  - the 16 phase-1 bitstreams were re-timed the same way (`results/decode_timing_phase1_bitstreams.csv`)
- **Reuse:** the 16 phase-1 configurations (BlowingBubbles/BQMall × fast/medium) have identical settings, so they were reused, not re-encoded. Several were repeated for timing (section 4).

## 4. Timing reliability (phase 3)

- **Controls:**
  - a warm-up encode/decode before each block, logged and discarded
  - AC power checked before every run; the runner waits on battery
  - the system kept awake for the process only; no power or security setting was changed
  - random order with recorded seeds (Block A 20261111, Block B 20261112)
  - CPU utility and CPU performance (% of nominal frequency) sampled every 5 s (`logs/monitor_phase2.csv`)
- **CPU temperature** is not readable without administrator rights and was not recorded.
- **CPU performance:** the mean during phase-2 runs ranged from 97 % to 141 % of nominal (per run). This range covers turbo behaviour on a hybrid laptop CPU; it is a coarse indicator only.

| Configuration | n | Median (s) | Spread (max−min)/median | CV | Measurements | Flagged |
|---|---|---|---|---|---|---|
| BasketballPass QP29 faster | 4 | 8.40 | 3.0 % | 1.2 % | A004=8.27s; A023=8.39s; A029=8.42s; A031=8.52s | – |
| BasketballPass QP29 slow | 4 | 261.30 | 1.2 % | 0.6 % | A005=260.39s; A006=262.00s; A009=263.52s; A034=260.60s | – |
| BlowingBubbles QP34 fast | 5 | 13.79 | 77.9 % | 29.2 % | R04=23.98s; R17=13.24s; A017=13.79s; A038=13.57s; A050=14.29s | R04 (1.74x median) |
| BlowingBubbles QP24 medium | 4 | 99.77 | 22.6 % | 10.6 % | R03=122.09s; A012=99.66s; A026=99.58s; A039=99.88s | R03 (1.22x median) |
| BlowingBubbles QP34 medium | 5 | 48.58 | 3.5 % | 1.3 % | R16=48.58s; R18=47.58s; A019=48.80s; A033=49.29s; A044=48.50s | – |
| BQMall QP29 medium | 4 | 149.37 | 1.5 % | 0.7 % | R15=150.54s; A041=148.33s; A049=148.72s; A053=150.02s | – |
| BQMall QP39 medium | 4 | 76.72 | 11.7 % | 5.3 % | R01=84.72s; A007=76.61s; A008=75.76s; A022=76.84s | – |
| BasketballDrive QP34 faster | 4 | 48.43 | 4.7 % | 2.3 % | B004=49.18s; B011=49.39s; B016=47.12s; B021=47.68s | – |
| BasketballDrive QP34 fast | 4 | 106.01 | 4.6 % | 2.1 % | B009=107.03s; B010=108.48s; B015=103.56s; B020=104.99s | – |

**The 45 % R04/R17 difference was investigated:**
1. **Machine-speed probe.** Decode time measures the machine's speed independently of the encoder.
   - In phase 1, R03 and R04 (started 11:24–11:26) decoded about 1.7–1.8× slower than all later decodes of the same sequence.
   - R04's encode was 1.74× its configuration's median. R03's was 1.22× and R01's was 1.10×.
2. **Repeats under controlled conditions.** All 31 phase-2 measurements of these configurations were within ±3.7 % of their configuration's median, with identical bitstreams. All measurements of R04's configuration: R04=23.98s; R17=13.24s; A017=13.79s; A038=13.57s; A050=14.29s.
3. **Conclusion.** R04 (and to a lesser degree R03 and R01) was measured during a transient slow state of the whole computer in the first ~6 minutes of phase 1. It is not encoder variability.
   - The cause cannot be identified from the logs; candidates are charging at about 49 % battery, or background scanning of newly written files.
   - The original values are kept, flagged and covered by median reporting.
   - **Caution:** the other phase-1 configurations that ran only once in that window (R02) may also be slightly inflated.
- **Power event:** the laptop switched to battery at 17:51 during B022. B022's time is excluded from timing statistics (rate/quality are unaffected), and the configuration was re-timed on AC (C001).

## 5. Rate and quality results (64 configurations)

Full table: `results/config_summary.csv`. Raw runs: `results/results_all_runs.csv`, `results/results_raw.csv`, `results/results_phase2.csv`.

| Sequence | Preset | QP 24 kbps / Y dB | QP 29 | QP 34 | QP 39 | Encode time QP24→39, median (s) |
|---|---|---|---|---|---|---|
| BasketballPass | faster | 976 / 38.49 | 462 / 34.81 | 223 / 31.70 | 112 / 29.07 | 10 → 8 → 7 → 5 |
| BasketballPass | fast | 909 / 38.77 | 424 / 34.99 | 204 / 31.84 | 102 / 29.13 | 29 → 20 → 15 → 12 |
| BasketballPass | medium | 849 / 38.93 | 404 / 35.25 | 200 / 32.16 | 102 / 29.49 | 105 → 71 → 48 → 33 |
| BasketballPass | slow | 828 / 39.09 | 396 / 35.44 | 197 / 32.35 | 101 / 29.70 | 379 → 261 → 170 → 105 |
| BlowingBubbles | faster | 905 / 35.74 | 422 / 32.65 | 200 / 29.91 | 94 / 27.42 | 8 → 7 → 6 → 4 |
| BlowingBubbles | fast | 841 / 36.00 | 390 / 32.89 | 187 / 30.14 | 89 / 27.65 | 28 → 20 → 14 → 11 |
| BlowingBubbles | medium | 813 / 36.37 | 388 / 33.33 | 188 / 30.54 | 90 / 27.97 | 100 → 80 → 49 → 44 |
| BlowingBubbles | slow | 791 / 36.49 | 380 / 33.46 | 186 / 30.67 | 90 / 28.08 | 334 → 234 → 159 → 103 |
| BQMall | faster | 2,177 / 38.88 | 1,046 / 36.18 | 521 / 33.42 | 269 / 30.77 | 23 → 18 → 13 → 12 |
| BQMall | fast | 2,025 / 39.09 | 967 / 36.41 | 481 / 33.65 | 250 / 31.01 | 76 → 57 → 35 → 24 |
| BQMall | medium | 1,902 / 39.36 | 919 / 36.77 | 466 / 34.08 | 247 / 31.48 | 233 → 149 → 141 → 77 |
| BQMall | slow | 1,830 / 39.45 | 888 / 36.90 | 452 / 34.23 | 240 / 31.63 | 770 → 524 → 351 → 235 |
| BasketballDrive | faster | 7,824 / 38.30 | 3,584 / 36.63 | 1,776 / 34.66 | 917 / 32.58 | 99 → 66 → 48 → 38 |
| BasketballDrive | fast | 7,076 / 38.39 | 3,264 / 36.77 | 1,626 / 34.84 | 829 / 32.74 | 239 → 147 → 106 → 82 |
| BasketballDrive | medium | 6,703 / 38.52 | 3,113 / 36.98 | 1,559 / 35.13 | 797 / 33.09 | 853 → 550 → 377 → 271 |
| BasketballDrive | slow | 6,487 / 38.59 | 3,032 / 37.09 | 1,528 / 35.28 | 784 / 33.26 | 3280 → 1998 → 1307 → 804 |

Charts in `results/charts_full/`:
- `qp_vs_bitrate.png`, `qp_vs_ypsnr.png`, `rd_curves.png`
- `encode_time_vs_preset.png`, `bitstream_size.png`, `bitstream_size_vs_preset.png`
- `decode_time.png`, `bdrate_vs_time_and_bpp.png`, `timing_repeatability.png`

## 6. Preset complexity and BD-rate (phases 4 and 7)

**BD-rate method:** `analysis/metrics.py`.
- log10(bitrate) is interpolated as a function of PSNR with a piecewise cubic Hermite (PCHIP) curve over the 4 QP points and integrated over the overlapping PSNR interval. BD-rate = 10^(mean difference) − 1.
- The original VCEG-M33 cubic-polynomial version is computed as a cross-check.
- **Validity rules, checked before computing:**
  - 4 points per curve
  - PSNR strictly increasing with rate
  - overlap ≥ 50 % of the smaller PSNR range
- **Self-tests:** identical curves → 0.0 %; rate ×0.9 → −10.0 %; rate ×1.2 → +20.0 %.
- **Anchor:** medium. Negative = fewer bits for the same quality.

| Sequence | Test vs medium | BD-rate Y (PCHIP) | BD-rate Y (poly, check) | BD-rate YUV 6:1:1 | BD-PSNR Y (dB) | PSNR overlap | Encode time vs medium |
|---|---|---|---|---|---|---|---|
| BasketballPass | faster | **+25.14 %** | +25.16 % | +26.23 % | -0.983 | 96% | ×0.126 |
| BasketballPass | fast | **+10.62 %** | +10.65 % | +12.23 % | -0.445 | 98% | ×0.311 |
| BasketballPass | slow | **-5.88 %** | -5.87 % | -6.40 % | +0.270 | 98% | ×3.505 |
| BlowingBubbles | faster | **+27.75 %** | +27.75 % | +27.13 % | -0.912 | 93% | ×0.095 |
| BlowingBubbles | fast | **+11.61 %** | +11.59 % | +11.15 % | -0.413 | 96% | ×0.268 |
| BlowingBubbles | slow | **-4.92 %** | -4.92 % | -5.12 % | +0.194 | 99% | ×2.943 |
| BQMall | faster | **+31.89 %** | +31.86 % | +33.07 % | -1.073 | 94% | ×0.114 |
| BQMall | fast | **+15.02 %** | +15.00 % | +15.80 % | -0.541 | 97% | ×0.315 |
| BQMall | slow | **-6.60 %** | -6.59 % | -7.06 % | +0.264 | 99% | ×3.065 |
| BasketballDrive | faster | **+33.60 %** | +33.46 % | +34.15 % | -0.758 | 96% | ×0.126 |
| BasketballDrive | fast | **+15.03 %** | +14.98 % | +16.71 % | -0.364 | 98% | ×0.283 |
| BasketballDrive | slow | **-6.88 %** | -6.86 % | -7.30 % | +0.181 | 99% | ×3.463 |

**Same-QP comparison** (not an efficiency measure; it shows why BD-rate is needed):
- faster vs medium: time ×0.08–0.16, size +4.0 to +16.7 %, Y-PSNR -0.71 to -0.23 dB.
- fast vs medium: time ×0.25–0.38, size -1.6 to +7.0 %, Y-PSNR -0.47 to -0.13 dB.
- slow vs medium: time ×2.34–3.85, size -3.8 to -0.7 %, Y-PSNR +0.07 to +0.21 dB.

**Interpretation:**
- The ranking faster < fast < medium < slow in compression efficiency is the same for all four sequences.
- slow saves 4.9–6.9 % bitrate for about ×2.9–3.5 encoding time.
- Going from medium to faster saves about 87–90 % of the time but costs 25–34 % more bitrate.
- **Diminishing returns:** each step towards slower presets buys a smaller bitrate saving per unit of extra time.
- **Resolution:** faster's BD-rate penalty grows from BasketballPass/BlowingBubbles (416×240) to BQMall (832×480) and BasketballDrive (1080p), and slow's saving is largest for the two larger sequences. With one sequence per larger resolution, resolution cannot be separated from content; this is a trend, not a proven effect.

## 7. Decoding time

- Without writing an output file, the median decode time was 0.112–3.283 s for 500–600 frames.
  - BasketballDrive 1080p: 1.72–3.28 s, i.e. 152–291 frames per second, with 8 threads.
  - BasketballPass: median over presets QP 24 0.289 s vs QP 39 0.158 s; median over QPs per preset faster 0.169, fast 0.175, medium 0.221, slow 0.228 s.
  - BlowingBubbles: median over presets QP 24 0.301 s vs QP 39 0.151 s; median over QPs per preset faster 0.171, fast 0.192, medium 0.228, slow 0.220 s.
  - BQMall: median over presets QP 24 0.793 s vs QP 39 0.490 s; median over QPs per preset faster 0.503, fast 0.598, medium 0.661, slow 0.639 s.
  - BasketballDrive: median over presets QP 24 3.106 s vs QP 39 2.103 s; median over QPs per preset faster 2.079, fast 2.362, medium 2.593, slow 2.602 s.
- Encoding took ×22 to ×1174 the decoding time.
- See `decode_time.png`. Decode times are short, so these differences are small in absolute terms.

## 8. Visual quality (phase 5)

**Selection rule (fixed before viewing, same for every sequence):**
- typical frame = median QP-39 Y-PSNR
- hardest frame = minimum QP-39 Y-PSNR
- crop = the most detailed quarter-width window of the original frame
- the same frame and crop are used for the original and all four QPs (medium preset)

**Metrics:** luma Y-PSNR, SSIM (Gaussian 11×11, σ 1.5) and MS-SSIM (5 scales). SSIM was cross-checked against scikit-image:
- BasketballPass: own 0.82265 vs scikit-image 0.82265
- BlowingBubbles: own 0.80365 vs scikit-image 0.80365
- BQMall: own 0.88551 vs scikit-image 0.88551
- BasketballDrive: own 0.86425 vs scikit-image 0.86425

The images are **script renderings** of the decoded files (`visual/v2/`), **not YUView screenshots**.

| Sequence | Frame (kind) | QP 24 PSNR / SSIM / MS-SSIM | QP 29 | QP 34 | QP 39 |
|---|---|---|---|---|---|
| BasketballPass | 359 (typical) | 38.88 / 0.966 / 0.9942 | 35.08 / 0.934 / 0.9858 | 31.93 / 0.888 / 0.9697 | 29.13 / 0.823 / 0.9414 |
| BasketballPass | 370 (hardest) | 36.13 / 0.945 / 0.9891 | 32.37 / 0.893 / 0.9719 | 29.20 / 0.824 / 0.9418 | 26.68 / 0.742 / 0.8908 |
| BlowingBubbles | 365 (typical) | 36.31 / 0.963 / 0.9955 | 33.41 / 0.934 / 0.9902 | 30.58 / 0.884 / 0.9801 | 28.06 / 0.804 / 0.9586 |
| BlowingBubbles | 485 (hardest) | 34.64 / 0.953 / 0.9937 | 30.90 / 0.906 / 0.9838 | 27.85 / 0.830 / 0.9640 | 24.89 / 0.719 / 0.9225 |
| BQMall | 432 (typical) | 39.53 / 0.965 / 0.9952 | 36.91 / 0.949 / 0.9910 | 34.06 / 0.923 / 0.9825 | 31.29 / 0.886 / 0.9670 |
| BQMall | 0 (hardest) | 37.45 / 0.957 / 0.9936 | 34.25 / 0.932 / 0.9870 | 31.19 / 0.891 / 0.9739 | 28.51 / 0.836 / 0.9508 |
| BasketballDrive | 98 (typical) | 38.42 / 0.923 / 0.9883 | 36.87 / 0.909 / 0.9823 | 35.10 / 0.890 / 0.9721 | 32.99 / 0.864 / 0.9535 |
| BasketballDrive | 154 (hardest) | 37.38 / 0.922 / 0.9872 | 35.49 / 0.900 / 0.9790 | 33.48 / 0.873 / 0.9656 | 31.32 / 0.839 / 0.9443 |

**Sequence-level SSIM / MS-SSIM** (every 10th frame, medium preset):

| Sequence | QP 24 | QP 29 | QP 34 | QP 39 |
|---|---|---|---|---|
| BasketballPass | 0.9628 / 0.9932 | 0.9274 / 0.9832 | 0.8776 / 0.9647 | 0.8128 / 0.9320 |
| BlowingBubbles | 0.9561 / 0.9942 | 0.9232 / 0.9878 | 0.8688 / 0.9745 | 0.7866 / 0.9499 |
| BQMall | 0.9626 / 0.9947 | 0.9452 / 0.9902 | 0.9181 / 0.9817 | 0.8789 / 0.9663 |
| BasketballDrive | 0.9247 / 0.9884 | 0.9097 / 0.9824 | 0.8894 / 0.9719 | 0.8641 / 0.9544 |

**Inspection status:**
- No person has inspected these frames yet. The visual statements in this report are limited to the metrics above.
- The earlier rendering note still applies: the BQMall phase-1 crop (frame 432) contains motion blur in the original.

## 9. Windows vs Linux (phase 6)

| Configuration | Size | Bitstream SHA-256 | Decoded SHA-256 | Frames | Y/U/V PSNR | Encoder parameters compared |
|---|---|---|---|---|---|---|
| BasketballPass QP24 slow, 500 frames | same | identical | identical | same | same | identical (16 lines) |
| BasketballPass QP39 faster, 500 frames | same | identical | identical | same | same | identical (16 lines) |
| BlowingBubbles QP29 slow, 500 frames | same | identical | identical | same | same | identical (16 lines) |
| BQMall QP34 faster, 600 frames | same | identical | identical | same | same | identical (16 lines) |
| BasketballDrive QP39 faster, 500 frames | same | identical | identical | same | same | identical (16 lines) |
| BlowingBubbles QP 34 fast, 500 frames (Windows run R04) (phase 1) | same | identical | identical | same | same | – |
| BQMall QP 29 medium, 600 frames (Windows run R15) (phase 1) | same | identical | identical | same | same | – |
| BlowingBubbles QP 34 fast, 16 frames (phase-1 smoke) | – | identical | identical | 16 | same | – |

- Windows MSVC 19.44 and Linux GCC 13.3 (WSL2) builds of the same tags produced byte-identical outputs in every comparison. That is 8 configurations, covering all 4 presets and all 4 sequences.
- Compared parameters: the encoder's printed configuration lines, with file paths and version/SIMD strings removed.
- Speed was not compared.

## 10. What the data supports, and what needs more work

**Supported by this data:**
- QP sets the rate–quality trade-off: about ÷2.1 bitrate per +5 QP, with a 1.5–3.8 dB Y-PSNR loss, in all 64 configurations.
- Slower presets are consistently more efficient (BD-rate), at steeply increasing encoding time.
- Extra encoding time gives diminishing returns.
- The Windows and Linux builds are bit-exact for the tested configurations.
- Phase-2 timing is repeatable to a few percent.

**Needs further experiments:**
- A resolution effect separate from content (needs several sequences per resolution, e.g. a JVET CTC class).
- The slower and slowest presets, and the other CTC QPs (22, 27, 32, 37).
- Comparison with a reference encoder (VTM).
- Perceptual quality beyond SSIM/MS-SSIM (e.g. VMAF or a subjective test).
- Timing on native Linux with fixed CPU frequency.

## 11. Limitations

- One laptop with a hybrid CPU and the Balanced power plan: times are relative, not a benchmark. Temperature was not available.
- One sequence each at 832×480 and 1080p.
- The 4 QPs are not the JVET CTC set (22/27/32/37).
- The BD-rate uses medium as the anchor, not VTM.
- Visual results are metrics plus script renderings; no YUView or subjective inspection has been done yet.
- 1080p and 832×480 reconstructions from phase 2 were not kept (disk space). Their SHA-256 is recorded, and they can be regenerated bit-exactly from the kept bitstreams.

## 12. Failed, skipped, unverified and flagged items

| Item | Status |
|---|---|
| Phase-2 attempt 1 | Aborted by a runner bug after the A001 encode, before any result row was written. Logs kept as `*_aborted.log`; the bug was fixed, the runner was self-tested on 16 frames, and the block was restarted |
| B022 timing | Flagged (battery during the run); excluded from timing; re-measured as C001 |
| R01, R03, R04 timing | Flagged as early-window outliers (section 4); kept |
| 7 Windows VVenC unit tests | Not run (Smart App Control blocked unsigned test programs) |
| VVdeC conformance tests | Skipped (bitstreams not included in the source) |
| CPU temperature | Not recorded (needs administrator rights) |
| YUView inspection, screenshots, Sadab's observation | **Not done**; Sadab must do these |

## 13. File index

- **Scripts:**
  - `experiment/run_phase2.py`, `run_supplement.py`, `monitor.ps1`, `linux_crossplatform_v2.sh`
  - `analysis/audit_phase1.py`, `metrics.py`, `analyze_full.py`, `visual_v2.py`, `compare_platforms_v2.py`, `make_report_v2.py`
- **Logs:** `logs/phase2/` (one per run), `logs/phase6_linux/`, `logs/monitor_phase2.csv`, `logs/2*_*.log`
- **Data:** `results/*.csv`, `results/*.json`, `results/charts_full/`, `visual/v2/`
- **Bitstreams:** `out/` (phase 1), `out/phase2/`, `out/linux2/`

## 14. Record of automated and personally verified work

**Automated by Claude (AI assistant):**
- builds and unit tests
- all 94 encoder runs and every decode
- PSNR, SSIM and MS-SSIM
- BD-rate and charts
- the Linux cross-platform runs
- this report and the presentation

**Personally performed or verified by Sadab:** none recorded yet.

**Before presenting, Sadab should:**
1. Open the decoded files in YUView and look at the selected frames himself (see `MISSING_EVIDENCE_CHECKLIST.md`), take screenshots, and write his own observation.
2. Re-run at least one configuration himself and compare its SHA-256 with `results/results_all_runs.csv`.
3. Be able to explain every number, especially BD-rate, timing reliability and their limitations.
4. Be open with Prof. Choi that the experiment was executed with an AI assistant.
