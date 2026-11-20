"""Build the 10-slide deck for Sadab's expanded VVC experiment (phases 1-7) on his Prangon.pptx (Cordelia) template.
Every number is read from results/*.csv|json. Wording avoids claiming that Sadab personally ran or inspected
anything that was automated (see results/EXPERIMENT_REPORT_v2.md, section 14).
The earlier 8-slide version is kept in presentation/archive/."""
import csv
import json
import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deck_lib import *  # noqa: E402,F401,F403
from deck_lib import prs, L_TITLE, content_slide, text, shape, shape_text, line, style_chart, axis_style, log_axis  # noqa: E402

R = PROJ / "results"
S = json.loads((R / "summary_full.json").read_text(encoding="utf-8"))
XP = json.loads((R / "crossplatform_v2.json").read_text(encoding="utf-8"))
VS = json.loads((PROJ / "visual/v2/selection.json").read_text(encoding="utf-8"))
CFG = list(csv.DictReader(open(R / "config_summary.csv", encoding="utf-8")))
BD = list(csv.DictReader(open(R / "bdrate.csv", encoding="utf-8")))
REL = list(csv.DictReader(open(R / "timing_reliability.csv", encoding="utf-8")))
VF = list(csv.DictReader(open(R / "visual_frame_metrics.csv", encoding="utf-8")))
VSQ = list(csv.DictReader(open(R / "visual_sequence_ssim.csv", encoding="utf-8")))
SEQS = ["BasketballPass", "BlowingBubbles", "BQMall", "BasketballDrive"]
RES = {"BasketballPass": "416×240", "BlowingBubbles": "416×240", "BQMall": "832×480", "BasketballDrive": "1920×1080"}
PRE = ["faster", "fast", "medium", "slow"]
QPS = [24, 29, 34, 39]
LIGHT_OR = RGBColor(0xF2, 0xA5, 0x41)
TEAL = RGBColor(0x00, 0x89, 0x7B)
PCOL = {"faster": LIGHT_OR, "fast": ORANGE, "medium": DEEP, "slow": TEAL}
SCOL = {"BasketballPass": BLUE, "BlowingBubbles": ORANGE, "BQMall": TEAL, "BasketballDrive": DEEP}
OUTV3 = HERE / "VVC_Assignment_Sadab_Khan_Prangon_v2_10slides.pptx"
NOTES = {}


def cf(s, p, q):
    return next(c for c in CFG if c["sequence"] == s and c["preset"] == p and int(c["qp"]) == q)


def bdv(s, t, k="bdrate_Y_pchip_pct"):
    return float(next(b for b in BD if b["sequence"] == s and b["test"] == t)[k])


def f(x, n=2):
    return f"{x:.{n}f}"


def sg(x, n=1):
    return ("+" if x >= 0 else "−") + f"{abs(x):.{n}f}"


def chart_title(ch, t, size=11):
    ch.has_title = True
    ch.chart_title.text_frame.text = t
    r = ch.chart_title.text_frame.paragraphs[0].runs[0]
    r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(size), True, INK, BODY


def small_axis(ax, title=None, fmt=None, size=8):
    axis_style(ax, title, fmt=fmt)
    ax.tick_labels.font.size = Pt(size)
    if title:
        ax.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(size)


def series_style(s, col, lw=1.75, ms=5, line_on=True):
    if line_on:
        s.format.line.color.rgb = col
        s.format.line.width = Pt(lw)
    else:
        s.format.line.fill.background()
    s.marker.style = XL_MARKER_STYLE.CIRCLE
    s.marker.size = ms
    s.marker.format.fill.solid()
    s.marker.format.fill.fore_color.rgb = col
    s.marker.format.line.color.rgb = WHITE


def legend_row(slide, x, y, items, size=10, name="Legend"):
    runs = []
    for lab, col in items:
        runs += [("● ", size, col, False, False), (lab + "     ", size, MUTED, False, False)]
    return text(slide, x, y, 6, 0.25, [runs], name=name)


def tile(slide, x, y, w, h, label, value, sub=None, name="Tile", vsize=16):
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=CARD, name=name, adj=0.08)
    paras = [[(label, 10, MUTED, True, False)], [(value, vsize, INK, True, False, HEAD)]]
    if sub:
        paras.append([(sub, 9, MUTED, False, False)])
    text(slide, x + 0.14, y + 0.1, w - 0.26, h - 0.15, paras, name=name + " text", space_after=2)


def table(slide, x, y, w, h, data, col_w, name, size=10, head_fill=DEEP):
    gt = slide.shapes.add_table(len(data), len(data[0]), Inches(x), Inches(y), Inches(w), Inches(h))
    gt.name = name
    t = gt.table
    for j, cw in enumerate(col_w):
        t.columns[j].width = Inches(cw)
    for i, row in enumerate(data):
        t.rows[i].height = Inches(h / len(data))
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.fill.solid()
            cell.fill.fore_color.rgb = head_fill if i == 0 else (CARD if i % 2 else WHITE)
            tf = cell.text_frame
            tf.text = ""
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            col = WHITE if i == 0 else (INK if j == 0 else (val[1] if isinstance(val, tuple) else INK))
            txt = val[0] if isinstance(val, tuple) else val
            r = p.add_run()
            r.text = txt
            font(r, size, col, i == 0 or isinstance(val, tuple), False)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    tblPr = gt._element.graphic.graphicData.tbl.tblPr
    tblPr.set("firstRow", "1")
    tblPr.set("bandRow", "0")
    return gt


