# VVenC / VVdeC on Windows: preliminary results report

**Status:** preliminary. All 65 planned runs completed and passed automatic verification. The four configurations whose only timing sample was affected by battery operation were re-measured on AC power in a separate supplementary run (§9); the original values are unchanged. This report covers only the Windows (MSVC) build. The Linux build and the YUView visual comparison have not been done yet.
**Date of experiment:** 2026-11-04, 10:32:53 to about 16:50 (local time, UTC+06:00).
**Generated tables and figures:** `results/full/` and `figures/full/`. They are reproducible with `scripts/analyze_full.py`.

---

## 1. What was done

| Item | Value |
|---|---|
| Encoder | VVenC v1.14.0 (commit `9428ea8`), `vvencapp.exe` SHA256 `c74f3b63…160b` |
| Decoder | VVdeC v3.2.1 (commit `cb1a3ef`), `vvdecapp.exe` SHA256 `3f46677a…b6` |
| Build | MSVC 19.44 (VS Build Tools 2022 17.14), CMake 4.4.4, x64 Release, static, AVX2 |
| Machine | ASUS Zenbook Flip UP5302ZA (Intel hybrid CPU), Windows 11 Home 10.0.26200 |
| Power | Windows power mode "Best performance" for all 65 runs. AC power except one period (see §5.1). |
| Input | 4 sequences, 10-bit LE, 4:2:0. The trailing copyright frame is excluded. |
| Fixed encoder settings | `--qpa 0 -t 8 --refreshtype cra --refreshsec 1 -c yuv420_10`, constant QP (no rate control) |
| Decoder settings | `vvdecapp -t 8`. A timing pass is run without writing output, then a separate pass writes the reconstruction used for PSNR. |
| QP sweep | QP 22 / 27 / 32 / 37 at preset `medium` |
| Preset sweep | `faster` / `fast` / `medium` / `slow` / `slower` at QP 32 |
| Matrix | 1 warm-up + 32 unique configurations + 32 timing repeats = **65 runs**. The order is randomised (seed 2026); every repeat runs after its original. |

| Sequence | Resolution | fps | Frames encoded |
|---|---|---|---|
| BasketballPass | 416×240 | 50 | 500 |
| BlowingBubbles | 416×240 | 50 | 500 |
| BQMall | 832×480 | 60 | 600 |
| BasketballDrive | 1920×1080 | 50 | 500 |

The 8 unique configurations per sequence are QP {22, 27, 32, 37} at `medium` plus the 4 non-medium presets at QP 32. QP 32 / `medium` is shared by both sweeps and is encoded only once. The two 240p sequences have 3 timing samples per configuration (the original plus 2 repeats). The two larger sequences have 1 sample each.

**PSNR definition (primary):**
- Peak value 1020 (= 255 << 2), the HM/VTM/VVenC convention.
- The per-frame PSNR is averaged over all frames.
- YUV-PSNR = PSNR of the 4:1:1 pixel-weighted MSE.

Three other variants are stored in every `*_psnr.json`: peak 1023, PSNR of the average MSE, and the JVET 6:1:1 weighting. PSNR is computed independently by `scripts/psnr_yuv.py` from the decoded YUV and the original YUV.

---

## 2. Verification (measured)

| Check | Result |
|---|---|
| Runs present / expected | 65 / 65 |
| Runs with status `ok` | 65 (0 failed, 0 skipped, 0 retried) |
| Per-run automatic checks | all passed (see the list below) |
| Repeat runs whose bitstream is byte-identical (SHA256) to the original | **32 / 32** |
| Max \|independent PSNR − encoder-reported PSNR\| | **0.0000 dB** (all 33 non-repeat runs) |
| Decoded/original frame alignment (offset −2…+2) | best offset = 0 for every run |
| First IDR picture | POC 15 for the 50 fps sequences, POC 31 for BQMall (60 fps). This matches what Phase 4A predicted. |
| Safety-guard stops (failures / disk / thermal) | none |

The per-run automatic checks were:
- encoder and decoder exit codes
- the encoder echoed QPA = 0, constant QP, the frame count, 8 threads and 10-bit input
- the picture count equals the frame count
- the bitstream is non-empty
- the decoded frame count and reconstruction size are correct
- PSNR matches the encoder within 0.0001 dB
- bitrate matches the encoder within 0.001 kbps

