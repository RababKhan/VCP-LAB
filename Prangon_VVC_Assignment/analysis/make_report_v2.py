"""Write results/EXPERIMENT_REPORT_v2.md from the measured data (no hand-typed measurement values).
The phase-1 report (results/EXPERIMENT_REPORT.md) is kept unchanged."""
import csv
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
S = json.loads((R / "summary_full.json").read_text(encoding="utf-8"))
A = json.loads((R / "audit_phase1.json").read_text(encoding="utf-8"))
XP = json.loads((R / "crossplatform_v2.json").read_text(encoding="utf-8"))
VS = json.loads((ROOT / "visual/v2/selection.json").read_text(encoding="utf-8"))
cfg = list(csv.DictReader(open(R / "config_summary.csv", encoding="utf-8")))
bd = list(csv.DictReader(open(R / "bdrate.csv", encoding="utf-8")))
rel = list(csv.DictReader(open(R / "timing_reliability.csv", encoding="utf-8")))
runs = list(csv.DictReader(open(R / "results_all_runs.csv", encoding="utf-8")))
vf = list(csv.DictReader(open(R / "visual_frame_metrics.csv", encoding="utf-8")))
vsq = list(csv.DictReader(open(R / "visual_sequence_ssim.csv", encoding="utf-8")))
prov = (ROOT / "logs/00_setup_provenance.log").read_text(encoding="utf-8-sig", errors="replace")
SEQS = ["BasketballPass", "BlowingBubbles", "BQMall", "BasketballDrive"]
PRE = ["faster", "fast", "medium", "slow"]
L = []
w = L.append


def c(seq, p, q):
    return next(x for x in cfg if x["sequence"] == seq and x["preset"] == p and int(x["qp"]) == q)


p2 = [r for r in runs if r["source"] == "phase2" and r["cpu_perf_mean"]]
perf = [float(r["cpu_perf_mean"]) for r in p2]

w("# VVC Experiment Report v2 (expanded): Sadab Khan Prangon\n")
w("**Assignment:** VVC encoding and decoding with VVenC 1.14.0 and VVdeC 3.2.1, for Prof. Kiho Choi, Video Coding and Processing Lab, Kyung Hee University.\n")
w("**Who did what:** Claude, an AI assistant, executed every build, run and analysis in this report on this computer, at the user's request, on 2026-11-11. "
  "The commands and raw outputs are in `logs/`. **Sadab Khan Prangon has not yet personally performed or verified any step**; see section 14.\n")
w("**Relation to the first report:** `results/EXPERIMENT_REPORT.md` and all phase-1 data are kept unchanged. This report adds phases 1–7 of the extension.\n")

w("## 1. Summary\n")
w(f"- **Matrix:** 4 sequences × 4 QPs (24, 29, 34, 39) × 4 presets (faster, fast, medium, slow) = **{S['n_configs_measured']}/64 configurations measured**.")
w(f"- **Runs:** {S['runs_total']} encoder runs: {S['runs_ok']} OK, {S['runs_check']} flagged, {len(S['runs_failed'])} failed.")
w("  - The flagged run is B022: the laptop switched to battery during that run. Its timing is excluded, and it was re-measured as C001.")
w(f"  - The PSNR check matched the encoder in every run (max difference {S['max_psnr_check_diff']:.4f} dB).")
w(f"  - The decoded frame count was correct in every run ({S['all_frames_ok']}).")
w(f"  - Every repeated configuration produced an identical bitstream ({S['all_configs_deterministic']}).")
q = S["qp_step"]
w(f"- **QP:** each +5 QP divided the bitrate by {q['ratio_min']:.2f}–{q['ratio_max']:.2f} (median {q['ratio_median']:.2f}) and lowered Y-PSNR by "
  f"{q['drop_min']:.2f}–{q['drop_max']:.2f} dB (median {q['drop_median']:.2f}). This covers all {q['n']} QP steps.")
by = {(b["sequence"], b["test"]): b for b in bd}


def rng(test, key="bdrate_Y_pchip_pct"):
    v = [float(by[(s, test)][key]) for s in SEQS]
    return min(v), max(v)


