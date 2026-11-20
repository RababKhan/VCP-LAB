"""Phase 5: visual-quality material for all 4 sequences (medium preset, QP 24/29/34/39).

Selection rule (fixed in advance, applied the same way to every sequence):
  * "typical" frame = the frame whose QP-39 medium Y-PSNR is the median over all frames;
  * "hardest" frame = the frame with the lowest QP-39 medium Y-PSNR;
  * crop = the window (about 1/4 of the width, same aspect as the picture) with the highest luma variance in the
    original frame; the same frame and crop are used for the original and all four QPs.
Metrics per selected frame (luma): Y-PSNR (peak 1020), SSIM and MS-SSIM (analysis/metrics.py). SSIM is cross-checked
against scikit-image on one frame per sequence. Sequence-level SSIM/MS-SSIM is computed on every 10th frame.
Images are script renderings of the decoded YUV files (BT.709, 10 -> 8 bit, display only), NOT YUView screenshots.
"""
import csv
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.metrics import structural_similarity as sk_ssim

import metrics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "visual/v2"
OUT.mkdir(parents=True, exist_ok=True)
DEC = ROOT / "vvdec/bin/release-static/vvdecapp.exe"
SEQS = {"BasketballPass": ("BasketballPass_416_240_50_10_420.yuv", 416, 240, 500),
        "BlowingBubbles": ("BlowingBubbles_416_240_50_10_420.yuv", 416, 240, 500),
        "BQMall": ("BQMall_832_480_60_10_420.yuv", 832, 480, 600),
        "BasketballDrive": ("BasketballDrive_1920_1080_50_10_420.yuv", 1920, 1080, 500)}
QPS = [24, 29, 34, 39]
p1 = list(csv.DictReader(open(ROOT / "results/results_raw.csv", encoding="utf-8-sig")))
p2 = list(csv.DictReader(open(ROOT / "results/results_phase2.csv", encoding="utf-8")))


def recon_for(seq, qp):
    """Path of a decoded medium-preset file; decode the bitstream again if the file was not kept."""
    for r in p1:
        if r["sequence"] == seq and r["preset"] == "medium" and int(r["qp"]) == qp and not r["repeat_of"]:
            return next((ROOT / "out").glob(f"{r['run_id']}_{seq}_QP{qp}_medium_rec_*.yuv"))
    r = next(r for r in p2 if r["sequence"] == seq and r["preset"] == "medium" and int(r["qp"]) == qp and r["kind"] == "new")
    tag = f"{r['run_id']}_{seq}_QP{qp}_medium"
    kept = list((ROOT / "out/phase2").glob(f"{tag}_rec_*.yuv"))
    if kept:
        return kept[0]
    tmp = ROOT / "out/phase2" / f"_visual_{seq}_QP{qp}_rec.yuv"
    if not tmp.exists():
        subprocess.run([str(DEC), "-b", str(ROOT / "out/phase2" / f"{tag}.266"), "-o", str(tmp), "-t", "8"], check=True,
                       capture_output=True)
    return tmp