Details are in `results/full/runs/<run_id>.json` and `results/full/results.csv`.

---

## 3. Results (measured)

All timing values are medians over the timing samples. `Enc time` is the encoder-reported total time. Wall-clock time was always 0.09–0.36 s longer, which is process start-up and file I/O. `Dec time` is the wall-clock time of the decode pass without output. Full tables, including U/V PSNR, are in `results/full/tables.md` and `results/full/config_summary.csv`.

### 3.1 QP sweep (preset `medium`)

| Sequence | QP | Bitrate (kbps) | Y-PSNR (dB) | YUV-PSNR (dB) | Enc time (s) | Dec time (s) |
|---|---|---|---|---|---|---|
| BasketballPass | 22 | 1144.4 | 40.545 | 41.052 | 113.4 | 0.340 |
| | 27 | 535.4 | 36.611 | 37.268 | 78.4 | 0.261 |
| | 32 | 260.4 | 33.305 | 34.133 | 53.5 | 0.215 |
| | 37 | 133.5 | 30.539 | 31.486 | 36.4 | 0.171 |
| BlowingBubbles | 22 | 1107.0 | 37.675 | 38.595 | 108.9 | 0.351 |
| | 27 | 520.7 | 34.514 | 35.493 | 76.7 | 0.265 |
| | 32 | 251.7 | 31.621 | 32.689 | 53.5 | 0.203 |
| | 37 | 121.5 | 28.972 | 30.134 | 38.1 | 0.163 |
| BQMall | 22 | 2597.5 | 40.335 | 41.318 | 241.0 | 0.984 |
| | 27 | 1218.4 | 37.834 | 38.828 | 168.8 | 0.762 |
| | 32 | 608.7 | 35.160 | 36.181 | 118.7 | 0.604 |
| | 37 | 318.1 | 32.519 | 33.582 | 89.0 | 0.498 |
| BasketballDrive | 22 | 9697.6 | 39.074 | 40.261 | 1112.2 | 3.743 |
| | 27 | 4118.9 | 37.620 | 38.772 | 651.6 | 2.967 |
| | 32 | 2032.9 | 35.891 | 37.051 | 406.2 | 2.369 |
| | 37 | 1041.7 | 33.931 | 35.124 | 301.5 | 2.268 |

What the QP sweep shows:
- **Bitrate:** each +5 QP step reduced the bitrate by a factor of 1.91–2.35 (median about 2.06) across all 12 steps.
- **Y-PSNR:** each +5 QP step lowered Y-PSNR by 1.45–3.93 dB. The drop was largest for the 240p sequences at low QP and smallest for BasketballDrive at low QP (1.45 dB from QP 22 to 27).
- **Encoding time:** time fell as QP rose. QP 22 took 2.7–3.7× as long as QP 37.
- **Decoding time:** decoding also got faster as QP rose (for example BasketballDrive 3.74 s → 2.27 s), but the effect is much smaller in absolute terms.
- **Encode/decode asymmetry:** at `medium`, encoding took 133–333× longer than decoding. Decoding speed was 134–220 fps for 1080p and 1,400–2,900 fps for 240p.
- **Hierarchical QP:** the average slice QP of I pictures is about 3 below the `-q` value, and of B pictures 5.7–8.6 above it. For example, BasketballPass at QP 32 gives I 29.1 and B 39.9. `-q` is a base QP, not the QP of every picture.

### 3.2 Preset sweep (QP 32)