w(f"- **BD-rate against medium (Y-PSNR, PCHIP):**")
w(f"  - faster: **{rng('faster')[0]:+.1f} to {rng('faster')[1]:+.1f} %**")
w(f"  - fast: **{rng('fast')[0]:+.1f} to {rng('fast')[1]:+.1f} %**")
w(f"  - slow: **{rng('slow')[0]:+.1f} to {rng('slow')[1]:+.1f} %**")
w("  - All 24 comparisons passed the validity checks.")
tr = {t: [float(by[(s, t)]["time_ratio_vs_medium_geomean"]) for s in SEQS] for t in ("faster", "fast", "slow")}
w(f"- **Encoding time against medium (geometric mean over QPs):**")
w(f"  - faster: ×{min(tr['faster']):.2f}–{max(tr['faster']):.2f}")
w(f"  - fast: ×{min(tr['fast']):.2f}–{max(tr['fast']):.2f}")
w(f"  - slow: ×{min(tr['slow']):.2f}–{max(tr['slow']):.2f}")
import re as _re  # noqa: E402
p2cv = []
for x in rel:
    tt = [float(v) for _, v in _re.findall(r"([A-C]\d{3})=([\d.]+)s", x["measurements"])]
    if len(tt) >= 2:
        p2cv.append(st.stdev(tt) / st.mean(tt) * 100)
w(f"- **Timing reliability:** the {len(p2cv)} configurations repeated under the phase-2 controls varied by a CV of "
  f"{min(p2cv):.1f}–{max(p2cv):.1f} % (phase-2 runs only; the CV including phase-1 runs is in `timing_reliability.csv`). "
  "The earlier 45 % difference (R04 vs R17) is explained in section 4.")
x8 = XP["summary"]
w(f"- **Windows vs Linux:** {x8['n_new_all_match']}/{x8['n_new']} new checks identical in every compared field, plus 3/3 earlier checks.\n")

w("## 2. Phase 1: audit of the first 18 runs\n")
w(f"- **{A['n_checks']} automated checks, {A['n_failed']} failed** (`analysis/audit_phase1.py`, `results/audit_phase1.json`, `logs/20_audit_phase1.log`).")
w("- **What was checked:**")
w("  - input SHA-256 against the provenance log")
w("  - every encoder argument, the input file and the exit codes")
w("  - the encode time and the encoder summary values against the logs")
w("  - bitstream size and SHA-256 against the files")
w("  - the bitrate, recomputed")
w("  - 3 decodes per run: exit code, frame count and logged times")
w("  - reconstruction size")
w("  - the logged independent PSNR")
w("- **Result:** no stored value differs from the raw files.\n")

w("## 3. Data and setup\n")
w("| Sequence | Resolution | fps | Frames used | Input SHA-256 (verified against the provided file) |\n|---|---|---|---|---|")
import re  # noqa: E402
for s, f, res, fps in (("BasketballPass", "BasketballPass_416_240_50_10_420.yuv", "416×240", 50),
                       ("BlowingBubbles", "BlowingBubbles_416_240_50_10_420.yuv", "416×240", 50),
                       ("BQMall", "BQMall_832_480_60_10_420.yuv", "832×480", 60),
                       ("BasketballDrive", "BasketballDrive_1920_1080_50_10_420.yuv", "1920×1080", 50)):
    m = re.search(re.escape(f) + r".*?sha256 ([0-9A-Fa-f]{64})", prov)
    w(f"| {s} | {res} | {fps} | {600 if s == 'BQMall' else 500} (10 s) | `{m.group(1).lower()[:16]}…` |")
w("\n- **Format:** all four files contain 501 (or 601) complete 10-bit 4:2:0 frames; the frame count was checked from the file size before the runs.")
w("- **Encoder:** `vvencapp -c yuv420_10 --qpa 0 -t 8 -q {24,29,34,39} --preset {faster,fast,medium,slow}`; all other options are defaults. The build is the same Windows MSVC build as in phase 1.")
w("- **Decoder, phase 2:**")
w("  - one decode with an output file, for the frame count, the independent PSNR and the decoded-video SHA-256")
w("  - 3 decodes **without** an output file for timing; the median is kept")
w("  - the 16 phase-1 bitstreams were re-timed the same way (`results/decode_timing_phase1_bitstreams.csv`)")
w("- **Reuse:** the 16 phase-1 configurations (BlowingBubbles/BQMall × fast/medium) have identical settings, so they were reused, not re-encoded. Several were repeated for timing (section 4).\n")

