"""Phase 1 audit of the first 18 runs. Read-only: checks every stored number against the raw files and logs.
Writes results/audit_phase1.json and prints a summary."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader(open(ROOT / "results/results_raw.csv", encoding="utf-8-sig")))
checks, problems = [], []


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def ok(name, cond, detail=""):
    checks.append({"check": name, "pass": bool(cond), "detail": detail})
    if not cond:
        problems.append(f"{name}: {detail}")


# 1. input hashes against the provenance log
prov = (ROOT / "logs/00_setup_provenance.log").read_text(encoding="utf-8-sig", errors="replace")
for f in ("BlowingBubbles_416_240_50_10_420.yuv", "BQMall_832_480_60_10_420.yuv"):
    m = re.search(re.escape(f) + r".*?sha256 ([0-9A-Fa-f]{64})", prov)
    now = sha(ROOT / "dataset" / f)
    ok(f"input sha256 {f}", m and m.group(1).lower() == now, f"log {m.group(1).lower() if m else None} now {now}")

SEQ = {"BlowingBubbles": (416, 240, 50, 500), "BQMall": (832, 480, 60, 600)}
for r in rows:
    rid, seq = r["run_id"], r["sequence"]
    w, h, fps, n = SEQ[seq]
    log = (ROOT / r["log_file"]).read_text(encoding="utf-8", errors="replace")
    enc_part = log.split("=== DECODE 1")[0]
    cmd = re.search(r"Command: .*vvencapp\.exe\" (.*)", enc_part).group(1)
    exp = {"-s": f"{w}x{h}", "-c": "yuv420_10", "--fps": str(fps), "-f": str(n), "-q": r["qp"], "--preset": r["preset"],
           "--qpa": "0", "-t": "8"}
    toks = cmd.split()
    for k, v in exp.items():
        ok(f"{rid} encoder arg {k}", k in toks and toks[toks.index(k) + 1] == v, f"expected {v}")
    ok(f"{rid} encoder input file", f"{seq}_" in toks[toks.index("-i") + 1], toks[toks.index("-i") + 1])
    ok(f"{rid} encoder exit 0", re.search(r"Exit code: 0", enc_part) is not None)
    tt = re.findall(r"Total Time:\s*([\d.]+)", enc_part)
    ok(f"{rid} encode time matches log", tt and abs(float(tt[-1]) - float(r["encode_time_s"])) < 1e-9, f"{tt} vs {r['encode_time_s']}")
    sm = re.search(r"vvenc \[info\]:\s+(\d+)\s+a\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", enc_part)
    ok(f"{rid} encoder frames", sm and int(sm.group(1)) == n, sm.group(1) if sm else None)
    for i, k in enumerate(["enc_bitrate_kbps", "enc_y_psnr", "enc_u_psnr", "enc_v_psnr", "enc_yuv_psnr"], start=2):
        ok(f"{rid} {k} matches log", sm and abs(float(sm.group(i)) - float(r[k])) < 1e-9)
    tag = f"{rid}_{seq}_QP{r['qp']}_{r['preset']}"
    bs = ROOT / "out" / f"{tag}.266"
    ok(f"{rid} bitstream size", bs.stat().st_size == int(r["bitstream_bytes"]), f"{bs.stat().st_size}")
    ok(f"{rid} bitstream sha256", sha(bs) == r["bitstream_sha256"])
    br = int(r["bitstream_bytes"]) * 8 / (n / fps) / 1000
    ok(f"{rid} bitrate recomputed", abs(br - float(r["bitrate_kbps"])) < 0.001, f"{br:.3f}")
    dec = re.findall(r"=== DECODE (\d)(.*?)(?==== DECODE|=== PSNR|$)", log, re.S)
    ok(f"{rid} 3 decodes", len(dec) == 3, str(len(dec)))
    dts = []
    for _, part in dec:
        ok(f"{rid} decoder exit 0", "Exit code: 0" in part)
        ok(f"{rid} decoder args -t 8", re.search(r"vvdecapp\.exe\" -b .* -t 8", part) is not None)
        m = re.search(r"(\d+) frames decoded @ [\d.]+ fps \(([\d.]+) sec\)", part)
        ok(f"{rid} decoded frame count", m and int(m.group(1)) == n)
        dts.append(float(m.group(2)))
    ok(f"{rid} decode times match", ";".join(f"{x:.3f}" for x in dts) == r["decode_times_s"])
    rec = next((ROOT / "out").glob(f"{tag}_rec_*.yuv"))
    ok(f"{rid} recon size = {n} frames", rec.stat().st_size == w * h * 3 * n)
    pj = re.search(r"\{\"Y\".*\}", log)
    ok(f"{rid} psnr check logged", pj is not None)
    if pj:
        p = json.loads(pj.group(0))
        ok(f"{rid} psnr check matches csv", abs(p["Y"] - float(r["check_y_psnr"])) < 1e-9 and p["frames_checked"] == n)

# 2. R04 vs R17 investigation: decode time as a probe of overall machine speed (same work, independent of encoder)
probe = []
for r in sorted(rows, key=lambda r: r["started"]):
    probe.append({"run": r["run_id"], "started": r["started"], "seq": r["sequence"], "qp": r["qp"], "preset": r["preset"],
                  "encode_s": float(r["encode_time_s"]), "encode_wall_s": float(r["encode_wall_s"]),
                  "decode_runs_s": r["decode_times_s"]})
out = {"n_checks": len(checks), "n_failed": len(problems), "problems": problems, "run_order_probe": probe}
(ROOT / "results/audit_phase1.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(f"checks: {len(checks)}, failed: {len(problems)}")
for p in problems:
    print("  FAIL", p)
print("\nrun order | started | config | encode s (wall s) | decode runs s")
for p in probe:
    print(f"{p['run']} {p['started'][11:]} {p['seq']:14s} QP{p['qp']} {p['preset']:6s} {p['encode_s']:8.2f} ({p['encode_wall_s']:7.2f}) | {p['decode_runs_s']}")