| Sequence | Preset | Size vs medium | ΔY-PSNR vs medium (dB) | Enc time (s) | × medium time |
|---|---|---|---|---|---|
| BasketballPass | faster | +12.54% | −0.468 | 6.6 | 0.12 |
| | fast | +3.59% | −0.305 | 15.5 | 0.29 |
| | medium | 0 | 0 | 53.5 | 1.00 |
| | slow | −1.34% | +0.191 | 192.3 | 3.59 |
| | slower | −2.20% | +0.375 | 897.1 | 16.76 |
| BlowingBubbles | faster | +6.30% | −0.658 | 5.6 | 0.11 |
| | fast | −0.58% | −0.438 | 14.7 | 0.27 |
| | medium | 0 | 0 | 53.5 | 1.00 |
| | slow | −1.38% | +0.146 | 173.8 | 3.25 |
| | slower | −1.51% | +0.296 | 773.0 | 14.44 |
| BQMall | faster | +12.11% | −0.651 | 13.7 | 0.12 |
| | fast | +3.94% | −0.413 | 35.3 | 0.30 |
| | medium | 0 | 0 | 118.7 | 1.00 |
| | slow | −3.49% | +0.129 | 407.5 | 3.43 |
| | slower | −4.31% | +0.328 | 1887.8 | 15.91 |
| BasketballDrive | faster | +13.79% | −0.448 | 53.1 | 0.13 |
| | fast | +4.64% | −0.262 | 113.7 | 0.28 |
| | medium | 0 | 0 | 406.2 | 1.00 |
| | slow | −2.08% | +0.137 | 1505.6 | 3.71 |
| | slower | −3.59% | +0.239 | 6928.9 | 17.06 |

What the preset sweep shows:
- **Encoding time** grows steeply and consistently across all four sequences, relative to `medium`:
  - `faster` ≈ 0.11–0.13×
  - `fast` ≈ 0.27–0.30×
  - `slow` ≈ 3.3–3.7×
  - `slower` ≈ 14–17×

  The single most expensive run was BasketballDrive at `slower`: 6,929 s (1 h 55 min) for 500 frames at 1080p, which is 0.07 fps.
- **Quality and size:** at a fixed QP, a slower preset gave both a higher Y-PSNR and a smaller bitstream, with one exception (BlowingBubbles `fast`, see §4.3). Moving from `faster` to `slower` gained 0.69–0.98 dB of Y-PSNR while the bitstream shrank by 7–15%.
- **Diminishing returns:** going from `medium` to `slower` costs 14–17× the encoding time for +0.24 to +0.38 dB and 1.5–4.3% smaller files. Going from `faster` to `medium` costs 7.7–9.1× the time for +0.45 to +0.66 dB and 6–12% smaller files.
- **Decoding time** depends only weakly on the preset (§4.4).

### 3.3 Figures

All figures are in `figures/full/`:
- **QP sweep:** `qp_vs_bitrate.png` (log scale), `qp_vs_psnr_y.png`, `qp_vs_psnr_yuv.png`, `qp_vs_encoding_time.png` (log), and `rd_curves_medium.png` (rate–distortion curves, one panel per sequence).
- **Preset sweep:**
  - `preset_vs_encoding_time.png` (log scale)
  - `preset_vs_bitstream_size.png` (indexed to medium = 100)
  - `preset_vs_psnr_y.png` and `preset_vs_psnr_yuv.png`
  - `preset_vs_decoding_time.png`
  - `preset_tradeoff_time_vs_psnr.png`: encoding time against the Y-PSNR gain over `medium`
- **System monitor:** `monitor_processor_performance.png` and `monitor_thermal_zone.png` (the battery period is shaded).

---

## 4. Anomalies and how they were interpreted

### 4.1 One timing outlier: BasketballPass `slower`, repeat 3 (measured)
The three samples were 893.6 s, **1133.5 s** and 897.3 s. The outlier ran from 15:19 to 15:38. During 15:24–15:31 the 30-second monitor recorded:
- % Processor Performance of only 67–70% (median elsewhere: 117%)
- frequency 0.48–0.68 GHz
- the laptop on battery

This is the only stretch of the whole run with such values. **Interpretation:** the CPU was power-limited while running on battery, most likely because charge was low. The power-limit mechanism itself (OS battery saver or firmware) was not measured. The median (897.3 s) is not affected, and the bitstream is byte-identical to the other two samples.

### 4.2 The first sample of a configuration is usually the slowest (measured; cause assumed)
In 14 of the 16 repeated configurations, the original run was the slowest of the three samples. The median ratio of original to the median of its repeats was 1.036, so originals were about 3.6% slower.

All 32 repeats ran at the end of the session (15:17–16:48). In that period % Processor Performance was higher, with a median of about 134% after 15:32 against about 111% before 14:27.

**Interpretation (not proven):** time-of-run conditions explain this better than any property of the configurations, because the bitstreams are identical. The randomised order mixed sequences and configurations, but not the "original then repeat" ordering. A systematic first-versus-later difference of a few percent should therefore be treated as part of the timing uncertainty.

