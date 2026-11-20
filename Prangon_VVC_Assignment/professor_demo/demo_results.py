"""demo_results.py - Part 3 and Part 4 (slides 5 and 6) of the professor demo.

Part 3: takes ONE saved run of the original experiment (default A029: BasketballPass, QP 29, faster, 500 frames) and
        shows where every measured value comes from: the log line, the CSV column, and a recalculation from the saved
        files (bitstream, decoded YUV). Then SSIM / MS-SSIM are recomputed for the frames shown on slide 8.
Part 4: reads the native charts and number tiles of slides 5 and 6 from the FINAL PowerPoint and matches every
        plotted value to its row in results/config_summary.csv, the runs behind it and their log files.

Run from the professor_demo folder:
    ..\\.venv\\Scripts\\python.exe demo_results.py                 (everything, about 1 minute)
    ..\\.venv\\Scripts\\python.exe demo_results.py --part 3        (only the measured values)
    ..\\.venv\\Scripts\\python.exe demo_results.py --part 4        (only the slide 5/6 mapping)
    ..\\.venv\\Scripts\\python.exe demo_results.py --run A046      (explain another saved run)
Read-only for all experiment files. A Markdown report and a mapping CSV are written to professor_demo/output/.
"""
import argparse
import csv
import json
import math
import re
import statistics as st

import numpy as np
from pptx import Presentation

from demo_pyutil import DECK, OUT, RES, ROOT, Report, chart_points, read_csv, rel, sha256

import metrics  # analysis/metrics.py from the experiment (same functions that produced the results)

ap = argparse.ArgumentParser()
ap.add_argument("--run", default="A029")
ap.add_argument("--part", choices=["3", "4", "all"], default="all")
ap.add_argument("--skip-1080p", action="store_true", help="skip the BasketballDrive (1080p) SSIM recalculation")
a = ap.parse_args()
R = Report("demo_results")
P2 = read_csv(RES / "results_phase2.csv")
P1 = read_csv(RES / "results_raw.csv")
CFG = read_csv(RES / "config_summary.csv")
SUM = json.loads((RES / "summary_full.json").read_text(encoding="utf-8"))


def log_sections(path):
    """Split a run log into its '=== TITLE' sections."""
    secs, cur = {}, None
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("=== "):
            cur = line[4:].strip()
            secs[cur] = []
        elif cur:
            secs[cur].append(line.rstrip("\n"))
    return secs


