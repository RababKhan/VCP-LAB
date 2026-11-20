"""Phase 2/3 runner: expand Sadab's experiment to 4 sequences x 4 QPs x 4 presets, with timing-reliability controls.

* The 16 configurations of phase 1 (BlowingBubbles/BQMall x fast/medium) are reused, not re-encoded as new data;
  some of them are repeated here to measure timing reliability.
* Block A = 416x240 and 832x480 sequences, Block B = 1920x1080. Each block runs in a random order (seed recorded),
  after a warm-up encode/decode that is logged and discarded.
* Before every run: wait (and log the wait) while the laptop is on battery. The system is kept awake for the run
  (SetThreadExecutionState); no power or security setting is changed.
* Per run: encode (timed by the encoder's "Total Time" and by wall clock), bitstream size/SHA-256/bitrate, one decode
  WITH output for frame count + independent PSNR, then 3 decodes WITHOUT output for decode timing (median kept).
* A monitor process samples CPU utility/performance and power state every 5 s into logs/monitor_phase2.csv.
* Large reconstructions (> 416x240) go to one scratch file per sequence that is overwritten (the bitstream is kept and
  decodes to exactly the same file again); small reconstructions are kept.

Usage:  .venv\\Scripts\\python.exe experiment\\run_phase2.py [--block A|B|AB] [--plan] [--pilot]
"""
import argparse
import csv
import ctypes
import hashlib
import json
import random
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENC = ROOT / "vvenc/bin/release-static/vvencapp.exe"
DEC = ROOT / "vvdec/bin/release-static/vvdecapp.exe"
PSNR = ROOT / "experiment/psnr_check.py"
PY = sys.executable
OUT = ROOT / "out/phase2"
LOGS = ROOT / "logs/phase2"
CSV = ROOT / "results/results_phase2.csv"
THREADS = 8
SEQS = {
    "BlowingBubbles": dict(file="BlowingBubbles_416_240_50_10_420.yuv", w=416, h=240, fps=50, n=500, block="A"),
    "BQMall": dict(file="BQMall_832_480_60_10_420.yuv", w=832, h=480, fps=60, n=600, block="A"),
    "BasketballPass": dict(file="BasketballPass_416_240_50_10_420.yuv", w=416, h=240, fps=50, n=500, block="A"),
    "BasketballDrive": dict(file="BasketballDrive_1920_1080_50_10_420.yuv", w=1920, h=1080, fps=50, n=500, block="B"),
}
QPS = [24, 29, 34, 39]
PRESETS = ["faster", "fast", "medium", "slow"]
PHASE1 = {("BlowingBubbles", "fast"), ("BlowingBubbles", "medium"), ("BQMall", "fast"), ("BQMall", "medium")}
# configurations repeated 3 extra times (timing reliability); phase-1 run ids where they exist
REPEATS = [("BlowingBubbles", 34, "fast", "R04/R17"), ("BlowingBubbles", 34, "medium", "R16/R18"),
           ("BlowingBubbles", 24, "medium", "R03"), ("BQMall", 39, "medium", "R01"), ("BQMall", 29, "medium", "R15"),
           ("BasketballPass", 29, "faster", ""), ("BasketballPass", 29, "slow", ""),
           ("BasketballDrive", 34, "faster", ""), ("BasketballDrive", 34, "fast", "")]
SEED = {"A": 20261111, "B": 20261112}
COLS = ["run_id", "block", "kind", "repeat_of", "status", "sequence", "width", "height", "fps", "frames", "qp", "preset",
        "threads", "start_iso", "end_iso", "encode_time_s", "encode_wall_s", "bitstream_bytes", "bitrate_kbps",
        "enc_bitrate_kbps", "enc_y_psnr", "enc_u_psnr", "enc_v_psnr", "enc_yuv_psnr", "check_y_psnr", "check_u_psnr",
        "check_v_psnr", "max_psnr_diff_db", "recon_frames", "recon_kept", "decode_with_output_s",
        "decode_noout_times_s", "decode_noout_median_s", "bitstream_sha256", "recon_sha256", "ac_wait_s", "log_file",
        "notes"]


class SPS(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte), ("BatteryLifePercent", ctypes.c_byte),
                ("SystemStatusFlag", ctypes.c_byte), ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]