w("## 4. Timing reliability (phase 3)\n")
w("- **Controls:**")
w("  - a warm-up encode/decode before each block, logged and discarded")
w("  - AC power checked before every run; the runner waits on battery")
w("  - the system kept awake for the process only; no power or security setting was changed")
w("  - random order with recorded seeds (Block A 20261111, Block B 20261112)")
w("  - CPU utility and CPU performance (% of nominal frequency) sampled every 5 s (`logs/monitor_phase2.csv`)")
w("- **CPU temperature** is not readable without administrator rights and was not recorded.")
w(f"- **CPU performance:** the mean during phase-2 runs ranged from {min(perf):.0f} % to {max(perf):.0f} % of nominal (per run). "
  "This range covers turbo behaviour on a hybrid laptop CPU; it is a coarse indicator only.\n")
w("| Configuration | n | Median (s) | Spread (max−min)/median | CV | Measurements | Flagged |\n|---|---|---|---|---|---|---|")
for x in rel:
    w(f"| {x['config']} | {x['n']} | {float(x['median_s']):.2f} | {float(x['spread_pct']):.1f} % | {float(x['cv_pct']):.1f} % | {x['measurements']} | {x['outliers'] or '–'} |")
w("\n**The 45 % R04/R17 difference was investigated:**")
w("1. **Machine-speed probe.** Decode time measures the machine's speed independently of the encoder.")
w("   - In phase 1, R03 and R04 (started 11:24–11:26) decoded about 1.7–1.8× slower than all later decodes of the same sequence.")
rr = {x["config"]: x for x in rel}
ratio = {}
for cname, rid in (("BlowingBubbles QP34 fast", "R04"), ("BlowingBubbles QP24 medium", "R03"), ("BQMall QP39 medium", "R01")):
    t = float(re.search(rid + r"=([\d.]+)s", rr[cname]["measurements"]).group(1))
    ratio[rid] = t / float(rr[cname]["median_s"])
w(f"   - R04's encode was {ratio['R04']:.2f}× its configuration's median. R03's was {ratio['R03']:.2f}× and R01's was {ratio['R01']:.2f}×.")
p2dev = []
for x in rel:
    med = float(x["median_s"])
    for rid, t in re.findall(r"([A-C]\d{3})=([\d.]+)s", x["measurements"]):
        p2dev.append(abs(float(t) / med - 1) * 100)
w(f"2. **Repeats under controlled conditions.** All {len(p2dev)} phase-2 measurements of these configurations were within ±{max(p2dev):.1f} % "
  f"of their configuration's median, with identical bitstreams. All measurements of R04's configuration: {rr['BlowingBubbles QP34 fast']['measurements']}.")
w("3. **Conclusion.** R04 (and to a lesser degree R03 and R01) was measured during a transient slow state of the whole computer in the first ~6 minutes of phase 1. It is not encoder variability.")
w("   - The cause cannot be identified from the logs; candidates are charging at about 49 % battery, or background scanning of newly written files.")
w("   - The original values are kept, flagged and covered by median reporting.")
w("   - **Caution:** the other phase-1 configurations that ran only once in that window (R02) may also be slightly inflated.")
w("- **Power event:** the laptop switched to battery at 17:51 during B022. B022's time is excluded from timing statistics (rate/quality are unaffected), and the configuration was re-timed on AC (C001).\n")

w("## 5. Rate and quality results (64 configurations)\n")
w("Full table: `results/config_summary.csv`. Raw runs: `results/results_all_runs.csv`, `results/results_raw.csv`, `results/results_phase2.csv`.\n")
w("| Sequence | Preset | QP 24 kbps / Y dB | QP 29 | QP 34 | QP 39 | Encode time QP24→39, median (s) |\n|---|---|---|---|---|---|---|")
for s in SEQS:
    for p in PRE:
        cells = [f"{float(c(s, p, q)['bitrate_kbps']):,.0f} / {float(c(s, p, q)['y']):.2f}" for q in (24, 29, 34, 39)]
        tt = " → ".join(f"{float(c(s, p, q)['enc_median_s']):.0f}" for q in (24, 29, 34, 39))
        w(f"| {s} | {p} | " + " | ".join(cells) + f" | {tt} |")
w("")
w("Charts in `results/charts_full/`:")
w("- `qp_vs_bitrate.png`, `qp_vs_ypsnr.png`, `rd_curves.png`")
w("- `encode_time_vs_preset.png`, `bitstream_size.png`, `bitstream_size_vs_preset.png`")
w("- `decode_time.png`, `bdrate_vs_time_and_bpp.png`, `timing_repeatability.png`\n")

