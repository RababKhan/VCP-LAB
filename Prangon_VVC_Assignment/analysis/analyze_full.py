"""Full analysis of Sadab's expanded experiment (phase 1 + phase 2). Only measured values are used.

Outputs:
  results/results_all_runs.csv      every run of both phases in one table (source column says which)
  results/config_summary.csv        one row per configuration (64): rate/quality + timing statistics
  results/timing_reliability.csv    every configuration with >= 2 encode measurements
  results/bdrate.csv                BD-rate of faster / fast / slow against medium, per sequence
  results/summary_full.json         numbers used in the report and the deck
  results/charts_full/*.png         charts for the report
"""
import csv
import json
import math
import statistics as st
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import metrics  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
CH = RES / "charts_full"
CH.mkdir(exist_ok=True)
SEQS = ["BasketballPass", "BlowingBubbles", "BQMall", "BasketballDrive"]
RESO = {"BasketballPass": "416×240", "BlowingBubbles": "416×240", "BQMall": "832×480", "BasketballDrive": "1920×1080"}
PRESETS = ["faster", "fast", "medium", "slow"]
QPS = [24, 29, 34, 39]

p1 = list(csv.DictReader(open(RES / "results_raw.csv", encoding="utf-8-sig")))
p2 = list(csv.DictReader(open(RES / "results_phase2.csv", encoding="utf-8")))
dp = {r["run_id"]: r for r in csv.DictReader(open(RES / "decode_timing_phase1_bitstreams.csv", encoding="utf-8"))} \
    if (RES / "decode_timing_phase1_bitstreams.csv").exists() else {}
mon = []
if (ROOT / "logs/monitor_phase2.csv").exists():
    for r in csv.DictReader(open(ROOT / "logs/monitor_phase2.csv", encoding="utf-8-sig")):
        try:
            mon.append((datetime.fromisoformat(r["time_iso"]), float(r["cpu_utility_pct"]), float(r["cpu_performance_pct"]), int(r["on_ac"])))
        except (ValueError, KeyError):
            pass

# ---- unified run table --------------------------------------------------------------------------
runs = []
for r in p1:
    runs.append(dict(source="phase1", run_id=r["run_id"], kind="repeat" if r["repeat_of"] else "main", repeat_of=r["repeat_of"],
                     status=r["status"], sequence=r["sequence"], qp=int(r["qp"]), preset=r["preset"],
                     start=r["started"], encode_time_s=float(r["encode_time_s"]), bitstream_bytes=int(r["bitstream_bytes"]),
                     bitrate_kbps=float(r["bitrate_kbps"]), y=float(r["enc_y_psnr"]), u=float(r["enc_u_psnr"]), v=float(r["enc_v_psnr"]),
                     check_diff=float(r["max_psnr_diff_db"]), sha=r["bitstream_sha256"], frames_ok=float(r["recon_frames"]) == float(r["frames"]),
                     dec_with_output_median=float(r["decode_time_s_median"]),
                     dec_noout_median=float(dp[r["run_id"]]["decode_noout_median_s"]) if r["run_id"] in dp else None,
                     cpu_perf_mean=None, notes=r["notes"]))
for r in p2:
    if r["status"] not in ("OK", "CHECK"):
        runs.append(dict(source="phase2", run_id=r["run_id"], kind=r["kind"], repeat_of=r["repeat_of"], status=r["status"],
                         sequence=r["sequence"], qp=int(r["qp"]), preset=r["preset"], start=r["start_iso"], notes=r["notes"]))
        continue
    t0, t1 = datetime.fromisoformat(r["start_iso"]), datetime.fromisoformat(r["end_iso"])
    win = [m for m in mon if t0 <= m[0] <= t1]
    runs.append(dict(source="phase2", run_id=r["run_id"], kind=r["kind"], repeat_of=r["repeat_of"], status=r["status"],
                     sequence=r["sequence"], qp=int(r["qp"]), preset=r["preset"], start=r["start_iso"],
                     encode_time_s=float(r["encode_time_s"]), bitstream_bytes=int(r["bitstream_bytes"]),
                     bitrate_kbps=float(r["bitrate_kbps"]), y=float(r["enc_y_psnr"]), u=float(r["enc_u_psnr"]), v=float(r["enc_v_psnr"]),
                     check_diff=float(r["max_psnr_diff_db"]), sha=r["bitstream_sha256"],
                     frames_ok=float(r["recon_frames"]) == float(r["frames"]),
                     dec_with_output_median=float(r["decode_with_output_s"]) if r["decode_with_output_s"] else None,
                     dec_noout_median=float(r["decode_noout_median_s"]) if r["decode_noout_median_s"] else None,
                     cpu_perf_mean=round(st.mean(m[2] for m in win), 1) if win else None,
                     cpu_util_mean=round(st.mean(m[1] for m in win), 1) if win else None,
                     ac_all=all(m[3] == 1 for m in win) if win else None, notes=r["notes"]))
