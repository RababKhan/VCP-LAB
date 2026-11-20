"""Shared helpers for Sadab's deck builders (extracted from build_deck.py so later versions reuse the same design)."""
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
from pptx.chart.data import CategoryChartData, XyChartData  # noqa: F401
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE  # noqa: F401
PROJ = HERE.parent

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


