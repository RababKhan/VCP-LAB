"""demo_bdrate.py - Part 4 (slide 7): reproduce every BD-rate number from the saved CSV values.

What it does:
  1. Shows, step by step, how the four QP points of medium (anchor) and of one test preset give one BD-rate value.
  2. Recomputes all 12 BD-rates (4 sequences x faster/fast/slow vs medium) with the experiment's own function
     analysis/metrics.py bd_rate() - the same code analyze_full.py used - from results/config_summary.csv.
  3. Compares them with results/bdrate.csv and with the numbers shown on slide 7 of the FINAL PowerPoint
     (table and native chart).
No estimated or typed-in values are used: every input is read from the CSV, every output is compared with the CSV/deck.

Run from the professor_demo folder:
    ..\\.venv\\Scripts\\python.exe demo_bdrate.py
    ..\\.venv\\Scripts\\python.exe demo_bdrate.py --sequence BQMall --preset slow     (walk through another pair)
"""
import argparse
import math
import statistics as st

import numpy as np
from pptx import Presentation
from scipy.integrate import quad
from scipy.interpolate import PchipInterpolator

from demo_pyutil import DECK, RES, Report, chart_points, read_csv

import metrics  # analysis/metrics.py (unchanged)

SEQS = ["BasketballPass", "BlowingBubbles", "BQMall", "BasketballDrive"]
QPS = [24, 29, 34, 39]
ap = argparse.ArgumentParser()
ap.add_argument("--sequence", default="BasketballPass", choices=SEQS)
ap.add_argument("--preset", default="faster", choices=["faster", "fast", "slow"])
a = ap.parse_args()
R = Report("demo_bdrate")
CFG = read_csv(RES / "config_summary.csv")
BD = read_csv(RES / "bdrate.csv")


def cfg(s, p, q):
    return next(c for c in CFG if c["sequence"] == s and c["preset"] == p and int(c["qp"]) == q)


def points(s, p):
    return [float(cfg(s, p, q)["bitrate_kbps"]) for q in QPS], [float(cfg(s, p, q)["y"]) for q in QPS]


# ---------------------------------------------------------------- 1. step-by-step example
s, p = a.sequence, a.preset
ra, pa = points(s, "medium")
rt, pt = points(s, p)
R.h(f"1. Step by step: BD-rate of {p} against medium, {s}")
R.p("Why BD-rate? At the same QP, presets give different bitrate AND different quality, so you cannot compare one number.")
R.p("BD-rate asks: for the SAME quality (Y-PSNR), how many percent more (+) or fewer (-) bits does the test preset need?")
R.p("Inputs: the 4 QP points (24, 29, 34, 39) of each preset, from results/config_summary.csv (columns bitrate_kbps and y).")
R.table(["QP", "medium kbps", "medium Y-PSNR", f"{p} kbps", f"{p} Y-PSNR"],
        [[q, f"{ra[i]:.3f}", f"{pa[i]:.4f}", f"{rt[i]:.3f}", f"{pt[i]:.4f}"] for i, q in enumerate(QPS)])
lo, hi = max(min(pa), min(pt)), min(max(pa), max(pt))
ov = metrics.overlap_fraction(pa, pt)
R.p("Step a - validity: 4 points per curve, PSNR rises with bitrate, and the two PSNR ranges must overlap by >= 50 %.")
R.p(f"         medium PSNR range {min(pa):.4f}-{max(pa):.4f} dB, {p} range {min(pt):.4f}-{max(pt):.4f} dB")
R.p(f"         common range = {lo:.4f} to {hi:.4f} dB = {ov:.0%} of the smaller range  -> {'valid' if ov >= 0.5 else 'NOT valid'}")
R.p("Step b - for each curve, take log10(bitrate) as a function of PSNR and draw a smooth piecewise-cubic curve")
R.p("         through the 4 points (PCHIP interpolation).")
areas = []
for name, r_, p_ in (("medium", ra, pa), (p, rt, pt)):
    o = np.argsort(p_)
    f = PchipInterpolator(np.asarray(p_)[o], np.log10(np.asarray(r_))[o])
    areas.append(quad(f, lo, hi)[0])
    R.p(f"         {name:7s}: log10(kbps) = {', '.join(f'{math.log10(x):.4f}' for x in r_)};  area under the curve from "
        f"{lo:.3f} to {hi:.3f} dB = {areas[-1]:.5f}")
avg = (areas[1] - areas[0]) / (hi - lo)
bd = (10 ** avg - 1) * 100
R.p(f"Step c - average log10 difference = ({areas[1]:.5f} - {areas[0]:.5f}) / ({hi:.4f} - {lo:.4f}) = {avg:.5f}")
R.p(f"Step d - BD-rate = (10^{avg:.5f} - 1) x 100 % = {bd:+.2f} %")
R.p(f"         {'Positive: ' + p + ' needs MORE bits than medium for the same quality.' if bd > 0 else 'Negative: ' + p + ' needs FEWER bits than medium for the same quality.'}")
fn, _ = metrics.bd_rate(ra, pa, rt, pt, "pchip")
row = next(b for b in BD if b["sequence"] == s and b["test"] == p)
R.check(f"step-by-step result {bd:+.2f} % = metrics.bd_rate() {fn:+.2f} % = results/bdrate.csv {float(row['bdrate_Y_pchip_pct']):+.2f} %",
        round(bd, 2) == round(fn, 2) == float(row["bdrate_Y_pchip_pct"]))

