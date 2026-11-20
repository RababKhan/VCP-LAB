"""Metric functions for Sadab's analysis, with self-tests (run this file directly).

BD-rate (Bjontegaard delta rate):
  * Method: log10(bitrate) as a function of PSNR, interpolated with piecewise cubic Hermite (PCHIP) and integrated
    over the overlapping PSNR interval. This is the piecewise-cubic variant used in current JVET/VCEG practice
    (instead of the original VCEG-M33 cubic polynomial). The VCEG-M33 polynomial version is also provided as a
    cross-check.
  * BD-rate = (10^(mean log-rate difference) - 1) * 100 %. Negative = the test needs fewer bits for the same quality.
  * Validity rules, checked before computing: 4 points per curve; PSNR strictly increasing with bitrate on both
    curves; the overlapping PSNR interval must cover at least 50 % of the smaller curve's PSNR range. Otherwise the
    result is reported as unavailable.

SSIM / MS-SSIM on the luma plane:
  * SSIM: Wang et al. 2004, 11x11 Gaussian window (sigma 1.5), K1 0.01, K2 0.03, data range 1023 (10-bit).
  * MS-SSIM: Wang et al. 2003, 5 scales, weights (0.0448, 0.2856, 0.3001, 0.2363, 0.1333), 2x2 average down-sampling.
"""
import math

import numpy as np
from scipy.integrate import quad
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter

MIN_OVERLAP = 0.5


def bd_check(r1, p1, r2, p2):
    for r, p in ((r1, p1), (r2, p2)):
        if len(r) != 4 or len(p) != 4:
            return "needs 4 points per curve"
        o = np.argsort(r)
        if np.any(np.diff(np.asarray(p)[o]) <= 0):
            return "PSNR not strictly increasing with bitrate"
    lo, hi = max(min(p1), min(p2)), min(max(p1), max(p2))
    if hi <= lo:
        return "no overlapping PSNR range"
    frac = (hi - lo) / min(max(p1) - min(p1), max(p2) - min(p2))
    if frac < MIN_OVERLAP:
        return f"overlap only {frac:.0%} of the smaller PSNR range (< {MIN_OVERLAP:.0%})"
    return None


def overlap_fraction(p1, p2):
    lo, hi = max(min(p1), min(p2)), min(max(p1), max(p2))
    return max(0.0, hi - lo) / min(max(p1) - min(p1), max(p2) - min(p2))


def bd_rate(r1, p1, r2, p2, method="pchip"):
    """BD-rate of test (r2, p2) against anchor (r1, p1), in percent. Returns (value or None, reason)."""
    why = bd_check(r1, p1, r2, p2)
    if why:
        return None, why
    lo, hi = max(min(p1), min(p2)), min(max(p1), max(p2))
    vals = []
    for r, p in ((r1, p1), (r2, p2)):
        o = np.argsort(p)
        x, y = np.asarray(p, float)[o], np.log10(np.asarray(r, float)[o])
        if method == "pchip":
            f = PchipInterpolator(x, y)
            vals.append(quad(f, lo, hi)[0])
        else:                                        # VCEG-M33: 3rd-order polynomial fit
            c = np.polyint(np.polyfit(x, y, 3))
            vals.append(np.polyval(c, hi) - np.polyval(c, lo))
    avg = (vals[1] - vals[0]) / (hi - lo)
    return (10 ** avg - 1) * 100, None


def bd_psnr(r1, p1, r2, p2):
    """BD-PSNR (dB) of test against anchor, PCHIP over the overlapping log-rate interval."""
    l1, l2 = np.log10(r1), np.log10(r2)
    lo, hi = max(min(l1), min(l2)), min(max(l1), max(l2))
    if hi <= lo:
        return None
    v = []
    for l, p in ((l1, p1), (l2, p2)):
        o = np.argsort(l)
        v.append(quad(PchipInterpolator(np.asarray(l)[o], np.asarray(p, float)[o]), lo, hi)[0])
    return (v[1] - v[0]) / (hi - lo)


def ssim(a, b, L=1023.0, sigma=1.5):
    a, b = a.astype(np.float64), b.astype(np.float64)
    C1, C2 = (0.01 * L) ** 2, (0.03 * L) ** 2
    t = 3.5                                           # truncate -> 11x11 window for sigma 1.5 (radius 5)
    mu1, mu2 = gaussian_filter(a, sigma, truncate=t), gaussian_filter(b, sigma, truncate=t)
    s11 = gaussian_filter(a * a, sigma, truncate=t) - mu1 * mu1
    s22 = gaussian_filter(b * b, sigma, truncate=t) - mu2 * mu2
    s12 = gaussian_filter(a * b, sigma, truncate=t) - mu1 * mu2
    m = ((2 * mu1 * mu2 + C1) * (2 * s12 + C2)) / ((mu1 ** 2 + mu2 ** 2 + C1) * (s11 + s22 + C2))
    cs = (2 * s12 + C2) / (s11 + s22 + C2)
    r = 5                                             # ignore the border where the window is incomplete
    return float(m[r:-r, r:-r].mean()), float(cs[r:-r, r:-r].mean())


def ms_ssim(a, b, L=1023.0):
    w = np.array([0.0448, 0.2856, 0.3001, 0.2363, 0.1333])
    a, b = a.astype(np.float64), b.astype(np.float64)
    mcs = []
    for k in range(5):
        s, cs = ssim(a, b, L)
        if k < 4:
            mcs.append(max(cs, 1e-12))
            h, wd = (a.shape[0] // 2) * 2, (a.shape[1] // 2) * 2
            a = a[:h, :wd].reshape(h // 2, 2, wd // 2, 2).mean(axis=(1, 3))
            b = b[:h, :wd].reshape(h // 2, 2, wd // 2, 2).mean(axis=(1, 3))
    return float(np.prod(np.array(mcs) ** w[:4]) * max(s, 1e-12) ** w[4])


def psnr(a, b, peak=1020.0):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return 999.99 if mse == 0 else 10 * math.log10(peak * peak / mse)


if __name__ == "__main__":
    r = np.array([100.0, 200.0, 400.0, 800.0]); p = np.array([30.0, 33.0, 36.0, 39.0])
    for m in ("pchip", "poly"):
        print(m, "identical:", round(bd_rate(r, p, r, p, m)[0], 6), "| rate x0.9:", round(bd_rate(r, p, r * 0.9, p, m)[0], 6),
              "| rate x1.2:", round(bd_rate(r, p, r * 1.2, p, m)[0], 6))
    print("BD-PSNR, +0.5 dB shift:", round(bd_psnr(r, p, r, p + 0.5), 6))
    print("no-overlap case:", bd_rate(r, p, r, p + 20)[1])
    rng = np.random.default_rng(0)
    img = rng.integers(0, 1024, (240, 416)).astype(float)
    img = gaussian_filter(img, 2)
    print("SSIM identical:", ssim(img, img)[0], "MS-SSIM identical:", round(ms_ssim(img, img), 6))
    noisy = img + rng.normal(0, 20, img.shape)
    try:
        from skimage.metrics import structural_similarity as sk
        ref = sk(img, noisy, data_range=1023, gaussian_weights=True, sigma=1.5, use_sample_covariance=False)
        print(f"SSIM noisy: own {ssim(img, noisy)[0]:.6f} vs scikit-image {ref:.6f}")
    except ImportError:
        print("scikit-image not installed; SSIM cross-check skipped")
