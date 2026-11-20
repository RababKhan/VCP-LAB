"""Frame-aligned PSNR between two raw planar 4:2:0 YUV files (8-bit or 16-bit LE container).

Streams frame by frame (memory use is independent of sequence length).

Conventions reported (all from the same per-frame, per-plane MSE):
  * peak 1020 = 255 << (bitdepth-8): HM/VTM/VVenC convention (vvenc Analyze.h)  <- PRIMARY
  * peak 1023 = 2^bitdepth - 1:      FFmpeg psnr filter convention
  * "avg_of_frame_psnr": mean over frames of per-frame PSNR (HM/VTM/VVenC summary style)  <- PRIMARY
  * "psnr_of_avg_mse":   PSNR of the mean MSE over frames (FFmpeg "average" style)
  * YUV combined:
      - "yuv_411_mse":  4:1:1 pixel-count-weighted mean MSE -> PSNR (VVenC "YUV-PSNR" style)  <- PRIMARY
      - "yuv_611_psnr": (6*Y + U + V) / 8 of avg-of-frame PSNRs (JVET CTC style)

An alignment check compares reconstructed frame i with reference frame i+d for
small offsets d over the first frames; the correct alignment (d=0) must give
the highest Y-PSNR.

Usage: python psnr_yuv.py <ref.yuv> <rec.yuv> <width> <height> <bitdepth> <frames> [out_prefix]
"""
import csv
import io
import json
import math
import os
import sys

import numpy as np

ALIGN_FRAMES = 16


def open_yuv(path, w, h, bitdepth, frames):
    dtype = np.dtype("<u2") if bitdepth > 8 else np.dtype("u1")
    per_frame = w * h + 2 * (w // 2) * (h // 2)
    available = os.path.getsize(path) // (per_frame * dtype.itemsize)
    if available < frames:
        raise SystemExit(f"{path}: need {frames} frames, file holds {available}")
    return np.memmap(path, dtype=dtype, mode="r", shape=(available, per_frame))


def split(frame, w, h):
    ys, cs = w * h, (w // 2) * (h // 2)
    f = frame.astype(np.float64)
    return f[:ys], f[ys : ys + cs], f[ys + cs :]


def psnr(mse, peak):
    return math.inf if mse == 0 else 10.0 * math.log10(peak * peak / mse)


def compute(ref_path, rec_path, w, h, bd, n):
    ref = open_yuv(ref_path, w, h, bd, n)
    rec = open_yuv(rec_path, w, h, bd, n)
    mse = np.empty((n, 3))
    for i in range(n):
        for p, (a, b) in enumerate(zip(split(ref[i], w, h), split(rec[i], w, h))):
            mse[i, p] = ((a - b) ** 2).mean()

    peaks = {"peak1020": 255 << (bd - 8), "peak1023": (1 << bd) - 1}
    result = {"ref": ref_path, "rec": rec_path, "width": w, "height": h, "bitdepth": bd, "frames": n}
    per_frame_psnr = None
    for name, peak in peaks.items():
        frame_psnr = np.array([[psnr(m, peak) for m in row] for row in mse])
        avg_frame = frame_psnr.mean(axis=0)
        avg_mse = mse.mean(axis=0)
        mse_411 = (4 * avg_mse[0] + avg_mse[1] + avg_mse[2]) / 6
        result[name] = {
            "peak": peak,
            "avg_of_frame_psnr": dict(zip("YUV", map(float, avg_frame))),
            "psnr_of_avg_mse": {c: psnr(m, peak) for c, m in zip("YUV", avg_mse)},
            "yuv_411_mse": psnr(mse_411, peak),
            "yuv_611_psnr": float((6 * avg_frame[0] + avg_frame[1] + avg_frame[2]) / 8),
        }
        if name == "peak1020":
            per_frame_psnr = frame_psnr

    # Alignment check on luma: rec[i] vs ref[i+d] over the first frames.
    k = min(n, ALIGN_FRAMES)
    ys = w * h
    align = {}
    for d in range(-2, 3):
        vals = []
        for i in range(k):
            if 0 <= i + d < ref.shape[0]:
                m = ((rec[i][:ys].astype(np.float64) - ref[i + d][:ys].astype(np.float64)) ** 2).mean()
                vals.append(psnr(m, peaks["peak1020"]))
        align[str(d)] = float(np.mean(vals))
    result["alignment_check_frames"] = k
    result["alignment_check_Y_psnr_peak1020"] = align
    result["alignment_best_offset"] = int(max(align, key=align.get))
    return result, mse, per_frame_psnr


def _atomic_write(path, text):
    with open(path + ".tmp", "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(path + ".tmp", path)


def write_outputs(out_prefix, result, mse, per_frame_psnr):
    _atomic_write(out_prefix + "_psnr.json", json.dumps(result, indent=2) + "\n")
    buf = io.StringIO()
    wr = csv.writer(buf)
    wr.writerow(["frame", "mse_Y", "mse_U", "mse_V", "psnrY_1020", "psnrU_1020", "psnrV_1020"])
    for i in range(len(mse)):
        wr.writerow([i, *(f"{v:.6f}" for v in mse[i]), *(f"{v:.4f}" for v in per_frame_psnr[i])])
    _atomic_write(out_prefix + "_psnr_per_frame.csv", buf.getvalue())


def main():
    ref_path, rec_path = sys.argv[1], sys.argv[2]
    w, h, bd, n = (int(v) for v in sys.argv[3:7])
    result, mse, per_frame_psnr = compute(ref_path, rec_path, w, h, bd, n)
    print(json.dumps(result, indent=2))
    if len(sys.argv) > 7:
        write_outputs(sys.argv[7], result, mse, per_frame_psnr)


if __name__ == "__main__":
    main()
