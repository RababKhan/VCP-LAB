"""Phase 6, step 1: prepare and verify the visual-comparison samples (no re-encoding).

Samples (reused from the verified full run, results/full):
  BasketballPass, BQMall x {QP 22, 32, 37 @ medium} U {faster, slower @ QP 32}  (QP 32 / medium is shared)

For every sample and both originals:
  * size = frames x frame size (10-bit 4:2:0 in 16-bit LE), SHA256 recorded
  * PSNR recomputed with scripts/psnr_yuv.py and compared with the value stored in results/full/results.csv
    (proves the reconstruction is the one that was measured); bitstream SHA256 checked against results.csv
  * a hard link with a YUView-parsable name is created in visual/yuview/ (no data copied, originals untouched)
Frames for comparison are chosen by fixed rules from the stored per-frame PSNR (see choose_frames()).

Outputs: visual/sample_manifest.json, visual/sample_manifest.csv, visual/frame_selection.json, visual/yuview/*.yuv

Usage: python prepare_visual.py
"""
import csv
import hashlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import psnr_yuv  # noqa: E402

VIS = os.path.join(ROOT, "visual")
LINKS = os.path.join(VIS, "yuview")
SEQS = {"BasketballPass": {"w": 416, "h": 240, "fps": 50, "frames": 500, "file": "BasketballPass_416_240_50_10_420.yuv",
                           "tag": "f500"},
        "BQMall": {"w": 832, "h": 480, "fps": 60, "frames": 600, "file": "BQMall_832_480_60_10_420.yuv", "tag": "f600"}}
VARIANTS = [(22, "medium"), (32, "medium"), (37, "medium"), (32, "faster"), (32, "slower")]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(1 << 22):
            h.update(b)
    return h.hexdigest()


def link(target, name):
    dst = os.path.join(LINKS, name)
    if not os.path.exists(dst):
        os.link(target, dst)
    assert os.path.samefile(target, dst), dst
    return dst


def choose_frames(seq, pf, intra_pocs):
    """Fixed, documented rules (same frame indices are then used for every variant of the sequence):
    1. intra: the first IDR picture (display index = POC)
    2. typical: frame whose QP 32 / medium Y-PSNR is closest to that variant's sequence mean (non-intra)
    3. worst: non-intra frame with the lowest QP 37 / medium Y-PSNR"""
    first_idr = int(intra_pocs.split(" ")[0].split(":")[0])
    intra = {int(p.split(":")[0]) for p in intra_pocs.split()}
    m32 = pf[(32, "medium")]
    mean32 = sum(m32) / len(m32)
    typical = min((i for i in range(len(m32)) if i not in intra), key=lambda i: abs(m32[i] - mean32))
    m37 = pf[(37, "medium")]
    worst = min((i for i in range(len(m37)) if i not in intra), key=lambda i: m37[i])
    return {"intra_first_idr": first_idr, "typical_qp32_medium": typical, "worst_qp37_medium": worst}