# ---------------------------------------------------------------- 2. all 12 values
R.h("2. All 12 BD-rates recomputed with analysis/metrics.py (PCHIP, and the VCEG-M33 cubic polynomial as a cross-check)")
rows, maxpd, minov = [], 0, 1
for s in SEQS:
    ra, pa = points(s, "medium")
    for p in ("faster", "fast", "slow"):
        rt, pt = points(s, p)
        v, why = metrics.bd_rate(ra, pa, rt, pt, "pchip")
        v2, _ = metrics.bd_rate(ra, pa, rt, pt, "poly")
        ov = metrics.overlap_fraction(pa, pt)
        tr = [float(cfg(s, p, q)["enc_median_s"]) / float(cfg(s, "medium", q)["enc_median_s"]) for q in QPS]
        gm = math.exp(st.mean(math.log(x) for x in tr))
        b = next(x for x in BD if x["sequence"] == s and x["test"] == p)
        ok = (round(v, 2) == float(b["bdrate_Y_pchip_pct"]) and round(v2, 2) == float(b["bdrate_Y_poly_pct"])
              and round(ov, 2) == float(b["overlap_Y"]) and round(gm, 3) == float(b["time_ratio_vs_medium_geomean"]))
        maxpd, minov = max(maxpd, abs(v - v2)), min(minov, ov)
        rows.append([s, p, f"{v:+.2f}", b["bdrate_Y_pchip_pct"], f"{v2:+.2f}", f"{ov:.0%}", f"{gm:.3f}", "yes" if ok else "NO"])
        R.checks.append((f"{s} {p}: recomputed = results/bdrate.csv", ok))
R.table(["sequence", "test", "BD-rate PCHIP %", "bdrate.csv", "poly check %", "overlap", "time vs medium", "match"], rows)
R.p("'time vs medium' = geometric mean over the 4 QPs of enc_median_s(test) / enc_median_s(medium)  (bdrate.csv: time_ratio_vs_medium_geomean)")
R.check(f"all 12 recomputed values equal results/bdrate.csv ({sum(r[-1] == 'yes' for r in rows)}/12)", all(r[-1] == "yes" for r in rows))

# ---------------------------------------------------------------- 3. compare with slide 7
R.h("3. Compare with slide 7 of the FINAL PowerPoint")
deck = Presentation(DECK)
sl = deck.slides[6]
tbl = next(sh.table for sh in sl.shapes if sh.has_table)
ok_t = []
for i in range(1, 5):
    s = tbl.cell(i, 0).text.split("\n")[0]
    for j, p in enumerate(("faster", "fast", "slow"), 1):
        v = float(next(x for x in BD if x["sequence"] == s and x["test"] == p)["bdrate_Y_pchip_pct"])
        shown = tbl.cell(i, j).text
        expect = f"{'+' if v > 0 else '−'}{abs(v):.1f} %"
        ok_t.append(shown == expect)
R.check(f"slide 7 table: all 12 BD-rate cells equal bdrate.csv rounded to 1 decimal ({sum(ok_t)}/12)", all(ok_t))
for j, p in enumerate(("faster", "fast", "slow"), 1):
    g = [float(next(x for x in BD if x["sequence"] == s and x["test"] == p)["time_ratio_vs_medium_geomean"]) for s in SEQS]
    expect = f"×{min(g):.2f}–{max(g):.2f}"
    R.check(f"slide 7 'time vs medium' {p}: shows {expect} (min-max of the 4 sequence geometric means)", tbl.cell(5, j).text == expect)
ch = next(sh for sh in sl.shapes if sh.has_chart).chart
ok_c, n = 0, 0
for name, xs, ys in chart_points(ch):
    if name.startswith("medium"):
        R.check("slide 7 chart: medium anchor drawn at (1.0, 0 %)", xs == [1.0] and ys == [0.0])
        continue
    for s, x, y in zip(SEQS, xs, ys):
        b = next(z for z in BD if z["sequence"] == s and z["test"] == name)
        n += 1
        ok_c += x == float(b["time_ratio_vs_medium_geomean"]) and y == float(b["bdrate_Y_pchip_pct"])
R.check(f"slide 7 chart: all {n} points = (time_ratio_vs_medium_geomean, bdrate_Y_pchip_pct) from bdrate.csv ({ok_c}/{n})", ok_c == n)
note = next(sh.text_frame.text for sh in sl.shapes if sh.name == "BD-rate note")
R.check(f"slide 7 note: overlap >= {minov:.0%} and polynomial check within {maxpd:.2f} %", f"≥ {minov:.0%}" in note and f"within {maxpd:.2f} %" in note)

R.h("What the numbers mean (slide 7)")
for p in ("faster", "fast", "slow"):
    v = [float(x["bdrate_Y_pchip_pct"]) for x in BD if x["test"] == p]
    g = [float(x["time_ratio_vs_medium_geomean"]) for x in BD if x["test"] == p]
    word = "MORE" if min(v) > 0 else "FEWER"
    R.p(f"{p:6s}: {min(abs(x) for x in v):.1f} to {max(abs(x) for x in v):.1f} % {word} bits than medium for the same quality, "
        f"using {min(g):.2f} to {max(g):.2f} x medium's encoding time.")
R.p("Each slower preset saves fewer bits per extra second of encoding: diminishing returns.")
bad = R.save("Demo: BD-rate reproduction for slide 7")
raise SystemExit(1 if bad else 0)