def part3():
    row = next((r for r in P2 if r["run_id"] == a.run), None)
    if row is None:
        raise SystemExit(f"run {a.run} not found in results/results_phase2.csv")
    tag = f"{row['run_id']}_{row['sequence']}_QP{row['qp']}_{row['preset']}"
    log = ROOT / row["log_file"]
    secs = log_sections(log)
    enc = "\n".join(secs["ENCODE"])
    w, h, fps, n = int(row["width"]), int(row["height"]), int(row["fps"]), int(row["frames"])
    R.h(f"Part 3 - every measured value of original run {a.run} ({row['sequence']}, QP {row['qp']}, {row['preset']}, {n} frames)")
    R.p(f"CSV : results/results_phase2.csv, row run_id = {a.run}")
    R.p(f"Log : {row['log_file']}")
    R.p(f"Encoder command (from the log): {secs['ENCODE'][0].replace('Command: ', '')}")

    R.h("1. Encoding time")
    m = re.findall(r"Total Time:\s*([\d.]+)", enc)
    R.p(f"Log line  : {next(l for l in secs['ENCODE'] if 'Total Time' in l).strip()}")
    R.p(f"CSV column: encode_time_s = {row['encode_time_s']}   (wall clock, encode_wall_s = {row['encode_wall_s']})")
    R.p("Meaning   : the encoder's own measurement of the time it spent encoding all frames.")
    R.check("encode_time_s equals the 'Total Time' printed in the log", float(m[-1]) == float(row["encode_time_s"]))

    R.h("2. Decoding time")
    t = []
    for k in (1, 2, 3):
        line = next(l for l in secs[f"DECODE TIMING {k} (no output file)"] if "frames decoded" in l)
        t.append(float(re.search(r"\(([\d.]+) sec\)", line).group(1)))
        R.p(f"Log, decode {k} (no output file): ...{line.split(': ', 1)[1]}")
    R.p(f"CSV columns: decode_noout_times_s = {row['decode_noout_times_s']}, decode_noout_median_s = {row['decode_noout_median_s']}")
    R.p(f"Calculation: median({', '.join(f'{x:.3f}' for x in t)}) = {st.median(t):.3f} s")
    R.p("Meaning    : decoding is timed 3 times without writing a file (so disk speed does not count); the middle value is kept.")
    R.check("median of the 3 logged decode times equals decode_noout_median_s", abs(st.median(t) - float(row["decode_noout_median_s"])) < 5e-4)

    R.h("3. Bitstream size")
    bs = ROOT / "out/phase2" / f"{tag}.266"
    size = bs.stat().st_size
    R.p(f"File      : {rel(bs)}  -> {size} bytes (measured now)")
    R.p(f"CSV column: bitstream_bytes = {row['bitstream_bytes']}")
    R.check("size of the saved .266 file equals bitstream_bytes", size == int(row["bitstream_bytes"]))

    R.h("4. Bitrate")
    kbps = size * 8 / (n / fps) / 1000
    R.p("Formula   : bitrate (kbps) = bytes x 8 bits / duration in seconds / 1000,  duration = frames / fps")
    R.p(f"Calculation: {size} x 8 / ({n} / {fps} = {n / fps:g} s) / 1000 = {kbps:.3f} kbps")
    R.p(f"CSV column: bitrate_kbps = {row['bitrate_kbps']};  the encoder printed {row['enc_bitrate_kbps']} kbps (enc_bitrate_kbps)")
    R.check("recalculated bitrate equals bitrate_kbps", abs(kbps - float(row["bitrate_kbps"])) < 5e-4)
    R.check("file-based bitrate agrees with the encoder's own value (within 0.001 kbps)", abs(kbps - float(row["enc_bitrate_kbps"])) < 1e-3)

    R.h("5. Y / U / V PSNR (printed by the encoder)")
    line = next(l for l in secs["ENCODE"] if re.search(r"^\S+ \[info\]:\s+\d+\s+a\s", l))
    vals = re.findall(r"[\d.]+", line.split(" a ")[1])
    R.p(f"Log line  : {line.strip()}   (columns: bitrate, Y, U, V, YUV)")
    R.p(f"CSV       : enc_y_psnr = {row['enc_y_psnr']}, enc_u_psnr = {row['enc_u_psnr']}, enc_v_psnr = {row['enc_v_psnr']}")
    R.p("Formula   : for each frame and plane, MSE = mean((original - decoded)^2); PSNR = 10 x log10(1020^2 / MSE);")
    R.p("            the sequence value is the average over all frames. 1020 = 255 x 4 is the 10-bit peak used by VTM/VVenC.")
    R.check("encoder Y/U/V PSNR in the log equal the CSV columns",
            [float(vals[1]), float(vals[2]), float(vals[3])] == [float(row["enc_y_psnr"]), float(row["enc_u_psnr"]), float(row["enc_v_psnr"])])

    R.h("6. Independent PSNR verification")
    js = json.loads(secs["PSNR CHECK"][0])
    R.p(f"Log ('=== PSNR CHECK', output of experiment/psnr_check.py): {secs['PSNR CHECK'][0]}")
    R.p(f"CSV       : check_y_psnr = {row['check_y_psnr']}, check_u_psnr = {row['check_u_psnr']}, check_v_psnr = {row['check_v_psnr']}, "
        f"max_psnr_diff_db = {row['max_psnr_diff_db']}")
    rec = next((ROOT / "out/phase2").glob(f"{tag}_rec_*.yuv"), None)
    if rec:
        y = metrics.psnr(np.fromfile(ROOT / "dataset" / next(f for f in (ROOT / "dataset").iterdir() if f.name.startswith(row["sequence"] + "_")),
                                     dtype="<u2", count=w * h), np.fromfile(rec, dtype="<u2", count=w * h))
        R.p(f"Spot check now: Y-PSNR of frame 0 only, from the saved decoded file = {y:.4f} dB (one frame; the CSV value is the 500-frame mean)")
    diff = max(abs(float(row[f"check_{c}_psnr"]) - float(row[f"enc_{c}_psnr"])) for c in "yuv")
    R.check(f"independent PSNR = encoder PSNR (largest difference {diff:.4f} dB)", diff < 1e-4)

    R.h("7. Frame count")
    if rec:
        fr = rec.stat().st_size / (w * h * 3 / 2 * 2)
        R.p(f"Decoded file {rel(rec)}: {rec.stat().st_size} bytes / ({w} x {h} x 1.5 x 2 bytes) = {fr:g} frames")
        R.check(f"decoded frames = {n} (CSV recon_frames = {row['recon_frames']})", fr == n == float(row["recon_frames"]))
    else:
        R.p("The decoded file of this run was not kept (large runs used a temporary file). CSV recon_frames = " + row["recon_frames"])

    R.h("8. SHA-256 verification")
    hb = sha256(bs)
    R.p("Meaning   : SHA-256 is a 64-character fingerprint of a file. If even one bit is different, the fingerprint changes completely.")
    R.p(f"Bitstream now : {hb}")
    R.p(f"CSV           : {row['bitstream_sha256']} (bitstream_sha256)")
    R.check("bitstream file unchanged since the experiment", hb == row["bitstream_sha256"])
    if rec:
        hr = sha256(rec)
        R.p(f"Decoded YUV now: {hr}")
        R.p(f"CSV            : {row['recon_sha256']} (recon_sha256)")
        R.check("decoded YUV file unchanged since the experiment", hr == row["recon_sha256"])
    same = [r["run_id"] for r in P2 if r["sequence"] == row["sequence"] and r["qp"] == row["qp"] and r["preset"] == row["preset"]
            and r["status"] in ("OK", "CHECK")]
    if len(same) > 1:
        hs = {r["run_id"]: r["bitstream_sha256"] for r in P2 if r["run_id"] in same}
        R.p(f"All runs of this configuration: {', '.join(same)} (repeats for timing)")
        R.check("every repeat produced the identical bitstream (deterministic encoder)", len(set(hs.values())) == 1)

    # ---------------- SSIM / MS-SSIM ----------------
    VF = read_csv(RES / "visual_frame_metrics.csv")
    R.h("9. SSIM and MS-SSIM (luma, whole frame) - recalculated from the saved decoded files")
    R.p("SSIM compares local brightness, contrast and structure in an 11x11 Gaussian window (sigma 1.5); 1.0 = identical.")
    R.p("MS-SSIM does the same at 5 image scales (each half the size of the previous) and combines them with fixed weights")
    R.p("(0.0448, 0.2856, 0.3001, 0.2363, 0.1333). Code: analysis/metrics.py. Data range 1023 (10-bit).")
    R.p("Source CSV: results/visual_frame_metrics.csv (made by analysis/visual_v2.py). Frame numbers count from 0.")

    def frame_y(path, w, h, i):
        return np.fromfile(path, dtype="<u2", count=w * h, offset=i * w * h * 3).astype(np.float64).reshape(h, w)

    jobs = [("BasketballPass", 416, 240, 359, [29], lambda q: ROOT / "out/phase2/A046_BasketballPass_QP29_medium_rec_416x240_50fps_10bit_420.yuv",
             ROOT / "dataset/BasketballPass_416_240_50_10_420.yuv")]
    if not a.skip_1080p:
        jobs.append(("BasketballDrive", 1920, 1080, 98, [24, 29, 34, 39],
                     lambda q: ROOT / f"visual/yuview/BasketballDrive_QP{q}_medium_1920x1080_50fps_10bit_420.yuv",
                     ROOT / "visual/yuview/BasketballDrive_original_1920x1080_50fps_10bit_420.yuv"))
    rows = []
    for seq, w, h, fr, qps, recf, orig in jobs:
        yo = frame_y(orig, w, h, fr)
        for q in qps:
            yr = frame_y(recf(q), w, h, fr)
            p, s, ms = metrics.psnr(yo, yr), metrics.ssim(yo, yr)[0], metrics.ms_ssim(yo, yr)
            c = next(v for v in VF if v["sequence"] == seq and int(v["frame"]) == fr and int(v["qp"]) == q)
            ok = round(p, 3) == float(c["y_psnr"]) and round(s, 5) == float(c["ssim"]) and round(ms, 5) == float(c["ms_ssim"])
            rows.append([seq, fr, q, f"{p:.3f} / {c['y_psnr']}", f"{s:.5f} / {c['ssim']}", f"{ms:.5f} / {c['ms_ssim']}", "yes" if ok else "NO"])
            R.checks.append((f"{seq} frame {fr} QP {q}: recalculated = CSV", ok))
    R.table(["sequence", "frame", "QP", "Y-PSNR now / CSV", "SSIM now / CSV", "MS-SSIM now / CSV", "match"], rows)
    R.p("Slide 8 shows the BasketballDrive frame-98 values rounded (PSNR 2 decimals, SSIM and MS-SSIM 3 decimals).")
    if not a.skip_1080p:
        deck = Presentation(DECK)
        caps = " ".join(sh.text_frame.text for sh in deck.slides[7].shapes if sh.has_text_frame)
        for r in rows[1:]:
            q, p, s, ms = r[2], float(r[3].split(" / ")[1]), float(r[4].split(" / ")[1]), float(r[5].split(" / ")[1])
            R.check(f"slide 8 caption QP {q} shows PSNR {p:.2f} dB, SSIM {s:.3f}, MS-SSIM {ms:.3f}",
                    f"PSNR {p:.2f} dB" in caps and f"SSIM {s:.3f}" in caps and f"MS-SSIM {ms:.3f}" in caps)
        SQ = read_csv(RES / "visual_sequence_ssim.csv")
        tbl = next(sh.table for sh in deck.slides[7].shapes if sh.has_table)
        ok = all(tbl.cell(i, j).text == f"{float(next(x for x in SQ if x['sequence'] == tbl.cell(i, 0).text and int(x['qp']) == q)['ms_ssim_mean']):.3f}"
                 for i in range(1, len(tbl.rows)) for j, q in enumerate([24, 29, 34, 39], 1))
        R.p("Slide 8 table = sequence-level MS-SSIM: mean over every 10th frame (50 or 60 frames), results/visual_sequence_ssim.csv, ms_ssim_mean.")
        R.check("all 16 values of the slide 8 MS-SSIM table equal results/visual_sequence_ssim.csv", ok)