### 4.3 BlowingBubbles `fast` is 0.58% smaller than `medium` (measured)
This is the only point where a faster preset gave a smaller bitstream than a slower one. It is not better compression: its Y-PSNR is 0.44 dB lower. At a fixed QP, the presets trade size and quality differently. A single-QP comparison cannot say which preset is more efficient; that needs a BD-rate comparison over several QPs (§6).

### 4.4 Decoding time is not monotonic in the preset (measured)
For BasketballDrive the decode times were 2.07 s (`faster`), 2.53 s (`fast`), 2.37 s (`medium`), 2.78 s (`slow`) and 2.73 s (`slower`). Each value is a single sample. At 240p, repeated decode samples varied with a CV of 2–8%.

**Interpretation:** decode times of 0.15–3.7 s are short enough that run-to-run noise is comparable to the preset effect. The only robust observation is that `faster` streams decoded fastest for every sequence.

### 4.5 Laptop ran on battery for 64 minutes (measured; protocol deviation)
See §5.1.

---

## 5. Experimental conditions and deviations (measured)

### 5.1 AC power loss
The preflight check confirmed AC power. However, the monitor recorded `BatteryStatus = 1` (discharging) from **14:27:34 to 15:31:17**: 124 of 726 samples, about 64 minutes. The runner's own per-run AC check flagged 10 runs that started on battery. Including runs that overlapped the period, timing samples from 11 runs are affected.

The cause is not known; for example, the charger may have been disconnected or the AC adapter may have stopped supplying power.

The safety guard did not stop the run. It was designed to watch failed runs, disk space and thermal-zone temperature only. **Loss of AC power was not a guard condition. That is a gap in the protocol.**

Effect on the results:
- **Bitstreams, sizes and PSNR:** none. Encoding is deterministic: all 32 repeats are byte-identical, including the 4 repeats and 3 originals that ran wholly or partly on battery.
- **Timing, 240p sequences:** % Processor Performance was normal (median 105–134%) for the first 57 minutes on battery. It dropped only during the last 7 minutes, which produced the single outlier in §4.1. Every 240p configuration with a battery-affected sample still has at least one clean AC sample, and the medians are robust.
- **Timing, single-sample configurations:** these have no repeat to compare with.
  - BQMall QP 22 `medium` (241.0 s), BQMall QP 32 `faster` (13.7 s) and BasketballDrive QP 32 `fast` (113.7 s) ran entirely on battery.
  - BasketballDrive QP 32 `slower` (6,929 s) had about 26 of its 115 minutes on battery.
  - The monitor shows no slowdown during these runs, and their times fit smoothly into the QP and preset trends. They are nevertheless flagged in `tables.md` (column "Power flag") and should be treated as lower-confidence timings.
  - These four configurations were re-measured on AC power afterwards. See §9 for the comparison.

### 5.2 Thermal zone
The ACPI thermal zone (`\_TZ.THRM`) read **91.9 °C for 707 of 726 samples**, with a maximum of 92.9 °C. It never reached the 95 °C guard threshold. It fell to 58–66 °C only during the battery slowdown.

This sensor is a firmware/ACPI zone value, not a per-core CPU temperature. The flat plateau suggests a coarse or held value. **No claim is made about actual core temperatures.**

The evidence against sustained thermal throttling is indirect: % Processor Performance stayed at or above 93% in every sample except the battery slowdown and one isolated counter glitch (0% at 11:35:03, while utility and frequency were normal at that moment).

### 5.3 Timing variability (measured; 16 configurations × 3 samples)
- Encoding wall-time CV: median **2.4%**, range 0.40–5.27%, excluding the battery outlier (14.1%).
- Decoding wall-time CV: median 3.7%.
- The shortest encodes, the `faster` runs of about 6 s, had the highest relative variability (CV about 5%).
- Range as a percentage of the median: up to 10% for normal runs.

**Practical reading:** differences in encoding time below about 5–10% between single runs on this laptop should not be interpreted.

---

## 6. Measured findings vs assumptions

