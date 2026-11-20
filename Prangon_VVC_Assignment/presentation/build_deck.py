"""Build Sadab Khan Prangon's VVC assignment deck on his own Prangon.pptx (Cordelia) template.

Stage 1 (now): structure, diagrams and speaker notes; every experimental number is a clearly marked placeholder.
Stage 2 (after Sadab's results arrive): placeholders are replaced by native charts built from results_raw.csv.

Run:  python build_deck.py
"""
import copy
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "template" / "Prangon_template_source.pptx"
OUT = HERE / "VVC_Assignment_Sadab_Khan_Prangon.pptx"

# ---- Sadab's measured data (stage 2) -----------------------------------------------------------
import csv  # noqa: E402
import json  # noqa: E402

from pptx.chart.data import CategoryChartData, XyChartData  # noqa: E402
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE  # noqa: E402

PROJ = HERE.parent
SUM = json.loads((PROJ / "results/summary.json").read_text(encoding="utf-8"))
XP = json.loads((PROJ / "results/crossplatform.json").read_text(encoding="utf-8"))
FRAME = json.loads((PROJ / "visual/BQMall_frame_selection.json").read_text(encoding="utf-8"))
RAW = [r for r in csv.DictReader(open(PROJ / "results/results_raw.csv", encoding="utf-8-sig"))]
MAIN = [r for r in RAW if not r["repeat_of"] and r["status"] == "OK"]


def run(seq, preset, qp):
    return next(r for r in MAIN if r["sequence"] == seq and r["preset"] == preset and int(r["qp"]) == qp)


Q, P = SUM["qp_steps"], SUM["preset"]
V = SUM["validation"]
REP = {x["run"]: x for x in V["repeats"]}
XP_ALL = all(all(i["match"].values()) for i in XP["full_length"]) and XP["smoke_16_frames"]["bitstream"] == "IDENTICAL"

# ---- palette: the template's own blues and slates, plus one warm accent for the "fast" preset ----
BLUE = RGBColor(0x00, 0x91, 0xEA)    # template accent1: titles, process nodes
DEEP = RGBColor(0x00, 0x53, 0xA3)    # template accent2: emphasis, "medium" preset
ORANGE = RGBColor(0xE8, 0x71, 0x0A)  # warm accent: "fast" preset (blue/orange stays distinct under colour-blindness)
INK = RGBColor(0x26, 0x32, 0x38)     # template dk1: body text
MUTED = RGBColor(0x60, 0x7D, 0x8B)   # template dk2: secondary text
LINE = RGBColor(0xCF, 0xD8, 0xDC)    # template accent4: hairlines
CARD = RGBColor(0xF3, 0xF6, 0xF8)    # light card fill
SKY = RGBColor(0xE3, 0xF2, 0xFD)     # light blue fill
PH_LINE = RGBColor(0x90, 0xA4, 0xAE)  # placeholder dashed border
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HEAD, BODY = "Roboto Slab", "Source Sans Pro"   # the template's fonts

# ------------------------------------------------------------------------------------------------
prs = Presentation(TEMPLATE)
sld_ids = prs.slides._sldIdLst
for sid in list(sld_ids):                       # remove the 7 academic-introduction slides
    prs.part.drop_rel(sid.get(qn("r:id")))
    sld_ids.remove(sid)
L_TITLE = prs.slide_layouts.get_by_name("TITLE")
L_CONTENT = prs.slide_layouts.get_by_name("TITLE_AND_BODY")


def font(run, size, color=INK, bold=False, italic=False, face=BODY):
    f = run.font
    f.size, f.bold, f.italic, f.name = Pt(size), bold, italic, face
    f.color.rgb = color
    rpr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs", "a:sym"):
        el = rpr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rpr, qn(tag))
        el.set("typeface", face)


def add_runs(p, t, size, color, bold, italic, face):
    """Add text to a paragraph; a newline becomes a real line break (<a:br/>), not a literal character."""
    for k, seg in enumerate(t.split("\n")):
        if k:
            p.add_line_break()
        run = p.add_run()
        run.text = seg
        font(run, size, color, bold, italic, face)


