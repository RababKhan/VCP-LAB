# Where the numbers on slides 5–9 come from

**Deck:** `presentation/VVC_Assignment_Sadab_Khan_Prangon_FINAL.pptx`

**Verified on 15 November 2026:**
- `demo_results.py` and `demo_bdrate.py` read the chart data and text directly from the deck and compared every value with the CSV files. All values matched.
- For a point-by-point list of all 88 chart points and tiles on slides 5 and 6 (with run IDs and log files), run `demo_results.py`. It writes `output/slide_mapping_5_6_<time>.csv`.

## How the results files are made

```
logs/runs/R*.log, logs/phase2/{A,B,C}*.log      one log per encoder run (command, encoder output, decode, PSNR check)
        |  written by experiment/run_experiment.ps1 (phase 1) and experiment/run_phase2.py (phase 2)
        v
results/results_raw.csv (phase 1, R01–R18)  +  results/results_phase2.csv (phase 2, A/B/C runs)   one row per run
        |  analysis/analyze_full.py
        v
results/config_summary.csv   one row per configuration (64): bitrate, PSNR, median encode/decode time
results/bdrate.csv           12 BD-rates against medium
results/timing_reliability.csv, results/summary_full.json
        |  presentation/build_deck_v3.py (reads only these files)
        v
slides 5–9
```

## Basic per-run values (log → CSV)