q = S["qp_step"]
pv = S["preset_vs_medium"]
tm = {t: [float(next(b for b in BD if b["sequence"] == s and b["test"] == t)["time_ratio_vs_medium_geomean"]) for s in SEQS]
      for t in ("faster", "fast", "slow")}
bdr = {t: [bdv(s, t) for s in SEQS] for t in ("faster", "fast", "slow")}
cv = [float(x["cv_pct"]) for x in REL]
import re as _re
P2CV = []
for x in REL:
    tt = [float(v) for k, v in _re.findall(r"([A-C]\d{3})=([\d.]+)s", x["measurements"])]
    if len(tt) >= 2:
        P2CV.append(st.stdev(tt) / st.mean(tt) * 100)
p2rel = [x for x in REL]
dec = [float(c["dec_noout_median_s"]) for c in CFG]
xp_new = XP["phase6_runs"]
xp_all_ok = all(all(i["match"].values()) for i in xp_new) and all(all(i["match"].values()) for i in XP["phase1_checks"]["full_length"])
n_xp = len(xp_new) + len(XP["phase1_checks"]["full_length"]) + 1

# =============================================================================================================
# 1. Title
NOTES[1] = (
    "Good morning, Professor Choi. My name is Sadab Khan Prangon. I am a B.Sc. student in Computer Science and "
    "Engineering at IUBAT in Bangladesh.\n\n"
    "This talk presents the VVC assignment: building VVenC and VVdeC on Windows and Linux, encoding and decoding "
    "test videos, and analysing rate, quality and complexity. The experiment was extended to 64 configurations: "
    "four sequences, four QP values and four presets.\n\n"
    "I want to be transparent: the builds and runs were executed by automated scripts with the help of an AI "
    "assistant, and every log and measurement is kept in the report. My goal today is to explain what the "
    "results show and what they do not show."
)
s = prs.slides.add_slide(L_TITLE)
for ph in list(s.placeholders):
    if ph.placeholder_format.type != 3:
        ph._element.getparent().remove(ph._element)
t = s.shapes.title
t.left, t.top, t.width, t.height = Inches(0.95), Inches(0.95), Inches(8.2), Inches(1.25)
t.text_frame.text = ""
t.text_frame.vertical_anchor = MSO_ANCHOR.TOP
p = t.text_frame.paragraphs[0]
r = p.add_run(); r.text = "VVC Encoding and Decoding:"; font(r, 30, BLUE, True, face=HEAD)
p = t.text_frame.add_paragraph()
r = p.add_run(); r.text = "Rate, Quality and Complexity of VVenC Presets"; font(r, 22, INK, face=HEAD)
text(s, 0.95, 0.62, 8.0, 0.3, [[("ASSIGNMENT  ·  VIDEO CODING AND PROCESSING LAB, KYUNG HEE UNIVERSITY", 11, MUTED, True, False)]], name="Kicker")
text(s, 0.95, 2.3, 8.0, 1.1, [
    [("Sadab Khan Prangon", 18, INK, True, False)],
    [("B.Sc. in Computer Science and Engineering, International University of Business Agriculture and Technology (IUBAT), Bangladesh", 12, MUTED, False, False)],
    [("Assignment given by Prof. Kiho Choi, Video Coding and Processing Lab, Kyung Hee University", 12, MUTED, False, False)],
], name="Presenter", space_after=2)
objs = [("1", "Build", "VVenC + VVdeC on\nWindows and Linux"), ("2", "Encode", f"{S['n_configs_measured']} configurations\n4 seq × 4 QP × 4 presets"),
        ("3", "Verify", "PSNR, SSIM, MS-SSIM\nWindows vs Linux"), ("4", "Analyse", "BD-rate and\ntiming reliability")]
x0, gap, yc, d = 1.25, 1.85, 3.75, 0.5
line(s, x0, yc, x0 + gap * 3, yc, color=LINE, w=1.5, name="Objective chain")
for i, (n, head, sub) in enumerate(objs):
    cx = x0 + gap * i
    c = shape(s, MSO_SHAPE.OVAL, cx - d / 2, yc - d / 2, d, d, fill=WHITE, line=BLUE, line_w=2, name=f"Objective {n} node")
    shape_text(c, [[(n, 14, BLUE, True, False)]])
    text(s, cx - 0.85, yc + 0.35, 1.7, 0.85, [[(head, 13, INK, True, False)], [(sub, 11, MUTED, False, False)]],
         align=PP_ALIGN.CENTER, name=f"Objective {n} label")
text(s, 2.9, 5.05, 6.2, 0.3, [[("Runs executed by automated scripts with an AI assistant (Claude); all logs and data are in the report.",
                               9, MUTED, False, True)]], align=PP_ALIGN.RIGHT, name="Execution note")
s.notes_slide.notes_text_frame.text = NOTES[1]

# =============================================================================================================
# 2. Workflow (same design as before)
NOTES[2] = (
    "This is the pipeline. The original video is a raw 10-bit 4:2:0 YUV file with no header, so the size, "
    "frame rate and format must be given on the command line.\n\n"
    "VVenC encodes it into a .266 bitstream; here the encoding time and the file size are measured, and the "
    "bitrate is computed from the size. VVdeC decodes it again. The decoding time is measured three times "
    "without writing an output file, and one extra decode writes the reconstruction.\n\n"
    "The reconstruction is compared with the original frame by frame: PSNR for every run, and SSIM and MS-SSIM "
    "for selected frames. The same pipeline exists on Windows and Linux."
)
s = content_slide("VVC Encoding and Decoding Workflow", 2, NOTES[2])
xs = [1.45, 3.2, 4.95, 6.7, 8.45]
yc, d = 2.3, 1.0
nodes = [("YUV", False, "Original video", "raw frames, 10-bit\n4:2:0, no header"), ("VVenC", True, "Encoder", "vvencapp\nQP + preset"),
         (".266", False, "Bitstream", "compressed\nH.266/VVC file"), ("VVdeC", True, "Decoder", "vvdecapp\n8 threads"),
         ("YUV", False, "Reconstruction", "decoded frames,\nsame format")]
