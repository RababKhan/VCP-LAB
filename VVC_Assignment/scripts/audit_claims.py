"""Phase 7, part A: recompute the key numerical claims of the derived reports from the primary data.

Primary data (read only): results/full/results.csv, results/full/config_summary.csv,
results/full/timing_variability.csv, results/full/analysis_summary.json, results/supp_ac/timing_comparison.csv,
results/supp_ac/supp_summary.json, results/phase5_linux/cross_platform_comparison.json,
visual/phase6/tables/frame_metrics.csv, visual/phase6/analysis.json.

Each claim: (report, claim text as written, recomputed value(s), PASS/FAIL). The recomputed values are printed in
full, so a reader can check them without re-running anything.

Outputs: results/audit/claims_audit.json, results/audit/claims_audit.md
Usage: python audit_claims.py
"""
import csv
import json
import os
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "audit")
SEQ = ["BasketballPass", "BlowingBubbles", "BQMall", "BasketballDrive"]
PRESETS = ["faster", "fast", "medium", "slow", "slower"]
QPS = [22, 27, 32, 37]


def load_csv(*p):
    return list(csv.DictReader(open(os.path.join(ROOT, *p), encoding="utf-8")))


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = load_csv("results", "full", "results.csv")
    cfg = {(r["sequence"], int(r["qp"]), r["preset"]): r for r in load_csv("results", "full", "config_summary.csv")}
    var = load_csv("results", "full", "timing_variability.csv")
    summ = json.load(open(os.path.join(ROOT, "results", "full", "analysis_summary.json"), encoding="utf-8"))
    f = lambda s, q, p, k: float(cfg[(s, q, p)][k])  # noqa: E731
    claims = []

    def claim(report, text, value, ok):
        claims.append({"report": report, "claim": text, "recomputed": value, "result": "PASS" if ok else "FAIL"})

    R4 = "report/preliminary_results_report.md"
    claim(R4, "65/65 runs ok, 32/32 repeats byte-identical, PSNR diff to encoder 0.0000",
          [summ["present_runs"], len(summ["failed_runs"]), summ["repeats_identical_bitstream"], summ["max_abs_psnr_diff_vs_encoder"]],
          summ["all_complete_and_ok"] and summ["repeats_identical_bitstream"] == "32/32" and summ["max_abs_psnr_diff_vs_encoder"] == 0)
    ratios = [f(s, QPS[i], "medium", "bitrate_kbps") / f(s, QPS[i + 1], "medium", "bitrate_kbps") for s in SEQ for i in range(3)]
    claim(R4, "bitrate falls by 1.91-2.35x per +5 QP (median about 2.06)",
          [round(min(ratios), 2), round(max(ratios), 2), round(st.median(ratios), 3)],
          round(min(ratios), 2) == 1.91 and round(max(ratios), 2) == 2.35)
    dps = [f(s, QPS[i], "medium", "psnr_y") - f(s, QPS[i + 1], "medium", "psnr_y") for s in SEQ for i in range(3)]
    claim(R4, "Y-PSNR falls 1.45-3.93 dB per +5 QP", [round(min(dps), 2), round(max(dps), 2)],
          round(min(dps), 2) == 1.45 and round(max(dps), 2) == 3.93)
    tr = [f(s, 22, "medium", "enc_reported_s_median") / f(s, 37, "medium", "enc_reported_s_median") for s in SEQ]
    claim(R4, "QP 22 takes 2.7-3.7x as long as QP 37", [round(min(tr), 2), round(max(tr), 2)], 2.7 <= round(min(tr), 1) and round(max(tr), 1) <= 3.7)
    ed = [f(s, q, "medium", "enc_reported_s_median") / f(s, q, "medium", "dec_wall_s_median") for s in SEQ for q in QPS]
    claim(R4, "encoding 133-333x slower than decoding (medium, QP sweep)", [round(min(ed)), round(max(ed))],
          round(min(ed)) == 133 and round(max(ed)) == 333)

    def rel(p, k, ref="medium", mode="ratio"):
        out = []
        for s in SEQ:
            a, b = f(s, 32, p, k), f(s, 32, ref, k)
            out.append(a / b if mode == "ratio" else a - b)
        return out
    dfps = {s: [f(s, q, "medium", "dec_fps_median") for q in QPS] for s in SEQ}
    small = dfps["BasketballPass"] + dfps["BlowingBubbles"]
    claim(R4, "decoding 134-220 fps (1080p) and 1,400-3,100 fps (240p), preset medium (corrected 2026-11-05 from 1,400-2,900)",
          {"1080p": [round(min(dfps["BasketballDrive"])), round(max(dfps["BasketballDrive"]))], "240p": [round(min(small)), round(max(small))]},
          round(min(dfps["BasketballDrive"])) == 134 and round(max(dfps["BasketballDrive"])) == 220 and 1400 <= min(small) and max(small) <= 3100)
    offI = [f(s, q, "medium", "avg_qp_I") - q for s in SEQ for q in QPS]
    offB = [f(s, q, "medium", "avg_qp_B") - q for s in SEQ for q in QPS]
    claim("report/phase7_professor_QA.md", "average slice QP: I pictures 2.7-3.6 below -q, B pictures 5.7-8.6 above -q",
          {"I": [round(min(offI), 2), round(max(offI), 2)], "B": [round(min(offB), 2), round(max(offB), 2)]},
          round(-max(offI), 1) >= 2.7 and round(-min(offI), 1) <= 3.6 and round(min(offB), 1) >= 5.7 and round(max(offB), 1) <= 8.6)
    for p, lo, hi in (("faster", 0.11, 0.13), ("fast", 0.27, 0.30), ("slow", 3.25, 3.71), ("slower", 14.44, 17.06)):
        v = rel(p, "enc_reported_s_median")
        claim(R4, f"{p} encode time vs medium {lo}-{hi}x", [round(x, 3) for x in v], lo - 0.005 <= min(v) and max(v) <= hi + 0.005)
    v_db, v_sz = rel("slower", "psnr_y", mode="diff"), [100 * (1 - x) for x in rel("slower", "bitstream_bytes")]
    claim(R4, "MEDIUM -> SLOWER: +0.24 to +0.37 dB Y-PSNR, 1.5-4.3% smaller (4 sequences, sequence level; corrected 2026-11-05 from +0.38)",
          {"dB": [round(x, 4) for x in v_db], "pct_smaller": [round(x, 2) for x in v_sz]},
          round(min(v_db), 2) == 0.24 and round(max(v_db), 2) == 0.37 and round(min(v_sz), 1) == 1.5 and round(max(v_sz), 1) == 4.3)
    v_db2 = rel("slower", "psnr_y", ref="faster", mode="diff")
    v_sz2 = [100 * (1 - x) for x in rel("slower", "bitstream_bytes", ref="faster")]
    claim(R4, "FASTER -> SLOWER: +0.69 to +0.98 dB, 7-15% smaller (4 sequences, sequence level)",
          {"dB": [round(x, 4) for x in v_db2], "pct_smaller": [round(x, 2) for x in v_sz2]},
          round(min(v_db2), 2) == 0.69 and round(max(v_db2), 2) == 0.98 and 7 <= min(v_sz2) and max(v_sz2) < 15.5)
    v_db3 = rel("medium", "psnr_y", ref="faster", mode="diff")
    v_sz3 = [100 * (1 - x) for x in rel("medium", "bitstream_bytes", ref="faster")]
    v_t3 = [1 / x for x in rel("faster", "enc_reported_s_median")]
    claim(R4, "FASTER -> MEDIUM: 7.7-9.5x time, +0.45 to +0.66 dB, 6-12% smaller (corrected 2026-11-05 from 7.7-9.1x)",
          {"time_x": [round(x, 2) for x in v_t3], "dB": [round(x, 3) for x in v_db3], "pct_smaller": [round(x, 2) for x in v_sz3]},
          7.6 <= min(v_t3) and max(v_t3) <= 9.55 and round(min(v_db3), 2) >= 0.44 and round(max(v_db3), 2) <= 0.66)
    cv = sorted(float(v["enc_wall_cv_pct"]) for v in var)
    claim(R4, "encode CV median 2.4%, range 0.40-5.27% excluding the 14.1% battery outlier",
          {"median": round(st.median(cv), 2), "min": round(cv[0], 2), "max_excl_outlier": round(cv[-2], 2), "max": round(cv[-1], 2)},
          round(st.median(cv), 1) == 2.4 and round(cv[-2], 2) == 5.27)
    bf = float(cfg[("BlowingBubbles", 32, "fast")]["bitstream_bytes"]) / float(cfg[("BlowingBubbles", 32, "medium")]["bitstream_bytes"])
    claim(R4, "BlowingBubbles fast is 0.58% smaller than medium, with -0.44 dB", [round(100 * (1 - bf), 2),
          round(f("BlowingBubbles", 32, "fast", "psnr_y") - f("BlowingBubbles", 32, "medium", "psnr_y"), 3)], round(100 * (1 - bf), 2) == 0.58)
    claim(R4, "battery interval 14:27:34-15:31:17; 11 runs with battery exposure",
          [summ["battery_intervals"], len(summ["runs_with_battery_samples"])],
          summ["battery_intervals"] == [["2026-11-04T14:27:34", "2026-11-04T15:31:17"]] and len(summ["runs_with_battery_samples"]) == 11)

    RS = "report/preliminary_results_report.md section 9"
    tc = {(r["configuration"], r["metric"]): r for r in load_csv("results", "supp_ac", "timing_comparison.csv")}
    for c, d in (("BQMall_f600_q32_faster_t8", -18.71), ("BasketballDrive_f500_q32_fast_t8", -2.39),
                 ("BQMall_f600_q22_medium_t8", 0.87), ("BasketballDrive_f500_q32_slower_t8", -2.82)):
        x = float(tc[(c, "encode_reported_s")]["diff_pct"])
        claim(RS, f"{c}: encode reported diff {d:+.2f}%", x, abs(x - d) < 0.005)
    ss = json.load(open(os.path.join(ROOT, "results", "supp_ac", "supp_summary.json"), encoding="utf-8"))
    claim(RS, "all supplementary runs AC-valid and bitstream-identical",
          {k: [v["timing_valid_ac"], v["bitstream_sha256_identical"]] for k, v in ss["runs"].items()},
          all(v["timing_valid_ac"] and v["bitstream_sha256_identical"] for v in ss["runs"].values()) and ss["results_full_unchanged"])

    R5 = "report/phase5_linux_build_report.md"
    cp = json.load(open(os.path.join(ROOT, "results", "phase5_linux", "cross_platform_comparison.json"), encoding="utf-8"))
    claim(R5, "Windows and Linux smoke bitstream and recon byte-identical; PSNR identical; 16 frames",
          {k: cp["checks"][k] for k in ("bitstream_identical_windows_linux", "recon_identical_windows_linux", "psnr_identical_windows_linux",
                                         "decoded_frames_16_both", "linux_runs_deterministic_bitstream")},
          all(cp["checks"][k] for k in ("bitstream_identical_windows_linux", "recon_identical_windows_linux", "psnr_identical_windows_linux",
                                         "decoded_frames_16_both", "linux_runs_deterministic_bitstream")))

    R6 = "report/phase6_visual_evaluation_report.md + phase6_summary_for_prof_kiho.md"
    fm = load_csv("visual", "phase6", "tables", "frame_metrics.csv")
    g = {(r["sequence"], int(r["frame_index"]), int(r["qp"]), r["preset"]): r for r in fm}
    frames = sorted({(r["sequence"], int(r["frame_index"])) for r in fm})
    dq = {s: [float(g[(s, i, 22, "medium")]["frame_psnr_y"]) - float(g[(s, i, 37, "medium")]["frame_psnr_y"]) for (s2, i) in frames if s2 == s]
          for s in ("BasketballPass", "BQMall")}
    claim(R6, "frame Y-PSNR QP22->QP37 drop 9.8-10.2 dB (BasketballPass), 7.9-8.7 dB (BQMall)",
          {s: [round(min(v), 2), round(max(v), 2)] for s, v in dq.items()},
          round(min(dq["BasketballPass"]), 1) == 9.8 and round(max(dq["BasketballPass"]), 1) == 10.2 and round(min(dq["BQMall"]), 1) == 7.9)
    sp = [float(g[(s, i, 32, "slower")]["frame_psnr_y"]) - float(g[(s, i, 32, "faster")]["frame_psnr_y"]) for s, i in frames]
    claim(R6, "FRAME-level faster->slower spread 0.24-1.31 dB (6 selected frames)", [round(x, 2) for x in sp],
          round(min(sp), 2) == 0.24 and round(max(sp), 2) == 1.31)
    sq = {s: (f(s, 32, "slower", "psnr_y") - f(s, 32, "faster", "psnr_y"), 100 * (1 - f(s, 32, "slower", "bitstream_bytes") / f(s, 32, "faster", "bitstream_bytes")))
          for s in ("BasketballPass", "BQMall")}
    claim(R6, "SEQUENCE-level FASTER->SLOWER +0.84 to +0.98 dB and 13% / 15% smaller (BasketballPass, BQMall only)",
          {s: [round(a, 4), round(b, 2)] for s, (a, b) in sq.items()},
          round(sq["BasketballPass"][0], 2) == 0.84 and round(sq["BQMall"][0], 2) == 0.98)
    va = json.load(open(os.path.join(ROOT, "visual", "phase6", "analysis.json"), encoding="utf-8"))
    pi = va["preset_investigation"]["BasketballPass"]["medium_lower_than_faster"]
    claim(R6, "BasketballPass: medium below faster in 67 frames (13.4%), all with more bits in faster, 59 with lower slice QP",
          [pi["frames"], pi["pct_of_frames"], pi["of_which_faster_preset_spent_more_bits"], pi["of_which_faster_preset_had_lower_slice_qp"]],
          pi["frames"] == 67 and pi["of_which_faster_preset_spent_more_bits"] == 67 and pi["of_which_faster_preset_had_lower_slice_qp"] == 59)
    idr = {s: va["preset_investigation"][s]["selected_frames_detail"][str(fi)]["medium"]["qp"]
           for s, fi in (("BasketballPass", 15), ("BQMall", 31))}
    claim(R6, "IDR slice QP for -q 32: BasketballPass 27, BQMall 29 (corrected 2026-11-05; was 'IDR at QP 27')", idr,
          idr == {"BasketballPass": 27, "BQMall": 29})

    with open(os.path.join(OUT, "claims_audit.json"), "w", encoding="utf-8") as fo:
        json.dump(claims, fo, indent=2)
    md = ["| # | Report | Claim | Recomputed | Result |", "|---|---|---|---|---|"]
    for i, c in enumerate(claims, 1):
        md.append(f"| {i} | {c['report']} | {c['claim']} | `{json.dumps(c['recomputed'])}` | {c['result']} |")
    open(os.path.join(OUT, "claims_audit.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\n{sum(c['result'] == 'PASS' for c in claims)}/{len(claims)} PASS")


if __name__ == "__main__":
    main()
