"""Analyse Sadab's measured results (results/results_raw.csv) -> summary JSON, charts and validation numbers.
Only values present in the CSV are used; nothing is estimated or filled in."""
import csv
import json
import math
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
CH = RES / "charts"
CH.mkdir(exist_ok=True)
rows = list(csv.DictReader(open(RES / "results_raw.csv", encoding="utf-8-sig")))
NUM = ["width", "height", "fps", "frames", "qp", "threads", "encode_time_s", "encode_wall_s", "decode_time_s_median",
       "bitstream_bytes", "bitrate_kbps", "enc_bitrate_kbps", "enc_y_psnr", "enc_u_psnr", "enc_v_psnr", "enc_yuv_psnr",
       "check_y_psnr", "check_u_psnr", "check_v_psnr", "max_psnr_diff_db", "recon_frames"]
for r in rows:
    for k in NUM:
        r[k] = float(r[k]) if r.get(k) not in (None, "") else None

SEQS = ["BlowingBubbles", "BQMall"]
PRESETS = ["fast", "medium"]
QPS = [24, 29, 34, 39]
main = [r for r in rows if not r["repeat_of"]]
reps = [r for r in rows if r["repeat_of"]]
ok = [r for r in main if r["status"] == "OK"]


def get(seq, preset, qp):
    m = [r for r in main if r["sequence"] == seq and r["preset"] == preset and int(r["qp"]) == qp and r["status"] == "OK"]
    return m[0] if m else None


summary = {"status_counts": {}, "per_config": [], "qp_steps": {}, "preset": {}, "validation": {}}
for r in rows:
    summary["status_counts"][r["status"]] = summary["status_counts"].get(r["status"], 0) + 1

for seq in SEQS:
    for p in PRESETS:
        for q in QPS:
            r = get(seq, p, q)
            if r:
                summary["per_config"].append({k: r[k] for k in ["run_id", "sequence", "preset", "qp", "encode_time_s",
                                                                "decode_time_s_median", "bitstream_bytes", "bitrate_kbps",
                                                                "enc_y_psnr", "check_y_psnr", "max_psnr_diff_db"]})

# effect of +5 QP (consecutive QP pairs)
ratios, drops = [], []
for seq in SEQS:
    for p in PRESETS:
        for a, b in zip(QPS, QPS[1:]):
            ra, rb = get(seq, p, a), get(seq, p, b)
            if ra and rb:
                ratios.append(ra["bitrate_kbps"] / rb["bitrate_kbps"])
                drops.append(ra["enc_y_psnr"] - rb["enc_y_psnr"])
summary["qp_steps"] = {"n_pairs": len(ratios), "bitrate_ratio_min": min(ratios), "bitrate_ratio_max": max(ratios),
                       "bitrate_ratio_median": st.median(ratios), "ypsnr_drop_min": min(drops),
                       "ypsnr_drop_max": max(drops), "ypsnr_drop_median": st.median(drops)}
for seq in SEQS:
    for p in PRESETS:
        lo, hi = get(seq, p, 24), get(seq, p, 39)
        if lo and hi:
            summary["qp_steps"][f"{seq}_{p}_24_to_39"] = {"bitrate_ratio": lo["bitrate_kbps"] / hi["bitrate_kbps"],
                                                          "ypsnr_drop": lo["enc_y_psnr"] - hi["enc_y_psnr"]}

# medium vs fast at the same QP
tr, sz, dp, ed = [], [], [], []
pairs = []
for seq in SEQS:
    for q in QPS:
        f, m = get(seq, "fast", q), get(seq, "medium", q)
        if f and m:
            pairs.append({"sequence": seq, "qp": q, "fast_run": f["run_id"], "medium_run": m["run_id"],
                          "t_fast": f["encode_time_s"], "t_medium": m["encode_time_s"],
                          "time_ratio": m["encode_time_s"] / f["encode_time_s"],
                          "size_change_pct": (m["bitstream_bytes"] / f["bitstream_bytes"] - 1) * 100,
                          "ypsnr_gain": m["enc_y_psnr"] - f["enc_y_psnr"],
                          "dec_fast": f["decode_time_s_median"], "dec_medium": m["decode_time_s_median"],
                          "dec_runs_fast": f["decode_times_s"], "dec_runs_medium": m["decode_times_s"]})
            tr.append(m["encode_time_s"] / f["encode_time_s"])
            sz.append((m["bitstream_bytes"] / f["bitstream_bytes"] - 1) * 100)
            dp.append(m["enc_y_psnr"] - f["enc_y_psnr"])