def reader(path, w, h):
    fs = w * h * 3 // 2

    def get(i, planes=False):
        a = np.fromfile(path, dtype="<u2", count=fs, offset=i * fs * 2).astype(np.float64)
        y = a[:w * h].reshape(h, w)
        if not planes:
            return y
        u = a[w * h:w * h * 5 // 4].reshape(h // 2, w // 2)
        v = a[w * h * 5 // 4:].reshape(h // 2, w // 2)
        return y, u, v
    return get


def to_rgb(y, u, v):
    u, v = np.repeat(np.repeat(u, 2, 0), 2, 1), np.repeat(np.repeat(v, 2, 0), 2, 1)
    yy, cb, cr = (y / 4 - 16) * 255 / 219, (u / 4 - 128) * 255 / 224, (v / 4 - 128) * 255 / 224
    rgb = np.dstack([yy + 1.5748 * cr, yy - 0.1873 * cb - 0.4681 * cr, yy + 1.8556 * cb])
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 20)
small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 17)
rows, seqrows, info = [], [], {}
for seq, (f, w, h, n) in SEQS.items():
    orig = reader(ROOT / "dataset" / f, w, h)
    recs = {q: reader(recon_for(seq, q), w, h) for q in QPS}
    p39 = [metrics.psnr(orig(i), recs[39](i)) for i in range(n)]
    order = sorted(range(n), key=lambda i: p39[i])
    picks = {"typical": order[n // 2], "hardest": order[0]}
    cw = (w // 4) // 8 * 8
    ch = int(round(cw * h / w / 8)) * 8
    info[seq] = {}
    for kind, fr in picks.items():
        yo, uo, vo = orig(fr, True)
        _, cx, cy = max((yo[y:y + ch, x:x + cw].var(), x, y) for y in range(0, h - ch + 1, 8) for x in range(0, w - cw + 1, 8))
        scale = max(1, 416 // cw)
        tiles = [("Original", (yo, uo, vo), None)]
        for q in QPS:
            yr, ur, vr = recs[q](fr, True)
            s, _ = metrics.ssim(yo, yr)
            ms = metrics.ms_ssim(yo, yr)
            p = metrics.psnr(yo, yr)
            rows.append(dict(sequence=seq, frame_kind=kind, frame=fr, qp=q, preset="medium", y_psnr=round(p, 3),
                             ssim=round(s, 5), ms_ssim=round(ms, 5), crop_xywh=f"{cx},{cy},{cw},{ch}"))
            tiles.append((f"QP {q}", (yr, ur, vr), (p, s, ms)))
        if kind == "typical":                          # cross-check own SSIM with scikit-image at QP 39
            ref = sk_ssim(yo, recs[39](fr), data_range=1023, gaussian_weights=True, sigma=1.5, use_sample_covariance=False)
            info[seq]["ssim_crosscheck_qp39"] = {"own": rows[-1]["ssim"], "scikit_image": round(float(ref), 5)}
        tw, th = cw * scale, ch * scale
        strip = Image.new("RGB", (5 * (tw + 14) - 14, th + 74), "white")
        d = ImageDraw.Draw(strip)
        for k, (lab, (y, u, v), m) in enumerate(tiles):
            crop = to_rgb(y, u, v).crop((cx, cy, cx + cw, cy + ch)).resize((tw, th), Image.NEAREST)
            name = f"{seq}_f{fr}_{kind}_{'original' if k == 0 else lab.replace(' ', '')}_crop.png"
            crop.save(OUT / name)
            strip.paste(crop, (k * (tw + 14), 0))
            d.text((k * (tw + 14), th + 6), lab, font=font, fill=(38, 50, 56))
            if m:
                d.text((k * (tw + 14), th + 30), f"PSNR {m[0]:.2f} dB  SSIM {m[1]:.3f}", font=small, fill=(96, 125, 139))
                d.text((k * (tw + 14), th + 50), f"MS-SSIM {m[2]:.4f}", font=small, fill=(96, 125, 139))
        strip.save(OUT / f"{seq}_f{fr}_{kind}_strip.png")
        full = to_rgb(yo, uo, vo)
        ImageDraw.Draw(full).rectangle([cx, cy, cx + cw, cy + ch], outline=(232, 113, 10), width=max(2, w // 300))
        full.save(OUT / f"{seq}_f{fr}_{kind}_full_with_crop.png")
        info[seq][kind] = {"frame_0based": fr, "crop_xywh": [cx, cy, cw, ch], "strip": f"{seq}_f{fr}_{kind}_strip.png"}
    for q in QPS:                                      # sequence-level SSIM on every 10th frame
        s_, m_ = [], []
        for i in range(0, n, 10):
            a, b = orig(i), recs[q](i)
            s_.append(metrics.ssim(a, b)[0])
            m_.append(metrics.ms_ssim(a, b))
        seqrows.append(dict(sequence=seq, qp=q, preset="medium", frames_sampled=len(s_), ssim_mean=round(float(np.mean(s_)), 5),
                            ms_ssim_mean=round(float(np.mean(m_)), 5)))
    print(seq, json.dumps(info[seq]), flush=True)

for name, data in (("visual_frame_metrics.csv", rows), ("visual_sequence_ssim.csv", seqrows)):
    with open(ROOT / "results" / name, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, list(data[0].keys()))
        wr.writeheader()
        wr.writerows(data)
(OUT / "selection.json").write_text(json.dumps({"rule": __doc__.strip(), "sequences": info}, indent=2), encoding="utf-8")
print("done")