def on_ac():
    s = SPS()
    ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s))
    return s.ACLineStatus == 1, s.BatteryLifePercent


def keep_awake(on=True):
    ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run_cmd(args, log, title):
    t0 = time.perf_counter()
    p = subprocess.run([str(a) for a in args], capture_output=True, text=True, errors="replace")
    wall = time.perf_counter() - t0
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"=== {title}\nCommand: {' '.join(str(a) for a in args)}\nStarted: {now()}\n{p.stdout}{p.stderr}"
                f"Exit code: {p.returncode}\nWall time (s): {wall:.3f}\n")
    return p.returncode, p.stdout + p.stderr, wall


def configs(block):
    out = []
    for s, d in SEQS.items():
        if d["block"] not in block:
            continue
        for q in QPS:
            for p in PRESETS:
                if (s, p) not in PHASE1:
                    out.append((s, q, p, "new", ""))
        for (rs, rq, rp, ref) in REPEATS:
            if rs == s:
                for k in range(3):
                    out.append((rs, rq, rp, "repeat", f"{ref}#{k + 1}" if ref else f"#{k + 1}"))
    return out


def one_run(rid, blk, seq, qp, preset, kind, rep, writer, fcsv):
    d = SEQS[seq]
    w, h, fps, n = d["w"], d["h"], d["fps"], d["n"]
    tag = f"{rid}_{seq}_QP{qp}_{preset}"
    log = LOGS / f"{tag}.log"
    row = {c: "" for c in COLS}
    row.update(run_id=rid, block=blk, kind=kind, repeat_of=rep, sequence=seq, width=w, height=h, fps=fps, frames=n,
               qp=qp, preset=preset, threads=THREADS, log_file=str(log.relative_to(ROOT)) if log.is_relative_to(ROOT) else str(log))
    notes = []
    waited = 0.0
    ac, pct = on_ac()
    while not ac:                                     # never time a run on battery
        if waited == 0:
            print(f"  on battery ({pct}%), waiting for AC power ...", flush=True)
        time.sleep(30)
        waited += 30
        ac, pct = on_ac()
    row["ac_wait_s"] = f"{waited:.0f}"
    if waited:
        notes.append(f"waited {waited:.0f} s for AC power before start")
    row["start_iso"] = now()
    bs = OUT / f"{tag}.266"
    keep = (w * h) <= 416 * 240 and kind == "new"      # repeats decode to the scratch file (identical output)
    rec = OUT / (f"{tag}_rec_{w}x{h}_{fps}fps_10bit_420.yuv" if keep else f"_scratch_{seq}_rec_{w}x{h}_{fps}fps_10bit_420.yuv")
    code, txt, wall = run_cmd([ENC, "-i", ROOT / "dataset" / d["file"], "-s", f"{w}x{h}", "-c", "yuv420_10", "--fps", fps,
                               "-f", n, "-q", qp, "--preset", preset, "--qpa", 0, "-t", THREADS, "-o", bs], log, "ENCODE")
    row["encode_wall_s"] = f"{wall:.3f}"
    m = re.findall(r"Total Time:\s*([\d.]+)", txt)
    row["encode_time_s"] = m[-1] if m else ""
    sm = re.search(r"vvenc \[info\]:\s+(\d+)\s+a\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", txt)
    if sm:
        row.update(enc_bitrate_kbps=sm.group(2), enc_y_psnr=sm.group(3), enc_u_psnr=sm.group(4), enc_v_psnr=sm.group(5),
                   enc_yuv_psnr=sm.group(6))
    if code != 0 or not bs.exists() or not sm:
        row.update(status="FAILED", end_iso=now(), notes=f"encoder exit {code}")
        writer.writerow(row); fcsv.flush()
        return row
    size = bs.stat().st_size
    row.update(bitstream_bytes=size, bitrate_kbps=f"{size * 8 / (n / fps) / 1000:.3f}", bitstream_sha256=sha(bs))
    code, txt, wall = run_cmd([DEC, "-b", bs, "-o", rec, "-t", THREADS], log, "DECODE WITH OUTPUT (frame count + PSNR)")
    row["decode_with_output_s"] = (re.findall(r"\(([\d.]+) sec\)", txt) or [""])[-1]
    if code != 0:
        notes.append(f"decoder exit {code}")
    frames = rec.stat().st_size / (w * h * 3) if rec.exists() else 0
    row["recon_frames"] = f"{frames:g}"
    row["recon_kept"] = "yes" if keep else "no (scratch, regenerable from bitstream)"
    if frames != n:
        notes.append(f"decoded {frames} frames, expected {n}")
    row["recon_sha256"] = sha(rec)
    p = subprocess.run([str(a) for a in (PY, PSNR, ROOT / "dataset" / d["file"], rec, w, h, n)], capture_output=True, text=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"=== PSNR CHECK\n{p.stdout}{p.stderr}")
    try:
        pj = json.loads(p.stdout.strip().splitlines()[-1])
        row.update(check_y_psnr=pj["Y"], check_u_psnr=pj["U"], check_v_psnr=pj["V"])
        diff = max(abs(pj[c] - float(row[f"enc_{c.lower()}_psnr"])) for c in "YUV")
        row["max_psnr_diff_db"] = f"{diff:.4f}"
        if diff > 0.01:
            notes.append("PSNR check differs from encoder by > 0.01 dB")
    except Exception as e:  # noqa: BLE001
        notes.append(f"PSNR check failed: {e}")
    dts = []
    for k in range(3):
        code, txt, wall = run_cmd([DEC, "-b", bs, "-t", THREADS], log, f"DECODE TIMING {k + 1} (no output file)")
        m = re.findall(r"(\d+) frames decoded @ [\d.]+ fps \(([\d.]+) sec\)", txt)
        if code == 0 and m and int(m[-1][0]) == n:
            dts.append(float(m[-1][1]))
        else:
            notes.append(f"timing decode {k + 1} problem (exit {code})")
    row["decode_noout_times_s"] = ";".join(f"{x:.3f}" for x in dts)
    if dts:
        row["decode_noout_median_s"] = f"{statistics.median(dts):.3f}"
    ac, _ = on_ac()
    if not ac:
        notes.append("power changed to battery during the run")
    row["end_iso"] = now()
    row["status"] = "OK" if not notes or notes == [f"waited {waited:.0f} s for AC power before start"] else "CHECK"
    row["notes"] = " | ".join(notes)
    writer.writerow(row); fcsv.flush()
    print(f"  {rid} {seq} QP{qp} {preset:6s} enc {row['encode_time_s']} s | dec {row['decode_noout_median_s']} s | "
          f"{size:,} B | Y {row['enc_y_psnr']} / {row.get('check_y_psnr')} | {row['status']}", flush=True)
    return row