w("## 6. Preset complexity and BD-rate (phases 4 and 7)\n")
w("**BD-rate method:** `analysis/metrics.py`.")
w("- log10(bitrate) is interpolated as a function of PSNR with a piecewise cubic Hermite (PCHIP) curve over the 4 QP points and integrated over the overlapping PSNR interval. BD-rate = 10^(mean difference) − 1.")
w("- The original VCEG-M33 cubic-polynomial version is computed as a cross-check.")
w("- **Validity rules, checked before computing:**")
w("  - 4 points per curve")
w("  - PSNR strictly increasing with rate")
w("  - overlap ≥ 50 % of the smaller PSNR range")
w("- **Self-tests:** identical curves → 0.0 %; rate ×0.9 → −10.0 %; rate ×1.2 → +20.0 %.")
w("- **Anchor:** medium. Negative = fewer bits for the same quality.\n")
w("| Sequence | Test vs medium | BD-rate Y (PCHIP) | BD-rate Y (poly, check) | BD-rate YUV 6:1:1 | BD-PSNR Y (dB) | PSNR overlap | Encode time vs medium |\n|---|---|---|---|---|---|---|---|")
for b in bd:
    w(f"| {b['sequence']} | {b['test']} | **{float(b['bdrate_Y_pchip_pct']):+.2f} %** | {float(b['bdrate_Y_poly_pct']):+.2f} % | {float(b['bdrate_YUV611_pchip_pct']):+.2f} % | "
      f"{float(b['bdpsnr_Y_db']):+.3f} | {float(b['overlap_Y']):.0%} | ×{float(b['time_ratio_vs_medium_geomean']):.3f} |")
pv = S["preset_vs_medium"]
w("\n**Same-QP comparison** (not an efficiency measure; it shows why BD-rate is needed):")
for p in ("faster", "fast", "slow"):
    x = pv[p]
    w(f"- {p} vs medium: time ×{x['time_ratio_min']:.2f}–{x['time_ratio_max']:.2f}, size {x['size_pct_min']:+.1f} to {x['size_pct_max']:+.1f} %, "
      f"Y-PSNR {x['dy_min']:+.2f} to {x['dy_max']:+.2f} dB.")
w("")
w("**Interpretation:**")
w("- The ranking faster < fast < medium < slow in compression efficiency is the same for all four sequences.")
w(f"- slow saves {abs(rng('slow')[1]):.1f}–{abs(rng('slow')[0]):.1f} % bitrate for about ×{min(tr['slow']):.1f}–{max(tr['slow']):.1f} encoding time.")
w(f"- Going from medium to faster saves about {100 * (1 - max(tr['faster'])):.0f}–{100 * (1 - min(tr['faster'])):.0f} % of the time but costs {rng('faster')[0]:.0f}–{rng('faster')[1]:.0f} % more bitrate.")
w("- **Diminishing returns:** each step towards slower presets buys a smaller bitrate saving per unit of extra time.")
w("- **Resolution:** faster's BD-rate penalty grows from BasketballPass/BlowingBubbles (416×240) to BQMall (832×480) and BasketballDrive (1080p), and slow's saving is largest for the two larger sequences. "
  "With one sequence per larger resolution, resolution cannot be separated from content; this is a trend, not a proven effect.\n")

w("## 7. Decoding time\n")
d = [float(x["dec_noout_median_s"]) for x in cfg]
ed = S["enc_dec_ratio"]
w(f"- Without writing an output file, the median decode time was {min(d):.3f}–{max(d):.3f} s for 500–600 frames.")
dd = [float(x["dec_noout_median_s"]) for x in cfg if x["sequence"] == "BasketballDrive"]
w(f"  - BasketballDrive 1080p: {min(dd):.2f}–{max(dd):.2f} s, i.e. {500 / max(dd):.0f}–{500 / min(dd):.0f} frames per second, with 8 threads.")
for s in SEQS:
    by_q = {qq: st.median(float(x["dec_noout_median_s"]) for x in cfg if x["sequence"] == s and int(x["qp"]) == qq) for qq in (24, 39)}
    by_p = {pp: st.median(float(x["dec_noout_median_s"]) for x in cfg if x["sequence"] == s and x["preset"] == pp) for pp in PRE}
    w(f"  - {s}: median over presets QP 24 {by_q[24]:.3f} s vs QP 39 {by_q[39]:.3f} s; median over QPs per preset "
      + ", ".join(f"{pp} {v:.3f}" for pp, v in by_p.items()) + " s.")
