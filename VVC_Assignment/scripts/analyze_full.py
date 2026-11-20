"""Verify and summarise the full experiment matrix, then draw the comparison figures.

Inputs : configs/full_manifest.json, results/full/results.csv, logs/phase4b_system_monitor_*.csv
Outputs: results/full/analysis_summary.json, config_summary.csv, timing_variability.csv, tables.md
         figures/full/*.png

Timing values reported per configuration are the MEDIAN of all samples (3 for the 240p sequences,
1 otherwise); every sample stays in results.csv. Works on partial results (reports what is missing).

Usage: python analyze_full.py
"""
import csv
import glob
import json
import os
import statistics
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "full")
FIG = os.path.join(ROOT, "figures", "full")
SEQ_ORDER = ["BasketballPass", "BlowingBubbles", "BQMall", "BasketballDrive"]
SEQ_LABEL = {"BasketballPass": "BasketballPass 416x240", "BlowingBubbles": "BlowingBubbles 416x240",
             "BQMall": "BQMall 832x480", "BasketballDrive": "BasketballDrive 1920x1080"}
PRESETS = ["faster", "fast", "medium", "slow", "slower"]
QPS = [22, 27, 32, 37]
# Categorical slots 1-4 of the validated reference palette (fixed order, colour follows the sequence).
COLOR = dict(zip(SEQ_ORDER, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]))
MARKER = dict(zip(SEQ_ORDER, ["o", "s", "^", "D"]))
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
LOW_PERF = 80  # % Processor Performance below this counts as a slowed-down sample (0 = counter glitch, ignored)


def fnum(x):
    return float(x) if x not in ("", None) else None


def atomic_write(path, text):
    with open(path + ".tmp", "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(path + ".tmp", path)


def style(ax, title, xlabel, ylabel):
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=10)
    ax.set_xlabel(xlabel, color=INK2)
    ax.set_ylabel(ylabel, color=INK2)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#b5b3ad")
    ax.tick_params(colors=INK2)


def read_monitor(path):
    """Parse the 30 s monitor CSV. The frequency field may contain a thousands comma ("1,800")."""
    from datetime import datetime
    samples, guard_lines = [], []
    for line in open(path, encoding="utf-8-sig").read().splitlines()[1:]:
        if line.startswith("GUARD"):
            guard_lines.append(line)
            continue
        parts = line.split(",")
        if len(parts) < 5 or parts[1] == "sample_error":
            continue
        samples.append({"t": datetime.fromisoformat(parts[0]), "battery_status": parts[1], "temp": float(parts[2]),
                        "perf": float(parts[3])})
    return samples, guard_lines


def run_power_exposure(rows, samples):
    """Per run: monitor samples taken while the run was active that were on battery (BatteryStatus != 2)
    or showed % Processor Performance < LOW_PERF. A run is active from its start to the next run's start."""
    from datetime import datetime, timedelta
    by_id = {r["run_id"]: r for r in rows}
    start = {rid: datetime.fromisoformat(r["started"]).replace(tzinfo=None) for rid, r in by_id.items()}
    order = sorted(start, key=start.get)
    out = {}
    for i, rid in enumerate(order):
        r = by_id[rid]
        end = start[order[i + 1]] if i + 1 < len(order) else start[rid] + timedelta(
            seconds=(fnum(r["encode_wall_s"]) or 0) + (fnum(r["decode_wall_s"]) or 0) + (fnum(r["decode_recon_wall_s"]) or 0))
        win = [s for s in samples if start[rid] <= s["t"] < end]
        # The runner's own AC check at run start also counts (short runs can fall between monitor samples).
        out[rid] = {"samples": len(win), "started_on_battery": r["ac_power"] != "True",
                    "battery_samples": sum(s["battery_status"] != "2" for s in win) + (r["ac_power"] != "True"),
                    "low_perf_samples": sum(0 < s["perf"] < LOW_PERF for s in win)}
    return out


