"""Independent PSNR check for 10-bit 4:2:0 YUV files.

Usage:  py psnr_check.py ORIGINAL.yuv DECODED.yuv WIDTH HEIGHT FRAMES

PSNR uses peak 1020 (= 255 * 4, the HM/VTM/VVenC convention for 10-bit). It is computed per frame and
averaged over frames, the same way the encoder reports its sequence PSNR. Prints one JSON line.
"""
import json
import math
import os
import sys

import numpy as np

PEAK = 1020.0


def psnr(mse):
    return 999.99 if mse == 0 else 10.0 * math.log10(PEAK * PEAK / mse)


def main():
    if len(sys.argv) != 6:
        sys.exit(__doc__)
    orig, dec = sys.argv[1], sys.argv[2]
    w, h, frames = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    cw, ch = w // 2, h // 2
    plane_sizes = [w * h, cw * ch, cw * ch]          # samples per plane (Y, U, V)
    frame_samples = sum(plane_sizes)
    frame_bytes = frame_samples * 2                  # 10-bit samples are stored in 2 bytes (little-endian)

    dec_frames = os.path.getsize(dec) / frame_bytes
    if dec_frames < frames:
        sys.exit(f"decoded file has only {dec_frames:.2f} frames, expected {frames}")

    sums = {"Y": 0.0, "U": 0.0, "V": 0.0}
    with open(orig, "rb") as fo, open(dec, "rb") as fd:
        for _ in range(frames):
            a = np.frombuffer(fo.read(frame_bytes), dtype="<u2").astype(np.int32)
            b = np.frombuffer(fd.read(frame_bytes), dtype="<u2").astype(np.int32)
            start = 0
            for name, n in zip("YUV", plane_sizes):
                d = a[start:start + n] - b[start:start + n]
                sums[name] += psnr(float(np.mean(d * d)))
                start += n
    out = {k: round(v / frames, 4) for k, v in sums.items()}
    out["frames_checked"] = frames
    out["decoded_frames_in_file"] = dec_frames
    print(json.dumps(out))


if __name__ == "__main__":
    main()