def decode_pass_phase1():
    """Re-time the 16 phase-1 bitstreams with 3 decodes each WITHOUT an output file, so that all 64 configurations
    have comparable decode times. The phase-1 values (which included writing the YUV file) are kept unchanged."""
    path = ROOT / "results/decode_timing_phase1_bitstreams.csv"
    if path.exists():
        return
    log = LOGS / "decode_pass_phase1.log"
    rows = [r for r in csv.DictReader(open(ROOT / "results/results_raw.csv", encoding="utf-8-sig")) if not r["repeat_of"]]
    with open(path, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, ["run_id", "sequence", "qp", "preset", "time_iso", "decode_noout_times_s", "decode_noout_median_s", "notes"])
        wr.writeheader()
        for r in rows:
            while not on_ac()[0]:
                time.sleep(30)
            bs = ROOT / "out" / f"{r['run_id']}_{r['sequence']}_QP{r['qp']}_{r['preset']}.266"
            dts, notes = [], []
            for k in range(3):
                code, txt, _ = run_cmd([DEC, "-b", bs, "-t", THREADS], log, f"{r['run_id']} DECODE TIMING {k + 1} (no output)")
                m = re.findall(r"(\d+) frames decoded @ [\d.]+ fps \(([\d.]+) sec\)", txt)
                if code == 0 and m and int(m[-1][0]) == int(r["frames"]):
                    dts.append(float(m[-1][1]))
                else:
                    notes.append(f"decode {k + 1} problem")
            wr.writerow(dict(run_id=r["run_id"], sequence=r["sequence"], qp=r["qp"], preset=r["preset"], time_iso=now(),
                             decode_noout_times_s=";".join(f"{x:.3f}" for x in dts),
                             decode_noout_median_s=f"{statistics.median(dts):.3f}" if dts else "", notes=" | ".join(notes)))
            f.flush()
    print(f"  phase-1 decode timing pass written: {path.name}", flush=True)