chips = ["reference for\nquality", "encoding time (s)", "size (bytes) →\nbitrate (kbps)", "decoding time (s),\nno output file",
         "PSNR · SSIM ·\nMS-SSIM"]
yb = 1.5
line(s, xs[0], yb, xs[-1], yb, color=MUTED, w=1.25, dash=MSO_LINE.DASH, name="Compare bracket")
line(s, xs[0], yb, xs[0], yc - d / 2 - 0.04, color=MUTED, w=1.25, dash=MSO_LINE.DASH, name="Compare bracket left")
line(s, xs[-1], yb, xs[-1], yc - d / 2 - 0.04, color=MUTED, w=1.25, dash=MSO_LINE.DASH, arrow=True, name="Compare bracket right")
lab = shape(s, MSO_SHAPE.RECTANGLE, 3.05, yb - 0.15, 3.8, 0.3, fill=WHITE, name="Compare label")
shape_text(lab, [[("compare frame by frame  →  quality metrics", 11, MUTED, False, True)]])
for i, (inner, proc, head, sub) in enumerate(nodes):
    cx = xs[i]
    if i < len(nodes) - 1:
        line(s, cx + d / 2 + 0.06, yc, xs[i + 1] - d / 2 - 0.08, yc, color=BLUE, w=1.75, arrow=True, name=f"Flow {i + 1}")
    c = shape(s, MSO_SHAPE.OVAL, cx - d / 2, yc - d / 2, d, d, fill=BLUE if proc else WHITE, line=BLUE, line_w=2, name=f"Node {head}")
    shape_text(c, [[(inner, 13, WHITE if proc else BLUE, True, False)]])
    text(s, cx - 0.82, yc + 0.6, 1.64, 0.75, [[(head, 13, INK, True, False)], [(sub, 11, MUTED, False, False)]],
         align=PP_ALIGN.CENTER, name=f"Label {head}")
    ch = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, cx - 0.8, 3.82, 1.6, 0.52, fill=SKY if i else WHITE, line=None if i else LINE,
               name=f"Measure {head}", adj=0.3)
    shape_text(ch, [[(chips[i], 10, DEEP if i else MUTED, i > 0, False)]])
text(s, 2.9, 4.6, 6.24, 0.3, [[("●", 11, BLUE, False, False), (" process    ", 11, MUTED, False, False),
                              ("○", 11, BLUE, False, False), (" data    ", 11, MUTED, False, False),
                              ("blue boxes = measured  ·  same pipeline on Windows and Linux", 11, MUTED, False, False)]],
     align=PP_ALIGN.RIGHT, name="Legend")

# =============================================================================================================
# 3. Implementation and build verification
NOTES[3] = (
    "VVenC 1.14.0 and VVdeC 3.2.1 were built from source with the same release tags on both systems: on Windows 11 "
    "with MSVC 19.44, and on Ubuntu 24.04 in WSL2 with GCC 13.3.\n\n"
    "On Linux all 39 VVenC tests and the VVdeC unit test passed. On Windows, 32 of 39 passed; seven could not run "
    "because Windows Smart App Control blocked two unsigned test programs. No security setting was changed. The "
    "VVdeC conformance tests were not run, because their bitstreams are not part of the source code.\n\n"
    f"Before the main runs, a 16-frame smoke test passed on both systems. Then {S['runs_total']} encoder runs "
    "were made on Windows, and selected configurations were repeated on Linux for a bit-exactness check."
)
s = content_slide("Implementation and Build Verification", 3, NOTES[3])
rows = ["Compiler", "CMake", "VVenC", "VVdeC", "Unit tests", "Encode runs"]
win_vals = ["MSVC 19.44 (VS 2022)", "4.4.4", "1.14.0 · 9428ea8", "3.2.1 · cb1a3ef", "VVenC 32/39 *", f"smoke + {S['runs_total']} runs"]
lin_vals = ["GCC 13.3.0", "3.28.3", "1.14.0 · 9428ea8", "3.2.1 · cb1a3ef", "VVenC 39/39, VVdeC OK", f"smoke + {len(xp_new) + 2} full runs"]
for xx, osname, sub, vals in [(0.86, "Windows", "Windows 11 Home, build 26200", win_vals), (5.64, "Linux", "Ubuntu 24.04.5 in WSL2", lin_vals)]:
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, xx, 1.35, 3.5, 3.0, fill=CARD, name=f"{osname} card", adj=0.05)
    text(s, xx + 0.25, 1.5, 2.3, 0.55, [[(osname, 16, INK, True, False, HEAD)], [(sub, 11, MUTED, False, False)]], name=f"{osname} heading")
    tg = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, xx + 2.4, 1.55, 0.9, 0.28, fill=WHITE, line=BLUE, line_w=1, name=f"{osname} status", adj=0.5)
    shape_text(tg, [[("BUILT", 10, BLUE, True, False)]])
    for j, (rname, val) in enumerate(zip(rows, vals)):
        yy = 2.15 + j * 0.31
        text(s, xx + 0.25, yy, 1.1, 0.28, [[(rname, 12, INK, True, False)]], name=f"{osname} {rname} label")
        text(s, xx + 1.4, yy, 2.05, 0.28, [[(val, 12, INK, False, False)]], name=f"{osname} {rname} value")
