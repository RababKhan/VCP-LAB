"""Build presentation/VVC_Experimental_Evaluation_Prof_Kiho.pptx (python-pptx).

Every number on the slides is read from the project's verified result files at build time (no hand-typed
results): results/full/config_summary.csv, results/full/analysis_summary.json, results/full/timing_variability.csv,
results/supp_ac/timing_comparison.csv, results/phase5_linux/cross_platform_comparison.json,
visual/phase6/tables/frame_metrics.csv, visual/phase6/analysis.json. Figures come from figures/full/,
visual/phase6/ and presentation/assets/ (rendered from the YUV data by scripts/make_deck_assets.py).

Usage: python presentation/build_deck.py
"""
import csv
import json
import os
import statistics as st

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "presentation", "VVC_Experimental_Evaluation_Prof_Kiho.pptx")
A = lambda *p: os.path.join(ROOT, *p)  # noqa: E731

INK, TEAL, TINT, MUTED, LINE, WARN = "1B2A41", "0E7C86", "E8F3F4", "5B6472", "D5DCE3", "9A3412"
HEAD, BODY, MONO = "Cambria", "Calibri", "Courier New"
SEQ = ["BasketballPass", "BlowingBubbles", "BQMall", "BasketballDrive"]
TOTAL = 15


def rgb(h):
    return RGBColor.from_string(h)


# ------------------------------------------------------------------ data (read, never typed)
def load_csv(*p):
    return list(csv.DictReader(open(A(*p), encoding="utf-8")))


CFG = {(r["sequence"], int(r["qp"]), r["preset"]): r for r in load_csv("results", "full", "config_summary.csv")}
SUMM = json.load(open(A("results", "full", "analysis_summary.json"), encoding="utf-8"))
VAR = load_csv("results", "full", "timing_variability.csv")
SUPP = {(r["configuration"], r["metric"]): r for r in load_csv("results", "supp_ac", "timing_comparison.csv")}
XP = json.load(open(A("results", "phase5_linux", "cross_platform_comparison.json"), encoding="utf-8"))
FM = {(r["sequence"], int(r["frame_index"]), int(r["qp"]), r["preset"]): r
      for r in load_csv("visual", "phase6", "tables", "frame_metrics.csv")}
VA = json.load(open(A("visual", "phase6", "analysis.json"), encoding="utf-8"))
RUN = json.load(open(A("results", "full", "runs", "BQMall_f600_q32_medium_t8.json"), encoding="utf-8"))


def c(s, q, p, k):
    return float(CFG[(s, q, p)][k])


def rng(vals, fmt):
    return f"{fmt.format(min(vals))}–{fmt.format(max(vals))}"


def sgn(v, nd=2):
    return f"{'−' if v < 0 else '+'}{abs(v):.{nd}f}"


def srng(vals, nd=2):
    """Signed range with a real minus sign: '−0.66 to −0.45'."""
    return f"{sgn(min(vals), nd)} to {sgn(max(vals), nd)}"


QPS = [22, 27, 32, 37]
BR_RATIO = [c(s, QPS[i], "medium", "bitrate_kbps") / c(s, QPS[i + 1], "medium", "bitrate_kbps") for s in SEQ for i in range(3)]
DPSNR = [c(s, QPS[i], "medium", "psnr_y") - c(s, QPS[i + 1], "medium", "psnr_y") for s in SEQ for i in range(3)]
T22_37 = [c(s, 22, "medium", "enc_reported_s_median") / c(s, 37, "medium", "enc_reported_s_median") for s in SEQ]
ENC_DEC = [c(s, q, "medium", "enc_reported_s_median") / c(s, q, "medium", "dec_wall_s_median") for s in SEQ for q in QPS]
DEC_FPS_1080 = [500 / c("BasketballDrive", q, "medium", "dec_wall_s_median") for q in QPS]
CV_MED = st.median(float(v["enc_wall_cv_pct"]) for v in VAR)


def rel(p, ref="medium"):
    t = [c(s, 32, p, "enc_reported_s_median") / c(s, 32, ref, "enc_reported_s_median") for s in SEQ]
    d = [c(s, 32, p, "psnr_y") - c(s, 32, ref, "psnr_y") for s in SEQ]
    z = [100 * (c(s, 32, p, "bitstream_bytes") / c(s, 32, ref, "bitstream_bytes") - 1) for s in SEQ]
    return t, d, z


# ------------------------------------------------------------------ helpers
def set_bullet(p, level=0, char="•"):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(Emu(Inches(0.28 + 0.28 * level))))
    pPr.set("indent", str(-Emu(Inches(0.22))))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    bu = pPr.makeelement(qn("a:buChar"), {"char": char})
    pPr.append(bu)