def warmup(blk, log):
    print("  warm-up (discarded)", flush=True)
    s = SEQS["BasketballPass"]
    bs = OUT / f"_warmup_{blk}.266"
    run_cmd([ENC, "-i", ROOT / "dataset" / s["file"], "-s", "416x240", "-c", "yuv420_10", "--fps", 50, "-f", 64, "-q", 34,
             "--preset", "medium", "--qpa", 0, "-t", THREADS, "-o", bs], log, f"WARM-UP ENCODE block {blk} (discarded)")
    run_cmd([DEC, "-b", bs, "-t", THREADS], log, f"WARM-UP DECODE block {blk} (discarded)")


def pilot():
    """Short encodes to estimate the run time of the full matrix (not used as results)."""
    log = LOGS / "pilot.log"
    est = {}
    while not on_ac()[0]:
        print("  pilot: on battery, waiting for AC power ...", flush=True)
        time.sleep(30)
    for seq in ("BasketballPass", "BasketballDrive"):
        d = SEQS[seq]
        for p in PRESETS:
            n = 32
            code, txt, wall = run_cmd([ENC, "-i", ROOT / "dataset" / d["file"], "-s", f"{d['w']}x{d['h']}", "-c", "yuv420_10",
                                       "--fps", d["fps"], "-f", n, "-q", 29, "--preset", p, "--qpa", 0, "-t", THREADS,
                                       "-o", OUT / f"_pilot_{seq}_{p}.266"], log, f"PILOT {seq} {p} QP29 {n} frames")
            t = float(re.findall(r"Total Time:\s*([\d.]+)", txt)[-1])
            est[f"{seq}_{p}"] = t / n
            print(f"  pilot {seq:15s} {p:6s}: {t:7.2f} s for {n} frames -> {t / n * d['n']:7.0f} s for {d['n']} frames", flush=True)
    return est


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", default="AB")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    if a.pilot:
        keep_awake(True)
        print(json.dumps(pilot(), indent=1))
        keep_awake(False)
        return
    plan = {}
    for blk in "AB":
        if blk in a.block:
            cf = configs(blk)
            random.Random(SEED[blk]).shuffle(cf)
            plan[blk] = cf
    if a.plan:
        for blk, cf in plan.items():
            print(f"Block {blk}: {len(cf)} runs (seed {SEED[blk]})")
            for i, c in enumerate(cf, 1):
                print(f"  {blk}{i:03d} {c}")
        return
    mon = subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                            str(ROOT / "experiment/monitor.ps1"), "-Out", str(ROOT / "logs/monitor_phase2.csv")])
    keep_awake(True)
    new = not CSV.exists()
    done = set()
    if not new:
        done = {r["run_id"] for r in csv.DictReader(open(CSV, encoding="utf-8")) if r["status"] in ("OK", "CHECK")}
    with open(CSV, "a", newline="", encoding="utf-8") as fcsv:
        wr = csv.DictWriter(fcsv, COLS)
        if new:
            wr.writeheader()
        try:
            for blk, cf in plan.items():
                print(f"Block {blk}: {len(cf)} runs, seed {SEED[blk]}, start {now()}", flush=True)
                warmup(blk, LOGS / f"warmup_{blk}.log")
                for i, (seq, qp, p, kind, rep) in enumerate(cf, 1):
                    rid = f"{blk}{i:03d}"
                    if rid in done:
                        continue
                    print(f"[{rid}] {seq} QP{qp} {p} ({kind}{' ' + rep if rep else ''})", flush=True)
                    one_run(rid, blk, seq, qp, p, kind, rep, wr, fcsv)
                if blk == "A":
                    decode_pass_phase1()
                print(f"Block {blk} done {now()}", flush=True)
        finally:
            keep_awake(False)
            mon.terminate()
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