| Statement | Basis |
|---|---|
| Bitrate roughly halves per +5 QP; PSNR falls 1.5–3.9 dB per +5 QP | Measured (§3.1) |
| Slower presets: much longer encoding, higher PSNR, smaller files at fixed QP | Measured (§3.2), one sequence family, one QP |
| Encoding is 130–330× slower than decoding at `medium` | Measured |
| Same settings give byte-identical bitstreams on this build | Measured (32/32) |
| PSNR values are correct | Measured: the independent tool agrees with the encoder to 0.0000 dB, and with FFmpeg to 6 decimals in Phase 4A |
| The 1133 s outlier was caused by battery power limiting | Inference from the monitor's correlated time window, not a controlled test |
| The originals being about 3.6% slower is a time-of-run effect | Assumption, not tested |
| No thermal throttling | Indirect: % Processor Performance only; there is no core-temperature sensor |
| Single-sample timings of the larger sequences are representative | Assumption, supported only by the 240p CV of about 2–5% |
| "Preset X is more efficient than Y" | **Not established.** That needs BD-rate over several QPs per preset. |

---

## 7. Limitations

1. **Preset comparison at one QP only.** Size and PSNR change together, so the efficiency of a preset (BD-rate) cannot be computed from this data. The QP sweep was run only at `medium`.
2. **Timing on a laptop with a hybrid CPU (P-cores and E-cores).** Thread scheduling across core types, turbo behaviour and background OS activity add noise. The two larger sequences have only one timing sample per configuration.
3. **Power conditions were not constant** (§5.1). 64 minutes on battery and 7 minutes of power limiting. The affected samples are flagged, not removed. The four affected single-sample configurations have a supplementary AC measurement (§9), but it was taken in a different session, at a different time.
4. **The temperature sensor is not a core sensor** (§5.2).
5. **8-bit effective precision.** All four inputs are 8-bit content up-shifted into a 10-bit container (the 2 LSBs are always 0, Phase 4A). The 10-bit PSNR uses peak 1020, consistent with HM/VTM/VVenC, but the content does not exercise true 10-bit detail.
6. **Windows/MSVC only.** The Linux (GCC/Clang) build has not been run yet. Timing and possibly bitstreams may differ across compilers; the bitstreams are expected to be identical, but this has not been verified.
7. **Thread count changes the bitstream** (Phase 4A). All results are for 8 encoder and 8 decoder threads, and they are not directly comparable with single-threaded or other-thread-count results.
8. **Fixed intra refresh** (CRA every 1 s; first IDR at POC 15 or 31). Results apply to this random-access configuration only, not to low-delay or all-intra.
9. **The pilot (Phase 4A) ran under an unknown power mode.** The full run, under "Best performance", was about 2× faster than the pilot estimates, so the pilot timings must not be mixed with these.
10. **Monitor CSV format.** In this run the frequency field was written with a thousands separator (`1,800`). The analysis script parses it correctly, and the script has been fixed for future runs.
11. **No visual comparison yet.** YUView inspection of the reconstructed video has not been performed. Nothing in this report is a claim about visual quality.

---

## 8. Reproducing

```
.venv\Scripts\python.exe scripts\validate_manifest.py           # checks the 65-run design
powershell -File scripts\run_full_with_monitor.ps1              # runs/resumes the matrix + 30 s monitor
.venv\Scripts\python.exe scripts\analyze_full.py                # verification, tables, figures
```

**Raw outputs:**
- `bitstreams/full/` (65 MB)
- `recon/full/` (34 GB of decoded YUV; repeats do not keep a reconstruction)
- `logs/runs/full/` (encoder and decoder logs for every run)
- `logs/phase4b_full_console_20261104_103252.log`
- `logs/phase4b_system_monitor_20261104_103252.csv`

---

## 9. Supplementary AC-powered timing verification

**Status:** completed 2026-11-04, 17:26:31 to 19:26:01. Every supplementary timing is **valid AC-powered**. The original 65-run results were **not modified**: the SHA256 fingerprint of `results/full/` (136 files) was the same before and after the run, `44eb11e4…2c47`.

### 9.1 What was re-run, and how
- **Configurations:** the four whose only timing sample in the full run was taken wholly or partly on battery (§5.1):
  - BQMall QP 22 `medium`
  - BQMall QP 32 `faster`
  - BasketballDrive QP 32 `fast`
  - BasketballDrive QP 32 `slower`