def line_chart(fname, title, xlabel, ylabel, xs_by_seq, ys_by_seq, xticks=None, xticklabels=None, logy=False,
               label_fmt=None):
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ends = []
    for seq in SEQ_ORDER:
        if seq not in ys_by_seq:
            continue
        xs, ys = xs_by_seq[seq], ys_by_seq[seq]
        ax.plot(xs, ys, color=COLOR[seq], linewidth=2, marker=MARKER[seq], markersize=6,
                markeredgecolor="white", markeredgewidth=1.2, label=SEQ_LABEL[seq])
        ends.append((xs[-1], ys[-1]))
    if logy:
        ax.set_yscale("log")
    if xticks is not None:
        ax.set_xticks(xticks)
        if xticklabels:
            ax.set_xticklabels(xticklabels)
    if label_fmt and ends:  # direct labels at the line ends, pushed apart vertically so they never overlap
        fig.canvas.draw()
        to_px = ax.transData.transform
        px = sorted((to_px(e)[1], e) for e in ends)
        min_gap = 11 * fig.dpi / 72  # 11 pt in pixels
        placed = []
        for y, e in px:
            placed.append((max(y, placed[-1][0] + min_gap) if placed else y, y, e))
        for ty, y, (xv, yv) in placed:
            ax.annotate(label_fmt(yv), (xv, yv), textcoords="offset points", xytext=(6, (ty - y) * 72 / fig.dpi),
                        va="center", fontsize=8, color=INK2)
    style(ax, title, xlabel, ylabel)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(frameon=False, fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, fname))
    plt.close(fig)


