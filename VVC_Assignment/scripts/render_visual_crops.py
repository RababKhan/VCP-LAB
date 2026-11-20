"""Phase 6: render side-by-side comparison images from the actual YUV data (not YUView screenshots).

For each sequence and each frame in visual/frame_selection.json:
  * QP set     : Original | QP 22 | QP 32 | QP 37          (preset medium)
  * preset set : Original | faster | medium | slower       (QP 32)
as (a) full frames and (b) one zoomed crop, at the same position in every panel.

Crop position rule: the window (CROP_W x CROP_H, on a 8-pixel grid) with the largest luma squared error of
QP 37 / medium in that frame, i.e. where the strongest degradation of the set is expected.

Display conversion (identical for every panel): 10-bit -> 8-bit by >> 2; YCbCr BT.709 limited range -> sRGB;
chroma upsampled by pixel repetition; zoom by pixel repetition (no smoothing, so coding artefacts are not
hidden). The sequences carry no colour metadata, so BT.709 is an assumption; it affects all panels equally.

Outputs: visual/rendered/*.png, visual/rendered/crops.json

Usage: python render_visual_crops.py
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIS = os.path.join(ROOT, "visual")
OUT = os.path.join(VIS, "rendered")
CROP = {"BasketballPass": (104, 80, 4), "BQMall": (160, 120, 3)}  # crop w, h, zoom
SETS = {"qp": [("Original", None), ("QP 22 medium", (22, "medium")), ("QP 32 medium", (32, "medium")),
               ("QP 37 medium", (37, "medium"))],
        "preset": [("Original", None), ("QP 32 faster", (32, "faster")), ("QP 32 medium", (32, "medium")),
                   ("QP 32 slower", (32, "slower"))]}


def read_frame(path, w, h, idx):
    fs = w * h + 2 * (w // 2) * (h // 2)
    a = np.fromfile(path, dtype="<u2", count=fs, offset=idx * fs * 2).astype(np.float64)
    y = a[:w * h].reshape(h, w)
    u = a[w * h:w * h + (w // 2) * (h // 2)].reshape(h // 2, w // 2)
    v = a[w * h + (w // 2) * (h // 2):].reshape(h // 2, w // 2)
    return y, u, v


def to_rgb(y, u, v):
    y8, u8, v8 = y / 4.0, np.repeat(np.repeat(u / 4.0, 2, 0), 2, 1), np.repeat(np.repeat(v / 4.0, 2, 0), 2, 1)
    yl, cb, cr = (y8 - 16) / 219.0, (u8 - 128) / 224.0, (v8 - 128) / 224.0
    r = yl + 1.5748 * cr
    g = yl - 0.1873 * cb - 0.4681 * cr
    b = yl + 1.8556 * cb
    return (np.clip(np.stack([r, g, b], -1), 0, 1) * 255 + 0.5).astype(np.uint8)


def worst_window(y_ref, y_rec, cw, ch):
    err = (y_ref - y_rec) ** 2
    best, pos = -1, (0, 0)
    H, W = err.shape
    integ = np.pad(err.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    for yy in range(0, H - ch + 1, 8):
        for xx in range(0, W - cw + 1, 8):
            s = integ[yy + ch, xx + cw] - integ[yy, xx + cw] - integ[yy + ch, xx] + integ[yy, xx]
            if s > best:
                best, pos = s, (xx, yy)
    return pos


def panel_strip(images, labels, sub, title, footer):
    font = ImageFont.load_default()
    pad, lab_h = 8, 34
    w, h = images[0].width, images[0].height
    top = 22
    canvas = Image.new("RGB", (len(images) * (w + pad) + pad, top + h + lab_h + 18), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    d.text((pad, 5), title, fill=(11, 11, 11), font=font)
    for i, (im, lab, s) in enumerate(zip(images, labels, sub)):
        x = pad + i * (w + pad)
        canvas.paste(im, (x, top))
        d.text((x, top + h + 4), lab, fill=(11, 11, 11), font=font)
        d.text((x, top + h + 18), s, fill=(82, 81, 78), font=font)
    d.text((pad, top + h + lab_h + 2), footer, fill=(120, 120, 120), font=font)
    return canvas


def main():
    os.makedirs(OUT, exist_ok=True)
    man = json.load(open(os.path.join(VIS, "sample_manifest.json"), encoding="utf-8"))["samples"]
    sel = json.load(open(os.path.join(VIS, "frame_selection.json"), encoding="utf-8"))
    crops = {}
    for seq, info in sel.items():
        smp = {(m["qp"], m["preset"]) if m["role"] != "original" else None: m for m in man if m["sequence"] == seq}
        w, h = smp[None]["width"], smp[None]["height"]
        cw, ch, zoom = CROP[seq]
        for fname, idx in info["frames"].items():
            frames = {k: read_frame(os.path.join(ROOT, m["file"]), w, h, idx) for k, m in smp.items()}
            x0, y0 = worst_window(frames[None][0], frames[(37, "medium")][0], cw, ch)
            crops[f"{seq}/{fname}"] = {"frame_index": idx, "crop_x": x0, "crop_y": y0, "crop_w": cw, "crop_h": ch,
                                       "zoom": zoom}
            for set_name, members in SETS.items():
                full_imgs, crop_imgs, labels, subs = [], [], [], []
                for lab, key in members:
                    rgb = to_rgb(*frames[key])
                    full_imgs.append(Image.fromarray(rgb))
                    c = rgb[y0:y0 + ch, x0:x0 + cw]
                    crop_imgs.append(Image.fromarray(np.repeat(np.repeat(c, zoom, 0), zoom, 1)))
                    labels.append(lab)
                    if key is None:
                        subs.append(f"{os.path.basename(smp[None]['file'])[:22]}")
                    else:
                        fy = info["per_frame_y_psnr"][f"QP{key[0]}_{key[1]}"][fname]
                        subs.append(f"frame Y {fy:.2f} dB | seq {smp[key]['bitstream_bytes']:,} B")
                foot = (f"rendered from YUV data: 10->8 bit, BT.709 limited->sRGB, pixel-repeat chroma/zoom | "
                        f"frame {idx}")
                base = f"{seq}_{set_name}_frame{idx:03d}_{fname}"
                panel_strip(full_imgs, labels, subs, f"{seq}  frame {idx} ({fname})  full frame", foot).save(
                    os.path.join(OUT, base + "_full.png"))
                panel_strip(crop_imgs, labels, subs,
                            f"{seq}  frame {idx} ({fname})  crop x={x0} y={y0} {cw}x{ch}, zoom {zoom}x", foot).save(
                    os.path.join(OUT, base + "_crop.png"))
    with open(os.path.join(OUT, "crops.json"), "w", encoding="utf-8") as f:
        json.dump(crops, f, indent=2)
    print(json.dumps(crops, indent=1))
    print(sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