keys = sorted({k for r in runs for k in r})
with open(RES / "results_all_runs.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, keys)
    w.writeheader()
    w.writerows(runs)
good = [r for r in runs if r["status"] in ("OK", "CHECK")]

# ---- per configuration -----------------------------------------------------------------------------
cfg = {}
for s in SEQS:
    for p in PRESETS:
        for q in QPS:
            rs = [r for r in good if r["sequence"] == s and r["preset"] == p and r["qp"] == q]
            if not rs:
                cfg[(s, p, q)] = None
                continue
            timed = [r for r in rs if "battery" not in (r.get("notes") or "")]   # power-flagged runs: not used for timing
            t = [r["encode_time_s"] for r in timed]
            d = [r["dec_noout_median"] for r in rs if r["dec_noout_median"] is not None]
            m = rs[0]
            cfg[(s, p, q)] = dict(sequence=s, preset=p, qp=q, n_runs=len(rs), n_timed=len(timed),
                                  runs=";".join(r["run_id"] for r in rs),
                                  excluded_from_timing=";".join(r["run_id"] for r in rs if r not in timed),
                                  deterministic=len({r["sha"] for r in rs}) == 1, bitstream_bytes=m["bitstream_bytes"],
                                  bitrate_kbps=m["bitrate_kbps"], y=m["y"], u=m["u"], v=m["v"], yuv611=(6 * m["y"] + m["u"] + m["v"]) / 8,
                                  enc_median_s=st.median(t), enc_min_s=min(t), enc_max_s=max(t),
                                  enc_spread_pct=(max(t) - min(t)) / st.median(t) * 100 if len(t) > 1 else None,
                                  enc_times="; ".join(f"{x:.2f}" for x in t),
                                  dec_noout_median_s=st.median(d) if d else None, max_check_diff=max(r["check_diff"] for r in rs))
with open(RES / "config_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(next(c for c in cfg.values() if c).keys()))
    w.writeheader()
    for c in cfg.values():
        if c:
            w.writerow(c)
missing = [k for k, c in cfg.items() if c is None]

# ---- timing reliability ----------------------------------------------------------------------------
rel = []
for c in cfg.values():
    if c and c["n_timed"] >= 2:
        rs = [r for r in good if r["sequence"] == c["sequence"] and r["preset"] == c["preset"] and r["qp"] == c["qp"]
              and "battery" not in (r.get("notes") or "")]
        med = c["enc_median_s"]
        rel.append(dict(config=f"{c['sequence']} QP{c['qp']} {c['preset']}", n=len(rs), median_s=round(med, 3),
                        min_s=round(c["enc_min_s"], 3), max_s=round(c["enc_max_s"], 3), spread_pct=round(c["enc_spread_pct"], 1),
                        cv_pct=round(st.stdev([r["encode_time_s"] for r in rs]) / st.mean([r["encode_time_s"] for r in rs]) * 100, 1),
                        measurements="; ".join(f"{r['run_id']}={r['encode_time_s']:.2f}s" for r in rs),
                        outliers="; ".join(f"{r['run_id']} ({r['encode_time_s'] / med:.2f}x median)" for r in rs
                                           if abs(r["encode_time_s"] / med - 1) > 0.15),
                        identical_bitstreams=c["deterministic"]))
with open(RES / "timing_reliability.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(rel[0].keys()) if rel else ["config"])
    w.writeheader()
    w.writerows(rel)

# ---- BD-rate against medium ------------------------------------------------------------------------
bd = []
for s in SEQS:
    a = [cfg[(s, "medium", q)] for q in QPS]
    if None in a:
        continue
    for p in ("faster", "fast", "slow"):
        t = [cfg[(s, p, q)] for q in QPS]
        if None in t:
            bd.append(dict(sequence=s, test=p, anchor="medium", status="unavailable: missing runs"))
            continue
        ra, rt = [c["bitrate_kbps"] for c in a], [c["bitrate_kbps"] for c in t]
        row = dict(sequence=s, resolution=RESO[s], test=p, anchor="medium")
        for metric, key in (("Y", "y"), ("YUV611", "yuv611")):
            pa, pt = [c[key] for c in a], [c[key] for c in t]
            v, why = metrics.bd_rate(ra, pa, rt, pt, "pchip")
            v2, _ = metrics.bd_rate(ra, pa, rt, pt, "poly")
            row[f"bdrate_{metric}_pchip_pct"] = round(v, 2) if v is not None else ""
            row[f"bdrate_{metric}_poly_pct"] = round(v2, 2) if v2 is not None else ""
            row[f"overlap_{metric}"] = round(metrics.overlap_fraction(pa, pt), 2)
            row[f"status_{metric}"] = "ok" if v is not None else f"unavailable: {why}"
        row["bdpsnr_Y_db"] = round(metrics.bd_psnr(ra, [c["y"] for c in a], rt, [c["y"] for c in t]), 3)
        tr = [cfg[(s, p, q)]["enc_median_s"] / cfg[(s, "medium", q)]["enc_median_s"] for q in QPS]
        row["time_ratio_vs_medium_geomean"] = round(math.exp(st.mean(math.log(x) for x in tr)), 3)
        row["status"] = "ok"
        bd.append(row)
with open(RES / "bdrate.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, sorted({k for r in bd for k in r}))
    w.writeheader()
    w.writerows(bd)

# ---- QP steps, preset ratios, resolution -----------------------------------------------------------
steps = []
for s in SEQS:
    for p in PRESETS:
        for a_, b_ in zip(QPS, QPS[1:]):
            ca, cb = cfg[(s, p, a_)], cfg[(s, p, b_)]
            if ca and cb:
                steps.append(dict(seq=s, preset=p, ratio=ca["bitrate_kbps"] / cb["bitrate_kbps"], drop=ca["y"] - cb["y"]))
pr = {}
for p in ("faster", "fast", "slow"):
    tr, sz, dy = [], [], []
    for s in SEQS:
        for q in QPS:
            c, m = cfg[(s, p, q)], cfg[(s, "medium", q)]
            if c and m:
                tr.append(c["enc_median_s"] / m["enc_median_s"])
                sz.append((c["bitstream_bytes"] / m["bitstream_bytes"] - 1) * 100)
                dy.append(c["y"] - m["y"])
    if tr:
        pr[p] = dict(time_ratio_min=min(tr), time_ratio_max=max(tr), size_pct_min=min(sz), size_pct_max=max(sz),
                     dy_min=min(dy), dy_max=max(dy), n=len(tr))
encdec = [c["enc_median_s"] / c["dec_noout_median_s"] for c in cfg.values() if c and c["dec_noout_median_s"]]
summary = dict(
    n_configs_measured=sum(1 for c in cfg.values() if c), missing_configs=[f"{k[0]} {k[1]} QP{k[2]}" for k in missing],
    runs_total=len(runs), runs_ok=sum(r["status"] == "OK" for r in runs), runs_check=sum(r["status"] == "CHECK" for r in runs),
    runs_failed=[r["run_id"] for r in runs if r["status"] not in ("OK", "CHECK")],
    max_psnr_check_diff=max(r["check_diff"] for r in good), all_frames_ok=all(r["frames_ok"] for r in good),
    all_configs_deterministic=all(c["deterministic"] for c in cfg.values() if c),
    qp_step=dict(ratio_min=min(x["ratio"] for x in steps), ratio_max=max(x["ratio"] for x in steps),
                 ratio_median=st.median(x["ratio"] for x in steps), drop_min=min(x["drop"] for x in steps),
                 drop_max=max(x["drop"] for x in steps), drop_median=st.median(x["drop"] for x in steps), n=len(steps)),
    preset_vs_medium=pr, enc_dec_ratio=dict(min=min(encdec), max=max(encdec)) if encdec else None,
    timing=dict(n_configs=len(rel), spread_median_pct=st.median(x["spread_pct"] for x in rel) if rel else None,
                cv_median_pct=st.median(x["cv_pct"] for x in rel) if rel else None,
                configs_with_outliers=[x["config"] for x in rel if x["outliers"]]),
    bdrate=bd,
)
(RES / "summary_full.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

# ---- charts ----------------------------------------------------------------------------------------
COL = {"faster": "#F2A541", "fast": "#E8710A", "medium": "#0053A3", "slow": "#00897B"}
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#90A4AE", "axes.grid": True, "grid.color": "#ECEFF1", "xtick.color": "#607D8B",
                     "ytick.color": "#607D8B", "axes.labelcolor": "#263238"})


def grid(fname, title, fn):
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.3))
    for ax, s in zip(axs, SEQS):
        fn(ax, s)
        ax.set_title(f"{s} ({RESO[s]})", fontsize=10, loc="left", color="#263238")
    axs[0].legend(frameon=False, fontsize=8)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, color="#263238")
    fig.tight_layout()
    fig.savefig(CH / fname, dpi=150)
    plt.close(fig)