# ===================================================================== Part 4 (slides 5 and 6)
def cfg(s, p, q):
    return next(c for c in CFG if c["sequence"] == s and c["preset"] == p and int(c["qp"]) == q)


def sources(c):
    ids = c["runs"].split(";")
    logs = []
    for i in ids:
        r = next((x for x in P2 if x["run_id"] == i), None) or next(x for x in P1 if x["run_id"] == i)
        logs.append(r["log_file"].replace("\\", "/"))
    return ids, logs


def part4():
    deck = Presentation(DECK)
    mapping = []
    R.h("Part 4 - Slide 5: QP and rate-distortion charts (4 native XY charts)")
    R.p("Each point = one configuration: x = bitrate_kbps, y = y (Y-PSNR, dB) from results/config_summary.csv.")
    R.p("config_summary.csv is built by analysis/analyze_full.py from results_raw.csv (phase 1) and results_phase2.csv (phase 2).")
    R.p("Bitrate and PSNR are identical for all repeats of a configuration (identical bitstreams), so the first run's values are used.")
    n_ok = n_all = 0
    for sh in deck.slides[4].shapes:
        if not sh.has_chart:
            continue
        seq = sh.name.replace("RD chart ", "")
        for name, xs, ys in chart_points(sh.chart):
            for q, x, y in zip([24, 29, 34, 39], xs, ys):
                c = cfg(seq, name, q)
                ok = x == float(c["bitrate_kbps"]) and y == float(c["y"])
                n_all += 1; n_ok += ok
                ids, logs = sources(c)
                mapping.append(dict(slide=5, element=f"RD chart {seq}", series=name, point=f"QP {q}", displayed=f"x={x} kbps, y={y} dB",
                                    source_csv="results/config_summary.csv", columns="bitrate_kbps, y", csv_value=f"{c['bitrate_kbps']}, {c['y']}",
                                    runs=";".join(ids), source_logs=";".join(logs), calculation="bitrate = bytes*8/(frames/fps)/1000; y = encoder Y-PSNR",
                                    match=ok))
    R.check(f"slide 5: all {n_all} chart points equal results/config_summary.csv ({n_ok}/{n_all})", n_ok == n_all)
    ex = next(m for m in mapping if m["series"] == "medium" and m["point"] == "QP 29" and "BasketballPass" in m["element"])
    R.p(f"Example: {ex['element']}, {ex['series']}, {ex['point']}: {ex['displayed']} <- config_summary row; run {ex['runs']}; log {ex['source_logs']}")

    # stat tiles on slide 5
    QPS, PRE, SEQS = [24, 29, 34, 39], ["faster", "fast", "medium", "slow"], ["BasketballPass", "BlowingBubbles", "BQMall", "BasketballDrive"]
    steps = [(float(cfg(s, p, q1)["bitrate_kbps"]) / float(cfg(s, p, q2)["bitrate_kbps"]), float(cfg(s, p, q1)["y"]) - float(cfg(s, p, q2)["y"]))
             for s in SEQS for p in PRE for q1, q2 in zip(QPS, QPS[1:])]
    rr, dd = [x for x, _ in steps], [y for _, y in steps]
    tiles = {sh.name: sh.text_frame.text for sh in deck.slides[4].shapes if sh.has_text_frame}
    t1 = f"÷{min(rr):.2f}–{max(rr):.2f}"
    t2 = f"−{min(dd):.1f}–{max(dd):.1f} dB"
    R.p(f"Tile 'Bitrate per +5 QP': {len(steps)} QP steps (4 sequences x 4 presets x 3 steps); ratio = bitrate(QP) / bitrate(QP+5)")
    R.p(f"   recalculated: min {min(rr):.3f}, max {max(rr):.3f}, median {st.median(rr):.3f}")
    R.check(f"slide 5 tile shows {t1} and median ÷{st.median(rr):.2f}", t1 in tiles["Stat 1 text"] and f"median ÷{st.median(rr):.2f}" in tiles["Stat 1 text"])
    R.p(f"Tile 'Y-PSNR per +5 QP': drop = Y-PSNR(QP) - Y-PSNR(QP+5); min {min(dd):.3f}, max {max(dd):.3f}, median {st.median(dd):.3f} dB")
    R.check(f"slide 5 tile shows {t2} and median −{st.median(dd):.2f} dB", t2 in tiles["Stat 2 text"] and f"median −{st.median(dd):.2f}" in tiles["Stat 2 text"])
    allruns = read_csv(RES / "results_all_runs.csv")
    good = [r for r in allruns if r["status"] in ("OK", "CHECK")]
    mx = max(float(r["check_diff"]) for r in good)
    R.p(f"Tile 'Independent PSNR check': largest |check - encoder| over {len(allruns)} runs (results_all_runs.csv, check_diff) = {mx:.4f} dB")
    R.check(f"slide 5 tile shows delta {mx:.4f} dB and {len(allruns)} runs", f"Δ {mx:.4f} dB" in tiles["Stat 3 text"] and f"all {len(allruns)} runs" in tiles["Stat 3 text"])
    for nm, val, how in (("Stat 1", t1, "min/max over 48 QP-step bitrate ratios, config_summary.csv bitrate_kbps"),
                         ("Stat 2", t2, "min/max over 48 QP-step Y-PSNR drops, config_summary.csv y"),
                         ("Stat 3", f"delta {mx:.4f} dB", "max of check_diff, results_all_runs.csv")):
        mapping.append(dict(slide=5, element=nm, displayed=val, source_csv="results/config_summary.csv" if nm != "Stat 3" else "results/results_all_runs.csv",
                            calculation=how, match=True))

    R.h("Part 4 - Slide 6: median encoding time at QP 29 (native line chart, log scale)")
    R.p("Each point = enc_median_s of results/config_summary.csv at QP 29 = median of the encoder 'Total Time' of all runs of that")
    R.p("configuration (runs flagged 'battery' are excluded from timing, e.g. B022 -> re-measured as C001).")
    ch = next(sh for sh in deck.slides[5].shapes if sh.has_chart).chart
    n_ok = n_all = 0
    rows = []
    for name, cats, ys in chart_points(ch):
        seq = name.split(" (")[0]
        for p, y in zip(cats, ys):
            c = cfg(seq, p, 29)
            ok = y == float(c["enc_median_s"])
            n_all += 1; n_ok += ok
            ids, logs = sources(c)
            rows.append([seq, p, f"{y:g}", f"{float(c['enc_median_s']):g}", c["enc_times"], ";".join(ids)])
            mapping.append(dict(slide=6, element="Encode time vs preset chart", series=name, point=p, displayed=f"{y} s",
                                source_csv="results/config_summary.csv", columns="enc_median_s (QP 29)", csv_value=c["enc_median_s"],
                                runs=";".join(ids), source_logs=";".join(logs), calculation="median of encoder 'Total Time' over the runs", match=ok))
    R.table(["sequence", "preset", "chart value (s)", "CSV enc_median_s", "single runs (s)", "runs"], rows)
    R.check(f"slide 6: all {n_all} chart points equal config_summary.csv enc_median_s ({n_ok}/{n_all})", n_ok == n_all)

    tiles = {sh.name: sh.text_frame.text for sh in deck.slides[5].shapes if sh.has_text_frame}
    R.p("Tiles 'faster/fast/slow vs medium': ratio = enc_median_s(preset, QP) / enc_median_s(medium, same QP),")
    R.p("over 4 sequences x 4 QPs = 16 ratios; the tile shows min-max.")
    for p, nd in (("faster", 2), ("fast", 2), ("slow", 1)):
        tr = [float(cfg(s, p, q)["enc_median_s"]) / float(cfg(s, "medium", q)["enc_median_s"]) for s in SEQS for q in QPS]
        shown = f"×{min(tr):.{nd}f}–{max(tr):.{nd}f}"
        R.p(f"   {p}: min {min(tr):.3f}, max {max(tr):.3f} -> {ascii_safe(shown)}")
        R.check(f"slide 6 tile '{p} vs medium' shows {shown}", shown in tiles[f"Ratio tile {p} text"])
        mapping.append(dict(slide=6, element=f"Ratio tile {p}", displayed=shown, source_csv="results/config_summary.csv", columns="enc_median_s",
                            calculation="min-max of 16 per-QP time ratios vs medium", match=shown in tiles[f"Ratio tile {p} text"]))
    dec = [float(c["dec_noout_median_s"]) for c in CFG]
    shown = f"{min(dec):.2f}–{max(dec):.1f} s"
    R.p(f"Tile 'decode time': min/max of dec_noout_median_s over all 64 configurations = {min(dec):.3f} / {max(dec):.3f} s")
    R.check(f"slide 6 decode tile shows {shown}", shown in tiles["Decode tile text"])
    REL = read_csv(RES / "timing_reliability.csv")
    cv = []
    for x in REL:
        tt = [float(v) for _, v in re.findall(r"([A-C]\d{3})=([\d.]+)s", x["measurements"])]
        if len(tt) >= 2:
            cv.append(st.stdev(tt) / st.mean(tt) * 100)
    shown = f"CV {min(cv):.1f}–{max(cv):.1f} %"
    R.p("Tile 'Timing repeatability': coefficient of variation CV = standard deviation / mean x 100 %, using only the phase-2")
    R.p(f"runs (ids A..., B..., C...) in results/timing_reliability.csv 'measurements'; {len(cv)} configurations.")
    R.check(f"slide 6 tile shows {shown} and {len(cv)} configurations", shown in tiles["Reliability tile text"] and f"{len(cv)} configurations" in tiles["Reliability tile text"])
    mapping += [dict(slide=6, element="Decode tile", displayed=f"{min(dec):.2f}-{max(dec):.1f} s", source_csv="results/config_summary.csv",
                     columns="dec_noout_median_s", calculation="min/max over 64 configurations", match=True),
                dict(slide=6, element="Reliability tile", displayed=f"CV {min(cv):.1f}-{max(cv):.1f} %", source_csv="results/timing_reliability.csv",
                     columns="measurements", calculation="stdev/mean of phase-2 runs per configuration", match=True)]

    path = OUT / R.path.name.replace("demo_results_", "slide_mapping_5_6_").replace(".md", ".csv")
    keys = ["slide", "element", "series", "point", "displayed", "source_csv", "columns", "csv_value", "runs", "source_logs", "calculation", "match"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(mapping)
    R.p(f"Full point-by-point mapping (slides 5 and 6, {len(mapping)} rows): {path}")


def ascii_safe(s):
    from demo_pyutil import ascii_text
    return ascii_text(s)


if a.part in ("3", "all"):
    part3()
if a.part in ("4", "all"):
    part4()
bad = R.save("Demo: measured values and slide 5/6 data sources")
raise SystemExit(1 if bad else 0)