- **Warm-up:** the same warm-up run as the full run was executed first. It is not a measurement.
- **Same parameters:** `configs/supp_ac_manifest.json` was generated by `scripts/make_supp_manifest.py`, which copies the full manifest verbatim. Its run entries, tools, encoder and decoder settings, sequence entries and dataset SHA256 values are identical to the full manifest (checked programmatically). The runner also confirmed identical frames, QP, preset, QPA, thread counts, GOP size, intra period, first-IDR POC and encoder/decoder version strings.
- **Same measurement method:** each run was executed by the unchanged `scripts/vvc_runner.py` (`--only <run_id>`). That is the same commands, the same timing code (encode wall + encoder-reported time, then a decode timing pass without output, then a recon decode pass + PSNR) and the same automatic checks.
- **Active power guard (`scripts/run_supplementary_ac.py`):**
  - Before any run, a preflight checked AC power (95% charge, battery saver off), Windows power mode = Best performance, the executable / dataset / manifest SHA256, disk space, and the `results/full` fingerprint. All checks passed.
  - Before each run, AC and Best performance were re-checked; otherwise no new run would be launched.
  - During each run, the AC line status and the effective power mode were polled every 2 s (3,583 samples in total). Any non-AC or non-Best-performance sample would have stopped the run, marked it INVALID and ended the experiment, keeping its partial files.
  - CPU counters (% Processor Performance, utility, frequency, ACPI thermal zone) were logged every 5 s with the built-in `typeperf`.
- **The guard was tested before the real run**, on a separate self-test manifest (`configs/supp_ac_selftest_manifest.json`, results in `results/supp_ac_selftest/`), using a test-only simulated AC loss:
  - AC loss before the first launch: no run launched.
  - AC loss 2 s into a run: the run was stopped within one poll and marked INTERRUPTED / timing invalid. Its partial bitstream was preserved and later moved to `_interrupted/` by the runner.
  - Normal operation: both runs completed and were valid.

### 9.2 Power monitoring results (measured)

| Supplementary run | Power samples (AC / total) | Battery % | Battery saver | CPU % Processor Performance, median (min) | Samples < 80% | Thermal zone max |
|---|---|---|---|---|---|---|
| warm-up | 1 / 1 | 95 | off | – (run shorter than one 5-s sample) | 0 | – |
| BQMall QP 32 `faster` | 9 / 9 | 95 | off | 133.5 (128.0) | 0 | 91.9 °C |
| BasketballDrive QP 32 `fast` | 68 / 68 | 95 | off | 108.3 (104.8) | 0 | 91.9 °C |
| BQMall QP 22 `medium` | 125 / 125 | 95–96 | off | 118.0 (107.7) | 0 | 91.9 °C |
| BasketballDrive QP 32 `slower` | 3,380 / 3,380 | 96–100 | off | 106.9 (96.8) | 0 | 91.9 °C |

There was no AC loss, no change of power mode and no low-performance sample. The thermal-zone caveat of §5.2 applies unchanged.

### 9.3 Bitstream and quality consistency (measured)

| Configuration | Bitstream SHA256 = original | Bytes (orig = supp) | Decoded frames | PSNR = original (Y, U, V, YUV) | \|PSNR − encoder\| |
|---|---|---|---|---|---|
| warm-up | yes | 28,271 | 64 ✓ | identical | 0.0000 |
| BQMall QP 32 `faster` | yes | 853,056 | 600 ✓ | identical | 0.0000 |
| BasketballDrive QP 32 `fast` | yes | 2,659,099 | 500 ✓ | identical | 0.0000 |
| BQMall QP 22 `medium` | yes | 3,246,923 | 600 ✓ | identical | 0.0000 |
| BasketballDrive QP 32 `slower` | yes | 2,450,006 | 500 ✓ | identical | 0.0000 |

This confirms that battery operation affected **only timing**, never the encoder output.

### 9.4 Timing comparison (measured; one sample on each side)
Diff = (supplementary − original) / original.

| Configuration | Original power | Encode, reported (s): original → AC | Diff | Decode timing pass (s): original → AC | Diff |
|---|---|---|---|---|---|
| BQMall QP 32 `faster` | battery, whole run | 13.652 → 11.098 | **−18.71%** | 0.458 → 0.432 | −5.68% |
| BasketballDrive QP 32 `fast` | battery, whole run | 113.711 → 110.992 | −2.39% | 2.533 → 2.252 | −11.09% |
| BQMall QP 22 `medium` | battery, whole run | 241.045 → 243.136 | +0.87% | 0.984 → 0.901 | −8.43% |
| BasketballDrive QP 32 `slower` | partly battery (≈26 of 115 min) | 6928.936 → 6733.726 | −2.82% | 2.730 → 2.438 | −10.70% |
| *warm-up (reference; original was on AC)* | AC | 0.523 → 0.559 | +6.88% | 0.027 → 0.028 | +3.70% |