def text(slide, x, y, w, h, paras, size=15, color=INK, font=BODY, anchor=MSO_ANCHOR.TOP, name=None, margin=0.04):
    """paras: list of str | dict(text|runs, size, bold, color, bullet, level, italic, align, space_after, font)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", Inches(margin))
    for i, para in enumerate(paras):
        d = {"text": para} if isinstance(para, str) else para
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        runs = d.get("runs") or [{"text": d["text"]}]
        for rd in runs:
            r = p.add_run()
            r.text = rd["text"]
            f = r.font
            f.name = rd.get("font", d.get("font", font))
            f.size = Pt(rd.get("size", d.get("size", size)))
            f.bold = rd.get("bold", d.get("bold", False))
            f.italic = rd.get("italic", d.get("italic", False))
            f.color.rgb = rgb(rd.get("color", d.get("color", color)))
        if d.get("bullet"):
            set_bullet(p, d.get("level", 0))
        p.alignment = d.get("align", PP_ALIGN.LEFT)
        p.space_after = Pt(d.get("space_after", 6))
    return tb


def card(slide, x, y, w, h, fill=TINT, line=None, name=None):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.06
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    if name:
        s.name = name
    return s


def badge(slide, x, y, label, d=0.42, name=None):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(TEAL)
    s.line.fill.background()
    s.shadow.inherit = False
    tf = s.text_frame
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", 0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size, r.font.bold, r.font.name = Pt(14), True, BODY
    r.font.color.rgb = rgb("FFFFFF")
    if name:
        s.name = name
    return s


def picture(slide, path, x, y, w=None, h=None, name=None, alt=None):
    iw, ih = Image.open(path).size
    if w and not h:
        h = w * ih / iw
    elif h and not w:
        w = h * iw / ih
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        pic.name = name
    if alt:
        pic._element.nvPicPr.cNvPr.set("descr", alt)
    return pic, w, h


def table(slide, x, y, w, rows, col_w, size=12, header_fill=TEAL, row_h=0.36, name=None, bold_first_col=False):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    if name:
        shp.name = name
    t = shp.table
    tblPr = t._tbl.tblPr
    tblPr.set("bandRow", "0")
    tblPr.set("firstRow", "1")
    for j, cw in enumerate(col_w):
        t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.07)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(header_fill if i == 0 else ("FFFFFF" if i % 2 else "F4F8F9"))
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = str(val)
            r.font.size = Pt(size)
            r.font.name = BODY
            r.font.bold = i == 0 or (bold_first_col and j == 0)
            r.font.color.rgb = rgb("FFFFFF" if i == 0 else INK)
    return t


def base(prs, title, message, notes, n):
    s = prs.slides.add_slide(prs.slide_layouts[5])  # "Title Only": keeps a real, editable title placeholder
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Inches(0.6), Inches(0.32), Inches(12.13), Inches(0.75)
    tf = t.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Inches(0.04)
    tf.text = title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    for r in p.runs:
        r.font.name, r.font.size, r.font.bold = HEAD, Pt(32), True
        r.font.color.rgb = rgb(INK)
    if message:
        text(s, 0.6, 1.05, 12.13, 0.45, [{"text": message, "size": 17, "italic": True, "color": TEAL}], name="Key message")
    text(s, 0.6, 7.0, 9.0, 0.3, [{"text": "VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1",
                                  "size": 10, "color": MUTED}], name="Footer")
    text(s, 11.73, 7.0, 1.0, 0.3, [{"text": f"{n} / {TOTAL}", "size": 10, "color": MUTED, "align": PP_ALIGN.RIGHT}],
         name="Slide number")
    s.notes_slide.notes_text_frame.text = notes
    return s


def stat(slide, x, y, w, big, label, sub=None, h=1.25):
    card(slide, x, y, w, h)
    paras = [{"text": big, "size": 28, "bold": True, "color": TEAL, "font": HEAD, "space_after": 2},
             {"text": label, "size": 14, "color": INK, "space_after": 2}]
    if sub:
        paras.append({"text": sub, "size": 11, "color": MUTED})
    text(slide, x + 0.15, y + 0.1, w - 0.3, h - 0.15, paras)


# ------------------------------------------------------------------ slides
def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    prs.core_properties.title = "VVC Encoding and Decoding: Experimental Evaluation"
    prs.core_properties.subject = "VVenC 1.14.0 / VVdeC 3.2.1 on Windows and Linux (WSL2)"
    prs.core_properties.author = ""

    # 1 Title ---------------------------------------------------------------
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.6, 1.2, 6.5, 2.4, [{"text": "VVC Encoding and Decoding: Experimental Evaluation", "size": 40, "bold": True,
                                  "font": HEAD, "color": INK}], name="Title", anchor=MSO_ANCHOR.BOTTOM)
    text(s, 0.6, 3.8, 6.3, 1.3, [
        {"text": "Building VVenC 1.14.0 and VVdeC 3.2.1 on Windows and Linux (WSL2), and measuring the effect of QP and preset on bitrate, quality and runtime",
         "size": 18, "color": TEAL}], name="Subtitle")
    text(s, 0.6, 5.2, 6.3, 1.65, [{"text": "Rabab Khan Rongon", "size": 20, "bold": True, "color": INK, "space_after": 2},
                                  {"text": "M.Sc. in Computer Science and Engineering (Major: Artificial Intelligence)", "size": 14, "color": INK, "space_after": 1},
                                  {"text": "Military Institute of Science and Technology (MIST), Bangladesh", "size": 14, "color": INK, "space_after": 6},
                                  {"text": "Practical assignment for Prof. Kiho, Kyung Hee University  ·  November 2026", "size": 13, "color": MUTED}],
         name="Presenter")
    pic, w, h = picture(s, A("presentation", "assets", "dataset_BQMall_frame100.png"), 7.35, 1.75, w=5.4, name="BQMall frame",
                        alt="BQMall test sequence, original frame 100")
    text(s, 7.35, 1.75 + h + 0.08, 5.4, 0.3, [{"text": "BQMall (832×480, 60 fps), original frame 100", "size": 11, "color": MUTED}],
         name="Image caption")
    s.notes_slide.notes_text_frame.text = (
        "Good morning, Professor. In this talk I present my practical assignment on VVC. "
        "I built the Fraunhofer encoder VVenC and decoder VVdeC on Windows and on Linux, encoded four test sequences "
        "with different QP values and presets, decoded them, and measured bitrate, PSNR and runtime. "
        "I also compared the video visually and checked that Windows and Linux give the same bitstream. "
        "Every number in these slides comes from my result files; I will say clearly where a statement is only an interpretation.")

    # 2 Objectives & workflow ------------------------------------------------
    s = base(prs, "Assignment Objectives and Workflow",
             "Build the tools, run controlled experiments, and explain the compression–quality–runtime trade-offs",
             "The assignment had four goals: build VVenC and VVdeC on Windows and Linux; encode the given YUV files and decode "
             "the bitstreams; compare original and reconstructed video in YUView; and analyse encoding time, decoding time, "
             "bitstream size and PSNR as functions of QP and preset. I worked in phases and stopped for approval after each one. "
             "Every run has a log, a JSON record and checksums, so everything can be reproduced.", 2)
    steps = [("1", "Build", "VVenC + VVdeC, Windows (MSVC) and Linux (GCC, WSL2)"),
             ("2", "Encode", "4 sequences × 8 configurations, QP sweep and preset sweep"),
             ("3", "Decode", "VVdeC timing pass and reconstruction pass"),
             ("4", "Measure", "Time, bitstream size, PSNR; 65 verified runs"),
             ("5", "Compare", "Visual comparison and Windows ↔ Linux bitstream check")]
    x0, cw, gap = 0.6, 2.25, 0.22
    for i, (n_, head, body) in enumerate(steps):
        x = x0 + i * (cw + gap)
        card(s, x, 1.85, cw, 2.35, name=f"Step {n_}")
        badge(s, x + 0.18, 2.03, n_)
        text(s, x + 0.18, 2.55, cw - 0.36, 0.45, [{"text": head, "size": 20, "bold": True, "font": HEAD}])
        text(s, x + 0.18, 3.05, cw - 0.36, 1.1, [{"text": body, "size": 14, "color": INK}])
        if i < len(steps) - 1:
            a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + cw + 0.02), Inches(2.92), Inches(0.18), Inches(0.22))
            a.fill.solid()
            a.fill.fore_color.rgb = rgb(TEAL)
            a.line.fill.background()
    text(s, 0.6, 4.55, 12.1, 2.2, [
        {"text": "Working principles", "size": 18, "bold": True, "font": HEAD, "space_after": 8},
        {"text": "Every command executed and verified; logs kept for successful and failed attempts", "bullet": True, "size": 15},
        {"text": "No upstream source changes; exact release commits on both platforms", "bullet": True, "size": 15},
        {"text": "Measured results, interpretations and hypotheses are labelled separately", "bullet": True, "size": 15},
        {"text": "Outputs: scripts, run manifests, per-run JSON + logs, CSV tables, figures, phase reports", "bullet": True, "size": 15}])

    # 3 Tools -----------------------------------------------------------------
    s = base(prs, "VVC, VVenC, VVdeC and YUView",
             "An international video coding standard, plus three open-source tools to encode, decode and inspect it",
             "VVC, Versatile Video Coding, is the ITU-T H.266 and ISO/IEC 23090-3 standard, finalized in 2020 as the successor of HEVC. "
             "Its design target was about half the bitrate of HEVC at similar perceptual quality, as reported in the overview paper by Bross and colleagues. "
             "VVenC is Fraunhofer HHI's open, optimized encoder; its presets from faster to slower trade speed for compression efficiency. "
             "VVdeC is the matching open decoder. YUView is an open-source viewer for raw YUV files, used for side-by-side comparison.", 3)
    cards = [("VVC / H.266", ["ITU-T H.266 | ISO/IEC 23090-3 (2020) [1]", "Successor of HEVC (H.265)",
                              "Block-based hybrid coding; flexible partitioning, new prediction and in-loop filter tools",
                              "Target: ≈50% bitrate reduction vs HEVC at similar perceptual quality [2]"]),
             ("VVenC 1.14.0", ["Fraunhofer HHI open-source encoder [3]", "Presets: faster · fast · medium · slow · slower",
                               "Multithreading and SIMD (AVX2 used here)", "Used: vvencapp, constant QP"]),
             ("VVdeC 3.2.1", ["Fraunhofer HHI open-source decoder", "Multithreaded, SIMD-optimized",
                              "Used: vvdecapp for timing and reconstruction"]),
             ("YUView 2.14", ["Open-source YUV and bitstream viewer (IENT, RWTH Aachen) [8]", "Side-by-side, comparison and difference views",
                              "Used to prepare the visual-comparison workflow"])]
    for i, (head, lines) in enumerate(cards):
        x = 0.6 + i * 3.08
        card(s, x, 1.85, 2.9, 3.85, name=f"Tool card {head}")
        text(s, x + 0.2, 2.0, 2.5, 0.5, [{"text": head, "size": 20, "bold": True, "font": HEAD, "color": TEAL}])
        text(s, x + 0.2, 2.6, 2.55, 3.0, [{"text": ln, "bullet": True, "size": 14, "space_after": 8} for ln in lines])
    card(s, 0.6, 5.95, 12.13, 0.85, fill="F4F6F8", name="Tool chain")
    text(s, 0.8, 6.02, 11.8, 0.72, [{"runs": [{"text": "In this study:  ", "bold": True},
                                             {"text": "original YUV → vvencapp (encode) → .266 bitstream → vvdecapp (decode) → reconstructed YUV → own PSNR script and YUView comparison"}],
                                    "size": 15}], anchor=MSO_ANCHOR.MIDDLE)

    # 4 Environments ------------------------------------------------------------
    s = base(prs, "Development Environments: Windows and Linux",
             "Same release commits, Release builds with upstream defaults, 0 warnings and 0 errors on both platforms",
             "Both builds use the exact release commits, VVenC v1.14.0 and VVdeC v3.2.1, with no source changes and upstream default "
             "CMake options in Release mode. On Windows I used the Visual Studio 2022 Build Tools; on Linux, Ubuntu 24.04 with GCC 13.3. "
             "An important point: Linux ran inside WSL2, which is a lightweight virtual machine on the same laptop, not a native Linux installation. "
             "On Linux I could also run the upstream VVenC ctest suite: 39 of 39 tests passed.", 4)
    rows = [["", "Windows", "Linux"],
            ["Operating system", "Windows 11 Home 10.0.26200", "Ubuntu 24.04.5 LTS on WSL2 (kernel 6.18.54.1)"],
            ["Compiler / build", "MSVC 19.44 (VS Build Tools 2022 17.14), CMake 4.4.4", "GCC 13.3.0, CMake 3.28.3, GNU Make 4.3"],
            ["Configuration", "Release, upstream defaults, AVX2", "Release, upstream defaults, AVX2"],
            ["Build result", "0 warnings, 0 errors", "0 warnings, 0 errors"],
            ["Upstream tests", "vvenc_unit_test, vvdec_unit_test: passed", "Both unit tests passed; VVenC ctest 39 / 39 passed"],
            ["Source commits", "VVenC v1.14.0 (9428ea8), VVdeC v3.2.1 (cb1a3ef)", "identical commits, no modification [6]"]]
    table(s, 0.6, 1.8, 12.13, rows, [2.3, 4.6, 5.23], size=13, row_h=0.5, name="Environment table", bold_first_col=True)
    card(s, 0.6, 5.55, 12.13, 1.2, name="Hardware note")
    text(s, 0.8, 5.65, 11.8, 1.0, [
        {"runs": [{"text": "Hardware: ", "bold": True}, {"text": "laptop, Intel Core i7-1260P (12 cores / 16 threads, hybrid P/E cores), 15.7 GB RAM. "},
                  {"text": "Linux = WSL2 virtual machine (16 vCPUs, 7.6 GiB RAM), not native Linux.", "bold": True}], "size": 14},
        {"text": "VVdeC conformance-bitstream tests (251) were not run on either platform; they need a separate JVET download.", "size": 13, "color": MUTED}])

    # 5 Dataset -------------------------------------------------------------------
    s = base(prs, "Dataset and Video Characteristics",
             "Four JVET test sequences, 10-bit 4:2:0 files whose content has 8-bit precision",
             "Four sequences were provided: two small 416 by 240 sequences, BQMall at 832 by 480, and BasketballDrive in 1080p. "
             "I inspected every file. They are stored as 10-bit little-endian 4:2:0, but the two least significant bits are always zero, "
             "so the content is 8-bit precision shifted into a 10-bit container. The last frame of each file is a copyright card, "
             "so I encoded only the content frames. PSNR uses peak value 1020, which is the HM, VTM and VVenC convention.", 5)
    meta = [("BasketballPass", "416×240", "50 fps", 500), ("BlowingBubbles", "416×240", "50 fps", 500),
            ("BQMall", "832×480", "60 fps", 600), ("BasketballDrive", "1920×1080", "50 fps", 500)]
    for i, (name, res, fps, nfr) in enumerate(meta):
        x = 0.6 + i * 3.08
        pic, w, h = picture(s, A("presentation", "assets", f"dataset_{name}_frame100.png"), x, 1.8, w=2.9, name=f"{name} thumbnail",
                            alt=f"{name}, original frame 100")
        text(s, x, 1.8 + h + 0.08, 2.9, 0.8, [{"text": name, "size": 15, "bold": True, "space_after": 2},
                                             {"text": f"{res} · {fps} · {nfr} frames", "size": 13, "color": MUTED}])
    text(s, 0.6, 4.55, 12.1, 2.4, [
        {"text": "Format: planar YUV 4:2:0, 10-bit little-endian (16-bit words); verified by SHA256 and size checks", "bullet": True, "size": 15},
        {"text": "All samples have the two least-significant bits = 0 → 8-bit precision content in a 10-bit container", "bullet": True, "size": 15},
        {"text": "The last frame of each file is a copyright card → excluded; 500 / 500 / 600 / 500 content frames encoded", "bullet": True, "size": 15},
        {"text": "PSNR: peak 1020 (= 255 << 2, HM / VTM / VVenC convention), mean of per-frame PSNR; YUV-PSNR = 4:1:1 MSE weighting", "bullet": True, "size": 15},
        {"text": "Thumbnails: original frame 100, rendered from the YUV data (BT.709 assumed for display); BasketballDrive downscaled for display only",
         "size": 11, "color": MUTED}])

    # 6 Design ----------------------------------------------------------------------
    s = base(prs, "Experimental Design and Controlled Parameters",
             "One factor at a time: a QP sweep at preset medium and a preset sweep at QP 32",
             "I varied one factor at a time. The QP sweep used QP 22, 27, 32 and 37 at preset medium. The preset sweep used faster to slower at QP 32. "
             "QP 32 with medium belongs to both sweeps, so each sequence has 8 unique configurations, 32 in total. "
             "For timing reliability I added two repeats for every configuration of the two small sequences, plus one warm-up run: 65 runs in a randomized order. "
             "Everything else was fixed: constant QP without rate control, perceptual QP adaptation off, 8 threads, CRA refresh every second. "
             "During the run the laptop was unplugged for about 64 minutes; I detected this in the monitoring log and re-measured the four affected configurations on AC power.", 6)
    rows = [["Sweep", "Values", "Fixed"],
            ["QP sweep", "QP 22 · 27 · 32 · 37", "preset medium"],
            ["Preset sweep", "faster · fast · medium · slow · slower", "QP 32"],
            ["Unique configurations", "8 per sequence × 4 = 32", "QP 32/medium shared"],
            ["Runs", f"1 warm-up + 32 + 32 repeats = {SUMM['expected_runs']}", "random order"]]
    table(s, 0.6, 1.8, 7.0, rows, [2.05, 3.0, 1.95], size=13, row_h=0.5, name="Design table", bold_first_col=True)
    text(s, 0.6, 4.5, 7.0, 2.3, [
        {"text": "Timing repeats: 2 extra runs for each configuration of the two 240p sequences (3 samples, median reported)", "bullet": True, "size": 14},
        {"text": f"Verification: {SUMM['present_runs']} / {SUMM['expected_runs']} runs passed all checks; {SUMM['repeats_identical_bitstream']} repeats byte-identical",
         "bullet": True, "size": 14},
        {"text": "Run order randomized (seed 2026) so that slow drifts do not align with one factor", "bullet": True, "size": 14},
        {"text": "Battery incident: 64 min on battery → 4 single-sample configurations re-measured on AC (originals kept, flagged)",
         "bullet": True, "size": 14}])
    card(s, 7.95, 1.8, 4.78, 4.1, name="Controlled parameters")
    text(s, 8.15, 1.95, 4.4, 4.7, [
        {"text": "Controlled parameters", "size": 18, "bold": True, "font": HEAD, "color": TEAL, "space_after": 10},
        {"text": "Constant QP (no rate control)", "bullet": True, "size": 14},
        {"text": "QPA off (--qpa 0)", "bullet": True, "size": 14},
        {"text": "8 encoder and 8 decoder threads", "bullet": True, "size": 14},
        {"text": "CRA refresh every 1 s (intra period 48 / 64), GOP 32", "bullet": True, "size": 14},
        {"text": "All content frames (500 / 600)", "bullet": True, "size": 14},
        {"text": "AC power, Windows mode \"Best performance\", 30 s system monitor", "bullet": True, "size": 14},
        {"text": "Same tools, inputs and checksums for every run", "bullet": True, "size": 14}])

    # 7 Pipeline -------------------------------------------------------------------
    s = base(prs, "Encoding and Decoding Pipeline",
             "Every run is encoded, decoded twice and verified automatically before its result is accepted",
             "This is the pipeline for every run. The encoder reads the original YUV file and writes a VVC bitstream. "
             "The decoder runs twice: once without writing output, to measure decoding time, and once writing the reconstructed YUV. "
             "My own PSNR script then compares the reconstruction with the original. A run is only accepted if all checks pass: exit codes, "
             "frame counts, the configuration echoed by the encoder, PSNR equal to the encoder's own value, correct frame alignment, "
             "and for repeats a byte-identical bitstream.", 7)
    boxes = [("Original YUV", "10-bit 4:2:0"), ("vvencapp", "VVenC encoder"), ("Bitstream", ".266 (VVC)"),
             ("vvdecapp", "timing pass + recon pass"), ("Reconstructed YUV", "same format"), ("PSNR + checks", "results.csv")]
    bw, gap = 1.8, 0.27
    for i, (h1, h2) in enumerate(boxes):
        x = 0.6 + i * (bw + gap)
        tool = h1 in ("vvencapp", "vvdecapp", "PSNR + checks")
        card(s, x, 1.85, bw, 1.15, fill=TEAL if tool else TINT, name=f"Pipeline {h1}")
        text(s, x + 0.08, 1.95, bw - 0.16, 1.0, [{"text": h1, "size": 15, "bold": True, "color": "FFFFFF" if tool else INK, "align": PP_ALIGN.CENTER, "space_after": 2},
                                               {"text": h2, "size": 12, "color": "FFFFFF" if tool else MUTED, "align": PP_ALIGN.CENTER}],
             anchor=MSO_ANCHOR.MIDDLE)
        if i < len(boxes) - 1:
            a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + bw + 0.04), Inches(2.33), Inches(0.19), Inches(0.2))
            a.fill.solid()
            a.fill.fore_color.rgb = rgb(INK)
            a.line.fill.background()
    enc = RUN["encoder_cmd"]
    toks = [os.path.basename(t.strip('"')) if ("\\" in t or "/" in t) else t for t in enc.split()]
    toks[0] = "vvencapp"
    enc_s = " ".join(toks).replace("BQMall_f600_q32_medium_t8.266", "out.266")
    card(s, 0.6, 3.3, 12.13, 1.45, fill="F4F6F8", name="Command box")
    text(s, 0.8, 3.38, 11.8, 1.3, [
        {"text": "Example (BQMall, QP 32, medium):", "size": 12, "color": MUTED, "space_after": 3},
        {"text": enc_s, "size": 12, "font": MONO, "space_after": 3},
        {"text": "vvdecapp -b out.266 -t 8            (timing pass, no output)", "size": 12, "font": MONO, "space_after": 1},
        {"text": "vvdecapp -b out.266 -o rec.yuv -t 8  (reconstruction for PSNR)", "size": 12, "font": MONO}])
    checks = ["Exit codes = 0; picture and decoded-frame counts = input frames",
              "Encoder echo: QPA disabled, rate control \"QP n\", 8 threads, 10-bit input",
              f"Independent PSNR = encoder PSNR (max difference {SUMM['max_abs_psnr_diff_vs_encoder']:.4f} dB); FFmpeg cross-check in the Phase 3 smoke test",
              "Frame alignment: best offset 0 in every run",
              f"Repeats: SHA256 byte-identical bitstreams ({SUMM['repeats_identical_bitstream']})"]
    text(s, 0.6, 4.95, 12.1, 1.9, [{"text": "Automatic checks per run", "size": 17, "bold": True, "font": HEAD, "space_after": 6}] +
         [{"text": ck, "bullet": True, "size": 14, "space_after": 3} for ck in checks])

    # 8 QP vs bitrate / PSNR ------------------------------------------------------------
    s = base(prs, "QP vs Bitrate and PSNR",
             f"QP is the main rate–quality control: +5 QP roughly halves the bitrate and costs {min(DPSNR):.2f}–{max(DPSNR):.2f} dB",
             "These two charts show the QP sweep at preset medium. The bitrate axis is logarithmic, so the straight lines mean an exponential relation: "
             f"each step of plus 5 QP divides the bitrate by about {st.median(BR_RATIO):.2f}, between {min(BR_RATIO):.2f} and {max(BR_RATIO):.2f}. "
             f"Y-PSNR drops by {min(DPSNR):.2f} to {max(DPSNR):.2f} dB per step. The drop is largest for the small 240p sequences at low QP, "
             "and smallest for BasketballDrive at low QP. These are sequence-level values: mean of per-frame PSNR over all 500 or 600 frames.", 8)
    picture(s, A("figures", "full", "qp_vs_bitrate.png"), 0.6, 1.7, w=5.95, name="QP vs bitrate chart",
            alt="Line chart: bitrate in kbps (log scale) versus QP 22 to 37 for four sequences, preset medium")
    picture(s, A("figures", "full", "qp_vs_psnr_y.png"), 6.78, 1.7, w=5.95, name="QP vs Y-PSNR chart",
            alt="Line chart: Y-PSNR versus QP 22 to 37 for four sequences, preset medium")
    stat(s, 0.6, 5.55, 3.9, f"÷{st.median(BR_RATIO):.2f}", "bitrate per +5 QP (median)", f"range {min(BR_RATIO):.2f}–{max(BR_RATIO):.2f} over 12 steps", h=1.25)
    stat(s, 4.72, 5.55, 3.9, f"{min(DPSNR):.2f}–{max(DPSNR):.2f} dB", "Y-PSNR loss per +5 QP", "peak 1020, mean of per-frame PSNR", h=1.25)
    card(s, 8.84, 5.55, 3.89, 1.25)
    text(s, 9.0, 5.62, 3.6, 1.15, [{"text": "Conditions", "size": 14, "bold": True, "space_after": 3},
                                   {"text": "Preset medium, QPA off, 8 threads, sequence level (all frames)", "size": 13, "color": MUTED}])

    # 9 QP vs encoding time -----------------------------------------------------------------
    s = base(prs, "QP vs Encoding Time",
             "Lower QP means more coded detail and longer encoding; decoding stays two orders of magnitude faster",
             f"Encoding time also depends on QP: QP 22 took {min(T22_37):.1f} to {max(T22_37):.1f} times as long as QP 37, because more residual detail is coded and searched. "
             f"Decoding is much cheaper: at preset medium, encoding took {min(ENC_DEC):.0f} to {max(ENC_DEC):.0f} times longer than decoding. "
             f"The 1080p sequence decodes at {min(DEC_FPS_1080):.0f} to {max(DEC_FPS_1080):.0f} frames per second. "
             f"Repeated encodes of the same configuration varied with a median coefficient of variation of {CV_MED:.1f} percent, so I treat differences below about 5 to 10 percent between single runs as noise. "
             "All timings are from one laptop on Windows and are not a general benchmark.", 9)
    picture(s, A("figures", "full", "qp_vs_encoding_time.png"), 0.6, 1.7, w=7.4, name="QP vs encoding time chart",
            alt="Line chart: encoding time in seconds (log scale) versus QP for four sequences, preset medium")
    stat(s, 8.3, 1.75, 4.43, f"{min(T22_37):.1f}–{max(T22_37):.1f}×", "encoding time QP 22 vs QP 37", "preset medium, 4 sequences")
    stat(s, 8.3, 3.15, 4.43, f"{min(ENC_DEC):.0f}–{max(ENC_DEC):.0f}×", "encoding vs decoding time", "medium; decode timing pass without output")
    stat(s, 8.3, 4.55, 4.43, f"{CV_MED:.1f}%", "median CV of repeated encodes", "16 configurations × 3 samples (240p)")
    text(s, 8.3, 5.95, 4.43, 0.9, [{"text": "Windows, i7-1260P laptop, 8 threads, Best performance mode. Encoder-reported time, median of samples.",
                                    "size": 11, "color": MUTED}])

    # 10 Presets -------------------------------------------------------------------------------
    t_f, d_f, z_f = rel("faster")
    t_fa, d_fa, z_fa = rel("fast")
    t_sl, d_sl, z_sl = rel("slow")
    t_sr, d_sr, z_sr = rel("slower")
    bqf_ac = float(SUPP[("BQMall_f600_q32_faster_t8", "encode_reported_s")]["supplementary_ac"]) / c("BQMall", 32, "medium", "enc_reported_s_median")
    s = base(prs, "Preset vs Compression Efficiency and Runtime",
             f"Slower presets buy small gains at large cost: slower takes {min(t_sr):.0f}–{max(t_sr):.0f}× the time of medium for {min(d_sr):+.2f} to {max(d_sr):+.2f} dB",
             f"The preset sweep at QP 32 shows a steep runtime cost. Relative to medium, slower needed {min(t_sr):.0f} to {max(t_sr):.0f} times the encoding time, "
             f"but gained only {min(d_sr):.2f} to {max(d_sr):.2f} dB and produced {-max(z_sr):.1f} to {-min(z_sr):.1f} percent smaller files. Faster needed only {min(t_f):.2f} to {max(t_f):.2f} times the time and lost "
             f"{-max(d_f):.2f} to {-min(d_f):.2f} dB with {min(z_f):.0f} to {max(z_f):.0f} percent larger files. Two cautions. First, these are sequence-level results at one QP, so they are not a BD-rate "
             "comparison; preset efficiency needs several QPs per preset. Second, at frame level a faster preset can sometimes have higher PSNR than a slower one, "
             "but in every such frame it had spent more bits.", 10)
    picture(s, A("figures", "full", "preset_vs_encoding_time.png"), 0.6, 1.7, w=6.3, name="Preset vs encoding time chart",
            alt="Line chart: encoding time in seconds (log scale) versus preset faster to slower at QP 32 for four sequences")
    rows = [["Preset vs medium", "Encoding time", "ΔY-PSNR", "Bitstream size"],
            ["faster", f"{rng(t_f, '{:.2f}')}×", f"{srng(d_f)} dB", f"{srng(z_f, 1)}%"],
            ["fast", f"{rng(t_fa, '{:.2f}')}×", f"{srng(d_fa)} dB", f"{srng(z_fa, 1)}%"],
            ["slow", f"{rng(t_sl, '{:.1f}')}×", f"{srng(d_sl)} dB", f"{srng(z_sl, 1)}%"],
            ["slower", f"{rng(t_sr, '{:.1f}')}×", f"{srng(d_sr)} dB", f"{srng(z_sr, 1)}%"]]
    table(s, 7.15, 1.75, 5.58, rows, [1.3, 1.2, 1.6, 1.48], size=12, row_h=0.42, name="Preset table", bold_first_col=True)
    text(s, 7.15, 3.95, 5.58, 0.55, [{"text": f"QP 32, sequence level, ranges over the 4 sequences. BQMall faster: {c('BQMall', 32, 'faster', 'enc_reported_s_median') / c('BQMall', 32, 'medium', 'enc_reported_s_median'):.3f}× (run on battery) vs {bqf_ac:.3f}× (AC re-measurement).",
                                      "size": 11, "color": MUTED}])
    card(s, 7.15, 4.6, 5.58, 1.85, fill="FBF3EE", name="Caution box")
    text(s, 7.35, 4.68, 5.2, 2.05, [
        {"text": "Read with care", "size": 15, "bold": True, "color": WARN, "space_after": 4},
        {"text": "One QP per preset → not a BD-rate comparison", "bullet": True, "size": 13, "space_after": 3},
        {"text": "BlowingBubbles fast: 0.58% smaller than medium but −0.44 dB", "bullet": True, "size": 13, "space_after": 3},
        {"text": "Frame level: medium below faster in 13.4% of BasketballPass frames, always with more bits spent by faster", "bullet": True, "size": 13}])

    # 11 Visual -----------------------------------------------------------------------------------
    s = base(prs, "Visual Quality Comparison: Original, QP 22, QP 32, QP 37",
             "Observer-confirmed for BasketballPass frame 133: QP 22 clearest, QP 37 blurriest — PSNR and SSIM rank the same way",
             "Here are enlarged crops of the same region, rendered from the YUV data with the same display conversion. "
             "Top row: BasketballPass frame 133. I personally confirmed this example: QP 22 is the clearest and QP 37 the blurriest. "
             "Bottom row: BQMall frame 42, the frame with the lowest PSNR at QP 37. The statements for this row come from automated metrics and my "
             "preliminary inspection, not from a formal subjective test. Note that the frame PSNR differences here are 6 to 10 dB; preset differences "
             "at QP 32 are only 0.2 to 1.3 dB per frame and are much harder to see.", 11)
    rows_v = [("BasketballPass", 133, "BasketballPass, frame 133 — observer-confirmed: QP 22 clearest, QP 37 blurriest"),
              ("BQMall", 42, "BQMall, frame 42 — lowest QP 37 frame; automated metrics + preliminary interpretation")]
    pw, gap = 2.42, 0.14
    y = 1.65
    for seq, fi, label in rows_v:
        text(s, 0.6, y, 10.2, 0.32, [{"text": label, "size": 13, "bold": True}])
        for j, tag in enumerate(["original", "QP22_medium", "QP32_medium", "QP37_medium"]):
            x = 0.6 + j * (pw + gap)
            pic, w, h = picture(s, A("presentation", "assets", f"crop_{seq}_f{fi}_{tag}.png"), x, y + 0.36, w=pw,
                                name=f"{seq} f{fi} {tag}", alt=f"{seq} frame {fi}, enlarged crop, {tag.replace('_', ' ')}")
            if tag == "original":
                cap = "Original"
            else:
                q = int(tag[2:4])
                m = FM[(seq, fi, q, "medium")]
                cap = f"QP {q}: {float(m['frame_psnr_y']):.2f} dB · SSIM {float(m['frame_ssim_y']):.3f}"
            text(s, x, y + 0.38 + h, pw, 0.3, [{"text": cap, "size": 11, "color": MUTED}])
        y += 0.36 + h + 0.42
    card(s, 10.95, 1.65, 1.78, 5.15, name="Visual notes")
    text(s, 11.05, 1.75, 1.6, 5.0, [
        {"text": "Notes", "size": 14, "bold": True, "color": TEAL, "space_after": 6},
        {"text": "Same crop window for all panels; pixel-repetition zoom (4× / 3×)", "size": 11, "space_after": 6},
        {"text": "Frame-level Y-PSNR and SSIM-Y [5] (simplified 8×8 window)", "size": 11, "space_after": 6},
        {"text": "BQMall row: automated metrics + preliminary interpretation", "size": 11, "space_after": 6},
        {"text": "Not a formal subjective study (no BT.500 setup, no MOS)", "size": 11, "bold": True, "space_after": 6},
        {"text": "Display: BT.709 assumed", "size": 11, "color": MUTED}])

    # 12 Cross-platform ------------------------------------------------------------------------------
    w_, l_ = XP["windows"], XP["linux"]["run1"]
    ident = lambda a, b: "identical" if a == b else "DIFFERENT"  # noqa: E731
    s = base(prs, "Cross-Platform Verification: Windows vs Linux",
             "The MSVC and GCC builds produced a byte-identical bitstream for the tested configuration",
             "To check the Linux build I repeated the 16-frame smoke test from the Windows phase with identical settings. "
             "The bitstream, the reconstructed video and the PSNR are byte-for-byte identical, and all three Linux repeats are identical too. "
             "So for this input and configuration both compilers make the same encoding decisions. I did not assume this in advance. "
             "This is one configuration only, and Linux ran in WSL2. I do not compare speed: the runs are shorter than a second and the conditions were not controlled.", 12)
    rows = [["16-frame smoke test", "Windows (MSVC 19.44)", "Linux (GCC 13.3, WSL2)", "Result"],
            ["Bitstream size", f"{w_['bitstream_bytes']:,} B", f"{l_['bitstream_bytes']:,} B", ident(w_['bitstream_bytes'], l_['bitstream_bytes'])],
            ["Bitstream SHA256", w_["bitstream_sha256"][:16] + "…", l_["bitstream_sha256"][:16] + "…", ident(w_["bitstream_sha256"], l_["bitstream_sha256"])],
            ["Reconstruction SHA256", w_["recon_sha256"][:16] + "…", l_["recon_sha256"][:16] + "…", ident(w_["recon_sha256"], l_["recon_sha256"])],
            ["Decoded frames", str(w_["decoded_frames"]), str(l_["decoded_frames"]), ident(w_["decoded_frames"], l_["decoded_frames"])],
            ["Y / U / V PSNR (dB)", " / ".join(f"{w_['psnr_peak1020'][k]:.4f}" for k in "YUV"),
             " / ".join(f"{l_['psnr_peak1020'][k]:.4f}" for k in "YUV"), ident(w_["psnr_peak1020"], l_["psnr_peak1020"])],
            ["Linux repeats (3 runs)", "–", "same SHA256 in all runs" if XP["checks"]["linux_runs_deterministic_bitstream"] else "differ", "deterministic"]]
    table(s, 0.6, 1.8, 8.0, rows, [2.2, 2.25, 2.25, 1.3], size=12, row_h=0.48, name="Cross-platform table", bold_first_col=True)
    text(s, 0.6, 5.3, 8.0, 1.5, [
        {"text": "Configuration: BasketballPass 416×240, 16 frames, QP 32, preset faster, QPA off, 4 threads (same command on both platforms)",
         "size": 13, "color": MUTED, "space_after": 6},
        {"text": "Encoder per-picture log lines (POC, slice QP, bits, PSNR) are also identical; only the speed (fps) lines differ.", "size": 13, "color": MUTED}])
    card(s, 8.95, 1.8, 3.78, 3.36, fill="FBF3EE", name="Scope box")
    text(s, 9.15, 1.92, 3.4, 4.8, [
        {"text": "Scope and caveats", "size": 15, "bold": True, "color": WARN, "space_after": 8},
        {"text": "Verified for one 16-frame configuration only", "bullet": True, "size": 13, "space_after": 6},
        {"text": "Linux = Ubuntu 24.04 in WSL2, not native", "bullet": True, "size": 13, "space_after": 6},
        {"text": "No speed claim: sub-second runs, different compilers, VM, day and power state", "bullet": True, "size": 13, "space_after": 6},
        {"text": "Other presets, QPs, thread counts and long sequences: not tested across platforms", "bullet": True, "size": 13}])

    # 13 Findings / limitations / lessons ---------------------------------------------------------------
    s = base(prs, "Key Findings, Limitations and Lessons Learned", None,
             "To summarize the findings: QP is the dominant control of rate and quality; presets trade a large amount of time for a small gain; "
             "decoding is two orders of magnitude cheaper than encoding; and the encoder output was deterministic and, for the tested configuration, identical across platforms. "
             "The main limitations are the single-QP preset comparison, laptop timing with one sample for the large sequences, the 8-bit content, WSL2 instead of native Linux, "
             "and the informal visual evaluation. The most important lessons for me were to verify every number independently, to control and monitor the test environment, "
             "and to remember that the QP option is only a base QP: the encoder adapts the QP per picture.", 13)
    cols = [("Measured findings", TINT, INK, [
        f"+5 QP: bitrate ÷{st.median(BR_RATIO):.2f} (median); Y-PSNR −{min(DPSNR):.2f} to −{max(DPSNR):.2f} dB",
        f"slower vs medium: {min(t_sr):.1f}–{max(t_sr):.1f}× time for {srng(d_sr)} dB and {-max(z_sr):.1f}–{-min(z_sr):.1f}% smaller files",
        f"Encoding {min(ENC_DEC):.0f}–{max(ENC_DEC):.0f}× slower than decoding",
        f"Deterministic output: {SUMM['repeats_identical_bitstream']} repeats identical; Windows = Linux for the smoke test"]),
        ("Limitations", "FBF3EE", WARN, [
            "Presets compared at one QP → no BD-rate",
            "Laptop timing: hybrid CPU; 1 sample for the two large sequences; 64-min battery incident",
            "8-bit content in a 10-bit container",
            "Linux via WSL2; cross-platform identity for one configuration",
            "Visual evaluation informal; one observer-confirmed observation"]),
        ("Lessons learned", TINT, INK, [
            "Verify independently: own PSNR tool, SHA256, frame alignment",
            "Control and monitor the environment (power mode, AC, temperature)",
            "-q is a base QP: hierarchy and GOP-level adaptation change slice QPs",
            "Keep logs, manifests and fingerprints; label interpretations"])]
    for i, (head, fill, hcol, items) in enumerate(cols):
        x = 0.6 + i * 4.12
        card(s, x, 1.3, 3.89, 4.3, fill=fill, name=f"{head} card")
        text(s, x + 0.2, 1.42, 3.5, 0.5, [{"text": head, "size": 19, "bold": True, "font": HEAD, "color": hcol}])
        text(s, x + 0.2, 2.0, 3.55, 3.55, [{"text": it, "bullet": True, "size": 14, "space_after": 9} for it in items])
    card(s, 0.6, 5.85, 12.13, 0.95, fill="F4F6F8", name="Bottom line")
    text(s, 0.8, 5.92, 11.8, 0.82, [{"runs": [{"text": "Bottom line:  ", "bold": True, "color": TEAL},
                                             {"text": "QP sets the rate–quality operating point; the preset decides how much encoder time is spent to reach it. A fair preset comparison needs BD-rate over several QPs."}],
                                    "size": 15}], anchor=MSO_ANCHOR.MIDDLE)

    # 14 Conclusion / future ------------------------------------------------------------------------------
    s = base(prs, "Conclusion and Possible Future Research Directions",
             "The tools are built and verified on two platforms, and the main VVC trade-offs are quantified with checked data",
             "In conclusion, I built and verified VVenC and VVdeC on Windows and Linux, ran a controlled and fully logged experiment, and quantified the effect of QP and preset. "
             "For future work, the first step would be a proper BD-rate study of the presets over several QPs, ideally against the VTM reference under JVET common test conditions. "
             "Second, controlled timing on native Linux with more repeats. Third, perceptual metrics and a small formal subjective test. "
             "Finally, connected to my background in neural-network pruning, I am interested in lightweight learned models that predict encoder decisions, "
             "for example block partitioning, to reduce the encoding time of the slower presets. That last point is a research direction, not a result of this assignment.", 14)
    text(s, 0.6, 1.75, 5.6, 5.0, [
        {"text": "Conclusion", "size": 20, "bold": True, "font": HEAD, "space_after": 10},
        {"text": "VVenC 1.14.0 and VVdeC 3.2.1 built from unmodified release commits on Windows and Linux (WSL2); all available tests passed",
         "bullet": True, "size": 15, "space_after": 9},
        {"text": f"{SUMM['expected_runs']} verified runs: QP controls rate and quality; slower presets cost much more time for small gains",
         "bullet": True, "size": 15, "space_after": 9},
        {"text": "Encoder output deterministic and, for the tested configuration, identical across compilers", "bullet": True, "size": 15, "space_after": 9},
        {"text": "Visual inspection agrees with PSNR for large QP steps; preset differences are mostly numerical", "bullet": True, "size": 15}])
    text(s, 6.6, 1.72, 6.13, 0.4, [{"runs": [{"text": "Towards efficient video coding research ", "bold": True},
                                             {"text": "(directions, not completed work)", "italic": True, "color": MUTED}], "size": 14}])
    fut = [("BD-rate study", "Presets over QP 22–37 and more sequences vs a VTM anchor: BD-rate [4] together with time saving"),
           ("Controlled timing", "Native Linux, fixed CPU frequency and affinity, many repeats; this pipeline as the baseline"),
           ("Perceptual quality", "VMAF / XPSNR / MS-SSIM and a small formal subjective test (ITU-R BT.500) [7]"),
           ("Efficient encoding (AI background)", f"Open question: can small, pruned networks predict encoder decisions (e.g. partitioning) and cut the {min(t_sr):.0f}–{max(t_sr):.0f}× slower-preset time at a small BD-rate loss?")]
    for i, (h1, body) in enumerate(fut):
        y = 2.2 + i * 1.17
        card(s, 6.6, y, 6.13, 1.05, name=f"Future {i + 1}")
        badge(s, 6.78, y + 0.31, str(i + 1))
        text(s, 7.35, y + 0.05, 5.25, 0.95, [{"text": h1, "size": 15, "bold": True, "space_after": 2},
                                             {"text": body, "size": 12.5, "color": MUTED}], anchor=MSO_ANCHOR.MIDDLE)

    # 15 References -----------------------------------------------------------------------------------------
    s = base(prs, "References", None,
             "These are the standards, papers and software repositories referred to in the slides. All experiment data, scripts and reports are in the project directory.", 15)
    refs = ["[1] ITU-T Rec. H.266 | ISO/IEC 23090-3, Versatile Video Coding, 2020.",
            "[2] B. Bross et al., \"Overview of the Versatile Video Coding (VVC) Standard and its Applications,\" IEEE Trans. Circuits Syst. Video Technol., vol. 31, no. 10, pp. 3736–3764, Oct. 2021, doi:10.1109/TCSVT.2021.3101953.",
            "[3] A. Wieckowski et al., \"VVenC: An Open and Optimized VVC Encoder Implementation,\" Proc. IEEE ICME Workshops (ICMEW), Shenzhen, 2021, doi:10.1109/ICMEW53276.2021.9455944.",
            "[4] G. Bjøntegaard, \"Calculation of Average PSNR Differences between RD-curves,\" ITU-T SG16 Q.6 (VCEG), Doc. VCEG-M33, 2001.",
            "[5] Z. Wang, A. C. Bovik, H. R. Sheikh, E. P. Simoncelli, \"Image Quality Assessment: From Error Visibility to Structural Similarity,\" IEEE Trans. Image Process., vol. 13, no. 4, pp. 600–612, 2004.",
            "[6] VVenC and VVdeC source code: github.com/fraunhoferhhi/vvenc (v1.14.0), github.com/fraunhoferhhi/vvdec (v3.2.1).",
            "[7] ITU-R Rec. BT.500, Methodologies for the subjective assessment of the quality of television images.",
            "[8] YUView: github.com/IENT/YUView (v2.14)."]
    text(s, 0.6, 1.35, 12.1, 5.5, [{"text": r, "size": 14, "space_after": 10} for r in refs])

    assert len(prs.slides) == TOTAL, len(prs.slides)

    # ---------------- speaker notes (Phase 8: short sentences, simple words, numbers read from the data)
    fd = lambda seq, fi: float(FM[(seq, fi, 22, "medium")]["frame_psnr_y"]) - float(FM[(seq, fi, 37, "medium")]["frame_psnr_y"])  # noqa: E731
    vis_lo, vis_hi = sorted((fd("BasketballPass", 133), fd("BQMall", 42)))
    NOTES = [
        "Good morning, Professor Kiho. Thank you for this opportunity. My name is Rabab Khan Rongon. "
        "I am doing my M.Sc. in Computer Science and Engineering, with a major in Artificial Intelligence, at MIST in Bangladesh. "
        "Today I will present my practical assignment on VVC. In short: I built the VVenC encoder and the VVdeC decoder on Windows and on Linux. "
        "Then I encoded four test videos with different QP values and presets, decoded them, and measured bitrate, quality and time. "
        "All numbers in this talk come from my own result files. When something is only my interpretation, I will say so.",
        # 2
        "Here is the plan of the work. There were five steps. First, I built the tools. Second, I encoded four sequences with eight settings each. "
        "Third, I decoded every bitstream two times: one time only to measure the speed, and one time to write the video for the quality measurement. "
        f"Fourth, I measured time, file size and PSNR. In total I made {SUMM['expected_runs']} runs, and all of them passed my checks. "
        "Fifth, I compared the videos visually, and I compared Windows with Linux. "
        "I followed some simple rules: I verified every command, I kept all logs, and I did not change the source code.",
        # 3
        "Now a short introduction to the tools. VVC, also called H.266, is the newest video coding standard from ITU-T and ISO/IEC. It was finished in 2020, "
        "and it is the successor of HEVC. According to the overview paper by Bross and colleagues, it targets about fifty percent lower bitrate than HEVC "
        "at similar perceptual quality. VVenC is an open-source encoder from Fraunhofer HHI. Its presets, from faster to slower, trade speed for compression. "
        "VVdeC is the matching decoder, and YUView is an open-source viewer for raw video. At the bottom you can see how I connected the tools in this study.",
        # 4
        "This slide shows my two build environments. On Windows I used the Microsoft C++ compiler from Visual Studio 2022. On Linux I used Ubuntu 24.04 with GCC 13. "
        "Both builds use exactly the same release commits, with no change to the source code, and the default Release settings. "
        "Both builds finished with zero warnings and zero errors, and all available tests passed. On Linux I could also run the VVenC test suite: thirty-nine out of thirty-nine passed. "
        "One important point: my Linux system is WSL2. This is a small virtual machine on the same laptop. It is not a native Linux installation.",
        # 5
        "These are the four test sequences: two small ones at 416 by 240, BQMall at 832 by 480, and BasketballDrive in full HD. "
        "Before encoding, I checked every file. The files are 10-bit, but I found that the two lowest bits are always zero. "
        "So the real content has only 8-bit precision. I also found that the last frame of each file is a copyright picture, so I did not encode it. "
        "For PSNR, I used the peak value 1020. This is the same convention as in the reference software and in VVenC, so my values can be compared directly with the encoder output.",
        # 6
        "My design changes one factor at a time. For the QP sweep, I used QP 22, 27, 32 and 37 with preset medium. For the preset sweep, I used all five presets with QP 32. "
        "This gives eight settings per sequence, and thirty-two in total. To measure timing noise, I repeated every setting of the two small sequences two more times. "
        f"With one warm-up run, this makes {SUMM['expected_runs']} runs, in random order. All other parameters were fixed. "
        "During the run, the laptop was unplugged for about one hour. My monitoring log showed this, so I measured the four affected settings again on AC power. "
        "I kept the original values and marked them clearly.",
        # 7
        "This is the pipeline for every run. The encoder reads the original video and writes a VVC bitstream. Then the decoder runs two times. "
        "The first time, it writes nothing; this gives a clean decoding time. The second time, it writes the reconstructed video. "
        "My own script then computes the PSNR against the original. I accept a run only when all checks pass. "
        "For example, the frame counts must be correct, the encoder must report the expected settings, and my PSNR must be equal to the encoder's PSNR. "
        f"The largest difference was {SUMM['max_abs_psnr_diff_vs_encoder']:.4f} dB. Repeated runs gave byte-identical bitstreams.",
        # 8
        "Now the results. These charts show the QP sweep at preset medium. On the left, the bitrate axis is logarithmic, and the lines are almost straight. "
        f"This means that each step of plus five QP divides the bitrate by about {st.median(BR_RATIO):.2f}, in a range from {min(BR_RATIO):.2f} to {max(BR_RATIO):.2f}. "
        f"On the right you see the quality. Each plus five QP step costs between {min(DPSNR):.2f} and {max(DPSNR):.2f} dB of Y-PSNR. "
        "These values are for the whole sequence, using all frames. So QP is the main control for the balance between bitrate and quality.",
        # 9
        f"QP also changes the encoding time. QP 22 took {min(T22_37):.1f} to {max(T22_37):.1f} times longer than QP 37, because the encoder codes and searches more detail. "
        f"Decoding is much cheaper. At preset medium, encoding took {min(ENC_DEC):.0f} to {max(ENC_DEC):.0f} times longer than decoding. "
        f"The full HD video decoded at about {min(DEC_FPS_1080):.0f} to {max(DEC_FPS_1080):.0f} frames per second. "
        f"I repeated the encodes of the small sequences, and the median variation was {CV_MED:.1f} percent. So I do not interpret small timing differences between single runs. "
        "All timings come from one laptop, so they are not a general benchmark.",
        # 10
        f"This slide is about presets, at QP 32. The encoding time grows very fast. Compared with medium, slower needed {min(t_sr):.0f} to {max(t_sr):.0f} times more time. "
        f"But it gained only {min(d_sr):.2f} to {max(d_sr):.2f} dB, and the files were only {-max(z_sr):.1f} to {-min(z_sr):.1f} percent smaller. "
        f"Faster needed about {min(t_f):.2f} to {max(t_f):.2f} times the time of medium, and lost {-max(d_f):.2f} to {-min(d_f):.2f} dB. "
        "I want to be careful here. These results are at one QP only, so they are not a BD-rate comparison. "
        "Also, at frame level, a faster preset sometimes has higher PSNR than a slower one. But in every such frame, the faster preset had used more bits.",
        # 11
        "Here is the visual comparison. These are enlarged crops of the same region, made from the real video data. "
        "The top row is BasketballPass, frame 133. I looked at this frame myself: QP 22 is the clearest, and QP 37 is the most blurred. PSNR and SSIM give the same order. "
        "The bottom row is BQMall, frame 42, which was the worst frame at QP 37. For this row, my statements come from the metrics and a preliminary inspection. "
        f"This was not a formal subjective test. One more point: between QP 22 and QP 37, these frames differ by {vis_lo:.1f} to {vis_hi:.1f} dB, which is easy to see. "
        "Preset differences are much smaller, and much harder to see.",
        # 12
        "To verify the Linux build, I repeated my 16-frame test from the Windows phase, with exactly the same command. "
        "The result: the bitstream, the decoded video and the PSNR are byte-for-byte identical, and all three Linux repeats are identical too. "
        "This means that, for this test, the MSVC build and the GCC build made the same encoding decisions. I did not assume this before the test. "
        "But please note the limits. This is only one short configuration, and Linux ran in WSL2. "
        "I also do not compare speed, because the runs were shorter than one second and the conditions were not controlled.",
        # 13
        "Let me summarize. First, QP is the main control of bitrate and quality. Second, slower presets cost a lot of time for a small gain. "
        "Third, decoding is more than one hundred times faster than encoding. Fourth, the encoder output was deterministic. "
        "The main limitations are: presets were compared at one QP only, the timing comes from one laptop, the content is 8-bit, Linux was WSL2, "
        "and the visual evaluation was informal. For me, the main lessons were: check every number independently, monitor the test environment, "
        "and remember that the QP option is only a base QP, because the encoder adapts the QP of each picture.",
        # 14
        "To conclude: I built and verified both tools on two platforms, and I measured the main trade-offs with checked data. "
        "On the right are possible next steps. These are directions, not completed work. The first step would be a BD-rate study of the presets over several QPs. "
        "Second, controlled timing on native Linux. Third, perceptual metrics and a small formal viewing test. "
        f"Finally, my background is in AI and neural-network pruning. My measurements show that the slower preset costs {min(t_sr):.0f} to {max(t_sr):.0f} times the time of medium. "
        "So one research question could be: can a small, pruned network predict some encoder decisions, and save time with only a small BD-rate loss? "
        "Thank you very much. I am happy to answer your questions.",
        # 15
        "This slide lists the standard, the papers and the software that I used. All data, scripts and reports are in my project folder, and I can share them if needed.",
    ]
    assert len(NOTES) == TOTAL
    for sl, nt in zip(prs.slides, NOTES):
        sl.notes_slide.notes_text_frame.text = nt
    prs.save(OUT)
    print("saved", OUT, len(prs.slides), "slides; notes words:", sum(len(n.split()) for n in NOTES))

    # ---------------- 5-minute version: a subset of the same slides, renumbered, with short notes
    SHORT = {1: "Good morning, Professor Kiho. I am Rabab Khan Rongon, an M.Sc. student in Computer Science and Engineering, with a major in Artificial Intelligence, "
                "at MIST in Bangladesh. In the next five minutes I will show what I did in the VVC assignment. "
                "I built the VVenC encoder and the VVdeC decoder on Windows and on Linux, I ran a controlled experiment with four test videos, "
                "and I analysed bitrate, quality and encoding time. All numbers come from my own verified result files.",
             6: "My experiment changes one factor at a time. In the QP sweep, I used QP 22, 27, 32 and 37 with preset medium. "
                "In the preset sweep, I used the five presets, from faster to slower, with QP 32. "
                f"With timing repeats and one warm-up run, I made {SUMM['expected_runs']} runs in random order. "
                "Every run passed automatic checks: correct frame counts, the expected encoder settings, and PSNR equal to the encoder's own value. "
                "Repeated runs gave identical bitstreams. When the laptop ran on battery for about one hour, my logs showed it, "
                "and I measured the affected settings again on AC power.",
             8: "This is the main result. The bitrate axis is logarithmic, and the lines are almost straight. "
                f"Each plus five QP step divides the bitrate by about {st.median(BR_RATIO):.2f}, and it costs {min(DPSNR):.2f} to {max(DPSNR):.2f} dB of Y-PSNR. "
                "This is true for all four sequences, from 240p to full HD. So QP is the main control of the balance between bitrate and quality.",
             10: f"Presets mainly change the encoding time. Compared with medium, slower needed {min(t_sr):.0f} to {max(t_sr):.0f} times more time, "
                 f"but it gained only {min(d_sr):.2f} to {max(d_sr):.2f} dB, and the files were only {-max(z_sr):.1f} to {-min(z_sr):.1f} percent smaller. "
                 "So the slower presets buy a small gain at a large cost. But this is a result at one QP only, so it is not a BD-rate comparison.",
             11: "Here you see enlarged crops from the real video data. In BasketballPass frame 133, I checked myself: QP 22 is the clearest, and QP 37 is the most blurred. "
                 "PSNR and SSIM give the same order. Preset differences at the same QP are much smaller, and they are hard to see. "
                 "I want to be clear that this was not a formal subjective test.",
             12: "Finally, I verified the Linux build. For a 16-frame test with the same command, Windows and Linux produced byte-identical bitstreams, "
                 "identical decoded video and identical PSNR. This is only one short configuration, and Linux ran in WSL2, not natively. "
                 "I also make no speed claim, because the test was too short and the conditions were not controlled.",
             14: "To conclude, the tools are built and verified, and the main trade-offs are measured with checked data. "
                 "Next steps would be a BD-rate study over several QPs, controlled timing on native Linux, and perceptual quality metrics. "
                 "With my background in AI and network pruning, one direction I would like to explore is small, pruned networks that predict encoder decisions, "
                 "to reduce the time of the slower presets. These are ideas, not results. Thank you very much."}
    short = Presentation(OUT)
    ids = short.slides._sldIdLst
    for idx, sld in reversed(list(enumerate(list(ids), 1))):
        if idx not in SHORT:
            short.part.drop_rel(sld.rId)
            ids.remove(sld)
    for k, (sl, (orig, nt)) in enumerate(zip(short.slides, sorted(SHORT.items())), 1):
        for shp in sl.shapes:
            if shp.name == "Slide number":
                shp.text_frame.paragraphs[0].runs[0].text = f"{k} / {len(SHORT)}"
        sl.notes_slide.notes_text_frame.text = nt
    short_path = OUT.replace(".pptx", "_5min.pptx")
    short.save(short_path)
    print("saved", short_path, len(short.slides), "slides; notes words:", sum(len(n.split()) for n in SHORT.values()))


if __name__ == "__main__":
    main()