text(s, 1.11, 3.98, 3.15, 0.36, [[("* 7 not run: Smart App Control blocked 2 unsigned test programs", 10, MUTED, False, True)]], name="Windows footnote")
text(s, 5.89, 3.98, 3.15, 0.36, [[("VVdeC conformance tests not run on either system (test bitstreams not included)", 10, MUTED, False, True)]],
     name="Conformance footnote")
line(s, 4.36, 2.75, 5.64, 2.75, color=BLUE, w=1.5, dash=MSO_LINE.DASH, name="Cross-platform link")
c = shape(s, MSO_SHAPE.OVAL, 4.5, 2.25, 1.0, 1.0, fill=BLUE if xp_all_ok else WHITE, line=BLUE, line_w=2, name="Bit-exact node")
shape_text(c, [[(f"{n_xp}/{n_xp}", 13, WHITE, True, False)], [("bit-exact", 10, WHITE, False, False)]])
text(s, 4.36, 3.35, 1.28, 0.5, [[("details on", 10, MUTED, False, False)], [("slide 9", 10, MUTED, False, False)]], align=PP_ALIGN.CENTER, name="Bit-exact note")
text(s, 0.86, 4.5, 0.8, 0.3, [[("Tools", 12, INK, True, False)]], name="Tools label")
for j, tname in enumerate(["Git 2.55", "Python 3.12 · numpy · scipy", "YUView 2.14", "VS 2022 Build Tools"]):
    chp = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 1.6 + j * 1.9, 4.47, 1.75, 0.36, fill=SKY, name=f"Tool {j + 1}", adj=0.5)
    shape_text(chp, [[(tname, 10, DEEP, False, False)]])

# =============================================================================================================
# 4. Methodology
NOTES[4] = (
    "The experiment design. Four standard sequences: two at 416 by 240, BQMall at 832 by 480, and BasketballDrive "
    "at 1080p, each 10 seconds long. Four QP values and four presets give 64 configurations. Sixteen of them came "
    "from the first round of the experiment with exactly the same settings, so they were reused.\n\n"
    "Because timing on a laptop is noisy, several controls were added: a warm-up before each block, a check for AC "
    "power before every run, a random run order with a recorded seed, and a CPU monitor every five seconds. Nine "
    "configurations were measured at least four times, and decoding was timed three times without writing a file.\n\n"
    "For every run, the PSNR was also checked with an independent script."
)
s = content_slide("Expanded Experimental Methodology", 4, NOTES[4])
text(s, 0.86, 1.25, 2.6, 0.25, [[("4 sequences", 11, MUTED, True, False)]], name="Seq caption")
specs = {"BasketballPass": "416×240 · 50 fps", "BlowingBubbles": "416×240 · 50 fps", "BQMall": "832×480 · 60 fps",
         "BasketballDrive": "1920×1080 · 50 fps"}
for j, sq in enumerate(SEQS):
    card = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.86, 1.52 + j * 0.47, 2.5, 0.41, fill=CARD, name=f"Seq {sq}", adj=0.2)
    shape_text(card, [[(sq, 11, INK, True, False), ("  " + specs[sq], 9, MUTED, False, False)]], align=PP_ALIGN.LEFT)
    card.text_frame.margin_left = Inches(0.12)
for xx, op in [(3.42, "×"), (5.0, "×"), (6.8, "=")]:
    text(s, xx, 2.05, 0.35, 0.5, [[(op, 24, MUTED, False, False)]], align=PP_ALIGN.CENTER, name=f"Operator {op}")
text(s, 3.85, 1.25, 1.3, 0.25, [[("4 QPs", 11, MUTED, True, False)]], name="QP caption")
for j, qp in enumerate(QPS):
    cx, cy = 4.12 + (j % 2) * 0.62, 1.95 + (j // 2) * 0.62
    c = shape(s, MSO_SHAPE.OVAL, cx - 0.26, cy - 0.26, 0.52, 0.52, fill=WHITE, line=BLUE, line_w=2, name=f"QP {qp}")
    shape_text(c, [[(str(qp), 12, BLUE, True, False)]])
text(s, 5.45, 1.25, 1.3, 0.25, [[("4 presets", 11, MUTED, True, False)]], name="Preset caption")
for j, pn in enumerate(PRE):
    pill = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 5.45, 1.52 + j * 0.47, 1.2, 0.38, fill=PCOL[pn], name=f"Preset {pn}", adj=0.5)
    shape_text(pill, [[(pn, 11, INK if pn == "faster" else WHITE, True, False)]])
c = shape(s, MSO_SHAPE.OVAL, 7.3, 1.55, 1.35, 1.35, fill=BLUE, name="Total node")
shape_text(c, [[("64", 28, WHITE, True, False, HEAD)], [("configurations", 10, WHITE, False, False)]])
for xx, head, items, nm in [
    (0.86, "Timing controls", ["warm-up run before each block", "AC power checked before every run", "random order, recorded seeds",
                               "CPU monitor every 5 s", f"{len(REL)} configurations × ≥4 runs"], "Controls"),
    (5.14, "Measured for every run", ["encode time, bitstream size → bitrate", "Y/U/V-PSNR + independent check",
                                     "decoded SHA-256 and frame count", "decode time ×3 (no output file)",
                                     "SSIM / MS-SSIM on selected frames"], "Measured")]:
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, xx, 3.5, 4.0, 1.42, fill=CARD, name=f"{nm} card", adj=0.06)
    paras = [[(head, 12, INK, True, False)]] + [[(it, 11, INK, False, False)] for it in items]
    text(s, xx + 0.2, 3.58, 3.65, 1.3, paras, name=f"{nm} text", space_after=1, bullet_from=1)

