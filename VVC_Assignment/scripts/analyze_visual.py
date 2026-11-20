"""Phase 6: automated, evidence-based visual quality analysis (no subjective claims are generated here).

Inputs (all verified in scripts/prepare_visual.py): visual/sample_manifest.json, visual/frame_selection.json,
visual/rendered/crops.json, dataset/*.yuv, recon/full/*_rec.yuv, results/full/runs/*_psnr_per_frame.csv,
logs/runs/full/*_enc.log (per-picture slice QP, bits, PSNR).

A. Frame-level objective metrics for every selected frame and variant, on the full frame and on the crop:
   Y/U/V PSNR (peak 1020), luma mean / max absolute difference (10-bit code values), share of luma pixels
   with |diff| > 16 and > 64, luma SSIM (8x8 uniform window, L = 1023), and the detail-retention ratio
   mean|Laplacian(rec)| / mean|Laplacian(orig)| (< 1 = high-frequency detail removed / smoothed).
B. Comparison figures (same display conversion for every panel, see render_visual_crops.to_rgb):
   row 1 full frame (crop marked), row 2 full-frame |dY| map, row 3 enlarged crop, row 4 enlarged-crop |dY| map.
   Difference maps: |Y_rec - Y_orig| in 10-bit code values, linear, 0 = white ... 64 = black (clipped);
   the same fixed scale for every map, with a colour bar.
C. Preset investigation over ALL frames: per-picture Y-PSNR, slice QP and bits from the encoder logs; frames
   where a slower preset has a lower Y-PSNR than a faster one, and how often it coincides with a lower slice
   QP or more bits in the faster preset.

Outputs (new folder, nothing existing is modified): visual/phase6/{figures,tables}/, visual/phase6/analysis.json

Usage: python analyze_visual.py
"""
import csv
import io
import json
import os
import re
import statistics
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from render_visual_crops import read_frame, to_rgb  # noqa: E402

VIS = os.path.join(ROOT, "visual")
OUT = os.path.join(VIS, "phase6")
FIG, TAB = os.path.join(OUT, "figures"), os.path.join(OUT, "tables")
DIFF_MAX = 64          # difference-map scale: 0..64 10-bit code values (= 0..16 in 8-bit terms)
SETS = {"qp": [("Original", None), ("QP 22 medium", (22, "medium")), ("QP 32 medium", (32, "medium")),
               ("QP 37 medium", (37, "medium"))],
        "preset": [("Original", None), ("QP 32 faster", (32, "faster")), ("QP 32 medium", (32, "medium")),
                   ("QP 32 slower", (32, "slower"))]}
VARIANTS = [(22, "medium"), (32, "medium"), (37, "medium"), (32, "faster"), (32, "slower")]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
PRESET_COLOR = {"faster": "#2a78d6", "medium": "#eb6834", "slower": "#1baf7a"}
POC_RE = re.compile(r"^POC\s+(\d+) TId:\s*(\d+) \(\s*(\S+), (\S)-SLICE, QP (\d+)[^)]*\)\s+(\d+) bits "
                    r"\[Y ([\d.]+) dB\s+U ([\d.]+) dB\s+V ([\d.]+) dB\]", re.M)


def box_mean(a, k):
    """Mean over every k x k window (valid positions only), via an integral image."""
    s = np.pad(a.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    return (s[k:, k:] - s[:-k, k:] - s[k:, :-k] + s[:-k, :-k]) / (k * k)


def ssim(x, y, L=1023.0, k=8):
    c1, c2 = (0.01 * L) ** 2, (0.03 * L) ** 2
    mx, my = box_mean(x, k), box_mean(y, k)
    vx, vy = box_mean(x * x, k) - mx * mx, box_mean(y * y, k) - my * my
    cxy = box_mean(x * y, k) - mx * my
    return float(np.mean(((2 * mx * my + c1) * (2 * cxy + c2)) / ((mx * mx + my * my + c1) * (vx + vy + c2))))


def lap_energy(a):
    lap = 4 * a[1:-1, 1:-1] - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:]
    return float(np.mean(np.abs(lap)))