def by_qp(key, logy=False, ylab=""):
    def fn(ax, s):
        for p in PRESETS:
            pts = [(q, cfg[(s, p, q)][key]) for q in QPS if cfg[(s, p, q)]]
            ax.plot([a for a, _ in pts], [b for _, b in pts], marker="o", ms=4, lw=1.6, color=COL[p], label=p)
        ax.set_xticks(QPS); ax.set_xlabel("QP"); ax.set_ylabel(ylab)
        if logy:
            ax.set_yscale("log")
    return fn


def rd(ax, s):
    for p in PRESETS:
        pts = [(cfg[(s, p, q)]["bitrate_kbps"], cfg[(s, p, q)]["y"]) for q in QPS if cfg[(s, p, q)]]
        ax.plot([a for a, _ in pts], [b for _, b in pts], marker="o", ms=4, lw=1.6, color=COL[p], label=p)
    ax.set_xscale("log"); ax.set_xlabel("bitrate (kbps, log)"); ax.set_ylabel("Y-PSNR (dB)")


grid("qp_vs_bitrate.png", "QP versus bitrate", by_qp("bitrate_kbps", True, "bitrate (kbps, log)"))
grid("qp_vs_ypsnr.png", "QP versus Y-PSNR", by_qp("y", False, "Y-PSNR (dB)"))
grid("rd_curves.png", "Rate-distortion curves per preset", rd)
grid("decode_time.png", "Decoding time (median of 3, no output file)", by_qp("dec_noout_median_s", False, "decode time (s)"))
grid("bitstream_size.png", "Bitstream size", by_qp("bitstream_bytes", True, "bytes (log)"))