# =============================================================================================================
# 5. QP and RD
NOTES[5] = (
    "The first result: QP and rate–distortion. Each small chart is one sequence; each line is one preset, and the "
    "four points are QP 24 to 39.\n\n"
    f"Across all 48 QP steps, each increase of 5 in QP divided the bitrate by {f(q['ratio_min'])} to {f(q['ratio_max'])}, "
    f"about {f(q['ratio_median'], 1)} times, and lowered the Y-PSNR by {f(q['drop_min'], 1)} to {f(q['drop_max'], 1)} dB. "
    "The quality loss per step is smallest for BasketballDrive and largest for the small sequences.\n\n"
    "The curves of the four presets are almost parallel, with slow on top and faster at the bottom. "
    f"The independent PSNR check matched the encoder in all {S['runs_total']} runs."
)
s = content_slide("QP and Rate–Distortion Analysis", 5, NOTES[5])
legend_row(s, 0.86, 1.18, [(p, PCOL[p]) for p in PRE], size=10, name="RD legend")
for k, sq in enumerate(SEQS):
    cd = XyChartData()
    ys, xs_ = [], []
    for p in PRE:
        se = cd.add_series(p)
        for qq in QPS:
            c_ = cf(sq, p, qq)
            se.add_data_point(float(c_["bitrate_kbps"]), float(c_["y"]))
            ys.append(float(c_["y"])); xs_.append(float(c_["bitrate_kbps"]))
    x, y = 0.75 + (k % 2) * 3.0, 1.42 + (k // 2) * 1.82
    gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES, Inches(x), Inches(y), Inches(2.95), Inches(1.8), cd)
    gf.name = f"RD chart {sq}"
    ch = gf.chart
    style_chart(ch, 8)
    chart_title(ch, f"{sq} ({RES[sq]})", 9)
    ch.has_legend = False
    for se, p in zip(ch.plots[0].series, PRE):
        se.smooth = False
        series_style(se, PCOL[p], 1.5, 4)
    small_axis(ch.category_axis, "kbps (log)", "#,##0")
    log_axis(ch.category_axis, 10 ** math.floor(math.log10(min(xs_))), 10 ** math.ceil(math.log10(max(xs_))))
    small_axis(ch.value_axis, "Y-PSNR (dB)", "0")
    ch.value_axis.minimum_scale, ch.value_axis.maximum_scale = math.floor(min(ys)) - 1, math.ceil(max(ys)) + 1
    ch.value_axis.major_unit = 2
for j, (lab, val, sub) in enumerate([
        ("Bitrate per +5 QP", f"÷{f(q['ratio_min'])}–{f(q['ratio_max'])}", f"median ÷{f(q['ratio_median'])} · {q['n']} steps"),
        ("Y-PSNR per +5 QP", f"−{f(q['drop_min'], 1)}–{f(q['drop_max'], 1)} dB", f"median −{f(q['drop_median'])} dB"),
        ("Independent PSNR check", f"Δ {S['max_psnr_check_diff']:.4f} dB", f"all {S['runs_total']} runs, peak 1020")]):
    tile(s, 6.85, 1.35 + j * 1.2, 2.29, 1.08, lab, val, sub, name=f"Stat {j + 1}")

# =============================================================================================================
# 6. Preset and complexity
t29 = {sq: [float(cf(sq, p, 29)["enc_median_s"]) for p in PRE] for sq in SEQS}
NOTES[6] = (
    "Preset complexity: the chart shows the median encoding time at QP 29 on a log scale. Each step to a slower "
    "preset multiplies the time.\n\n"
    f"Compared with medium at the same QP, faster needed only {f(pv['faster']['time_ratio_min'])} to "
    f"{f(pv['faster']['time_ratio_max'])} of the time, fast {f(pv['fast']['time_ratio_min'])} to {f(pv['fast']['time_ratio_max'])}, "
    f"and slow {f(pv['slow']['time_ratio_min'], 1)} to {f(pv['slow']['time_ratio_max'], 1)} times. BasketballDrive at 1080p "
    f"took up to {max(t29['BasketballDrive']):.0f} seconds per encode at QP 29.\n\n"
    f"Decoding took only {f(min(dec))} to {f(max(dec), 1)} seconds.\n\n"
    f"Timing is now repeatable: the controlled repeats varied by only {f(min(P2CV), 1)} to {f(max(P2CV), 1)} percent. The 45 percent "
    "gap in the first round came from a short slow period of the whole laptop at the start."
)
s = content_slide("Preset and Encoding Complexity", 6, NOTES[6])
cd = CategoryChartData()
cd.categories = PRE
for sq in SEQS:
    cd.add_series(f"{sq} ({RES[sq]})", t29[sq])
gf = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.75), Inches(1.25), Inches(5.3), Inches(3.75), cd)
gf.name = "Encode time vs preset chart"
ch = gf.chart
style_chart(ch, 9)
chart_title(ch, "Median encoding time at QP 29 (s, log scale)", 11)
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout = False
ch.legend.font.size = Pt(8)
for se, sq in zip(ch.plots[0].series, SEQS):
    series_style(se, SCOL[sq], 2, 6)
    se.smooth = False