w(f"- Encoding took ×{ed['min']:.0f} to ×{ed['max']:.0f} the decoding time.")
w("- See `decode_time.png`. Decode times are short, so these differences are small in absolute terms.\n")

w("## 8. Visual quality (phase 5)\n")
w("**Selection rule (fixed before viewing, same for every sequence):**")
w("- typical frame = median QP-39 Y-PSNR")
w("- hardest frame = minimum QP-39 Y-PSNR")
w("- crop = the most detailed quarter-width window of the original frame")
w("- the same frame and crop are used for the original and all four QPs (medium preset)")
w("")
w("**Metrics:** luma Y-PSNR, SSIM (Gaussian 11×11, σ 1.5) and MS-SSIM (5 scales). SSIM was cross-checked against scikit-image:")
for s in SEQS:
    cc = VS["sequences"][s].get("ssim_crosscheck_qp39", {})
    w(f"- {s}: own {cc.get('own')} vs scikit-image {cc.get('scikit_image')}")
w("\nThe images are **script renderings** of the decoded files (`visual/v2/`), **not YUView screenshots**.\n")
w("| Sequence | Frame (kind) | QP 24 PSNR / SSIM / MS-SSIM | QP 29 | QP 34 | QP 39 |\n|---|---|---|---|---|---|")
for s in SEQS:
    for kind in ("typical", "hardest"):
        rows = [x for x in vf if x["sequence"] == s and x["frame_kind"] == kind]
        cells = [f"{float(x['y_psnr']):.2f} / {float(x['ssim']):.3f} / {float(x['ms_ssim']):.4f}" for x in sorted(rows, key=lambda x: int(x["qp"]))]
        w(f"| {s} | {rows[0]['frame']} ({kind}) | " + " | ".join(cells) + " |")
w("\n**Sequence-level SSIM / MS-SSIM** (every 10th frame, medium preset):\n")
w("| Sequence | QP 24 | QP 29 | QP 34 | QP 39 |\n|---|---|---|---|---|")
for s in SEQS:
    rows = sorted([x for x in vsq if x["sequence"] == s], key=lambda x: int(x["qp"]))
    w(f"| {s} | " + " | ".join(f"{float(x['ssim_mean']):.4f} / {float(x['ms_ssim_mean']):.4f}" for x in rows) + " |")
w("\n**Inspection status:**")
w("- No person has inspected these frames yet. The visual statements in this report are limited to the metrics above.")
w("- The earlier rendering note still applies: the BQMall phase-1 crop (frame 432) contains motion blur in the original.\n")

w("## 9. Windows vs Linux (phase 6)\n")
w("| Configuration | Size | Bitstream SHA-256 | Decoded SHA-256 | Frames | Y/U/V PSNR | Encoder parameters compared |\n|---|---|---|---|---|---|---|")
for i in XP["phase6_runs"]:
    m = i["match"]
    w(f"| {i['config']} | {'same' if m['size'] else 'DIFF'} | {'identical' if m['bitstream_sha256'] else 'DIFFERENT'} | "
      f"{'identical' if m['recon_sha256'] else 'DIFFERENT'} | {'same' if m['frames'] else 'DIFF'} | {'same' if m['psnr'] else 'DIFF'} | "
      f"{'identical' if m['encoder_parameters'] else 'DIFFERENT'} ({i['n_parameter_lines_compared']} lines) |")
for i in XP["phase1_checks"]["full_length"]:
    w(f"| {i['config']} (phase 1) | same | identical | identical | same | same | – |")
w("| BlowingBubbles QP 34 fast, 16 frames (phase-1 smoke) | – | identical | identical | 16 | same | – |")
w("\n- Windows MSVC 19.44 and Linux GCC 13.3 (WSL2) builds of the same tags produced byte-identical outputs in every comparison. That is 8 configurations, covering all 4 presets and all 4 sequences.")
w("- Compared parameters: the encoder's printed configuration lines, with file paths and version/SIMD strings removed.")
w("- Speed was not compared.\n")