- Encode wall-clock differences are the same as the reported differences to within 0.03 percentage points.
- Recon-pass decode times (writing up to 3.1 GB of YUV) differed by −47.9% to +7.7%. That pass is dominated by disk I/O and is not used as a decoding-time result.
- All values: `results/supp_ac/timing_comparison.csv` and `results/supp_ac/supp_comparison.md`.

### 9.5 Interpretation (measured vs assumed)
- **Measured:** three of the four encode timings agree with the battery-affected originals within −2.8% to +0.9%. That is inside the normal run-to-run variability on this laptop (encode CV median 2.4%, range up to 10% of the median, §5.3). For these three, the original values and the conclusions drawn from them stand.
- **Measured:** BQMall QP 32 `faster` was 18.7% faster on AC. This is outside the variability seen for other `faster` runs (CV about 5%, range about 10%).
  - **Assumed, not proven:** a short (about 12 s), fully parallel run on battery may have been limited in its short-term turbo power. The 30 s monitor had no sample inside that 14 s run, so this cannot be confirmed.
  - With the AC value, BQMall `faster` costs 0.094× the `medium` time instead of 0.115×. If the AC value is used, the `faster` range in §3.2 widens from 0.11–0.13× to 0.09–0.13× of `medium`.
- **Measured:** the decode timing pass was 5.7–11.1% faster on AC in all four cases, whereas the AC-to-AC warm-up decode was within +3.7%. This suggests a small battery effect on short, highly parallel decodes. It rests on one sample per side, and decode CV at 240p was 2–8%, so it is not conclusive.
- **Effect on the main conclusions:** none of the QP or preset trends in §3 change.
  - BasketballDrive `slower` relative to `medium`: 17.06× with the original value, 16.58× with the AC value.
  - BasketballDrive `fast`: 0.280× → 0.273×.
  - BQMall QP 22 relative to QP 37: 2.71× → 2.73×.
- **Original values were not replaced.** §3 and `results/full/` still report the original measurements, flagged "on battery" in `tables.md`. The supplementary AC values are reported alongside them here. Choosing which value to cite is left to the final report.

### 9.6 Remaining measurement limitations
1. **One sample per side.** The supplementary run gives one AC sample per configuration, the same count as the original. A single pair cannot separate a battery effect from normal run-to-run noise when the difference is below about 5–10%.
2. **Different session.** The supplementary runs were made about 2.5–6.5 hours after the originals, in a fixed (not randomised) order, after the machine had just finished a 6-hour workload. Time-of-session effects (§4.2, about 3.6%) may contribute to the differences.
3. **No mechanism measured.** The BQMall `faster` difference is not explained by any monitored counter. Power-limit (PL1/PL2) state is not exposed by the built-in counters.
4. **Thermal zone is not a core sensor** (§5.2). It read 91.9 °C throughout, as in the full run.
5. **Interrupted-run logs.** Had a run been interrupted, the encoder's own log would have been incomplete, because the runner writes it when the process exits. The supervisor console log, the power log and the partial bitstream would have been kept. This did not occur.

**Files:**
- Configuration and scripts: `configs/supp_ac_manifest.json`, `scripts/make_supp_manifest.py`, `scripts/run_supplementary_ac.py`, `scripts/analyze_supplementary.py`.
- Results: `results/supp_ac/` (`results.csv`, `runs/`, `supplementary_status.json`, `timing_comparison.csv`, `supp_comparison.md`, `supp_summary.json`).
- Raw outputs: `bitstreams/supp_ac/`, `recon/supp_ac/`.
- Logs: `logs/runs/supp_ac/`, `logs/supp_ac_power_20261104_172627.csv`, `logs/supp_ac_cpu_20261104_172627.csv`, `logs/supp_ac_console_20261104_172627.log`, `logs/supp_ac_supervisor_20261104_172627.log`.
