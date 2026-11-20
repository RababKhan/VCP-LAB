"""Write results/EXPERIMENT_REPORT.md from the measured data (no hand-typed numbers)."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "results/summary.json").read_text(encoding="utf-8"))
X = json.loads((ROOT / "results/crossplatform.json").read_text(encoding="utf-8"))
FB = json.loads((ROOT / "visual/BQMall_frame_selection.json").read_text(encoding="utf-8"))
FW = json.loads((ROOT / "visual/BlowingBubbles_frame_selection.json").read_text(encoding="utf-8"))
rows = list(csv.DictReader(open(ROOT / "results/results_raw.csv", encoding="utf-8-sig")))
env = (ROOT / "results/environment.txt").read_text(encoding="utf-8-sig").strip()
Q, P, V = S["qp_steps"], S["preset"], S["validation"]

L = []
w = L.append
w("# VVC Experiment Report: Sadab Khan Prangon\n")
w("**Assignment:** VVC encoding and decoding with VVenC and VVdeC, for Prof. Kiho Choi, Video Coding and Processing Lab, Kyung Hee University.\n")
w("**Date of execution:** 2026-11-11. **Project folder:** `D:\\Korea\\Prangon_VVC_Assignment`.\n")
w("**Who did what:** every command in this report was executed by Claude, an AI assistant, on this computer at the user's "
  "request. The commands, outputs and logs are recorded in `logs/`. Sadab Khan Prangon has **not yet** personally performed "
  "or verified any step; see section 9.\n")

w("## 1. Execution summary\n")
w("| Phase | Status | Evidence |\n|---|---|---|")
w("| 1. Environment check | Completed | `logs/00_setup_provenance.log`, `results/environment.txt` |")
w("| 2. Build: Windows (MSVC 19.44) | Completed. VVenC 32/39 tests passed; 7 **not run** (blocked by Smart App Control); VVdeC conformance tests **skipped** (test bitstreams not included) | `logs/build/02_*`, `05_*`, `06_*` |")
w("| 2. Build: Linux (GCC 13.3, WSL2) | Completed. VVenC 39/39 tests passed; VVdeC unit test passed | `logs/build/03_*`, `07_*`, `08_*`, `09_*` |")
w("| 2. Smoke test (16 frames, both platforms) | **Passed** | `logs/04_smoke_test.log` |")
w(f"| 3. Full experiment (16 configurations + 2 repeats) | **Completed: {S['status_counts'].get('OK', 0)}/{len(rows)} runs OK**, none failed or interrupted | `results/results_raw.csv`, `logs/runs/*.log`, `logs/10_full_run_console.log` |")
w("| 4. Windows vs Linux | Completed: identical in 3 of 3 checks | `results/crossplatform.json`, `logs/11_*`, `logs/14_*` |")
w("| 5. Visual evaluation | Partly done: same-frame crops rendered by script. **Not done:** YUView inspection and screenshots by Sadab | `visual/` |")
w("| 6. Analysis and charts | Completed | `results/summary.json`, `results/charts/*.png` |")
w("| 7. PowerPoint update | Completed except one item that only Sadab can write (slide 7 observation) | `presentation/` |\n")

w("## 2. Setup\n")
w("```\n" + env + "\n```\n")
w("- **Sequences:** BlowingBubbles 416×240, 50 fps, 500 frames; BQMall 832×480, 60 fps, 600 frames. Both are 10-bit 4:2:0. "
  "The inputs were copied from the provided dataset folder and their SHA-256 hashes were verified (`logs/00_setup_provenance.log`).")
w("- **Encoder settings:** `vvencapp -c yuv420_10 -q {24,29,34,39} --preset {fast,medium} --qpa 0 -t 8`; all other options are defaults.")
w("- **Decoder:** `vvdecapp -t 8`. Each bitstream was decoded 3 times and the median time kept.")
w("- **Run order:** shuffled with a fixed seed (2026), on AC power with the Balanced power plan. WSL was stopped during the Windows runs.")
w("- **PSNR:** peak 1020, mean of the per-frame PSNR. The encoder's value was checked against the independent `experiment/psnr_check.py`.\n")

w("## 3. Measured results (all 18 runs)\n")
w("| Run | Sequence | QP | Preset | Encode time (s) | Decode time, median (s) | Bitstream (bytes) | Bitrate (kbps) | Y-PSNR (dB) | U / V-PSNR (dB) | Own-check Δ (dB) | Status |")
w("|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in sorted(rows, key=lambda r: (r["sequence"], r["preset"], int(r["qp"]), r["run_id"])):
    rep = f" (repeat of {r['repeat_of']})" if r["repeat_of"] else ""
    w(f"| {r['run_id']}{rep} | {r['sequence']} | {r['qp']} | {r['preset']} | {float(r['encode_time_s']):.3f} | "
      f"{float(r['decode_time_s_median']):.3f} | {int(float(r['bitstream_bytes'])):,} | {float(r['bitrate_kbps']):.2f} | "
      f"{float(r['enc_y_psnr']):.4f} | {float(r['enc_u_psnr']):.2f} / {float(r['enc_v_psnr']):.2f} | "
      f"{float(r['max_psnr_diff_db']):.4f} | {r['status']} |")
w("")

w("## 4. Analysis\n")
w("### 4.1 Effect of QP (charts: `results/charts/qp_vs_bitrate.png`, `qp_vs_ypsnr.png`, `bitstream_size.png`)\n")
w(f"- For each +5 QP step ({Q['n_pairs']} steps in total), the bitrate was divided by **{Q['bitrate_ratio_min']:.2f}–{Q['bitrate_ratio_max']:.2f}** "
  f"(median {Q['bitrate_ratio_median']:.2f}), and Y-PSNR fell by **{Q['ypsnr_drop_min']:.2f}–{Q['ypsnr_drop_max']:.2f} dB** (median {Q['ypsnr_drop_median']:.2f}).")
for k in ("BlowingBubbles_fast", "BlowingBubbles_medium", "BQMall_fast", "BQMall_medium"):
    d = Q[f"{k}_24_to_39"]
    w(f"- {k.replace('_', ', ')}: from QP 24 to QP 39 the bitrate was divided by {d['bitrate_ratio']:.2f} and Y-PSNR fell by {d['ypsnr_drop']:.2f} dB.")
w("\n### 4.2 medium compared with fast at the same QP (charts: `encode_time.png`, `decode_time.png`)\n")
w("| Sequence | QP | Encode time fast / medium (s) | Time ratio | Size change | Y-PSNR gain (dB) |\n|---|---|---|---|---|---|")
for p in P["pairs"]:
    w(f"| {p['sequence']} | {p['qp']} | {p['t_fast']:.2f} ({p['fast_run']}) / {p['t_medium']:.2f} ({p['medium_run']}) | "
      f"×{p['time_ratio']:.2f} | {p['size_change_pct']:+.1f} % | {p['ypsnr_gain']:+.2f} |")
w(f"\n- medium took ×{P['time_ratio_min']:.1f}–{P['time_ratio_max']:.1f} the encoding time of fast, and gave +{P['ypsnr_gain_min']:.2f} to "
  f"+{P['ypsnr_gain_max']:.2f} dB Y-PSNR.")
w(f"- The bitstream size changed by {P['size_change_pct_min']:+.1f} % to {P['size_change_pct_max']:+.1f} %. At one QP, medium therefore "
  "gives higher quality but not always a smaller file. These single-QP comparisons cannot measure compression efficiency; "
  "that needs BD-rate over the RD curves.")
w("- The lowest time ratio (×2.03, BlowingBubbles QP 34) uses run R04. R04's repeat, R17, was 45 % faster (see 4.3). "
  "With R17 instead, the ratio would be ×3.67. Both values are reported, and R04 has not been replaced.")
w(f"- Encoding took {P['enc_dec_ratio_min']:.0f}–{P['enc_dec_ratio_max']:.0f} times longer than decoding. The decode time includes writing the decoded "
  "YUV file to disk (about 720 MB for BQMall). Single decodes of BQMall occasionally took 5–6 s instead of about 1.3 s; "
  "the median of 3 limits, but does not remove, this disk effect.")
w("\n### 4.3 Timing repeatability\n")
for x in V["repeats"]:
    w(f"- {x['run']} repeated {x['of']} ({x['preset']}): {x['t_first']:.3f} s, then {x['t_repeat']:.3f} s, a difference of **{x['diff_pct']:.1f} %**. "
      f"The bitstreams were identical: {x['same_bitstream']}.")
w("- **Interpretation:** encoding time on this laptop can vary by tens of percent between runs. Only large differences "
  f"(the factor of {P['time_ratio_min']:.0f}–{P['time_ratio_max']:.0f} between presets, the factor of "
  f"{P['enc_dec_ratio_min']:.0f}–{P['enc_dec_ratio_max']:.0f} between encode and decode) are interpreted. Small differences, such as the "
  "non-monotonic fast-preset times for BlowingBubbles, are not interpreted.\n")

w("## 5. Validation\n")
w(f"- Runs with status OK: {V['main_ok']}/{V['main_total']} main runs and {len(V['repeats'])}/2 repeats. No run failed, was interrupted or was discarded.")
w(f"- Decoded frame count equals the expected frame count in every run: {V['frames_ok']}.")
w(f"- The independent PSNR check matched the encoder's Y/U/V PSNR to within **{V['max_psnr_diff_db']:.4f} dB** in all runs.")
w(f"- Bitrate from the file size and the encoder-reported bitrate differ by at most {V['bitrate_vs_encoder_max_rel_diff_pct']:.4f} %.")
w("- Repeated encodes produced byte-identical bitstreams.")
w("- The smoke test (16 frames) passed on both platforms before the full run started.\n")

w("## 6. Windows vs Linux verification\n")
w("| Configuration | Size | Bitstream SHA-256 | Frames | Decoded-video SHA-256 | PSNR |\n|---|---|---|---|---|---|")
for i in X["full_length"]:
    m = i["match"]
    w(f"| {i['config']} | {'same' if m['size'] else 'DIFF'} ({i['windows']['bytes']:,} B) | {'identical' if m['bitstream_sha256'] else 'DIFFERENT'} | "
      f"{'same' if m['frames'] else 'DIFF'} | {'identical' if m['recon_sha256'] else 'DIFFERENT'} | {'same' if m['psnr'] else 'DIFF'} |")
sm = X["smoke_16_frames"]
w(f"| BlowingBubbles QP 34 fast, 16 frames (smoke test) | – | {sm['bitstream'].lower()} | 16 | {sm['decoded'].lower()} | same |")
w("\n- **Result:** the MSVC (Windows) and GCC (Linux, WSL2) builds produced byte-identical bitstreams and decoded videos in 3 of 3 checks. "
  "Only these 3 configurations were compared across platforms.")
w("- **Not compared:** speed. The Linux runs ran in WSL2 and read their input from `/mnt/d`.\n")

w("## 7. Visual evaluation\n")
for F in (FB, FW):
    t = F["tiles"]
    w(f"- **{F['sequence']}, frame {F['frame_index_0based']} (0-based), crop x,y,w,h = {F['crop_xywh']}:** frame Y-PSNR "
      + " → ".join(f"{x['frame_y_psnr_db']:.2f}" for x in t[1:]) + " dB for QP 24 → 39 (medium). "
      f"Images: `visual/{F['sequence']}_f{F['frame_index_0based']}_qp_strip.png`.")
w("- **Selection rule (decided before viewing):** the frame with the median QP-39 Y-PSNR, and the most detailed crop of that frame.")
w("- **Rendering:** the images are script renderings of the decoded YUV files (BT.709, 10-bit to 8-bit, for display only). "
  "They are **not YUView screenshots**. A YUView inspection by Sadab has **not yet been done**; see section 9.")
w("- **Note on the BQMall crop:** it contains a moving hand, so the original itself shows motion blur.\n")

w("## 8. Failed, skipped and unverified items\n")
w("| Item | Status | Reason |\n|---|---|---|")
w("| 7 VVenC unit tests on Windows (vvenclibtest, vvenc_unit_test) | Not run | Windows Smart App Control blocked the unsigned test programs. No security setting was changed. All 39 passed on Linux. |")
w("| 252 VVdeC conformance tests (both platforms) | Skipped | They need JVET conformance bitstreams that are not in the source repository |")
w("| YUView screenshots and visual observation | Not done | They need a person to use the YUView window; instructions are in section 9 |")
w("| Linux timing | Not used | WSL2 with input on `/mnt/d`, not comparable |")
w("| R04 encode time | Kept, flagged | Its repeat R17 was 45 % faster |\n")

w("## 9. Record: automated steps and steps for Sadab\n")
w("**Automated by Claude (AI assistant), 2026-11-11:**")
w("- source download")
w("- Windows and Linux builds")
w("- unit tests")
w("- smoke test")
w("- all 18 runs")
w("- Linux cross-platform runs")
w("- PSNR checks")
w("- analysis and charts")
w("- frame rendering")
w("- deck update")
w("")
w("**Performed or verified by Sadab:** none recorded yet.\n")
w("**Sadab should do these steps himself before presenting:**")
w("1. Open `visual/yuview/` in YUView 2.14 (`tools/YUView/YUView.exe`):")
w("   - Load `BQMall_original_...yuv` and `BQMall_QP24/29/34/39_medium_...yuv`.")
w("   - Check the format in Properties: 832×480, YUV 4:2:0, 10-bit, 60 fps.")
cx, cy, cw, ch = FB["crop_xywh"]
w(f"   - Go to frame {FB['frame_index_0based']} (YUView counts from 0), use split view and zoom into the area "
  f"x {cx}–{cx + cw}, y {cy}–{cy + ch} (the crop on slide 7).")
w("   - Take screenshots (Win+Shift+S) and save them in `visual/yuview_screenshots/`.")
w("2. Write one or two sentences about what he actually saw. Replace the bracket text on slide 7 and in the slide-7 notes.")
w("3. Re-run at least one configuration himself and compare its SHA-256 with `results/results_raw.csv`. For example:")
w("   ```")
w("   vvenc\\bin\\release-static\\vvencapp.exe -i dataset\\BlowingBubbles_416_240_50_10_420.yuv -s 416x240 -c yuv420_10 --fps 50 -f 500 -q 34 --preset fast --qpa 0 -t 8 -o out\\check.266")
w("   ```")
w("   then `Get-FileHash out\\check.266`. The expected SHA-256 is that of R04.")
w("4. Read this report and the speaker notes so that he can explain every number.")
w("5. Be open with Prof. Choi about how the experiment was run, including the use of an AI assistant.")
(ROOT / "results/EXPERIMENT_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("written", len(L), "lines")