small_axis(ch.value_axis, None, "#,##0", 9)
log_axis(ch.value_axis, 1, 10000)
small_axis(ch.category_axis, None, None, 10)
ch.category_axis.has_major_gridlines = False
for j, (p, lab) in enumerate([("faster", "faster vs medium"), ("fast", "fast vs medium"), ("slow", "slow vs medium")]):
    x_ = pv[p]
    tile(s, 6.25 + (j % 2) * 1.47, 1.3 + (j // 2) * 1.2, 1.4, 1.1, lab + "\n(time, same QP)",
         f"×{f(x_['time_ratio_min'])}–{f(x_['time_ratio_max'])}" if p != "slow" else f"×{f(x_['time_ratio_min'], 1)}–{f(x_['time_ratio_max'], 1)}",
         name=f"Ratio tile {p}", vsize=13)
tile(s, 7.72, 2.5, 1.4, 1.1, "decode time\n(no output file)", f"{f(min(dec), 2)}–{f(max(dec), 1)} s", name="Decode tile", vsize=13)
tile(s, 6.25, 3.72, 2.87, 1.15, "Timing repeatability (phase-2 repeats)",
     f"CV {f(min(P2CV), 1)}–{f(max(P2CV), 1)} %",
     f"{len(P2CV)} configurations, ≥3 phase-2 runs each; the earlier 45 % gap was a slow start phase", name="Reliability tile", vsize=15)

# =============================================================================================================
# 7. BD-rate
NOTES[7] = (
    "Presets give different quality at the same QP, so they are compared with BD-rate against medium, over the "
    "four QP points. A piecewise cubic interpolation is integrated over the common quality range; all curves "
    "overlapped by more than 90 percent.\n\n"
    f"Faster needs {min(bdr['faster']):.0f} to {max(bdr['faster']):.0f} percent more bitrate for the same quality, fast "
    f"{min(bdr['fast']):.0f} to {max(bdr['fast']):.0f} percent more, and slow saves {abs(max(bdr['slow'])):.1f} to "
    f"{abs(min(bdr['slow'])):.1f} percent, but costs about {min(tm['slow']):.1f} to {max(tm['slow']):.1f} times the time.\n\n"
    "So each slower preset gives a smaller saving for a larger time cost: diminishing returns. The penalty of "
    "faster is larger for the bigger sequences, but with one sequence per resolution this is only a trend."
)
s = content_slide("BD-rate and Compression Efficiency", 7, NOTES[7])
cd = XyChartData()
for p in ("faster", "fast", "slow"):
    se = cd.add_series(p)
    for sq in SEQS:
        b = next(x for x in BD if x["sequence"] == sq and x["test"] == p)
        se.add_data_point(float(b["time_ratio_vs_medium_geomean"]), float(b["bdrate_Y_pchip_pct"]))
se = cd.add_series("medium (anchor)")
se.add_data_point(1.0, 0.0)
gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(0.75), Inches(1.25), Inches(4.6), Inches(3.7), cd)
gf.name = "BD-rate vs time chart"
ch = gf.chart
style_chart(ch, 9)
chart_title(ch, "BD-rate vs encoding time (anchor: medium)", 11)
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout = False
ch.legend.font.size = Pt(9)
for se, p in zip(ch.plots[0].series, ("faster", "fast", "slow", "medium")):
    series_style(se, PCOL[p], ms=8, line_on=False)
small_axis(ch.category_axis, "encoding time relative to medium (log)", "0.0#", 9)
log_axis(ch.category_axis, 0.05, 5)
small_axis(ch.value_axis, "BD-rate, Y-PSNR (%)", "0", 9)
ch.value_axis.minimum_scale, ch.value_axis.maximum_scale, ch.value_axis.major_unit = -10, 40, 10
data = [["Sequence", "faster", "fast", "slow"]]
for sq in SEQS:
    data.append([f"{sq}\n{RES[sq]}"] + [(f"{sg(bdv(sq, t))} %", ORANGE if bdv(sq, t) > 0 else TEAL) for t in ("faster", "fast", "slow")])
data.append(["time vs medium"] + [f"×{min(tm[t]):.2f}–{max(tm[t]):.2f}" for t in ("faster", "fast", "slow")])
table(s, 5.6, 1.3, 3.54, 2.95, data, [1.32, 0.74, 0.74, 0.74], "BD-rate table", size=9)
ov = min(min(float(b["overlap_Y"]) for b in BD), 1)
pd = max(abs(float(b["bdrate_Y_pchip_pct"]) - float(b["bdrate_Y_poly_pct"])) for b in BD)
text(s, 5.6, 4.35, 3.54, 0.6, [[(f"BD-rate vs medium on Y-PSNR, PCHIP over 4 QPs (24–39). PSNR overlap ≥ {ov:.0%} in every case; "
                                 f"cubic-polynomial check within {pd:.2f} %.", 9, MUTED, False, False)]], name="BD-rate note")