for r in ok:
    if r["decode_time_s_median"]:
        ed.append(r["encode_time_s"] / r["decode_time_s_median"])
summary["preset"] = {"n_pairs": len(tr), "time_ratio_min": min(tr), "time_ratio_max": max(tr),
                     "size_change_pct_min": min(sz), "size_change_pct_max": max(sz),
                     "ypsnr_gain_min": min(dp), "ypsnr_gain_max": max(dp),
                     "enc_dec_ratio_min": min(ed), "enc_dec_ratio_max": max(ed), "pairs": pairs}

# validation
noise = []
for r in reps:
    o = [x for x in rows if x["run_id"] == r["repeat_of"]][0]
    if r["encode_time_s"] and o["encode_time_s"]:
        noise.append({"run": r["run_id"], "of": o["run_id"], "preset": r["preset"],
                      "t_first": o["encode_time_s"], "t_repeat": r["encode_time_s"],
                      "diff_pct": abs(r["encode_time_s"] - o["encode_time_s"]) / o["encode_time_s"] * 100,
                      "same_bitstream": r["bitstream_sha256"] == o["bitstream_sha256"]})
summary["validation"] = {
    "runs_total": len(rows), "main_ok": len(ok), "main_total": len(main),
    "max_psnr_diff_db": max(r["max_psnr_diff_db"] for r in rows if r["max_psnr_diff_db"] is not None),
    "frames_ok": all(r["recon_frames"] == r["frames"] for r in rows if r["status"] == "OK"),
    "bitrate_vs_encoder_max_rel_diff_pct": max(abs(r["bitrate_kbps"] / r["enc_bitrate_kbps"] - 1) * 100
                                               for r in rows if r["enc_bitrate_kbps"]),
    "repeats": noise, "notes": [f'{r["run_id"]}: {r["notes"]}' for r in rows if r["notes"]],
}
(RES / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

# ---- charts (PNG for the report; the deck uses native PowerPoint charts) -------------------------
COL = {"fast": "#E8710A", "medium": "#0053A3"}
plt.rcParams.update({"font.family": "Arial", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#90A4AE", "axes.labelcolor": "#263238", "xtick.color": "#607D8B",
                     "ytick.color": "#607D8B", "axes.grid": True, "grid.color": "#ECEFF1"})


def panel_chart(fname, ylab, key, logy=False, title=""):
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
    for ax, seq in zip(axs, SEQS):
        for p in PRESETS:
            pts = [(q, get(seq, p, q)[key]) for q in QPS if get(seq, p, q)]
            ax.plot([a for a, _ in pts], [b for _, b in pts], marker="o", ms=6, lw=2, color=COL[p], label=p)
        ax.set_title(seq, fontsize=11, color="#263238", loc="left")
        ax.set_xticks(QPS); ax.set_xlabel("QP")
        if logy:
            ax.set_yscale("log")
        ax.set_ylabel(ylab)
    axs[0].legend(frameon=False)
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, color="#263238")
    fig.tight_layout()
    fig.savefig(CH / fname, dpi=160)
    plt.close(fig)


panel_chart("qp_vs_bitrate.png", "bitrate (kbps, log scale)", "bitrate_kbps", True, "QP versus bitrate")
panel_chart("qp_vs_ypsnr.png", "Y-PSNR (dB)", "enc_y_psnr", False, "QP versus Y-PSNR")
panel_chart("encode_time.png", "encoding time (s, log scale)", "encode_time_s", True, "Encoding time")
panel_chart("decode_time.png", "decoding time (s, median of 3)", "decode_time_s_median", False, "Decoding time")
panel_chart("bitstream_size.png", "bitstream size (bytes, log scale)", "bitstream_bytes", True, "Bitstream size")
for p in pairs:
    print("{sequence:14s} QP{qp} | {fast_run} {t_fast:7.2f}s  {medium_run} {t_medium:7.2f}s  x{time_ratio:4.2f} | size {size_change_pct:+5.1f}% "
          "| dY {ypsnr_gain:+.2f} dB | dec {dec_fast}/{dec_medium} [{dec_runs_fast}] [{dec_runs_medium}]".format(**p))
print(json.dumps({k: summary[k] for k in ("status_counts", "qp_steps")}, indent=1)[:3000])
print(json.dumps(summary["validation"], indent=1))
