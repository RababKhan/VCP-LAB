"""Phase 4: compare Linux (GCC, WSL2) outputs with the matching Windows (MSVC) runs and the 16-frame smoke test.
Compares bitstream size, bitstream SHA-256, decoded frame count, decoded-video SHA-256 and PSNR."""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
rows = {r["run_id"]: r for r in csv.DictReader(open(ROOT / "results/results_raw.csv", encoding="utf-8-sig"))}
SEQ = {"BlowingBubbles": ("BlowingBubbles_416_240_50_10_420.yuv", 416, 240), "BQMall": ("BQMall_832_480_60_10_420.yuv", 832, 480)}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def psnr(orig, rec, w, h, n):
    out = subprocess.run([PY, str(ROOT / "experiment/psnr_check.py"), str(orig), str(rec), str(w), str(h), str(n)],
                         capture_output=True, text=True).stdout.strip().splitlines()[-1]
    return json.loads(out)


res = []
for rid in ("R04", "R15"):
    r = rows[rid]
    f, w, h = SEQ[r["sequence"]]
    n = int(r["frames"])
    tag = f'{rid}_{r["sequence"]}_QP{r["qp"]}_{r["preset"]}'
    wbs, wrec = ROOT / f"out/{tag}.266", next((ROOT / "out").glob(f"{tag}_rec_*.yuv"))
    lbs, lrec = ROOT / f"out/linux/{tag}_linux.266", next((ROOT / "out/linux").glob(f"{tag}_linux_rec_*.yuv"))
    fs = w * h * 3
    lp = psnr(ROOT / "dataset" / f, lrec, w, h, n)
    item = {"config": f'{r["sequence"]} QP {r["qp"]} {r["preset"]}, {n} frames (Windows run {rid})',
            "windows": {"bytes": wbs.stat().st_size, "sha256": sha(wbs), "frames": wrec.stat().st_size / fs,
                        "recon_sha256": sha(wrec), "y_psnr": float(r["check_y_psnr"]), "u_psnr": float(r["check_u_psnr"]),
                        "v_psnr": float(r["check_v_psnr"])},
            "linux": {"bytes": lbs.stat().st_size, "sha256": sha(lbs), "frames": lrec.stat().st_size / fs,
                      "recon_sha256": sha(lrec), "y_psnr": lp["Y"], "u_psnr": lp["U"], "v_psnr": lp["V"]}}
    W, L = item["windows"], item["linux"]
    item["match"] = {"size": W["bytes"] == L["bytes"], "bitstream_sha256": W["sha256"] == L["sha256"],
                     "frames": W["frames"] == L["frames"] == n, "recon_sha256": W["recon_sha256"] == L["recon_sha256"],
                     "psnr": (W["y_psnr"], W["u_psnr"], W["v_psnr"]) == (L["y_psnr"], L["u_psnr"], L["v_psnr"])}
    res.append(item)

sm = ROOT / "out/smoke"   # compare the smoke-test files directly (the log has mixed text encodings)
sb = {p: sha(sm / f"smoke_{p}_QP34_fast_f16.266") for p in ("Windows", "Linux")}
sr = {p: sha(sm / f"smoke_{p}_QP34_fast_f16_rec_416x240_50fps_10bit_420.yuv") for p in ("Windows", "Linux")}
out = {"full_length": res,
       "smoke_16_frames": {"bitstream": "IDENTICAL" if sb["Windows"] == sb["Linux"] else "DIFFERENT",
                           "decoded": "IDENTICAL" if sr["Windows"] == sr["Linux"] else "DIFFERENT",
                           "bitstream_sha256": sb, "recon_sha256": sr},
       "note": "Linux timing is not compared: the Linux runs were made in WSL2 reading from /mnt/d."}
(ROOT / "results/crossplatform.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=1))