def text(slide, x, y, w, h, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name=None, space_after=0,
         bullet_from=None):
    """paras: list of paragraphs; each paragraph is a list of (text, size, color, bold, italic[, face]) runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, runs in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        if bullet_from is not None and i >= bullet_from:
            bullet(p)
        for r in runs:
            t, size, color, bold, italic = r[:5]
            add_runs(p, t, size, color, bold, italic, r[5] if len(r) > 5 else BODY)
    return tb


def bullet(p):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", "228600")
    pPr.set("indent", "-228600")
    for tag, attrs in (("a:buClr", None), ("a:buSzPct", {"val": "100000"}), ("a:buFont", {"typeface": "Arial"}),
                       ("a:buChar", {"char": "◎"})):
        el = etree.SubElement(pPr, qn(tag))
        if tag == "a:buClr":
            etree.SubElement(el, qn("a:srgbClr")).set("val", str(BLUE))
        else:
            for k, v in attrs.items():
                el.set(k, v)


def shape(slide, kind, x, y, w, h, fill=None, line=None, line_w=1.0, dash=None, name=None, adj=None):
    s = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        s.name = name
    if adj is not None:
        s.adjustments[0] = adj
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(line_w)
        if dash:
            s.line.dash_style = dash
    s.shadow.inherit = False
    s.text_frame.margin_left = s.text_frame.margin_right = 0
    s.text_frame.margin_top = s.text_frame.margin_bottom = 0
    return s


def shape_text(s, paras, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE):
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, runs in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        for r in runs:
            t, size, color, bold, italic = r[:5]
            add_runs(p, t, size, color, bold, italic, r[5] if len(r) > 5 else BODY)


def line(slide, x1, y1, x2, y2, color=LINE, w=1.25, dash=None, arrow=False, name=None):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    if name:
        c.name = name
    c.line.color.rgb = color
    c.line.width = Pt(w)
    if dash:
        c.line.dash_style = dash
    if arrow:
        ln = c.line._get_or_add_ln()
        tail = etree.SubElement(ln, qn("a:tailEnd"))
        tail.set("type", "triangle")
        tail.set("w", "med")
        tail.set("len", "med")
    return c


def placeholder(slide, x, y, w, h, heading, lines, name):
    """A clearly marked empty slot for evidence Sadab has not produced yet."""
    box = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=CARD, line=PH_LINE, line_w=1.0,
                dash=MSO_LINE.DASH, name=name, adj=0.06)
    paras = [[("AWAITING SADAB'S RESULTS", 10, MUTED, True, False)], [(heading, 13, INK, True, False)]]
    paras += [[(t, 11, MUTED, False, False)] for t in lines]
    tb = text(slide, x + 0.2, y + 0.18, w - 0.4, h - 0.36, paras, name=name + " text", space_after=3)
    return box, tb


def style_chart(ch, size=10):
    ch.font.name = BODY
    ch.font.size = Pt(size)
    ch.font.color.rgb = MUTED


def axis_style(ax, title=None, grid=True, fmt=None):
    ax.has_major_gridlines = grid
    if grid:
        ax.major_gridlines.format.line.color.rgb = RGBColor(0xE6, 0xEB, 0xEE)
        ax.major_gridlines.format.line.width = Pt(0.75)
    ax.format.line.color.rgb = PH_LINE
    ax.tick_labels.font.size = Pt(10)
    ax.tick_labels.font.color.rgb = MUTED
    if fmt:
        ax.tick_labels.number_format = fmt
        ax.tick_labels.number_format_is_linked = False
    if title:
        ax.has_title = True
        ax.axis_title.text_frame.text = title
        r = ax.axis_title.text_frame.paragraphs[0].runs[0]
        r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(10), False, MUTED, BODY


def log_axis(ax, lo, hi):
    scaling = ax._element.find(qn("c:scaling"))
    lb = etree.SubElement(scaling, qn("c:logBase"))
    lb.set("val", "10")
    scaling.remove(lb)
    scaling.insert(0, lb)
    ax.minimum_scale, ax.maximum_scale = lo, hi


def rd_chart(slide, seq, x, y, w, h):
    cd = XyChartData()
    for p in ("fast", "medium"):
        s = cd.add_series(p)
        for q in (24, 29, 34, 39):
            r = run(seq, p, q)
            s.add_data_point(float(r["bitrate_kbps"]), float(r["enc_y_psnr"]))
    gf = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    gf.name = f"RD chart {seq}"
    ch = gf.chart
    style_chart(ch)
    ch.has_title = True
    ch.chart_title.text_frame.text = seq
    tr = ch.chart_title.text_frame.paragraphs[0].runs[0]
    tr.font.size, tr.font.bold, tr.font.color.rgb, tr.font.name = Pt(12), True, INK, BODY
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.BOTTOM
    ch.legend.include_in_layout = False
    ch.legend.font.size = Pt(10)
    for s, col in zip(ch.plots[0].series, (ORANGE, DEEP)):
        s.smooth = False
        s.format.line.color.rgb = col
        s.format.line.width = Pt(2)
        s.marker.style = XL_MARKER_STYLE.CIRCLE
        s.marker.size = 7
        s.marker.format.fill.solid()
        s.marker.format.fill.fore_color.rgb = col
        s.marker.format.line.color.rgb = WHITE
    med = ch.plots[0].series[1]                          # label the QP of each medium point
    for i, q in enumerate((24, 29, 34, 39)):
        dl = med.points[i].data_label
        dl.has_text_frame = True
        dl.text_frame.text = f"QP{q}"
        dl.position = XL_LABEL_POSITION.LEFT
        dl.font.size = Pt(9)
        dl.font.color.rgb = MUTED
    axis_style(ch.category_axis, "bitrate (kbps, log scale)", fmt="#,##0")
    log_axis(ch.category_axis, 50, 5000)
    axis_style(ch.value_axis, "Y-PSNR (dB)", fmt="0")
    ch.value_axis.minimum_scale, ch.value_axis.maximum_scale, ch.value_axis.major_unit = 26, 40, 2
    return gf


def time_chart(slide, x, y, w, h):
    cats, fast, med = [], [], []
    for seq, short in (("BlowingBubbles", "BlowingBubbles"), ("BQMall", "BQMall")):
        for q in (24, 29, 34, 39):
            cats.append(f"{short}  QP {q}")
            fast.append(float(run(seq, "fast", q)["encode_time_s"]))
            med.append(float(run(seq, "medium", q)["encode_time_s"]))
    cats, fast, med = cats[::-1], fast[::-1], med[::-1]          # bar charts draw bottom-up
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("medium", med)
    cd.add_series("fast", fast)
    gf = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    gf.name = "Encoding time chart"
    ch = gf.chart
    style_chart(ch, 9)
    ch.has_title = True
    ch.chart_title.text_frame.text = "Encoding time per configuration (s)"
    tr = ch.chart_title.text_frame.paragraphs[0].runs[0]
    tr.font.size, tr.font.bold, tr.font.color.rgb, tr.font.name = Pt(12), True, INK, BODY
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.TOP
    ch.legend.include_in_layout = False
    ch.legend.font.size = Pt(10)
    plot = ch.plots[0]
    plot.gap_width, plot.overlap = 45, -5
    for s, col in zip(plot.series, (DEEP, ORANGE)):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = col
        s.invert_if_negative = False
    plot.has_data_labels = True
    dls = plot.data_labels
    dls.number_format, dls.number_format_is_linked = "0", False
    dls.position = XL_LABEL_POSITION.OUTSIDE_END
    dls.font.size, dls.font.color.rgb = Pt(8), MUTED
    axis_style(ch.value_axis, None, fmt="0")
    ch.value_axis.minimum_scale = 0
    axis_style(ch.category_axis, None, grid=False)
    ch.category_axis.tick_labels.font.size = Pt(9)
    return gf


def f2(x, n=2):
    return f"{x:.{n}f}"


def sgn(x, n=1):
    """Signed number with a real minus sign."""
    return ("+" if x >= 0 else "\u2212") + f"{abs(x):.{n}f}"


def blank(t):
    """Placeholder value text inside real content."""
    return (t, 12, MUTED, False, True)


def content_slide(title, number, notes):
    s = prs.slides.add_slide(L_CONTENT)
    for ph in list(s.placeholders):
        if ph.placeholder_format.type != 1:          # keep only the title placeholder
            ph._element.getparent().remove(ph._element)
    t = s.shapes.title
    t.text_frame.text = title
    for p in t.text_frame.paragraphs:
        for r in p.runs:
            font(r, 26, BLUE, face=HEAD)
    text(s, 9.19, 5.19, 0.6, 0.3, [[(str(number), 13, BLUE, True, False)]], align=PP_ALIGN.RIGHT,
         name="Slide number")
    s.notes_slide.notes_text_frame.text = notes
    return s


NOTES = {}

# ================================================================================================
# 1. Title and assignment objectives
NOTES[1] = (
    "Good morning, Professor Choi. My name is Sadab Khan Prangon. I am a B.Sc. student in Computer Science and "
    "Engineering at IUBAT in Bangladesh, and I expect to graduate in April 2027.\n\n"
    "In this short talk I will present the VVC assignment you gave me. I had four goals. First, build the VVenC "
    "encoder and the VVdeC decoder on Windows and on Linux. Second, encode raw YUV videos. Third, decode them "
    "again. And fourth, measure time, file size, bitrate and PSNR, and look at the decoded video in YUView.\n\n"
    "I will first explain the workflow and my setup, then show my results, and finish with what I learned."
)
s = prs.slides.add_slide(L_TITLE)
for ph in list(s.placeholders):
    if ph.placeholder_format.type not in (3,):       # keep the centre-title placeholder only
        ph._element.getparent().remove(ph._element)
t = s.shapes.title
t.left, t.top, t.width, t.height = Inches(0.95), Inches(0.95), Inches(8.2), Inches(1.25)
t.text_frame.text = ""
t.text_frame.vertical_anchor = MSO_ANCHOR.TOP
p = t.text_frame.paragraphs[0]
r = p.add_run(); r.text = "VVC Encoding and Decoding:"; font(r, 30, BLUE, True, face=HEAD)
p = t.text_frame.add_paragraph()
r = p.add_run(); r.text = "Implementation and Performance Analysis"; font(r, 22, INK, face=HEAD)
text(s, 0.95, 0.62, 8.0, 0.3, [[("ASSIGNMENT  ·  VIDEO CODING AND PROCESSING LAB, KYUNG HEE UNIVERSITY", 11, MUTED, True, False)]],
     name="Kicker")
text(s, 0.95, 2.3, 8.0, 1.1, [
    [("Sadab Khan Prangon", 18, INK, True, False)],
    [("B.Sc. in Computer Science and Engineering, International University of Business Agriculture and "
      "Technology (IUBAT), Bangladesh", 12, MUTED, False, False)],
    [("Assignment given by Prof. Kiho Choi, Video Coding and Processing Lab, Kyung Hee University", 12, MUTED, False, False)],
], name="Presenter", space_after=2)
# objectives as a chain of nodes (echoes the template's network graphic)
objs = [("1", "Build", "VVenC + VVdeC on\nWindows and Linux"), ("2", "Encode", "raw YUV → .266\nwith VVenC"),
        ("3", "Decode", ".266 → YUV\nwith VVdeC"), ("4", "Measure", "time, size, PSNR\nand YUView check")]
x0, gap, yc, d = 1.25, 1.85, 3.85, 0.5
line(s, x0, yc, x0 + gap * 3, yc, color=LINE, w=1.5, name="Objective chain")
for i, (n, head, sub) in enumerate(objs):
    cx = x0 + gap * i
    c = shape(s, MSO_SHAPE.OVAL, cx - d / 2, yc - d / 2, d, d, fill=WHITE, line=BLUE, line_w=2, name=f"Objective {n} node")
    shape_text(c, [[(n, 14, BLUE, True, False)]])
    text(s, cx - 0.8, yc + 0.35, 1.6, 0.85, [[(head, 13, INK, True, False)], [(sub, 11, MUTED, False, False)]],
         align=PP_ALIGN.CENTER, name=f"Objective {n} label")
s.notes_slide.notes_text_frame.text = NOTES[1]

# ================================================================================================
# 2. Workflow
NOTES[2] = (
    "This slide shows the complete pipeline I used.\n\n"
    "On the left is the original video. It is a raw YUV file, 10-bit, 4:2:0. A raw file has no header, so I "
    "must give the size, frame rate and format myself on the command line.\n\n"
    "VVenC compresses it into a .266 bitstream. Here I measure the encoding time and the file size, and from "
    "the size I calculate the bitrate. Then VVdeC decodes the bitstream back into a YUV video, and I measure "
    "the decoding time.\n\n"
    "Finally, I compare the decoded video with the original, frame by frame. This gives the PSNR, and I also "
    "look at the frames in YUView. I used the same pipeline on Windows and on Linux."
)
s = content_slide("VVC Encoding and Decoding Workflow", 2, NOTES[2])
xs = [1.45, 3.2, 4.95, 6.7, 8.45]
yc, d = 2.3, 1.0
nodes = [("YUV", False, "Original video", "raw frames, 10-bit\n4:2:0, no header"),
         ("VVenC", True, "Encoder", "vvencapp\nQP + preset"),
         (".266", False, "Bitstream", "compressed\nH.266/VVC file"),
         ("VVdeC", True, "Decoder", "vvdecapp\nmulti-threaded"),
         ("YUV", False, "Reconstruction", "decoded frames,\nsame format")]
chips = ["reference for\nquality", "encoding time (s)", "size (bytes) →\nbitrate (kbps)", "decoding time (s)",
         "PSNR Y / U / V (dB)"]
# comparison bracket above the chain
yb = 1.5
line(s, xs[0], yb, xs[-1], yb, color=MUTED, w=1.25, dash=MSO_LINE.DASH, name="Compare bracket")
line(s, xs[0], yb, xs[0], yc - d / 2 - 0.04, color=MUTED, w=1.25, dash=MSO_LINE.DASH, name="Compare bracket left")
line(s, xs[-1], yb, xs[-1], yc - d / 2 - 0.04, color=MUTED, w=1.25, dash=MSO_LINE.DASH, arrow=True,
     name="Compare bracket right")
lab = shape(s, MSO_SHAPE.RECTANGLE, 3.05, yb - 0.15, 3.8, 0.3, fill=WHITE, name="Compare label")
shape_text(lab, [[("compare frame by frame  →  PSNR and YUView", 11, MUTED, False, True)]])
for i, (inner, proc, head, sub) in enumerate(nodes):
    cx = xs[i]
    if i < len(nodes) - 1:
        line(s, cx + d / 2 + 0.06, yc, xs[i + 1] - d / 2 - 0.08, yc, color=BLUE, w=1.75, arrow=True, name=f"Flow {i + 1}")
    c = shape(s, MSO_SHAPE.OVAL, cx - d / 2, yc - d / 2, d, d, fill=BLUE if proc else WHITE, line=BLUE, line_w=2,
              name=f"Node {head}")
    shape_text(c, [[(inner, 13, WHITE if proc else BLUE, True, False)]])
    text(s, cx - 0.82, yc + 0.6, 1.64, 0.75, [[(head, 13, INK, True, False)], [(sub, 11, MUTED, False, False)]],
         align=PP_ALIGN.CENTER, name=f"Label {head}")
    ch = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, cx - 0.78, 3.82, 1.56, 0.5, fill=SKY if i else WHITE,
               line=None if i else LINE, name=f"Measure {head}", adj=0.3)
    shape_text(ch, [[(chips[i], 11, DEEP if i else MUTED, i > 0, False)]])
text(s, 2.9, 4.6, 6.24, 0.3, [[("●", 11, BLUE, False, False), (" process    ", 11, MUTED, False, False),
                              ("○", 11, BLUE, False, False), (" data    ", 11, MUTED, False, False),
                              ("blue boxes = measured  ·  same pipeline on Windows and Linux", 11, MUTED, False, False)]],
     align=PP_ALIGN.RIGHT, name="Legend")

# ================================================================================================
# 3. Environment and build verification
NOTES[3] = (
    "Next, the environment. I built VVenC 1.14.0 and VVdeC 3.2.1 from source: on Windows 11 with MSVC 19.44, "
    "and on Ubuntu 24.04 in WSL2 with GCC 13.3.\n\n"
    "On Linux all 39 VVenC tests and the VVdeC unit test passed. On Windows 32 of 39 passed; the other 7 did not "
    "run, because Smart App Control blocked two unsigned test programs. I did not change any security setting.\n\n"
    "Then I encoded the same video with the same settings on both systems. In all three checks, the bitstreams "
    "and the decoded videos had exactly the same SHA-256 hash. I do not compare speed, because Linux ran in WSL2."
)
s = content_slide("Environment and Build Verification", 3, NOTES[3])
rows = ["Compiler", "CMake", "VVenC", "VVdeC", "Unit tests", "Encode runs"]
win_vals = ["MSVC 19.44 (VS 2022)", "4.4.4", "1.14.0 · 9428ea8", "3.2.1 · cb1a3ef", "VVenC 32/39 *",
            "smoke test + 18 runs"]
lin_vals = ["GCC 13.3.0", "3.28.3", "1.14.0 · 9428ea8", "3.2.1 · cb1a3ef", "VVenC 39/39, VVdeC OK",
            "smoke test + 2 full runs"]
for k, (xx, osname, sub, vals) in enumerate([(0.86, "Windows", "Windows 11 Home, build 26200", win_vals),
                                              (5.64, "Linux", "Ubuntu 24.04.5 in WSL2", lin_vals)]):
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, xx, 1.35, 3.5, 3.0, fill=CARD, name=f"{osname} card", adj=0.05)
    text(s, xx + 0.25, 1.5, 2.3, 0.55, [[(osname, 16, INK, True, False, HEAD)], [(sub, 11, MUTED, False, False)]],
         name=f"{osname} heading")
    tag = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, xx + 2.4, 1.55, 0.9, 0.28, fill=WHITE, line=BLUE, line_w=1,
                name=f"{osname} status", adj=0.5)
    shape_text(tag, [[("BUILT", 10, BLUE, True, False)]])
    for j, (rname, val) in enumerate(zip(rows, vals)):
        yy = 2.15 + j * 0.31
        text(s, xx + 0.25, yy, 1.1, 0.28, [[(rname, 12, INK, True, False)]], name=f"{osname} {rname} label")
        text(s, xx + 1.4, yy, 2.05, 0.28, [[(val, 12, INK, False, False)]], name=f"{osname} {rname} value")
text(s, 1.11, 3.98, 3.15, 0.36, [[("* 7 not run: Smart App Control blocked 2 unsigned test programs", 10, MUTED, False, True)]],
     name="Windows footnote")
text(s, 5.89, 3.98, 3.15, 0.36, [[("VVdeC conformance tests not run on either system (test bitstreams not included)",
                                  10, MUTED, False, True)]], name="Conformance footnote")
# cross-platform check node between the cards
line(s, 4.36, 2.75, 5.64, 2.75, color=BLUE, w=1.5, dash=MSO_LINE.DASH, name="Cross-platform link")
c = shape(s, MSO_SHAPE.OVAL, 4.5, 2.25, 1.0, 1.0, fill=BLUE if XP_ALL else WHITE, line=BLUE, line_w=2, name="SHA node")
shape_text(c, [[("SHA-256", 11, WHITE if XP_ALL else BLUE, True, False)],
               [("identical" if XP_ALL else "differs", 11, WHITE if XP_ALL else BLUE, False, False)]])
text(s, 4.36, 3.35, 1.28, 0.6, [[("bitstream + decoded", 10, MUTED, False, False)], [("video, 3 of 3 checks", 10, MUTED, False, False)]],
     align=PP_ALIGN.CENTER, name="SHA result")
text(s, 0.86, 4.5, 0.8, 0.3, [[("Tools", 12, INK, True, False)]], name="Tools label")
for j, tname in enumerate(["Git 2.55", "Python 3.12 + numpy 2.5", "YUView 2.14", "VS 2022 Build Tools"]):
    ch = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 1.6 + j * 1.9, 4.47, 1.75, 0.36, fill=SKY, name=f"Tool {j + 1}", adj=0.5)
    shape_text(ch, [[(tname, 11, DEEP, False, False)]])

# ================================================================================================
# 4. Experimental setup
NOTES[4] = (
    "This is my experiment design. It is small, but it is controlled.\n\n"
    "I used two standard test sequences from the provided files: BlowingBubbles at 416 by 240, and BQMall at "
    "832 by 480. Both are 10-bit, 4:2:0 and 10 seconds long.\n\n"
    "For each sequence I used four QP values, 24, 29, 34 and 39, and two presets, fast and medium. Two times "
    "four times two gives sixteen encodings.\n\n"
    "I kept everything else fixed. I turned QP adaptation off, so QP is the only quality control, used eight "
    "threads, and ran all runs on the same laptop on AC power, in a shuffled order. I decoded every bitstream "
    "three times and kept the median time. I also repeated two encodings to see how much the timing changes."
)
s = content_slide("Experimental Setup and Methodology", 4, NOTES[4])
text(s, 0.86, 1.3, 2.6, 0.3, [[("2 sequences", 12, MUTED, True, False)]], name="Seq caption")
for j, (nm, spec) in enumerate([("BlowingBubbles", "416×240 · 50 fps · 500 frames"),
                                ("BQMall", "832×480 · 60 fps · 600 frames")]):
    card = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.86, 1.65 + j * 0.85, 2.55, 0.72, fill=CARD, name=f"Seq {nm}", adj=0.12)
    shape_text(card, [[(nm, 13, INK, True, False)], [(spec, 11, MUTED, False, False)]], align=PP_ALIGN.LEFT)
    card.text_frame.margin_left = Inches(0.18)
for xx, op in [(3.5, "×"), (5.45, "×"), (7.12, "=")]:
    text(s, xx, 2.05, 0.4, 0.5, [[(op, 26, MUTED, False, False)]], align=PP_ALIGN.CENTER, name=f"Operator {op}")
text(s, 3.95, 1.3, 1.5, 0.3, [[("4 QP values", 12, MUTED, True, False)]], name="QP caption")
for j, qp in enumerate([24, 29, 34, 39]):
    cx, cy = 4.32 + (j % 2) * 0.75, 1.98 + (j // 2) * 0.75
    c = shape(s, MSO_SHAPE.OVAL, cx - 0.3, cy - 0.3, 0.6, 0.6, fill=WHITE, line=BLUE, line_w=2, name=f"QP {qp}")
    shape_text(c, [[(str(qp), 13, BLUE, True, False)]])
text(s, 5.95, 1.3, 1.2, 0.3, [[("2 presets", 12, MUTED, True, False)]], name="Preset caption")
for j, (pn, col) in enumerate([("fast", ORANGE), ("medium", DEEP)]):
    pill = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 5.95, 1.75 + j * 0.62, 1.1, 0.45, fill=col, name=f"Preset {pn}", adj=0.5)
    shape_text(pill, [[(pn, 13, WHITE, True, False)]])
c = shape(s, MSO_SHAPE.OVAL, 7.65, 1.7, 1.3, 1.3, fill=BLUE, name="Total node")
shape_text(c, [[("16", 28, WHITE, True, False, HEAD)], [("encodings", 11, WHITE, False, False)]])
for xx, head, items, nm in [
    (0.86, "Kept fixed", ["10-bit 4:2:0 input, full sequences", "QPA off → constant QP", "8 threads, default GOP and intra refresh",
                          "same laptop, AC power, shuffled run order"], "Fixed"),
    (5.14, "Measured for every run", ["encoding time · decoding time (median of 3)", "bitstream size → bitrate",
                                     "PSNR: encoder report + my own check", "+ 2 repeated encodings for timing noise"], "Measured")]:
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, xx, 3.4, 4.0, 1.5, fill=CARD, name=f"{nm} card", adj=0.06)
    paras = [[(head, 13, INK, True, False)]] + [[(it, 12, INK, False, False)] for it in items]
    text(s, xx + 0.22, 3.52, 3.62, 1.3, paras, name=f"{nm} text", space_after=2, bullet_from=1)

# ================================================================================================
# 5. QP and compression quality
bb, bq = Q["BlowingBubbles_medium_24_to_39"], Q["BQMall_medium_24_to_39"]
NOTES[5] = (
    "Now the first result: what QP does to compression and quality. Each line is one preset, the points are "
    "QP 24 to 39, and the bitrate axis is logarithmic.\n\n"
    f"In my 16 runs, every increase of 5 in QP divided the bitrate by {f2(Q['bitrate_ratio_min'])} to "
    f"{f2(Q['bitrate_ratio_max'])}, about {f2(Q['bitrate_ratio_median'], 1)} times, and the Y-PSNR went down by "
    f"{f2(Q['ypsnr_drop_min'], 1)} to {f2(Q['ypsnr_drop_max'], 1)} dB. From QP 24 to QP 39 with the medium preset, "
    f"the bitrate became {f2(bb['bitrate_ratio'], 1)} times smaller for BlowingBubbles and "
    f"{f2(bq['bitrate_ratio'], 1)} times smaller for BQMall, and the quality dropped by about 8 dB.\n\n"
    "My own PSNR script matched the encoder's PSNR exactly in all 18 runs."
)
s = content_slide("QP and Compression Quality", 5, NOTES[5])
rd_chart(s, "BlowingBubbles", 0.75, 1.3, 2.95, 3.65)
rd_chart(s, "BQMall", 3.7, 1.3, 2.95, 3.65)
for j, (lbl, val, sub) in enumerate([
        ("Bitrate per +5 QP", f"÷ {f2(Q['bitrate_ratio_min'])}–{f2(Q['bitrate_ratio_max'])}",
         f"median ÷ {f2(Q['bitrate_ratio_median'])}, {Q['n_pairs']} QP steps"),
        ("Y-PSNR per +5 QP", f"− {f2(Q['ypsnr_drop_min'], 1)}–{f2(Q['ypsnr_drop_max'], 1)} dB",
         f"median − {f2(Q['ypsnr_drop_median'])} dB"),
        ("My PSNR check vs encoder", f"Δ {V['max_psnr_diff_db']:.4f} dB", "all 18 runs, peak 1020")]):
    yy = 1.35 + j * 1.22
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 6.75, yy, 2.39, 1.07, fill=CARD, name=f"Stat {j + 1}", adj=0.08)
    text(s, 6.93, yy + 0.12, 2.1, 0.9, [[(lbl, 11, MUTED, True, False)], [(val, 18, INK, True, False, HEAD)],
                                        [(sub, 10, MUTED, False, False)]], name=f"Stat {j + 1} text", space_after=2)

# ================================================================================================
# 6. Encoding and decoding performance
dec_all = [float(r["decode_time_s_median"]) for r in MAIN]
dec_bb = [float(r["decode_time_s_median"]) for r in MAIN if r["sequence"] == "BlowingBubbles"]
dec_bq = [float(r["decode_time_s_median"]) for r in MAIN if r["sequence"] == "BQMall"]
r17, r18 = REP["R17"], REP["R18"]
NOTES[6] = (
    "The second result is about time. Blue is medium, orange is fast.\n\n"
    f"At the same QP, medium took {f2(P['time_ratio_min'], 1)} to {f2(P['time_ratio_max'], 1)} times longer and "
    f"gave {f2(P['ypsnr_gain_min'])} to {f2(P['ypsnr_gain_max'])} dB higher Y-PSNR. But the file size changed by "
    f"{sgn(P['size_change_pct_min'])} to {sgn(P['size_change_pct_max'])} percent, so to say how much more "
    "efficient medium is, I would need BD-rate.\n\n"
    f"Decoding took only {f2(min(dec_all), 1)} to {f2(max(dec_all), 1)} seconds, including writing the file. "
    f"Encoding was {P['enc_dec_ratio_min']:.0f} to {P['enc_dec_ratio_max']:.0f} times slower.\n\n"
    f"One warning: of my two repeated encodings, one changed by {f2(r18['diff_pct'], 1)} percent, the other by "
    f"{r17['diff_pct']:.0f} percent. So I only trust large time differences. This is one laptop, not a benchmark."
)
s = content_slide("Encoding and Decoding Performance", 6, NOTES[6])
time_chart(s, 0.75, 1.25, 5.25, 3.75)
tiles = [("encode time,\nmedium ÷ fast", f"×{f2(P['time_ratio_min'], 1)}–{f2(P['time_ratio_max'], 1)}"),
         ("Y-PSNR gain (dB),\nmedium vs fast", f"+{f2(P['ypsnr_gain_min'])}–{f2(P['ypsnr_gain_max'])}"),
         ("size change (%),\nmedium vs fast", f"{sgn(P['size_change_pct_min'])}…{sgn(P['size_change_pct_max'])}"),
         ("decode time (s),\nmedian of 3", f"{f2(min(dec_all), 1)}–{f2(max(dec_all), 1)}")]
for j, (lbl, val) in enumerate(tiles):
    xx, yy = 6.2 + (j % 2) * 1.5, 1.35 + (j // 2) * 1.42
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, xx, yy, 1.42, 1.3, fill=CARD, name=f"Tile {j + 1}", adj=0.08)
    text(s, xx + 0.13, yy + 0.15, 1.2, 1.05, [[(lbl, 10, MUTED, True, False)], [(val, 14, INK, True, False, HEAD)]],
         name=f"Tile {j + 1} text", space_after=6)
text(s, 6.2, 4.2, 2.94, 0.75, [
    [("Timing noise: ", 10, INK, True, False),
     (f"repeat R18 differed by {f2(r18['diff_pct'], 1)} %, R17 by {r17['diff_pct']:.0f} % "
      "(identical bitstreams). Decode time includes writing the YUV file.", 10, MUTED, False, False)]],
     name="Noise note")

# ================================================================================================
# 7. Visual quality
FR = FRAME["frame_index_0based"]
cx_, cy_, cw_, chh_ = FRAME["crop_xywh"]
tps = [t["frame_y_psnr_db"] for t in FRAME["tiles"][1:]]
NOTES[7] = (
    "Numbers are not enough, so I also compared the pictures.\n\n"
    f"This is frame {FR} of BQMall, with the same crop for the original and for QP 24, 29, 34 and 39, medium "
    "preset. I chose the frame and the crop with a fixed rule before looking. The hand is moving, so the "
    "original is already a little blurred.\n\n"
    f"The frame PSNR goes down from {tps[0]:.2f} dB at QP 24 to {tps[-1]:.2f} dB at QP 39.\n\n"
    "[Sadab: after you check these frames in YUView, say here in one or two sentences what you saw, for example "
    "where texture or edges are lost.]\n\n"
    "These images were rendered from the decoded files by a script; this is not a formal subjective test."
)
s = content_slide("Visual Quality: Same Frame, Four QPs", 7, NOTES[7])
labels = ["Original"] + [f"QP {q}" for q in (24, 29, 34, 39)]
cw = 1.5
chh = cw * chh_ / cw_
for j, t in enumerate(FRAME["tiles"]):
    xx = 0.86 + j * (cw + 0.195)
    pic = s.shapes.add_picture(str(PROJ / "visual" / t["file"]), Inches(xx), Inches(1.35), Inches(cw), Inches(chh))
    pic.name = f"Crop {labels[j]}"
    pic._element.nvPicPr.cNvPr.set("descr", f"BQMall frame {FR}, same crop, {labels[j]}" + ("" if j == 0 else ", medium preset, decoded"))
    sub = f"frame {FR}" if j == 0 else f"Y-PSNR {t['frame_y_psnr_db']:.2f} dB"
    text(s, xx, 1.35 + chh + 0.08, cw, 0.5, [[(labels[j] + ("" if j == 0 else " · medium"), 12, INK, True, False)],
                                             [(sub, 10, MUTED, False, False)]], align=PP_ALIGN.CENTER,
         name=f"Crop caption {j + 1}")
fw = 2.3
full = s.shapes.add_picture(str(PROJ / "visual" / f"BQMall_f{FR}_original_full_with_crop.png"), Inches(0.86),
                            Inches(2.95), Inches(fw), Inches(fw * 480 / 832))
full.name = "Full frame with crop box"
full._element.nvPicPr.cNvPr.set("descr", f"BQMall original frame {FR} with the crop area marked in orange")
text(s, 0.86, 2.95 + fw * 480 / 832 + 0.05, fw, 0.3, [[(f"BQMall frame {FR}, crop in orange", 10, MUTED, False, False)]],
     name="Full frame caption")
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 3.4, 2.95, 5.74, 1.95, fill=CARD, name="Observation card", adj=0.06)
text(s, 3.6, 3.05, 5.35, 1.8, [
    [("Measured", 12, INK, True, False)],
    [(f"Frame Y-PSNR {tps[0]:.2f} → {tps[1]:.2f} → {tps[2]:.2f} → {tps[3]:.2f} dB from QP 24 to QP 39", 11, INK, False, False)],
    [("Frame and crop chosen by a fixed rule; images rendered from the decoded YUV files by script", 11, INK, False, False)],
    [("What I saw in YUView 2.14", 12, INK, True, False)],
    [blank("[Sadab: write one or two sentences about what you actually saw]")],
], name="Observation text", space_after=2, bullet_from=None)

# ================================================================================================
# 8. Key findings and conclusion
NOTES[8] = (
    "To conclude, three findings from my own data.\n\n"
    f"First, QP is the main control. Each step of 5 in QP divided the bitrate by about "
    f"{f2(Q['bitrate_ratio_median'], 1)} and cost {f2(Q['ypsnr_drop_min'], 1)} to {f2(Q['ypsnr_drop_max'], 1)} dB "
    "of Y-PSNR.\n\n"
    f"Second, at the same QP, the medium preset gave {f2(P['ypsnr_gain_min'])} to {f2(P['ypsnr_gain_max'])} dB "
    f"better quality than fast, but it needed {f2(P['time_ratio_min'], 1)} to {f2(P['time_ratio_max'], 1)} times "
    "the encoding time, and the file size did not always go down, so a fair comparison needs BD-rate.\n\n"
    "Third, Windows and Linux produced exactly the same bitstreams and decoded videos.\n\n"
    "I also learned that laptop timing is noisy, so repeated runs are necessary.\n\n"
    "My background is in computer vision and deep learning. After this assignment, I am interested in "
    "learning-based enhancement of decoded video, for example a small CNN that reduces coding artifacts at high "
    "QP. This is only a direction I would like to study, not work I have done.\n\n"
    "Thank you very much, Professor Choi. I am happy to answer your questions."
)
s = content_slide("Key Findings and Conclusion", 8, NOTES[8])
text(s, 0.86, 1.3, 4.3, 0.3, [[("Findings from my experiment", 12, MUTED, True, False)]], name="Findings caption")
finds = [("QP controls the trade-off",
          f"+5 QP: bitrate ÷{f2(Q['bitrate_ratio_min'])}–{f2(Q['bitrate_ratio_max'])}, "
          f"Y-PSNR −{f2(Q['ypsnr_drop_min'], 1)}–{f2(Q['ypsnr_drop_max'], 1)} dB"),
         ("medium vs fast, same QP",
          f"+{f2(P['ypsnr_gain_min'])}–{f2(P['ypsnr_gain_max'])} dB for ×{f2(P['time_ratio_min'], 1)}–"
          f"{f2(P['time_ratio_max'], 1)} time; size {sgn(P['size_change_pct_min'])}…{sgn(P['size_change_pct_max'])} %"),
         ("Windows = Linux", "identical bitstreams and decoded video, 3 of 3 checks" if XP_ALL else
          "outputs differed: see report")]
for j, (head, val) in enumerate(finds):
    yy = 1.72 + j * 0.86
    c = shape(s, MSO_SHAPE.OVAL, 0.86, yy, 0.5, 0.5, fill=WHITE, line=BLUE, line_w=2, name=f"Finding {j + 1} node")
    shape_text(c, [[(str(j + 1), 13, BLUE, True, False)]])
    text(s, 1.55, yy - 0.02, 3.65, 0.75, [[(head, 13, INK, True, False)], [(val, 11, INK, False, False)]],
         name=f"Finding {j + 1} text")
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 5.4, 1.35, 3.74, 1.6, fill=CARD, name="Learned card", adj=0.07)
text(s, 5.6, 1.47, 3.4, 1.4, [
    [("What I learned", 13, INK, True, False)],
    [("Laptop timing is noisy: repeat runs before trusting a time difference", 12, INK, False, False)],
    [("Same QP ≠ same quality across presets: compare with RD curves / BD-rate", 12, INK, False, False)],
], name="Learned text", space_after=3, bullet_from=1)
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 5.4, 3.1, 3.74, 1.3, fill=SKY, name="Interest card", adj=0.08)
text(s, 5.6, 3.22, 3.4, 1.1, [
    [("My research interest", 13, DEEP, True, False)],
    [("Learning-based enhancement of decoded video, e.g. a lightweight CNN against coding artifacts at high QP "
      "(a direction to study, not completed work)", 12, INK, False, False)],
], name="Interest text", space_after=3)
text(s, 2.9, 4.6, 6.24, 0.4, [[("Thank you, Professor Kiho Choi", 18, BLUE, False, False, HEAD)]], align=PP_ALIGN.RIGHT,
     name="Thanks")

prs.core_properties.title = "VVC Encoding and Decoding: Implementation and Performance Analysis"
prs.core_properties.author = "Sadab Khan Prangon"
prs.save(OUT)
(HERE / "speaker_notes.md").write_text(
    "# Speaker notes: Sadab Khan Prangon, VVC assignment\n\n"
    "All numbers come from results/results_raw.csv, results/summary.json and results/crossplatform.json. "
    "Text in [brackets] (slide 7) must be written by Sadab after his own YUView inspection.\n\n"
    + "\n\n".join(f"## Slide {k}\n\n{v}" for k, v in NOTES.items()) + "\n", encoding="utf-8")
words = sum(len(v.split()) for v in NOTES.values())
print(f"saved {OUT.name}: {len(prs.slides)} slides; notes {words} words")