def main():
    os.makedirs(LINKS, exist_ok=True)
    full = {r["run_id"]: r for r in csv.DictReader(open(os.path.join(ROOT, "results", "full", "results.csv"), encoding="utf-8"))}
    man = json.load(open(os.path.join(ROOT, "configs", "full_manifest.json"), encoding="utf-8"))
    samples, selection, problems = [], {}, []
    for seq, s in SEQS.items():
        w, h, n = s["w"], s["h"], s["frames"]
        fb = (w * h + 2 * (w // 2) * (h // 2)) * 2
        src = os.path.join(ROOT, "dataset", s["file"])
        src_sha = sha256(src)
        ok = src_sha == man["sequences"][seq]["sha256"]
        problems += [] if ok else [f"{seq}: original SHA256 mismatch"]
        orig_name = f"{seq}_original_{w}x{h}_{s['fps']}fps_10bit_420.yuv"
        samples.append({"sequence": seq, "role": "original", "qp": "", "preset": "", "file": os.path.relpath(src, ROOT),
                        "yuview_link": os.path.relpath(link(src, orig_name), ROOT), "width": w, "height": h,
                        "bitdepth": 10, "chroma": "4:2:0", "container": "16-bit LE",
                        "frames_in_file": os.path.getsize(src) / fb, "frames_compared": n, "sha256": src_sha,
                        "sha256_matches_manifest": ok})
        pf = {}
        for qp, preset in VARIANTS:
            rid = f"{seq}_{s['tag']}_q{qp}_{preset}_t8"
            row = full[rid]
            rec = os.path.join(ROOT, "recon", "full", f"{rid}_rec.yuv")
            bs = os.path.join(ROOT, "bitstreams", "full", f"{rid}.266")
            size_ok = os.path.getsize(rec) == n * fb
            res, mse, per_frame = psnr_yuv.compute(src, rec, w, h, 10, n)
            p = res["peak1020"]["avg_of_frame_psnr"]
            psnr_ok = all(round(p[c], 4) == float(row[f"psnr_{c.lower()}"]) for c in "YUV")
            bs_ok = sha256(bs) == row["bitstream_sha256"]
            for name, good in (("size", size_ok), ("psnr", psnr_ok), ("bitstream", bs_ok), ("status", row["status"] == "ok"),
                               ("alignment", res["alignment_best_offset"] == 0)):
                if not good:
                    problems.append(f"{rid}: {name} check failed")
            pf[(qp, preset)] = [float(v) for v in per_frame[:, 0]]
            name = f"{seq}_QP{qp}_{preset}_{w}x{h}_{s['fps']}fps_10bit_420.yuv"
            samples.append({"sequence": seq, "role": "reconstruction", "qp": qp, "preset": preset, "run_id": rid,
                            "file": os.path.relpath(rec, ROOT), "yuview_link": os.path.relpath(link(rec, name), ROOT),
                            "width": w, "height": h, "bitdepth": 10, "chroma": "4:2:0", "container": "16-bit LE",
                            "frames_in_file": os.path.getsize(rec) / fb, "frames_compared": n, "sha256": sha256(rec),
                            "size_ok": size_ok, "psnr_recomputed_matches_results": psnr_ok, "bitstream_sha256_ok": bs_ok,
                            "alignment_best_offset": res["alignment_best_offset"],
                            "psnr_y": float(row["psnr_y"]), "psnr_u": float(row["psnr_u"]), "psnr_v": float(row["psnr_v"]),
                            "psnr_yuv_411": float(row["psnr_yuv_411"]), "bitstream_bytes": int(row["bitstream_bytes"]),
                            "bitrate_kbps": float(row["bitrate_kbps"]), "intra_pocs": row["intra_pocs"]})
        fr = choose_frames(seq, pf, full[f"{seq}_{s['tag']}_q32_medium_t8"]["intra_pocs"])
        selection[seq] = {"frames": fr, "per_frame_y_psnr": {
            f"QP{qp}_{preset}": {k: round(pf[(qp, preset)][i], 4) for k, i in fr.items()} for qp, preset in VARIANTS}}

    out = {"samples": samples, "problems": problems}
    with open(os.path.join(VIS, "sample_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(VIS, "frame_selection.json"), "w", encoding="utf-8") as f:
        json.dump(selection, f, indent=2)
    buf = io.StringIO()
    keys = ["sequence", "role", "qp", "preset", "width", "height", "bitdepth", "chroma", "frames_in_file",
            "frames_compared", "psnr_y", "psnr_yuv_411", "bitstream_bytes", "bitrate_kbps", "sha256", "yuview_link"]
    wr = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore")
    wr.writeheader()
    wr.writerows(samples)
    with open(os.path.join(VIS, "sample_manifest.csv"), "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())
    for smp in samples:
        print(f"{smp['sequence']:15s} {smp['role'][:5]} QP{smp['qp']!s:3s} {smp['preset']:7s} frames {smp['frames_in_file']:6.1f} "
              f"Y {smp.get('psnr_y', ''):>8} bytes {smp.get('bitstream_bytes', ''):>9} sha {smp['sha256'][:12]}")
    print(json.dumps(selection, indent=1))
    print("PROBLEMS:", problems or "none")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