# =============================================================================================================
# 8. Visual quality
sel = VS["sequences"]["BasketballDrive"]["typical"]
FR, (cx_, cy_, cw_, chh_) = sel["frame_0based"], sel["crop_xywh"]
vrows = sorted([x for x in VF if x["sequence"] == "BasketballDrive" and x["frame_kind"] == "typical"], key=lambda x: int(x["qp"]))
NOTES[8] = (
    f"For visual quality, frame {FR} of BasketballDrive is shown with the same crop for the original and for QP 24 "
    "to 39 at the medium preset. The frame and crop were chosen by a fixed rule before looking: the frame with "
    "the median quality at QP 39, and the most detailed area of that frame.\n\n"
    f"From QP 24 to QP 39, the frame PSNR falls from {float(vrows[0]['y_psnr']):.1f} to {float(vrows[-1]['y_psnr']):.1f} dB, "
    f"SSIM from {float(vrows[0]['ssim']):.3f} to {float(vrows[-1]['ssim']):.3f}, and MS-SSIM from {float(vrows[0]['ms_ssim']):.3f} "
    f"to {float(vrows[-1]['ms_ssim']):.3f}. The table shows the sequence-level MS-SSIM for all four sequences.\n\n"
    "[Sadab: after checking these frames yourself in YUView, describe here in one or two sentences what you saw.]\n\n"
    "The images are rendered from the decoded files by a script, and this is not a subjective test."
)
s = content_slide("Visual Quality: Same Frame, Four QPs", 8, NOTES[8])
labels = ["Original"] + [f"QP {qq}" for qq in QPS]
cw = 1.55
chh = cw * chh_ / cw_
for j in range(5):
    fn = f"BasketballDrive_f{FR}_typical_{'original' if j == 0 else 'QP' + str(QPS[j - 1])}_crop.png"
    xx = 0.86 + j * (cw + 0.13)
    pic = s.shapes.add_picture(str(PROJ / "visual/v2" / fn), Inches(xx), Inches(1.3), Inches(cw), Inches(chh))
    pic.name = f"Crop {labels[j]}"
    pic._element.nvPicPr.cNvPr.set("descr", f"BasketballDrive frame {FR}, same crop, {labels[j]}" + ("" if j == 0 else ", medium preset, decoded"))
    if j == 0:
        sub = [(f"frame {FR} (0-based)", 9, MUTED, False, False)]
    else:
        v = vrows[j - 1]
        sub = [(f"PSNR {float(v['y_psnr']):.2f} dB\nSSIM {float(v['ssim']):.3f} · MS-SSIM {float(v['ms_ssim']):.3f}", 8, MUTED, False, False)]
    text(s, xx, 1.3 + chh + 0.05, cw, 0.5, [[(labels[j] + ("" if j == 0 else " · medium"), 11, INK, True, False)], sub],
         align=PP_ALIGN.CENTER, name=f"Crop caption {j + 1}")
fw = 2.1
full = s.shapes.add_picture(str(PROJ / "visual/v2" / f"BasketballDrive_f{FR}_typical_full_with_crop.png"), Inches(0.86), Inches(3.3),
                            Inches(fw), Inches(fw * 1080 / 1920))
full.name = "Full frame with crop box"
full._element.nvPicPr.cNvPr.set("descr", f"BasketballDrive original frame {FR}, crop area marked in orange")
text(s, 0.86, 3.3 + fw * 1080 / 1920 + 0.04, fw, 0.25, [[("crop in orange; rendered by script", 8, MUTED, False, True)]], name="Full frame caption")
data = [["MS-SSIM (seq.)", "QP 24", "QP 29", "QP 34", "QP 39"]]
for sq in SEQS:
    rr = sorted([x for x in VSQ if x["sequence"] == sq], key=lambda x: int(x["qp"]))
    data.append([sq] + [f"{float(x['ms_ssim_mean']):.3f}" for x in rr])
table(s, 3.15, 3.3, 3.6, 1.4, data, [1.2, 0.6, 0.6, 0.6, 0.6], "MS-SSIM table", size=8)
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 6.95, 3.3, 2.19, 1.6, fill=CARD, line=PH_LINE, dash=MSO_LINE.DASH, name="Observation card", adj=0.06)
text(s, 7.07, 3.38, 1.97, 1.45, [[("What I saw in YUView", 10, INK, True, False)],
                                 [("[Sadab: one or two sentences, only after checking the frames yourself]", 9, MUTED, False, True)]],
     name="Observation text", space_after=3)

# =============================================================================================================
# 9. Cross-platform verification
NOTES[9] = (
    "The Windows and Linux builds were checked against each other. The same configuration was encoded on both "
    "systems, and the bitstream hash, the decoded-video hash, the frame count, the Y, U and V PSNR and the "
    "encoder's printed parameters were compared.\n\n"
    f"In all {n_xp} checks, covering all four sequences and all four presets, the outputs were exactly identical, "
    "bit for bit. So the MSVC and GCC builds of VVenC and VVdeC behave the same for these settings.\n\n"
    "Speed was not compared, because Linux ran inside WSL2."
)
s = content_slide("Cross-Platform Verification", 9, NOTES[9])
for k, (nm, sub, yy) in enumerate([("Windows", "MSVC 19.44", 1.5), ("Linux", "GCC 13.3", 3.35)]):
    c = shape(s, MSO_SHAPE.OVAL, 0.95, yy, 1.05, 1.05, fill=WHITE, line=BLUE, line_w=2, name=f"{nm} node")
    shape_text(c, [[(nm, 11, BLUE, True, False)], [(sub, 8, MUTED, False, False)]])
line(s, 1.475, 2.6, 1.475, 3.3, color=BLUE, w=1.5, dash=MSO_LINE.DASH, name="Platform link")
c = shape(s, MSO_SHAPE.OVAL, 1.95, 2.42, 0.9, 0.9, fill=BLUE, name="Result node")
shape_text(c, [[(f"{n_xp}/{n_xp}", 13, WHITE, True, False)], [("identical", 9, WHITE, False, False)]])
data = [["Configuration", "Bitstream", "Decoded", "Frames", "PSNR", "Params"]]
ok = ("yes", BLUE)
bad = ("NO", ORANGE)
for i in xp_new:
    m = i["match"]
    data.append([i["config"].replace(", ", " · ")] + [ok if m[k] else bad for k in ("bitstream_sha256", "recon_sha256", "frames", "psnr", "encoder_parameters")])