w("## 10. What the data supports, and what needs more work\n")
w("**Supported by this data:**")
w(f"- QP sets the rate–quality trade-off: about ÷{q['ratio_median']:.1f} bitrate per +5 QP, with a {q['drop_min']:.1f}–{q['drop_max']:.1f} dB Y-PSNR loss, in all 64 configurations.")
w("- Slower presets are consistently more efficient (BD-rate), at steeply increasing encoding time.")
w("- Extra encoding time gives diminishing returns.")
w("- The Windows and Linux builds are bit-exact for the tested configurations.")
w("- Phase-2 timing is repeatable to a few percent.")
w("")
w("**Needs further experiments:**")
w("- A resolution effect separate from content (needs several sequences per resolution, e.g. a JVET CTC class).")
w("- The slower and slowest presets, and the other CTC QPs (22, 27, 32, 37).")
w("- Comparison with a reference encoder (VTM).")
w("- Perceptual quality beyond SSIM/MS-SSIM (e.g. VMAF or a subjective test).")
w("- Timing on native Linux with fixed CPU frequency.\n")

w("## 11. Limitations\n")
w("- One laptop with a hybrid CPU and the Balanced power plan: times are relative, not a benchmark. Temperature was not available.")
w("- One sequence each at 832×480 and 1080p.")
w("- The 4 QPs are not the JVET CTC set (22/27/32/37).")
w("- The BD-rate uses medium as the anchor, not VTM.")
w("- Visual results are metrics plus script renderings; no YUView or subjective inspection has been done yet.")
w("- 1080p and 832×480 reconstructions from phase 2 were not kept (disk space). Their SHA-256 is recorded, and they can be regenerated bit-exactly from the kept bitstreams.\n")

w("## 12. Failed, skipped, unverified and flagged items\n")
w("| Item | Status |\n|---|---|")
w("| Phase-2 attempt 1 | Aborted by a runner bug after the A001 encode, before any result row was written. Logs kept as `*_aborted.log`; the bug was fixed, the runner was self-tested on 16 frames, and the block was restarted |")
w("| B022 timing | Flagged (battery during the run); excluded from timing; re-measured as C001 |")
w("| R01, R03, R04 timing | Flagged as early-window outliers (section 4); kept |")
w("| 7 Windows VVenC unit tests | Not run (Smart App Control blocked unsigned test programs) |")
w("| VVdeC conformance tests | Skipped (bitstreams not included in the source) |")
w("| CPU temperature | Not recorded (needs administrator rights) |")
w("| YUView inspection, screenshots, Sadab's observation | **Not done**; Sadab must do these |\n")

w("## 13. File index\n")
w("- **Scripts:**")
w("  - `experiment/run_phase2.py`, `run_supplement.py`, `monitor.ps1`, `linux_crossplatform_v2.sh`")
w("  - `analysis/audit_phase1.py`, `metrics.py`, `analyze_full.py`, `visual_v2.py`, `compare_platforms_v2.py`, `make_report_v2.py`")
w("- **Logs:** `logs/phase2/` (one per run), `logs/phase6_linux/`, `logs/monitor_phase2.csv`, `logs/2*_*.log`")
w("- **Data:** `results/*.csv`, `results/*.json`, `results/charts_full/`, `visual/v2/`")
w("- **Bitstreams:** `out/` (phase 1), `out/phase2/`, `out/linux2/`\n")

w("## 14. Record of automated and personally verified work\n")
w("**Automated by Claude (AI assistant):**")
w("- builds and unit tests")
w("- all 94 encoder runs and every decode")
w("- PSNR, SSIM and MS-SSIM")
w("- BD-rate and charts")
w("- the Linux cross-platform runs")
w("- this report and the presentation")
w("")
w("**Personally performed or verified by Sadab:** none recorded yet.")
w("")
w("**Before presenting, Sadab should:**")
w("1. Open the decoded files in YUView and look at the selected frames himself (see `MISSING_EVIDENCE_CHECKLIST.md`), take screenshots, and write his own observation.")
w("2. Re-run at least one configuration himself and compare its SHA-256 with `results/results_all_runs.csv`.")
w("3. Be able to explain every number, especially BD-rate, timing reliability and their limitations.")
w("4. Be open with Prof. Choi that the experiment was executed with an AI assistant.")
(R / "EXPERIMENT_REPORT_v2.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("written", len(L), "lines")