def main():
    man = json.load(open(os.path.join(ROOT, "configs", "full_manifest.json"), encoding="utf-8"))
    rows = list(csv.DictReader(open(os.path.join(RES, "results.csv"), encoding="utf-8")))
    by_id = {r["run_id"]: r for r in rows}
    os.makedirs(FIG, exist_ok=True)

    # ---- completeness and verification ----
    expected = [r["run_id"] for r in man["runs"]]
    missing = [i for i in expected if i not in by_id]
    failed = [i for i in expected if i in by_id and by_id[i]["status"] != "ok"]
    originals = [r for r in man["runs"] if not r.get("repeat_of") and "warmup" not in r.get("groups", [])]
    repeats = [r for r in man["runs"] if r.get("repeat_of")]
    rep_ok = [r["run_id"] for r in repeats if r["run_id"] in by_id
              and by_id[r["run_id"]]["bitstream_sha256"] == by_id.get(r["repeat_of"], {}).get("bitstream_sha256")]
    summary = {
        "expected_runs": len(expected), "present_runs": len(by_id), "missing_runs": missing, "failed_runs": failed,
        "all_complete_and_ok": not missing and not failed,
        "repeats_identical_bitstream": f"{len(rep_ok)}/{len(repeats)}",
        "power_modes": sorted({r.get("power_mode", "") for r in rows}), "ac_power_all": all(r["ac_power"] == "True" for r in rows),
        "max_abs_psnr_diff_vs_encoder": max((fnum(r["max_abs_psnr_diff_vs_encoder"]) or 0) for r in rows if not r["repeat_of"]),
        "first_started": min(r["started"] for r in rows), "last_started": max(r["started"] for r in rows),
    }

    # ---- power exposure per run (AC loss / slowdown seen by the 30 s monitor) ----
    mon = sorted(glob.glob(os.path.join(ROOT, "logs", "phase4b_system_monitor_*.csv")))
    mon_samples, guard_lines = read_monitor(mon[-1]) if mon else ([], [])
    expo = run_power_exposure(rows, mon_samples) if mon_samples else {}
    summary["runs_started_on_battery"] = [r["run_id"] for r in rows if r["ac_power"] != "True"]
    summary["runs_with_battery_samples"] = {k: v for k, v in expo.items() if v["battery_samples"]}
    summary["runs_with_low_perf_samples"] = {k: v for k, v in expo.items() if v["low_perf_samples"]}
    bat_iv, cur = [], None
    for smp in mon_samples:
        if smp["battery_status"] != "2":
            cur = [cur[0] if cur else smp["t"], smp["t"]]
        elif cur:
            bat_iv.append(cur)
            cur = None
    if cur:
        bat_iv.append(cur)
    summary["battery_intervals"] = [[a.isoformat(), b.isoformat()] for a, b in bat_iv]

    # ---- per-configuration summary with timing medians ----
    cfg_rows, var_rows = [], []
    for o in originals:
        r = by_id.get(o["run_id"])
        if not r:
            continue
        samples = [r] + [by_id[x["run_id"]] for x in repeats if x["repeat_of"] == o["run_id"] and x["run_id"] in by_id]

        def med(key):
            return statistics.median(fnum(s[key]) for s in samples)

        enc_w = [fnum(s["encode_wall_s"]) for s in samples]
        row = {"sequence": r["sequence"], "qp": int(r["qp"]), "preset": r["preset"], "groups": r["groups"],
               "frames": int(r["frames"]), "fps": int(r["fps"]), "timing_samples": len(samples),
               "enc_wall_s_median": med("encode_wall_s"), "enc_reported_s_median": med("encode_reported_s"),
               "enc_fps_median": int(r["frames"]) / med("encode_reported_s"),
               "dec_wall_s_median": med("decode_wall_s"), "dec_reported_s_median": med("decode_reported_s"),
               "dec_fps_median": int(r["frames"]) / med("decode_wall_s"),
               "bitstream_bytes": int(r["bitstream_bytes"]), "bitrate_kbps": fnum(r["bitrate_kbps"]),
               "psnr_y": fnum(r["psnr_y"]), "psnr_u": fnum(r["psnr_u"]), "psnr_v": fnum(r["psnr_v"]),
               "psnr_yuv_411": fnum(r["psnr_yuv_411"]), "psnr_yuv_611": fnum(r["psnr_yuv_611"]),
               "avg_qp_I": fnum(r["avg_qp_I"]), "avg_qp_B": fnum(r["avg_qp_B"]), "intra_pocs_first": r["intra_pocs"].split(" ")[0],
               "status": r["status"],
               "timing_samples_with_battery": sum(expo.get(s["run_id"], {}).get("battery_samples", 0) > 0 for s in samples),
               "timing_samples_with_low_perf": sum(expo.get(s["run_id"], {}).get("low_perf_samples", 0) > 0 for s in samples)}
        cfg_rows.append(row)
        if len(samples) > 1:
            var_rows.append({"sequence": r["sequence"], "qp": r["qp"], "preset": r["preset"], "n": len(samples),
                             "enc_wall_samples": " ".join(f"{v:.3f}" for v in enc_w),
                             "enc_wall_median": statistics.median(enc_w), "enc_wall_min": min(enc_w),
                             "enc_wall_max": max(enc_w),
                             "enc_wall_range_pct_of_median": 100 * (max(enc_w) - min(enc_w)) / statistics.median(enc_w),
                             "enc_wall_cv_pct": 100 * statistics.stdev(enc_w) / statistics.mean(enc_w),
                             "dec_wall_samples": " ".join(s["decode_wall_s"] for s in samples),
                             "dec_wall_cv_pct": 100 * statistics.stdev([fnum(s["decode_wall_s"]) for s in samples])
                             / statistics.mean([fnum(s["decode_wall_s"]) for s in samples]),
                             "bitstreams_identical": len({s["bitstream_sha256"] for s in samples}) == 1,
                             "power_flags": " ".join(
                                 ("B" if expo.get(s["run_id"], {}).get("battery_samples") else "-")
                                 + ("L" if expo.get(s["run_id"], {}).get("low_perf_samples") else "-") for s in samples)})

    def write_csv(name, data):
        if not data:
            return
        import io
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(data[0]))
        w.writeheader()
        for d in data:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()})
        atomic_write(os.path.join(RES, name), buf.getvalue())

    write_csv("config_summary.csv", cfg_rows)
    write_csv("timing_variability.csv", var_rows)
    if var_rows:
        cvs = [v["enc_wall_cv_pct"] for v in var_rows]
        summary["timing_variability"] = {"configs_with_repeats": len(var_rows),
                                         "enc_wall_cv_pct_median": statistics.median(cvs), "enc_wall_cv_pct_max": max(cvs),
                                         "dec_wall_cv_pct_median": statistics.median(v["dec_wall_cv_pct"] for v in var_rows),
                                         "all_repeat_bitstreams_identical": all(v["bitstreams_identical"] for v in var_rows)}

    cfg = {(c["sequence"], c["qp"], c["preset"]): c for c in cfg_rows}

    # ---- relative numbers vs medium (preset sweep) and vs QP 32 ----
    rel = {}
    for seq in SEQ_ORDER:
        m = cfg.get((seq, 32, "medium"))
        if not m:
            continue
        for p in PRESETS:
            c = cfg.get((seq, 32, p))
            if c:
                rel[f"{seq}/{p}"] = {"enc_time_x_vs_medium": c["enc_reported_s_median"] / m["enc_reported_s_median"],
                                     "bytes_pct_vs_medium": 100 * (c["bitstream_bytes"] / m["bitstream_bytes"] - 1),
                                     "psnr_y_db_vs_medium": c["psnr_y"] - m["psnr_y"],
                                     "psnr_yuv_db_vs_medium": c["psnr_yuv_411"] - m["psnr_yuv_411"]}
    summary["preset_relative_to_medium"] = rel

    # ---- figures ----
    def series(group_key, keys, metric):
        xs, ys = {}, {}
        for seq in SEQ_ORDER:
            pts = [(i, cfg[(seq, *k)][metric]) for i, k in enumerate(keys) if (seq, *k) in cfg]
            if len(pts) == len(keys):
                xs[seq] = [QPS[i] if group_key == "qp" else i for i, _ in pts]
                ys[seq] = [v for _, v in pts]
        return xs, ys

    qkeys = [(q, "medium") for q in QPS]
    pkeys = [(32, p) for p in PRESETS]
    fr = "(preset medium, QPA off, 8 threads)"
    fp = "(QP 32, QPA off, 8 threads)"
    x, y = series("qp", qkeys, "bitrate_kbps")
    line_chart("qp_vs_bitrate.png", f"QP vs bitrate {fr}", "QP", "Bitrate (kbps, log scale)", x, y, QPS, logy=True,
               label_fmt=lambda v: f"{v:,.0f}")
    x, y = series("qp", qkeys, "psnr_y")
    line_chart("qp_vs_psnr_y.png", f"QP vs Y-PSNR {fr}", "QP", "Y-PSNR (dB, peak 1020)", x, y, QPS,
               label_fmt=lambda v: f"{v:.2f}")
    x, y = series("qp", qkeys, "psnr_yuv_411")
    line_chart("qp_vs_psnr_yuv.png", f"QP vs YUV-PSNR {fr}", "QP", "YUV-PSNR (dB, 4:1:1 MSE-weighted)", x, y, QPS,
               label_fmt=lambda v: f"{v:.2f}")
    x, y = series("qp", qkeys, "enc_reported_s_median")
    line_chart("qp_vs_encoding_time.png", f"QP vs encoding time {fr}", "QP", "Encoding time (s, log scale)", x, y, QPS,
               logy=True, label_fmt=lambda v: f"{v:,.0f} s")
    x, y = series("preset", pkeys, "enc_reported_s_median")
    line_chart("preset_vs_encoding_time.png", f"Preset vs encoding time {fp}", "Preset",
               "Encoding time (s, log scale)", x, y, range(5), PRESETS, logy=True, label_fmt=lambda v: f"{v:,.0f} s")
    x, y = series("preset", pkeys, "bitstream_bytes")
    y = {s: [100 * v / vals[2] for v in vals] for s, vals in y.items()}  # indexed to medium = 100
    line_chart("preset_vs_bitstream_size.png", f"Preset vs bitstream size, indexed to medium = 100 {fp}", "Preset",
               "Bitstream size (% of medium)", x, y, range(5), PRESETS, label_fmt=lambda v: f"{v:.1f}")
    x, y = series("preset", pkeys, "psnr_y")
    line_chart("preset_vs_psnr_y.png", f"Preset vs Y-PSNR {fp}", "Preset", "Y-PSNR (dB, peak 1020)", x, y, range(5),
               PRESETS, label_fmt=lambda v: f"{v:.2f}")
    x, y = series("preset", pkeys, "psnr_yuv_411")
    line_chart("preset_vs_psnr_yuv.png", f"Preset vs YUV-PSNR {fp}", "Preset", "YUV-PSNR (dB)", x, y, range(5),
               PRESETS, label_fmt=lambda v: f"{v:.2f}")
    x, y = series("preset", pkeys, "dec_wall_s_median")
    line_chart("preset_vs_decoding_time.png", f"Preset vs decoding time {fp}", "Preset",
               "Decoding time (s, no output written)", x, y, range(5), PRESETS, label_fmt=lambda v: f"{v:.2f} s")

    # Rate-distortion curves (QP sweep) as small multiples, one axis each.
    fig, axs = plt.subplots(2, 2, figsize=(10, 7), dpi=150)
    for ax, seq in zip(axs.flat, SEQ_ORDER):
        pts = [cfg[(seq, q, "medium")] for q in QPS if (seq, q, "medium") in cfg]
        if pts:
            ax.plot([p["bitrate_kbps"] for p in pts], [p["psnr_y"] for p in pts], color=COLOR[seq], linewidth=2,
                    marker=MARKER[seq], markersize=6, markeredgecolor="white")
            for p in pts:
                ax.annotate(f"QP{p['qp']}", (p["bitrate_kbps"], p["psnr_y"]), textcoords="offset points",
                            xytext=(5, -10), fontsize=8, color=INK2)
            ax.margins(x=0.08, y=0.15)
        style(ax, SEQ_LABEL[seq], "Bitrate (kbps)", "Y-PSNR (dB)")
    fig.suptitle("Rate-distortion curves, preset medium", x=0.02, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "rd_curves_medium.png"))
    plt.close(fig)

    # Preset trade-off: encoding time (x, log) vs size saving relative to medium, small multiples.
    fig, axs = plt.subplots(2, 2, figsize=(10, 7), dpi=150)
    for ax, seq in zip(axs.flat, SEQ_ORDER):
        pts = [(p, cfg[(seq, 32, p)]) for p in PRESETS if (seq, 32, p) in cfg]
        if len(pts) == 5:
            mb = cfg[(seq, 32, "medium")]
            xs = [c["enc_reported_s_median"] for _, c in pts]
            ys = [c["psnr_y"] - mb["psnr_y"] for _, c in pts]
            ax.plot(xs, ys, color=COLOR[seq], linewidth=2, marker=MARKER[seq], markersize=6, markeredgecolor="white")
            for (p, _), xv, yv in zip(pts, xs, ys):
                ax.annotate(p, (xv, yv), textcoords="offset points", xytext=(5, -10), fontsize=8, color=INK2)
            ax.set_xscale("log")
            ax.margins(x=0.08, y=0.15)  # room for the point labels at the extremes
        style(ax, SEQ_LABEL[seq], "Encoding time (s, log)", "Y-PSNR vs medium (dB)")
    fig.suptitle("Preset trade-off at QP 32: time spent vs Y-PSNR gained", x=0.02, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "preset_tradeoff_time_vs_psnr.png"))
    plt.close(fig)

    # System monitor (separate charts, no dual axis). Frequency may contain a thousands comma.
    if mon_samples:
        t = [s["t"] for s in mon_samples]
        temp = [s["temp"] for s in mon_samples]
        perf = [s["perf"] for s in mon_samples]
        summary["system_monitor"] = {"file": os.path.basename(mon[-1]), "samples": len(t),
                                     "thermal_zone_C_max": max(temp) if temp else None,
                                     "thermal_zone_C_median": statistics.median(temp) if temp else None,
                                     "proc_performance_pct_median": statistics.median(perf) if perf else None,
                                     "proc_performance_pct_min": min(perf) if perf else None,
                                     "battery_samples": sum(s["battery_status"] != "2" for s in mon_samples),
                                     "low_perf_samples": sum(0 < p < LOW_PERF for p in perf),
                                     "zero_perf_counter_glitches": [s["t"].isoformat() for s in mon_samples if s["perf"] == 0],
                                     "guard_events": guard_lines}
        for fname, vals, ylab, title in [("monitor_thermal_zone.png", temp, "ACPI thermal zone (°C)",
                                          "Thermal zone temperature during the full run"),
                                         ("monitor_processor_performance.png", perf, "% Processor Performance",
                                          "Processor performance during the full run (100 = nominal 2.1 GHz)")]:
            if vals:
                fig, ax = plt.subplots(figsize=(9, 3.6), dpi=150)
                ax.plot(t, vals, color=COLOR["BasketballPass"], linewidth=1.2)
                for i, (a, b) in enumerate(bat_iv):  # periods the monitor saw battery power
                    ax.axvspan(a, b, color="#e4e3df", zorder=0, label="on battery" if i == 0 else None)
                style(ax, title, "Time", ylab)
                if bat_iv:
                    ax.legend(frameon=False, fontsize=8, loc="lower left")
                fig.autofmt_xdate()
                fig.tight_layout()
                fig.savefig(os.path.join(FIG, fname))
                plt.close(fig)

    # ---- markdown tables ----
    md = ["# Full experiment tables (generated by scripts/analyze_full.py)", ""]
    md += ["Enc time = median of encoder-reported time (vvencapp 'Total Time'); Dec time = median wall-clock decode "
           "time (timing pass, no output written); n = timing samples. Power flag counts samples during which the "
           f"30 s monitor saw battery power or % Processor Performance < {LOW_PERF}.", ""]
    md += ["## QP sweep (preset medium)", "",
           "| Sequence | QP | Bitrate (kbps) | Bytes | Y-PSNR | U-PSNR | V-PSNR | YUV-PSNR | Enc time (s) | Enc fps | Dec time (s) | n | Power flag |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]

    def flag(c):
        if not (c["timing_samples_with_battery"] or c["timing_samples_with_low_perf"]):
            return ""
        f = f"{c['timing_samples_with_battery']}/{c['timing_samples']} on battery"
        return f + (f", {c['timing_samples_with_low_perf']} slowed" if c["timing_samples_with_low_perf"] else "")

    for seq in SEQ_ORDER:
        for q in QPS:
            c = cfg.get((seq, q, "medium"))
            if c:
                md.append(f"| {seq} | {q} | {c['bitrate_kbps']:.2f} | {c['bitstream_bytes']:,} | {c['psnr_y']:.4f} | "
                          f"{c['psnr_u']:.4f} | {c['psnr_v']:.4f} | {c['psnr_yuv_411']:.4f} | {c['enc_reported_s_median']:.2f} | "
                          f"{c['enc_fps_median']:.2f} | {c['dec_wall_s_median']:.3f} | {c['timing_samples']} | {flag(c)} |")
    md += ["", "## Preset sweep (QP 32)", "",
           "| Sequence | Preset | Bitrate (kbps) | Bytes | Size vs medium | Y-PSNR | YUV-PSNR | ΔY vs medium (dB) | Enc time (s) | × medium | Dec time (s) | n | Power flag |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for seq in SEQ_ORDER:
        for p in PRESETS:
            c, rr = cfg.get((seq, 32, p)), rel.get(f"{seq}/{p}")
            if c and rr:
                md.append(f"| {seq} | {p} | {c['bitrate_kbps']:.2f} | {c['bitstream_bytes']:,} | {rr['bytes_pct_vs_medium']:+.2f}% | "
                          f"{c['psnr_y']:.4f} | {c['psnr_yuv_411']:.4f} | {rr['psnr_y_db_vs_medium']:+.4f} | "
                          f"{c['enc_reported_s_median']:.2f} | {rr['enc_time_x_vs_medium']:.2f} | {c['dec_wall_s_median']:.3f} | {c['timing_samples']} | {flag(c)} |")
    if var_rows:
        md += ["", "## Timing variability (3 samples per configuration)", "",
               "Power flags per sample, in run order: B = battery seen, L = low processor performance, - = neither.", "",
               "| Sequence | QP | Preset | Encode wall samples (s) | Median | CV % | Range % of median | Decode CV % | Bitstreams identical | Power flags |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for v in var_rows:
            md.append(f"| {v['sequence']} | {v['qp']} | {v['preset']} | {v['enc_wall_samples']} | {v['enc_wall_median']:.3f} | "
                      f"{v['enc_wall_cv_pct']:.2f} | {v['enc_wall_range_pct_of_median']:.2f} | {v['dec_wall_cv_pct']:.2f} | {v['bitstreams_identical']} | {v['power_flags']} |")
    atomic_write(os.path.join(RES, "tables.md"), "\n".join(md) + "\n")
    atomic_write(os.path.join(RES, "analysis_summary.json"), json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: v for k, v in summary.items() if k != "preset_relative_to_medium"}, indent=2, default=str))
    sys.exit(0 if summary["all_complete_and_ok"] else 2)


if __name__ == "__main__":
    main()
