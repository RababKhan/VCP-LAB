"""Phase 7: render presentation assets from the YUV data with the same display conversion as Phase 6
(scripts/render_visual_crops.to_rgb): dataset thumbnails (frame 100 of each original) and individual enlarged crop
panels (same crop windows as visual/rendered/crops.json, pixel-repetition zoom). Output: presentation/assets/.

Usage: python make_deck_assets.py
"""
import json
import os
import sys

import numpy as np

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from render_visual_crops import read_frame, to_rgb  # noqa: E402

OUT = os.path.join(ROOT, "presentation", "assets")
SEQS = [("BasketballPass", "BasketballPass_416_240_50_10_420.yuv", 416, 240),
        ("BlowingBubbles", "BlowingBubbles_416_240_50_10_420.yuv", 416, 240),
        ("BQMall", "BQMall_832_480_60_10_420.yuv", 832, 480),
        ("BasketballDrive", "BasketballDrive_1920_1080_50_10_420.yuv", 1920, 1080)]
FRAME = 100
CROPS = [("BasketballPass", "typical_qp32_medium", [(22, "medium"), (32, "medium"), (37, "medium")]),
         ("BQMall", "worst_qp37_medium", [(22, "medium"), (32, "medium"), (37, "medium")]),
         ("BasketballPass", "worst_qp37_medium", [(32, "faster"), (32, "medium"), (32, "slower")])]


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn, w, h in SEQS:
        img = Image.fromarray(to_rgb(*read_frame(os.path.join(ROOT, "dataset", fn), w, h, FRAME)))
        if w > 832:
            img = img.resize((832, int(832 * h / w)), Image.LANCZOS)  # thumbnail size only; noted on the slide
        p = os.path.join(OUT, f"dataset_{name}_frame{FRAME}.png")
        img.save(p)
        print(p, img.size)
    man = json.load(open(os.path.join(ROOT, "visual", "sample_manifest.json"), encoding="utf-8"))["samples"]
    crops = json.load(open(os.path.join(ROOT, "visual", "rendered", "crops.json"), encoding="utf-8"))
    for seq, rule, variants in CROPS:
        c = crops[f"{seq}/{rule}"]
        smp = {(m["qp"], m["preset"]) if m["role"] != "original" else None: m for m in man if m["sequence"] == seq}
        w, h = smp[None]["width"], smp[None]["height"]
        for key in [None] + variants:
            rgb = to_rgb(*read_frame(os.path.join(ROOT, smp[key]["file"]), w, h, c["frame_index"]))
            cr = rgb[c["crop_y"]:c["crop_y"] + c["crop_h"], c["crop_x"]:c["crop_x"] + c["crop_w"]]
            z = c["zoom"]
            tag = "original" if key is None else f"QP{key[0]}_{key[1]}"
            p = os.path.join(OUT, f"crop_{seq}_f{c['frame_index']}_{tag}.png")
            Image.fromarray(np.repeat(np.repeat(cr, z, 0), z, 1)).save(p)
            print(p)


if __name__ == "__main__":
    main()