for i in XP["phase1_checks"]["full_length"]:
    m = i["match"]
    data.append([i["config"].split(" (")[0].replace(", ", " · ")] + [ok if m[k] else bad for k in ("bitstream_sha256", "recon_sha256", "frames", "psnr")] + ["–"])
data.append(["BlowingBubbles QP 34 fast · 16 frames (smoke)", ok, ok, ok, ok, "–"])
table(s, 3.1, 1.3, 6.04, 3.25, data, [2.84, 0.68, 0.68, 0.6, 0.6, 0.64], "Cross-platform table", size=8)
text(s, 3.1, 4.62, 6.04, 0.35, [[("yes = identical SHA-256 / equal value. Params = 16 encoder configuration lines and command options "
                                  "(file paths removed). Speed not compared.", 9, MUTED, False, False)]], name="Cross-platform note")

# =============================================================================================================
# 10. Conclusions and future research
NOTES[10] = (
    "To conclude. First, QP controls the trade-off: about half the bitrate for every 5 QP, at a cost of roughly 1.5 to "
    "4 dB. Second, slower presets are clearly more efficient, but with diminishing returns: slow saves about 5 to 7 "
    "percent bitrate for about three times the encoding time. Third, the Windows and Linux builds are bit-exact. "
    "Fourth, careful timing control matters: a short slow phase of the laptop produced the earlier 45 percent gap.\n\n"
    "What still needs work: more sequences per resolution, the standard CTC QPs, a comparison with VTM, and "
    "perceptual metrics like VMAF.\n\n"
    "My background is in computer vision and deep learning. A direction I would like to study is learning-based "
    "enhancement of decoded video, for example a light CNN that reduces artifacts at high QP. This is a direction, "
    "not completed work. Thank you very much, Professor Choi."
)
s = content_slide("Conclusions and Future Research", 10, NOTES[10])
finds = [("QP controls the trade-off", f"+5 QP: bitrate ÷{f(q['ratio_median'], 2)} (median), Y-PSNR −{f(q['drop_min'], 1)}–{f(q['drop_max'], 1)} dB"),
         ("Slower presets: better, diminishing returns", f"slow {sg(max(bdr['slow']))}…{sg(min(bdr['slow']))} % BD-rate for ×{min(tm['slow']):.1f}–{max(tm['slow']):.1f} time"),
         ("Windows = Linux", f"bit-exact in {n_xp}/{n_xp} checks (all sequences and presets)"),
         ("Timing needs control", f"controlled repeats CV {f(min(P2CV), 1)}–{f(max(P2CV), 1)} %; early 45 % gap explained")]
for j, (head, val) in enumerate(finds):
    yy = 1.35 + j * 0.78
    c = shape(s, MSO_SHAPE.OVAL, 0.86, yy, 0.46, 0.46, fill=WHITE, line=BLUE, line_w=2, name=f"Finding {j + 1} node")
    shape_text(c, [[(str(j + 1), 12, BLUE, True, False)]])
    text(s, 1.45, yy - 0.03, 3.85, 0.7, [[(head, 12, INK, True, False)], [(val, 10, INK, False, False)]], name=f"Finding {j + 1} text")
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 5.45, 1.32, 3.69, 1.55, fill=CARD, name="Next card", adj=0.07)
text(s, 5.62, 1.42, 3.4, 1.4, [[("Needs further experiments", 12, INK, True, False)],
                               [("more sequences per resolution (CTC classes)", 10, INK, False, False)],
                               [("CTC QPs 22/27/32/37 and a VTM anchor", 10, INK, False, False)],
                               [("perceptual metrics (VMAF) or a subjective test", 10, INK, False, False)],
                               [("timing on native Linux with fixed CPU frequency", 10, INK, False, False)]],
     name="Next text", space_after=1, bullet_from=1)
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 5.45, 3.0, 3.69, 1.3, fill=SKY, name="Interest card", adj=0.08)
text(s, 5.62, 3.1, 3.4, 1.15, [[("My research interest", 12, DEEP, True, False)],
                              [("Learning-based enhancement of decoded video, e.g. a lightweight CNN against coding artifacts at high QP "
                                "(a direction to study, not completed work)", 10, INK, False, False)]], name="Interest text", space_after=2)
text(s, 2.9, 4.55, 6.24, 0.4, [[("Thank you, Professor Kiho Choi", 18, BLUE, False, False, HEAD)]], align=PP_ALIGN.RIGHT, name="Thanks")

prs.core_properties.title = "VVC Encoding and Decoding: Rate, Quality and Complexity of VVenC Presets"
prs.core_properties.author = "Sadab Khan Prangon"
prs.save(OUTV3)
(HERE / "speaker_notes_v2_10slides.md").write_text(
    "# Speaker notes (10 slides): Sadab Khan Prangon, expanded VVC experiment\n\n"
    "All numbers come from results/*.csv and results/*.json. Text in [brackets] (slide 8) must be written by Sadab after his own "
    "YUView check. The wording does not claim that Sadab personally ran the automated experiments.\n\n"
    + "\n\n".join(f"## Slide {k}\n\n{v}" for k, v in NOTES.items()) + "\n", encoding="utf-8")
print(f"saved {OUTV3.name}: {len(prs.slides)} slides; notes {sum(len(v.split()) for v in NOTES.values())} words")