def enc_vs_preset(ax, s):
    for q, c in zip(QPS, ("#B3E5FC", "#4FC3F7", "#0288D1", "#01579B")):
        ys = [cfg[(s, p, q)]["enc_median_s"] if cfg[(s, p, q)] else np.nan for p in PRESETS]
        ax.plot(PRESETS, ys, marker="o", ms=4, lw=1.6, color=c, label=f"QP {q}")
    ax.set_yscale("log"); ax.set_ylabel("encode time, median (s, log)")


grid("encode_time_vs_preset.png", "Encoding time versus preset", enc_vs_preset)


def size_vs_preset(ax, s):
    for q, c in zip(QPS, ("#B3E5FC", "#4FC3F7", "#0288D1", "#01579B")):
        m = cfg[(s, "medium", q)]
        ys = [(cfg[(s, p, q)]["bitstream_bytes"] / m["bitstream_bytes"] - 1) * 100 if cfg[(s, p, q)] and m else np.nan for p in PRESETS]
        ax.plot(PRESETS, ys, marker="o", ms=4, lw=1.6, color=c, label=f"QP {q}")
    ax.axhline(0, color="#90A4AE", lw=0.8); ax.set_ylabel("size vs medium, same QP (%)")


grid("bitstream_size_vs_preset.png", "Bitstream size relative to medium at the same QP", size_vs_preset)

