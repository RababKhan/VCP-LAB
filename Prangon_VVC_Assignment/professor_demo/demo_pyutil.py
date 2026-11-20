"""Small helpers shared by demo_results.py, demo_bdrate.py and demo_crossplatform.py.
The demo scripts only READ the experiment files; everything they write goes to professor_demo/output/."""
import csv
import hashlib
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True                       # never write .pyc cache files into the experiment's analysis/ folder
ROOT = Path(__file__).resolve().parents[1]           # D:\Korea\Prangon_VVC_Assignment
DEMO = Path(__file__).resolve().parent
OUT = DEMO / "output"
RES = ROOT / "results"
DECK = ROOT / "presentation" / "VVC_Assignment_Sadab_Khan_Prangon_FINAL.pptx"
sys.path.insert(0, str(ROOT / "analysis"))            # to import the experiment's own metrics.py (unchanged)

_ASCII = {"×": "x", "÷": "/", "−": "-", "–": "-", "—": "-", "≥": ">=", "≤": "<=", "·": "|", "●": "*", "Δ": "delta ",
          "→": "->", "✓": "yes", "✗": "NO", "\u00a0": " "}


def ascii_text(s):
    """The Windows console cannot print some symbols; replace them with plain ASCII."""
    s = str(s)
    for a, b in _ASCII.items():
        s = s.replace(a, b)
    return s.encode("ascii", "replace").decode()


class Report:
    """Prints to the screen and keeps the same text for a Markdown report in professor_demo/output/."""

    def __init__(self, name):
        OUT.mkdir(exist_ok=True)
        self.path = OUT / f"{name}_{datetime.now():%Y%m%d_%H%M%S}.md"
        self.lines = []
        self.checks = []

    def h(self, text):
        print("\n=== " + ascii_text(text))
        self.lines += ["", "## " + text, ""]

    def p(self, text=""):
        print("  " + ascii_text(text))
        self.lines.append(text + "  ")

    def check(self, what, ok):
        self.checks.append((what, bool(ok)))
        tag = "[MATCH]" if ok else "[DIFFERENT]"
        print(f"  {tag} {ascii_text(what)}")
        self.lines.append(f"**{tag}** {what}  ")

    def table(self, header, rows):
        widths = [max(len(ascii_text(x)) for x in col) for col in zip(header, *rows)]
        for r in [header] + rows:
            print("  " + "  ".join(ascii_text(c).ljust(w) for c, w in zip(r, widths)))
        self.lines += ["", "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
        self.lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
        self.lines.append("")

    def save(self, title):
        n_bad = sum(1 for _, ok in self.checks if not ok)
        summary = f"{len(self.checks)} checks, {len(self.checks) - n_bad} match, {n_bad} different"
        head = [f"# {title}", "", f"Generated {datetime.now():%Y-%m-%d %H:%M:%S} by professor_demo/{Path(sys.argv[0]).name}. "
                "Only saved experiment files were read; nothing in results/, logs/, out/ or presentation/ was changed.",
                "", f"**Result: {summary}**"]
        self.path.write_text("\n".join(head + self.lines) + "\n", encoding="utf-8")
        print(f"\n  RESULT: {summary}")
        print(f"  Report saved: {self.path}")
        return n_bad


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


def chart_points(chart):
    """(series name, [x values], [y values]) for each series of a native chart, read from the chart XML in the deck."""
    out = []
    for ser in chart._chartSpace.xpath(".//c:ser"):
        name = "".join(ser.xpath("./c:tx//c:v/text()"))
        xs = [float(v) for v in ser.xpath("./c:xVal//c:v/text()")] or ser.xpath("./c:cat//c:v/text()")
        ys = [float(v) for v in ser.xpath("./c:yVal//c:v/text() | ./c:val//c:v/text()")]
        out.append((name, xs, ys))
    return out