| Value | Log line (in the run's log file) | CSV column (`results_phase2.csv`) | Calculation |
|---|---|---|---|
| Encoding time | `vvencapp [info]: Total Time: 8.422 sec.` | `encode_time_s` | The encoder's own measurement. `encode_wall_s` is the wall clock |
| Decoding time | `500 frames decoded @ … fps (0.185 sec)`, ×3 under "DECODE TIMING n (no output file)" | `decode_noout_times_s`, `decode_noout_median_s` | Median of the 3 decodes. No output file is written, so disk speed does not count |
| Bitstream size | – (file `out/phase2/<run>.266`) | `bitstream_bytes` | File size in bytes |
| Bitrate | Encoder prints `a 462.4584` in its summary | `bitrate_kbps` (`enc_bitrate_kbps` = encoder) | bytes × 8 ÷ (frames ÷ fps) ÷ 1000 |
| Y/U/V PSNR | Summary line `500 a 462.4584 34.8147 39.9791 38.2132 35.5616` | `enc_y_psnr`, `enc_u_psnr`, `enc_v_psnr` | For each frame and plane, 10·log10(1020² / MSE), then the mean over the frames |
| Independent PSNR | `=== PSNR CHECK` followed by JSON from `experiment/psnr_check.py` | `check_y/u/v_psnr`, `max_psnr_diff_db` | Same formula, computed from the original and decoded YUV files by our own script |
| Frame count | – (decoded YUV file) | `recon_frames` | size ÷ (W × H × 1.5 × 2 bytes) |
| SHA-256 | – | `bitstream_sha256`, `recon_sha256` | SHA-256 fingerprint of the file |

The phase-1 runs (R01–R18) use the same column names in `results/results_raw.csv`, with logs in `logs/runs/`. Their decode times without an output file were measured later and saved separately, in `results/decode_timing_phase1_bitstreams.csv`.

## Slide 5: QP and rate–distortion

| Displayed | Source CSV → columns | Behind it | Calculation |
|---|---|---|---|
| 4 RD charts, 4 lines × 4 points | `config_summary.csv` → `bitrate_kbps` (x), `y` (Y-PSNR) | Column `runs` lists the run IDs; each run's log is in `log_file` of `results_phase2.csv` / `results_raw.csv` | Values of the first run. All repeats have identical bitstreams |
| "Bitrate per +5 QP ÷1.88–2.18, median ÷2.06, 48 steps" | `config_summary.csv` → `bitrate_kbps` | 4 sequences × 4 presets × 3 QP steps = 48 | bitrate(QP) ÷ bitrate(QP+5): min, max, median |
| "Y-PSNR per +5 QP −1.5–3.8 dB, median −2.66 dB" | `config_summary.csv` → `y` | the same 48 steps | Y-PSNR(QP) − Y-PSNR(QP+5) |
| "Independent PSNR check Δ 0.0000 dB, all 94 runs" | `results_all_runs.csv` → `check_diff` | all 94 runs | Largest difference between the encoder's PSNR and our PSNR |

## Slide 6: preset and encoding complexity

| Displayed | Source CSV → columns | Calculation |
|---|---|---|
| Line chart: median encoding time at QP 29 (16 points) | `config_summary.csv` → `enc_median_s` (rows with qp = 29) | Median of `encode_time_s` over the configuration's runs. Runs flagged "battery" are excluded (B022 → re-measured as C001) |
| "faster vs medium ×0.08–0.16", "fast ×0.25–0.38", "slow ×2.3–3.8" | `config_summary.csv` → `enc_median_s` | enc_median_s(preset, QP) ÷ enc_median_s(medium, same QP), for 16 sequence/QP pairs: min–max |
| "decode time 0.11–3.3 s" | `config_summary.csv` → `dec_noout_median_s` | min–max over the 64 configurations |
| "CV 0.2–2.7 %, 9 configurations" | `timing_reliability.csv` → `measurements` | Coefficient of variation = standard deviation ÷ mean × 100, using only the phase-2 runs (A/B/C IDs) of each repeated configuration |

## Slide 7: BD-rate

| Displayed | Source CSV → columns | Calculation |
|---|---|---|
| Table: 12 BD-rates (e.g. BasketballPass faster +25.1 %) | `bdrate.csv` → `bdrate_Y_pchip_pct` (from `config_summary.csv` → `bitrate_kbps`, `y` at QP 24/29/34/39) | `analysis/metrics.py` `bd_rate()`, explained below |
| Row "time vs medium ×0.10–0.13 / ×0.27–0.32 / ×2.94–3.50" | `bdrate.csv` → `time_ratio_vs_medium_geomean` | Per sequence: geometric mean over the 4 QPs of the time ratio. The row shows the min–max over the 4 sequences |
| Chart (12 points + anchor) | x = `time_ratio_vs_medium_geomean`, y = `bdrate_Y_pchip_pct` | – |
| "overlap ≥ 93 %; polynomial check within 0.14 %" | `bdrate.csv` → `overlap_Y`, `bdrate_Y_poly_pct` | Smallest overlap; largest difference between PCHIP and polynomial |

Note the difference between the two time rows. Slide 6 tiles show the min–max over 16 single per-QP ratios. Slide 7 shows the min–max over 4 per-sequence geometric means.

**How one BD-rate is computed** (shown live by `demo_bdrate.py`; example BasketballPass, faster vs medium):

1. Take the 4 points (bitrate, Y-PSNR) of medium (the anchor) and of faster, at QP 24, 29, 34 and 39.
2. **Validity:** each curve has 4 points, and PSNR rises with bitrate. The common PSNR range (29.494–38.487 dB) must cover at least 50 % of the smaller range. Here it covers 96 %.
3. For each curve, draw log10(bitrate) as a smooth curve over PSNR (PCHIP, piecewise cubic). Integrate it over the common range: medium 22.24825, faster 23.12419.
4. Average log difference = (23.12419 − 22.24825) ÷ (38.4868 − 29.4942) = 0.09741.
5. BD-rate = (10^0.09741 − 1) × 100 % = **+25.14 %**. faster needs 25 % more bits than medium for the same quality.

## Slide 8: visual quality

| Displayed | Source |
|---|---|
| Crops of BasketballDrive frame 98 (original, QP 24–39, medium) | `visual/v2/BasketballDrive_f98_typical_*_crop.png`. Frame and crop are in `visual/v2/selection.json` (frame 98, crop x 472, y 456, 480 × 272) |
| PSNR / SSIM / MS-SSIM under each crop | `results/visual_frame_metrics.csv` → `y_psnr`, `ssim`, `ms_ssim`, computed on the whole luma frame (not only the crop). `demo_results.py` recomputes them from the decoded files |
| MS-SSIM table (4 sequences × 4 QPs) | `results/visual_sequence_ssim.csv` → `ms_ssim_mean`: the mean over every 10th frame |

## Slide 9: Windows vs Linux

| Displayed | Source |
|---|---|
| 8 rows, all "yes" | `results/crossplatform_v2.json`: 5 entries in `phase6_runs` (A018, A020, A021, A025, B019), 2 in `phase1_checks.full_length` (R04, R15), and 1 in `phase1_checks.smoke_16_frames` |
| The files | Windows: `out/phase2/*.266`, `out/R04…`, `out/R15…`, `out/smoke/smoke_Windows…` · Linux: `out/linux2/*_linux.266`, `out/linux/*`, `out/smoke/smoke_Linux…` · Linux logs: `logs/phase6_linux/` |

Only these 8 configurations were compared across platforms, not all 64.