# BD-rate vs encoding time (trade-off) and resolution efficiency (bits per pixel)
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
mk = {"BasketballPass": "o", "BlowingBubbles": "s", "BQMall": "^", "BasketballDrive": "D"}
for r in bd:
    if r.get("status") == "ok" and r["bdrate_Y_pchip_pct"] != "":
        axs[0].scatter(r["time_ratio_vs_medium_geomean"], r["bdrate_Y_pchip_pct"], color=COL[r["test"]], marker=mk[r["sequence"]], s=40)
axs[0].scatter([1], [0], color=COL["medium"], marker="*", s=120, label="medium (anchor)")
for p in ("faster", "fast", "slow"):
    axs[0].scatter([], [], color=COL[p], label=p)
for s in SEQS:
    axs[0].scatter([], [], color="#607D8B", marker=mk[s], label=s)
axs[0].axhline(0, color="#90A4AE", lw=0.8); axs[0].set_xscale("log")
axs[0].set_xlabel("encoding time relative to medium (geometric mean over QPs, log)"); axs[0].set_ylabel("BD-rate vs medium, Y (%)")
axs[0].legend(frameon=False, fontsize=7, ncol=2); axs[0].set_title("Compression efficiency vs encoding time", loc="left", fontsize=10)
W = {"BasketballPass": (416, 240, 50), "BlowingBubbles": (416, 240, 50), "BQMall": (832, 480, 60), "BasketballDrive": (1920, 1080, 50)}
for s in SEQS:
    pts = [(cfg[(s, "medium", q)]["bitrate_kbps"] * 1000 / (W[s][0] * W[s][1] * W[s][2]), cfg[(s, "medium", q)]["y"]) for q in QPS if cfg[(s, "medium", q)]]
    axs[1].plot([a for a, _ in pts], [b for _, b in pts], marker=mk[s], lw=1.4, label=f"{s} ({RESO[s]})")
axs[1].set_xscale("log"); axs[1].set_xlabel("bits per pixel (log)"); axs[1].set_ylabel("Y-PSNR (dB)")
axs[1].legend(frameon=False, fontsize=7); axs[1].set_title("Efficiency across resolutions (medium preset)", loc="left", fontsize=10)
fig.tight_layout(); fig.savefig(CH / "bdrate_vs_time_and_bpp.png", dpi=150); plt.close(fig)

# timing reliability chart
if rel:
    fig, ax = plt.subplots(figsize=(9, 3.6))
    for i, x in enumerate(rel):
        rs = [r for r in good if f"{r['sequence']} QP{r['qp']} {r['preset']}" == x["config"]]
        for r in rs:
            ax.scatter(r["encode_time_s"] / x["median_s"], i, color="#E8710A" if r["source"] == "phase1" else "#0053A3", s=22)
    ax.axvline(1, color="#90A4AE", lw=0.8)
    ax.set_yticks(range(len(rel))); ax.set_yticklabels([x["config"] for x in rel], fontsize=8)
    ax.set_xlabel("encode time / median of all runs of the configuration"); ax.scatter([], [], color="#E8710A", label="phase 1 run")
    ax.scatter([], [], color="#0053A3", label="phase 2 run (warm-up, monitored)"); ax.legend(frameon=False, fontsize=8)
    ax.set_title("Timing repeatability", loc="left", fontsize=10)
    fig.tight_layout(); fig.savefig(CH / "timing_repeatability.png", dpi=150); plt.close(fig)

print(json.dumps({k: v for k, v in summary.items() if k != "bdrate"}, indent=1, default=str))
for r in bd:
    print(r)