def psnr(mse, peak=1020.0):
    return float("inf") if mse == 0 else 10 * np.log10(peak * peak / mse)


def metrics(o, r):
    """o, r: (Y, U, V) float arrays of the same region."""
    d = r[0] - o[0]
    ad = np.abs(d)
    return {"psnr_y": psnr(np.mean(d * d)), "psnr_u": psnr(np.mean((r[1] - o[1]) ** 2)),
            "psnr_v": psnr(np.mean((r[2] - o[2]) ** 2)), "mae_y": float(ad.mean()), "max_abs_y": float(ad.max()),
            "pct_absdiff_gt16": float(100 * np.mean(ad > 16)), "pct_absdiff_gt64": float(100 * np.mean(ad > 64)),
            "ssim_y": ssim(o[0], r[0]), "detail_ratio": lap_energy(r[0]) / lap_energy(o[0])}


def crop3(f, c):
    x, y, w, h = c["crop_x"], c["crop_y"], c["crop_w"], c["crop_h"]
    return (f[0][y:y + h, x:x + w], f[1][y // 2:(y + h) // 2, x // 2:(x + w) // 2],
            f[2][y // 2:(y + h) // 2, x // 2:(x + w) // 2])


def parse_log(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    pics = {}
    for m in POC_RE.finditer(txt):
        poc = int(m.group(1))
        pics[poc] = {"tid": int(m.group(2)), "nal": m.group(3), "type": m.group(4), "qp": int(m.group(5)),
                     "bits": int(m.group(6)), "y": float(m.group(7)), "u": float(m.group(8)), "v": float(m.group(9))}
    return pics


def comparison_figure(seq, rule, idx, set_name, frames, crop, fm, cm, fname):
    members = SETS[set_name]
    w = frames[None][0].shape[1]
    h = frames[None][0].shape[0]
    cw, ch, zoom = crop["crop_w"], crop["crop_h"], crop["zoom"]
    col_w = 4.2 if w <= 416 else 4.6
    fig, axs = plt.subplots(4, 4, figsize=(4 * col_w, 4 * col_w * 0.62 + 1.4), dpi=130,
                            gridspec_kw={"height_ratios": [h / w, h / w, ch / cw, ch / cw]})
    im_diff = None
    for j, (lab, key) in enumerate(members):
        f = frames[key]
        rgb = to_rgb(*f)
        ax = axs[0, j]
        ax.imshow(rgb, interpolation="nearest")
        ax.add_patch(Rectangle((crop["crop_x"] - 0.5, crop["crop_y"] - 0.5), cw, ch, fill=False, ec="#ffffff", lw=1.2))
        ax.add_patch(Rectangle((crop["crop_x"] - 0.5, crop["crop_y"] - 0.5), cw, ch, fill=False, ec=INK, lw=0.6, ls="--"))
        sub = "reference" if key is None else (f"frame Y-PSNR {fm[key]['psnr_y']:.2f} dB  SSIM {fm[key]['ssim_y']:.3f}")
        ax.set_title(f"{lab}\n{sub}", fontsize=8.5, color=INK, loc="left")
        cr = rgb[crop["crop_y"]:crop["crop_y"] + ch, crop["crop_x"]:crop["crop_x"] + cw]
        axs[2, j].imshow(np.repeat(np.repeat(cr, zoom, 0), zoom, 1), interpolation="nearest")
        csub = "crop, reference" if key is None else (f"crop Y-PSNR {cm[key]['psnr_y']:.2f} dB  detail {cm[key]['detail_ratio']:.2f}")
        axs[2, j].set_title(csub, fontsize=8, color=INK2, loc="left")
        for r_, region in ((1, "full"), (3, "crop")):
            ax = axs[r_, j]
            if key is None:
                ax.text(0.5, 0.5, "difference maps:\n|Y_rec - Y_orig|", ha="center", va="center", fontsize=8,
                        color=INK2, transform=ax.transAxes)
                ax.set_facecolor("#f7f7f5")
                continue
            d = np.abs(f[0] - frames[None][0])
            if region == "crop":
                d = d[crop["crop_y"]:crop["crop_y"] + ch, crop["crop_x"]:crop["crop_x"] + cw]
                d = np.repeat(np.repeat(d, zoom, 0), zoom, 1)
            im_diff = ax.imshow(d, cmap="Greys", vmin=0, vmax=DIFF_MAX, interpolation="nearest")
            mm = fm[key] if region == "full" else cm[key]
            ax.set_title(f"{region}: mean |dY| {mm['mae_y']:.1f}, >16: {mm['pct_absdiff_gt16']:.1f}%",
                         fontsize=8, color=INK2, loc="left")
    for ax in axs.flat:
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color("#d0cfca")
    fig.suptitle(f"{seq}, frame {idx} ({rule.replace('_', ' ')}): {'QP comparison, preset medium' if set_name == 'qp' else 'preset comparison, QP 32'}",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.text(0.01, 0.005, f"Rows: full frame (crop marked) | full-frame luma difference | crop {cw}x{ch} at ({crop['crop_x']},{crop['crop_y']}) "
             f"enlarged {zoom}x (pixel repetition) | enlarged crop difference.  Display: 10->8 bit, BT.709 limited->sRGB, same for all panels.  "
             f"Difference maps: |Y_rec - Y_orig| in 10-bit code values, linear, white = 0, black >= {DIFF_MAX}.",
             fontsize=7, color=INK2)
    fig.tight_layout(rect=(0, 0.025, 0.93, 0.97))
    if im_diff is not None:
        cax = fig.add_axes((0.945, 0.3, 0.012, 0.4))
        cb = fig.colorbar(im_diff, cax=cax)
        cb.set_label("|dY| (10-bit code values)", fontsize=8, color=INK2)
        cb.ax.tick_params(labelsize=7, colors=INK2)
    fig.savefig(os.path.join(FIG, fname))
    plt.close(fig)


def style(ax, title, xl, yl):
    ax.set_title(title, loc="left", fontsize=10.5, color=INK, pad=8)
    ax.set_xlabel(xl, color=INK2)
    ax.set_ylabel(yl, color=INK2)
    ax.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#b5b3ad")
    ax.tick_params(colors=INK2)


def main():
    os.makedirs(FIG, exist_ok=True)
    os.makedirs(TAB, exist_ok=True)
    man = json.load(open(os.path.join(VIS, "sample_manifest.json"), encoding="utf-8"))["samples"]
    sel = json.load(open(os.path.join(VIS, "frame_selection.json"), encoding="utf-8"))
    crops = json.load(open(os.path.join(VIS, "rendered", "crops.json"), encoding="utf-8"))
    rows, analysis = [], {"frame_metrics": {}, "preset_investigation": {}, "checks": {}}

    # ---- A + B: frame metrics and comparison figures ----
    for seq, info in sel.items():
        smp = {(m["qp"], m["preset"]) if m["role"] != "original" else None: m for m in man if m["sequence"] == seq}
        w, h = smp[None]["width"], smp[None]["height"]
        for rule, idx in info["frames"].items():
            frames = {k: read_frame(os.path.join(ROOT, m["file"]), w, h, idx) for k, m in smp.items()}
            crop = crops[f"{seq}/{rule}"]
            fm, cm = {}, {}
            for key in VARIANTS:
                fm[key] = metrics(frames[None], frames[key])
                cm[key] = metrics(crop3(frames[None], crop), crop3(frames[key], crop))
                stored = info["per_frame_y_psnr"][f"QP{key[0]}_{key[1]}"][rule]
                analysis["checks"][f"{seq}/{idx}/QP{key[0]}_{key[1]}"] = abs(round(fm[key]["psnr_y"], 4) - stored) < 1e-4
                m = smp[key]
                rows.append({"sequence": seq, "frame_index": idx, "frame_rule": rule, "qp": key[0], "preset": key[1],
                             **{f"frame_{k}": round(v, 4) for k, v in fm[key].items()},
                             **{f"crop_{k}": round(v, 4) for k, v in cm[key].items()},
                             "sequence_y_psnr": m["psnr_y"], "bitstream_bytes": m["bitstream_bytes"]})
            analysis["frame_metrics"][f"{seq}/{idx}"] = {f"QP{k[0]}_{k[1]}": {"frame": fm[k], "crop": cm[k]} for k in VARIANTS}
            for set_name in SETS:
                comparison_figure(seq, rule, idx, set_name, frames, crop, fm, cm,
                                  f"{seq}_{set_name}_frame{idx:03d}_{rule}.png")
            print(f"{seq} frame {idx} done")

    buf = io.StringIO()
    wr = csv.DictWriter(buf, fieldnames=list(rows[0]))
    wr.writeheader()
    wr.writerows(rows)
    open(os.path.join(TAB, "frame_metrics.csv"), "w", encoding="utf-8", newline="").write(buf.getvalue())

    # ---- C: preset investigation over all frames ----
    pairs = [("faster", "medium"), ("medium", "slower"), ("faster", "slower")]
    md_prev = []
    fig, axs = plt.subplots(2, 1, figsize=(11.5, 6.4), dpi=150)
    for ax, (seq, tag, n) in zip(axs, (("BasketballPass", "f500", 500), ("BQMall", "f600", 600))):
        logs = {p: parse_log(os.path.join(ROOT, "logs", "runs", "full", f"{seq}_{tag}_q32_{p}_t8_enc.log"))
                for p in ("faster", "medium", "slower")}
        csvs = {}
        for p in logs:
            with open(os.path.join(ROOT, "results", "full", "runs", f"{seq}_{tag}_q32_{p}_t8_psnr_per_frame.csv"), encoding="utf-8") as f:
                csvs[p] = [float(r["psnrY_1020"]) for r in csv.DictReader(f)]
        # consistency: encoder per-picture Y-PSNR vs independent per-frame PSNR
        cons = max(abs(logs[p][i]["y"] - csvs[p][i]) for p in logs for i in range(n))
        res = {"pictures": {p: len(v) for p, v in logs.items()}, "max_abs_enc_vs_independent_psnr_y": cons}
        for a, b in pairs:
            worse = [i for i in range(n) if csvs[b][i] < csvs[a][i]]
            lower_qp = [i for i in worse if logs[a][i]["qp"] < logs[b][i]["qp"]]
            more_bits = [i for i in worse if logs[a][i]["bits"] > logs[b][i]["bits"]]
            same_qp = [i for i in worse if logs[a][i]["qp"] == logs[b][i]["qp"]]
            qp_diff_all = sum(logs[a][i]["qp"] != logs[b][i]["qp"] for i in range(n))
            res[f"{b}_lower_than_{a}"] = {
                "frames": len(worse), "pct_of_frames": round(100 * len(worse) / n, 1),
                "of_which_faster_preset_had_lower_slice_qp": len(lower_qp),
                "of_which_same_slice_qp": len(same_qp),
                "of_which_faster_preset_spent_more_bits": len(more_bits),
                "median_deficit_db": round(statistics.median([csvs[a][i] - csvs[b][i] for i in worse]), 4) if worse else None,
                "max_deficit_db": round(max([csvs[a][i] - csvs[b][i] for i in worse]), 4) if worse else None,
                "frames_with_different_slice_qp_overall": qp_diff_all,
                "by_tid": {t: sum(logs[b][i]["tid"] == t for i in worse) for t in sorted({logs[b][i]["tid"] for i in worse})}}
        res["slice_qp_by_tid"] = {p: {t: sorted({v["qp"] for v in logs[p].values() if v["tid"] == t})
                                      for t in sorted({v["tid"] for v in logs[p].values()})} for p in logs}
        res["mean_bits_per_picture"] = {p: round(statistics.mean(v["bits"] for v in logs[p].values()), 1) for p in logs}
        res["sequence_mean_frame_psnr_y"] = {p: round(statistics.mean(csvs[p]), 4) for p in logs}
        analysis["preset_investigation"][seq] = res
        sel_frames = sel[seq]["frames"]
        res["selected_frames_detail"] = {str(i): {p: {k: logs[p][i][k] for k in ("tid", "nal", "qp", "bits", "y")} for p in logs}
                                         for i in sel_frames.values()}
        x = np.arange(n)
        for p in ("faster", "slower"):
            dlt = np.array(csvs[p]) - np.array(csvs["medium"])
            ax.plot(x, dlt, color=PRESET_COLOR[p], lw=0.9, label=f"{p} minus medium")
        ax.axhline(0, color=INK2, lw=0.8)
        for i in sel_frames.values():
            ax.axvline(i, color="#b5b3ad", lw=0.8, ls=":")
        style(ax, f"{seq}: per-frame Y-PSNR difference to medium (QP 32)", "Frame index (display order)", "ΔY-PSNR (dB)")
        ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
        md_prev.append(res)
    fig.text(0.01, 0.005, "Dotted vertical lines: frames selected for the visual comparison.", fontsize=7, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(os.path.join(FIG, "preset_per_frame_psnr_delta.png"))
    plt.close(fig)

    # ---- objective summary charts for the selected frames ----
    for metric, label, fname in (("ssim_y", "Luma SSIM (8x8 window)", "selected_frames_ssim.png"),
                                 ("detail_ratio", "Detail retention ratio (Laplacian, rec / orig)", "selected_frames_detail_ratio.png")):
        fig, axs = plt.subplots(1, 2, figsize=(11, 4), dpi=150)
        for ax, set_name, keys in ((axs[0], "QP (medium)", [(22, "medium"), (32, "medium"), (37, "medium")]),
                                   (axs[1], "Preset (QP 32)", [(32, "faster"), (32, "medium"), (32, "slower")])):
            series = [(seq, idx) for seq, info in sel.items() for idx in info["frames"].values()]
            colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#8f63d9", "#d1447e"]
            for (seq, idx), col in zip(series, colors):
                ys = [analysis["frame_metrics"][f"{seq}/{idx}"][f"QP{k[0]}_{k[1]}"]["frame"][metric] for k in keys]
                ax.plot(range(3), ys, color=col, lw=2, marker="o", ms=5, mec="white", label=f"{seq} f{idx}")
            ax.set_xticks(range(3))
            ax.set_xticklabels([f"QP {k[0]}" if set_name.startswith("QP") else k[1] for k in keys])
            style(ax, f"{label}: {set_name}", "", label)
        h_, l_ = axs[1].get_legend_handles_labels()
        fig.legend(h_, l_, frameon=False, fontsize=8, loc="lower center", ncol=6)
        fig.tight_layout(rect=(0, 0.07, 1, 1))
        fig.savefig(os.path.join(FIG, fname))
        plt.close(fig)

    analysis["checks"]["all_frame_psnr_match_stored"] = all(v for k, v in analysis["checks"].items() if k != "all_frame_psnr_match_stored")
    with open(os.path.join(OUT, "analysis.json"), "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, default=lambda o: str(o))
    print(json.dumps(analysis["preset_investigation"], indent=1, default=str)[:6000])
    print("frame PSNR recomputation matches stored values:", analysis["checks"]["all_frame_psnr_match_stored"])


if __name__ == "__main__":
    main()
