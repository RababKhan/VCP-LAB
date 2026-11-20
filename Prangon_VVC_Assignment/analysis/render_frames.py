"""Phase 5 support: render the SAME frame and the SAME crop from the original and the decoded QP 24/29/34/39
(medium preset) files, so they can be compared side by side. These are script renderings of the decoded YUV
data (BT.709 limited-range conversion, 10-bit -> 8-bit, for display only). They are NOT YUView screenshots.

Frame choice (objective, decided before looking at the images): the frame whose QP 39 medium Y-PSNR is the median
of all frames. Crop choice: the 208x120 window with the highest luma variance in the original frame.
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SEQ = sys.argv[1] if len(sys.argv) > 1 else "BQMall"
rows = [r for r in csv.DictReader(open(ROOT / "results/results_raw.csv", encoding="utf-8-sig"))
        if r["sequence"] == SEQ and r["preset"] == "medium" and not r["repeat_of"] and r["status"] == "OK"]
W, H, N = int(rows[0]["width"]), int(rows[0]["height"]), int(rows[0]["frames"])
FS = W * H * 3 // 2                     # samples per frame
orig = ROOT / "dataset" / {"BQMall": "BQMall_832_480_60_10_420.yuv",
                           "BlowingBubbles": "BlowingBubbles_416_240_50_10_420.yuv"}[SEQ]
recs = {}
for r in rows:
    tag = f'{r["run_id"]}_{SEQ}_QP{r["qp"]}_medium'
    recs[int(r["qp"])] = next((ROOT / "out").glob(f"{tag}_rec_*.yuv"))


def frame(path, i):
    a = np.fromfile(path, dtype="<u2", count=FS, offset=i * FS * 2).astype(np.float64)
    y = a[:W * H].reshape(H, W)
    u = a[W * H:W * H + W * H // 4].reshape(H // 2, W // 2)
    v = a[W * H + W * H // 4:].reshape(H // 2, W // 2)
    return y, u, v


def psnr(a, b):
    mse = np.mean((a - b) ** 2)
    return 999.99 if mse == 0 else 10 * math.log10(1020.0 ** 2 / mse)


# 1) frame with the median QP-39 Y-PSNR
ypsnr39 = [psnr(frame(orig, i)[0], frame(recs[39], i)[0]) for i in range(N)]
order = sorted(range(N), key=lambda i: ypsnr39[i])
FR = order[N // 2]
# 2) crop with the highest luma variance
yo = frame(orig, FR)[0]
CW, CHh = (208, 120) if W >= 800 else (104, 60)
best = max(((yo[y:y + CHh, x:x + CW].var(), x, y) for y in range(0, H - CHh + 1, 8) for x in range(0, W - CW + 1, 8)))
_, CX, CY = best


def to_rgb(y, u, v):
    y8, u8, v8 = y / 4.0, np.repeat(np.repeat(u, 2, 0), 2, 1) / 4.0, np.repeat(np.repeat(v, 2, 0), 2, 1) / 4.0
    yy, cb, cr = (y8 - 16) * 255 / 219, (u8 - 128) * 255 / 224, (v8 - 128) * 255 / 224
    r = yy + 1.5748 * cr
    g = yy - 0.1873 * cb - 0.4681 * cr
    b = yy + 1.8556 * cb
    return Image.fromarray(np.clip(np.dstack([r, g, b]), 0, 255).astype(np.uint8))


out = ROOT / "visual"
out.mkdir(exist_ok=True)
info = {"sequence": SEQ, "frame_index_0based": FR, "crop_xywh": [CX, CY, CW, CHh], "rule": __doc__.strip(), "tiles": []}
tiles = [("Original", orig)] + [(f"QP {q} · medium", recs[q]) for q in (24, 29, 34, 39)]
scale = 2 if W >= 800 else 4
font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
tw, th = CW * scale, CHh * scale
strip = Image.new("RGB", (len(tiles) * (tw + 16) - 16, th + 64), "white")
for k, (label, path) in enumerate(tiles):
    y, u, v = frame(path, FR)
    img = to_rgb(y, u, v)
    crop = img.crop((CX, CY, CX + CW, CY + CHh)).resize((tw, th), Image.NEAREST)
    name = "original" if k == 0 else f"QP{label.split()[1]}_medium"
    crop.save(out / f"{SEQ}_f{FR}_{name}_crop.png")
    if k == 0:
        full = img.copy()
        ImageDraw.Draw(full).rectangle([CX, CY, CX + CW, CY + CHh], outline=(232, 113, 10), width=3)
        full.save(out / f"{SEQ}_f{FR}_original_full_with_crop.png")
    fp = None if k == 0 else round(psnr(yo, y), 2)
    info["tiles"].append({"label": label, "file": f"{SEQ}_f{FR}_{name}_crop.png", "frame_y_psnr_db": fp})
    x0 = k * (tw + 16)
    strip.paste(crop, (x0, 0))
    d = ImageDraw.Draw(strip)
    d.text((x0, th + 8), label, font=font, fill=(38, 50, 56))
    if fp:
        d.text((x0, th + 36), f"frame Y-PSNR {fp:.2f} dB", font=small, fill=(96, 125, 139))
strip.save(out / f"{SEQ}_f{FR}_qp_strip.png")
(out / f"{SEQ}_frame_selection.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
print(json.dumps(info, indent=1))
