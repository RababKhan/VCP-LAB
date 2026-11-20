"""Inspect a raw YUV file without trusting its filename (streams frame by frame).

Checks: exact size and SHA256, frame count / trailing bytes under several layout
hypotheses, whether the data is really 16-bit little-endian 10-bit samples,
per-plane value ranges, 8-bit-in-10-bit detection, spatial structure (correct
width), and temporal continuity (outlier frames such as appended title cards).

Usage: python inspect_yuv.py <file.yuv> <width> <height> [out.json]
"""
import hashlib
import json
import os
import sys

import numpy as np


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def main():
    path, w, h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    out_json = sys.argv[4] if len(sys.argv) > 4 else None
    size = os.path.getsize(path)
    r = {"file": os.path.basename(path), "size_bytes": size, "sha256": sha256(path), "width": w, "height": h}

    # Frame count under each candidate layout (bytes per frame).
    layouts = {
        "yuv420p10le": w * h * 3 // 2 * 2,
        "yuv420p (8-bit)": w * h * 3 // 2,
        "yuv444p (8-bit)": w * h * 3,
        "yuv422p10le": w * h * 2 * 2,
    }
    r["layouts"] = {k: {"bytes_per_frame": b, "frames": size // b, "trailing_bytes": size % b} for k, b in layouts.items()}

    fb = layouts["yuv420p10le"]
    n = size // fb
    ys, cs = w * h, (w // 2) * (h // 2)
    mm = np.memmap(path, dtype="<u2", mode="r", shape=(n, fb // 2))

    hi_le3 = 0
    hi_max = 0
    lsb_zero = 0
    pmin = [1 << 16] * 3
    pmax = [0] * 3
    psum = [0.0] * 3
    ymeans, tmad = [], []
    prev_y = None
    for i in range(n):
        f = np.asarray(mm[i])
        hi = f >> 8  # high byte of each little-endian 16-bit word
        hi_le3 += int(np.count_nonzero(hi <= 3))
        hi_max = max(hi_max, int(hi.max()))
        lsb_zero += int(np.count_nonzero((f & 3) == 0))
        for p, plane in enumerate((f[:ys], f[ys : ys + cs], f[ys + cs :])):
            pmin[p] = min(pmin[p], int(plane.min()))
            pmax[p] = max(pmax[p], int(plane.max()))
            psum[p] += float(plane.sum())
        y = f[:ys].astype(np.int32).reshape(h, w)
        ymeans.append(float(y.mean()))
        if prev_y is not None:
            tmad.append(float(np.abs(y - prev_y).mean()))
        else:
            # Correct width => vertically adjacent rows are about as similar as horizontal neighbours.
            r["frame0_mean_abs_vertical_diff"] = round(float(np.abs(np.diff(y, axis=0)).mean()), 2)
            r["frame0_mean_abs_horizontal_diff"] = round(float(np.abs(np.diff(y, axis=1)).mean()), 2)
        prev_y = y

    total = n * (fb // 2)
    r["frames_10bit_420"] = n
    r["high_byte_le_3_fraction"] = hi_le3 / total
    r["high_byte_max"] = hi_max
    counts = (ys, cs, cs)
    r["planes_10bit"] = {
        c: {"min": pmin[p], "max": pmax[p], "mean": round(psum[p] / (counts[p] * n), 2)} for p, c in enumerate("YUV")
    }
    # 1.0 means every sample has its two LSBs at zero, i.e. 8-bit content shifted left by 2.
    r["fraction_samples_lsb2_zero"] = lsb_zero / total

    t = np.array(tmad)
    med = float(np.median(t))
    r["temporal_mad"] = {
        "mean": round(float(t.mean()), 3),
        "median": round(med, 3),
        "max": round(float(t.max()), 3),
        "max_at_pair": [int(t.argmax()), int(t.argmax()) + 1],
        "zero_diff_pairs": [[int(i), int(i) + 1] for i in np.where(t == 0)[0]],
        # Transitions much larger than typical motion: scene cuts or appended non-video frames.
        "outlier_pairs_gt_5x_median": [[int(i), int(i) + 1, round(float(t[i]), 2)] for i in np.where(t > 5 * med)[0]],
    }
    r["luma_mean_first_last"] = {"first": round(ymeans[0], 2), "second_last": round(ymeans[-2], 2), "last": round(ymeans[-1], 2)}

    text = json.dumps(r, indent=2)
    print(text)
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
