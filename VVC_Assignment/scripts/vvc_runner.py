"""Run VVenC/VVdeC experiments described by a JSON manifest.

For every run in the manifest:
  1. encode with vvencapp (wall-clock time measured here, encoder-reported time parsed from its log)
  2. decode once WITHOUT output (pure decoding time, no disk writes)
  3. decode again WITH output (reconstructed YUV, its time is recorded separately)  [skipped for repeats]
  4. verify reconstructed size / frame count, compute PSNR with psnr_yuv.py        [skipped for repeats]
  5. run integrity checks, write a per-run JSON (status ok / failed) atomically
  6. regenerate results.csv atomically from all per-run JSONs

Resume semantics:
  * status ok      -> skipped
  * status failed  -> reported loudly and NOT re-run unless --retry-failed
                      (previous attempt's files are moved to _attempts/, never deleted)
  * outputs present but no per-run JSON (interrupted run) -> those files are moved to _interrupted/, then re-run
Nothing is ever deleted or overwritten.

Usage: python vvc_runner.py <manifest.json> [--only RUN_ID ...] [--dry-run] [--retry-failed]
"""
import argparse
import csv
import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psnr_yuv  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSV_FIELDS = [
    "run_id", "status", "failed_checks", "sequence", "width", "height", "fps", "bitdepth", "chroma", "frames",
    "qp", "preset", "qpa", "enc_threads", "dec_threads", "groups", "repeat_of",
    "encode_exit", "encode_wall_s", "encode_reported_s", "encode_fps_wall",
    "decode_exit", "decode_wall_s", "decode_reported_s", "decode_recon_wall_s",
    "bitstream_bytes", "bitrate_kbps", "encoder_reported_kbps", "bitstream_sha256",
    "psnr_y", "psnr_u", "psnr_v", "psnr_yuv_411", "psnr_yuv_611",
    "enc_psnr_y", "enc_psnr_u", "enc_psnr_v", "enc_psnr_yuv", "max_abs_psnr_diff_vs_encoder",
    "alignment_best_offset", "recon_bytes", "recon_frames_ok",
    "intra_pocs", "frames_I", "frames_B", "avg_qp_I", "avg_qp_B", "intra_period", "gop_size", "parallel_frames",
    "ac_power", "power_plan", "power_mode", "started", "vvenc_version", "vvdec_version",
]


def rel(p):
    return os.path.normpath(os.path.join(ROOT, p))


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def atomic_write_text(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(1 << 22):
            h.update(block)
    return h.hexdigest()


POWER_MODES = {"ded574b5-45a0-4f42-8737-46345c09c238": "Best performance",
               "961cc777-2547-4f9d-8174-7d86181b8a7a": "Best power efficiency",
               "00000000-0000-0000-0000-000000000000": "Balanced"}
POWER_PS = ("(Get-CimInstance Win32_Battery).BatteryStatus; "
            "Add-Type -Namespace PM -Name Api -MemberDefinition "
            "'[DllImport(\"powrprof.dll\")] public static extern uint PowerGetEffectiveOverlayScheme(out Guid g);'; "
            "$g=[Guid]::Empty; $null=[PM.Api]::PowerGetEffectiveOverlayScheme([ref]$g); \"$g\"")


def power_state():
    """(on AC power?, power plan, Windows power mode). Recorded, never changed."""
    if platform.system() != "Windows":
        return None, None, None
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", POWER_PS],
                             capture_output=True, text=True, timeout=60).stdout.split()
        plan = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, timeout=60).stdout
        m = re.search(r"\(([^)]+)\)", plan)
        ac = (out[0] == "2") if out else None
        mode = POWER_MODES.get(out[1], out[1]) if len(out) > 1 else None
        return ac, m.group(1) if m else plan.strip(), mode
    except (OSError, subprocess.SubprocessError):
        return None, None, None


def run_timed(cmd, log_path):
    started = now_iso()
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    wall = time.perf_counter() - t0
    out = proc.stdout.decode("utf-8", errors="replace")
    atomic_write_text(log_path, f"Command: {subprocess.list2cmdline(cmd)}\nStarted: {started}\n{out}"
                                f"\nExit code: {proc.returncode}\nWall time (s): {wall:.3f}\n")
    return proc.returncode, wall, out, started


def parse_encoder(out):
    info = {"notice": {}}
    for m in re.finditer(r"^vvenc \[notice\]: (.+?)\s+: (.*)$", out, re.M):
        info["notice"][m.group(1).strip()] = m.group(2).strip()
    m = re.search(r"^vvenc \[info\]:\s+(\d+)\s+a\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", out, re.M)
    if m:
        info["summary"] = {"frames": int(m.group(1)), "kbps": float(m.group(2)), "Y": float(m.group(3)),
                           "U": float(m.group(4)), "V": float(m.group(5)), "YUV": float(m.group(6))}
    m = re.search(r"Total Time:\s+([\d.]+) sec", out)
    info["total_time_s"] = float(m.group(1)) if m else None
    for t in ("I", "P", "B"):
        m = re.search(rf"stats summary: frame {t}:\s+(\d+), kbps:\s+(\S+), AvgQP:\s+(\S+)", out)
        info[f"frames_{t}"] = int(m.group(1)) if m else None
        info[f"avg_qp_{t}"] = float(m.group(3)) if m and m.group(3) != "nan" else None
    pics = [(int(p), nal, st, int(qp)) for p, nal, st, qp in
            re.findall(r"^POC\s+(\d+) TId:\s*\d+ \(\s*(\S+), (\S)-SLICE, QP (\d+)", out, re.M)]
    info["pictures"] = len(pics)
    info["distinct_pocs"] = len({p for p, *_ in pics})
    info["intra"] = [[p, nal] for p, nal, st, _ in pics if st == "I"]
    return info


def parse_decoder(out):
    m = re.search(r"(\d+) frames decoded @ ([\d.]+) fps \(([\d.]+) sec\)", out)
    s = re.search(r"SizeInfo: (\d+)x(\d+) \((\d+)b\)", out)
    return {"frames": int(m.group(1)) if m else None, "reported_s": float(m.group(3)) if m else None,
            "size_info": s.group(0) if s else None}


def first_line(path, flag):
    out = subprocess.run([path, flag], capture_output=True, text=True).stdout
    return out.strip().splitlines()[0] if out.strip() else ""


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def move_aside(paths, dest_root):
    """Preserve files of an interrupted / failed attempt by moving them (never deleting)."""
    moved = []
    os.makedirs(dest_root, exist_ok=True)
    for p in paths:
        if os.path.exists(p):
            shutil.move(p, os.path.join(dest_root, os.path.basename(p)))
            moved.append(p)
    return moved


def checks_for(row, e, run, threads, frames, dec_timing, dec_recon, original_sha):
    c = {"encode_exit_zero": row["encode_exit"] == 0}
    n = e["notice"]
    c["cfg_qpa_disabled"] = n.get("Perceptual optimization") == "Disabled"
    c["cfg_rate_control_qp"] = n.get("Rate control") == f"QP {run['qp']}"
    c["cfg_frames"] = n.get("Frames", "").startswith(f"encode {frames} frames")
    c["cfg_threads"] = n.get("Threads", "").split()[0:1] == [str(threads)]
    c["cfg_input_bitdepth_10"] = n.get("Input bit depth") == "(Y:10, C:10)"
    c["enc_pictures_eq_frames"] = e["pictures"] == frames and e["distinct_pocs"] == frames
    c["enc_summary_frames"] = e.get("summary", {}).get("frames") == frames
    c["bitstream_nonempty"] = (row.get("bitstream_bytes") or 0) > 0
    c["decode_timing_exit_zero"] = row.get("decode_exit") == 0
    c["decode_timing_frames"] = dec_timing is not None and dec_timing.get("frames") == frames
    if run.get("repeat_of"):
        c["repeat_bitstream_identical"] = original_sha is not None and original_sha == row.get("bitstream_sha256")
    else:
        c["decode_recon_exit_zero"] = dec_recon is not None and dec_recon.get("exit") == 0
        c["decode_recon_frames"] = dec_recon is not None and dec_recon.get("frames") == frames
        c["recon_size_ok"] = row.get("recon_frames_ok") is True
        c["alignment_offset_zero"] = row.get("alignment_best_offset") == 0
        c["psnr_matches_encoder"] = (row.get("max_abs_psnr_diff_vs_encoder") is not None
                                     and row["max_abs_psnr_diff_vs_encoder"] <= 0.0001)
        c["bitrate_matches_encoder"] = (row.get("encoder_reported_kbps") is not None
                                        and abs(row["bitrate_kbps"] - row["encoder_reported_kbps"]) <= 0.001)
    return c


def write_csv(man, out_dir):
    rows = []
    for run in man["runs"]:
        p = os.path.join(out_dir, "runs", f"{run['run_id']}.json")
        if os.path.exists(p):
            rows.append(load_json(p)["row"])
    buf = io.StringIO()
    wr = csv.DictWriter(buf, fieldnames=CSV_FIELDS, extrasaction="ignore")
    wr.writeheader()
    wr.writerows(rows)
    atomic_write_text(os.path.join(out_dir, "results.csv"), buf.getvalue())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--retry-failed", action="store_true")
    args = ap.parse_args()

    man = load_json(args.manifest)
    name = man["name"]
    enc, dec = rel(man["tools"]["vvencapp"]), rel(man["tools"]["vvdecapp"])
    common = man["encoder_common"]
    dec_threads = man["decoder_common"]["threads"]
    out_dir, log_dir = rel(f"results/{name}"), rel(f"logs/runs/{name}")
    bs_dir, rec_dir = rel(f"bitstreams/{name}"), rel(f"recon/{name}")
    runs_dir = os.path.join(out_dir, "runs")
    for d in (out_dir, log_dir, bs_dir, rec_dir, runs_dir):
        os.makedirs(d, exist_ok=True)
    vvenc_version, vvdec_version = first_line(enc, "--version"), first_line(dec, "--version")

    runs = [r for r in man["runs"] if not args.only or r["run_id"] in args.only]
    n_ok = n_failed = 0
    for idx, run in enumerate(runs, 1):
        rid = run["run_id"]
        tag = f"[{idx}/{len(runs)}] {rid}"
        run_json = os.path.join(runs_dir, f"{rid}.json")
        bs = os.path.join(bs_dir, f"{rid}.266")
        rec = os.path.join(rec_dir, f"{rid}_rec.yuv")
        artifacts = [bs, rec, run_json] + [os.path.join(log_dir, f"{rid}_{k}.log") for k in ("enc", "dec_timing", "dec_recon")] \
            + [os.path.join(runs_dir, f"{rid}_psnr.json"), os.path.join(runs_dir, f"{rid}_psnr_per_frame.csv")]
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if os.path.exists(run_json):
            prev = load_json(run_json)
            if prev.get("status") == "ok":
                n_ok += 1
                print(f"{tag}: already ok, skipping", flush=True)
                continue
            if not args.retry_failed:
                n_failed += 1
                print(f"{tag}: FAILED previously ({prev['row'].get('failed_checks')}); not re-run (use --retry-failed)",
                      flush=True)
                continue
            moved = move_aside(artifacts, rel(f"_attempts/{name}/{rid}_{stamp}"))
            print(f"{tag}: retrying failed run; previous files preserved: {len(moved)} moved to _attempts/", flush=True)
        elif any(os.path.exists(p) for p in artifacts):
            moved = move_aside(artifacts, rel(f"_interrupted/{name}/{rid}_{stamp}"))
            print(f"{tag}: interrupted earlier; {len(moved)} partial files preserved in _interrupted/, re-running", flush=True)

        seq = man["sequences"][run["sequence"]]
        w, h, fps, bd = seq["width"], seq["height"], seq["fps"], seq["bitdepth"]
        frames = run["frames"]
        threads = run.get("enc_threads", common["threads"])
        is_repeat = bool(run.get("repeat_of"))
        enc_cmd = [enc, "-i", rel(seq["file"]), "-s", f"{w}x{h}", "-c", common["format"], "--fps", str(fps),
                   "-f", str(frames), "-q", str(run["qp"]), "--preset", run["preset"], "--qpa", str(common["qpa"]),
                   "-t", str(threads), "-v", str(common["verbosity"]), *common.get("extra_args", []), "-o", bs]
        dec_time_cmd = [dec, "-b", bs, "-t", str(dec_threads)]
        dec_rec_cmd = [dec, "-b", bs, "-o", rec, "-t", str(dec_threads)]
        if args.dry_run:
            print(subprocess.list2cmdline(enc_cmd))
            continue

        ac, plan, mode = power_state()
        print(f"{tag}: encoding {frames} frames (QP {run['qp']}, {run['preset']}) ...", flush=True)
        e_code, e_wall, e_out, started = run_timed(enc_cmd, os.path.join(log_dir, f"{rid}_enc.log"))
        e = parse_encoder(e_out)
        row = {"run_id": rid, "sequence": run["sequence"], "width": w, "height": h, "fps": fps, "bitdepth": bd,
               "chroma": seq["chroma"], "frames": frames, "qp": run["qp"], "preset": run["preset"],
               "qpa": common["qpa"], "enc_threads": threads, "dec_threads": dec_threads,
               "groups": "+".join(run.get("groups", [])), "repeat_of": run.get("repeat_of", ""),
               "encode_exit": e_code, "encode_wall_s": round(e_wall, 3), "encode_reported_s": e["total_time_s"],
               "encode_fps_wall": round(frames / e_wall, 4), "ac_power": ac, "power_plan": plan,
               "power_mode": mode, "started": started,
               "vvenc_version": vvenc_version, "vvdec_version": vvdec_version,
               "intra_pocs": " ".join(f"{p}:{n}" for p, n in e["intra"]), "frames_I": e["frames_I"],
               "frames_B": e["frames_B"], "avg_qp_I": e["avg_qp_I"], "avg_qp_B": e["avg_qp_B"],
               "intra_period": e["notice"].get("Intra period (keyframe)"), "gop_size": e["notice"].get("GOP size"),
               "parallel_frames": e["notice"].get("Threads")}
        detail = {"run": run, "sequence": seq, "encoder_common": common, "encoder_cmd": subprocess.list2cmdline(enc_cmd),
                  "encoder": e}
        dec_timing = dec_recon = None
        original_sha = None
        if is_repeat:
            op = os.path.join(runs_dir, f"{run['repeat_of']}.json")
            original_sha = load_json(op)["row"].get("bitstream_sha256") if os.path.exists(op) else None

        if e_code == 0 and os.path.exists(bs):
            size = os.path.getsize(bs)
            row.update({"bitstream_bytes": size, "bitrate_kbps": round(size * 8 * fps / frames / 1000, 4),
                        "bitstream_sha256": sha256(bs)})
            if "summary" in e:
                s = e["summary"]
                row.update({"encoder_reported_kbps": s["kbps"], "enc_psnr_y": s["Y"], "enc_psnr_u": s["U"],
                            "enc_psnr_v": s["V"], "enc_psnr_yuv": s["YUV"]})

            print("    decoding (timing pass, no output) ...", flush=True)
            d_code, d_wall, d_out, _ = run_timed(dec_time_cmd, os.path.join(log_dir, f"{rid}_dec_timing.log"))
            dec_timing = parse_decoder(d_out)
            row.update({"decode_exit": d_code, "decode_wall_s": round(d_wall, 3),
                        "decode_reported_s": dec_timing["reported_s"]})
            detail.update({"decoder_timing_cmd": subprocess.list2cmdline(dec_time_cmd), "decoder_timing": dec_timing})

            if d_code == 0 and not is_repeat:
                print("    decoding (recon pass) + PSNR ...", flush=True)
                r_code, r_wall, r_out, _ = run_timed(dec_rec_cmd, os.path.join(log_dir, f"{rid}_dec_recon.log"))
                dec_recon = {**parse_decoder(r_out), "exit": r_code}
                detail.update({"decoder_recon_cmd": subprocess.list2cmdline(dec_rec_cmd), "decoder_recon": dec_recon})
                row["decode_recon_wall_s"] = round(r_wall, 3)
                if r_code == 0 and os.path.exists(rec):
                    frame_bytes = (w * h + 2 * (w // 2) * (h // 2)) * (2 if bd > 8 else 1)
                    rbytes = os.path.getsize(rec)
                    row.update({"recon_bytes": rbytes, "recon_frames_ok": rbytes == frames * frame_bytes})
                    if row["recon_frames_ok"]:
                        res, mse, pf = psnr_yuv.compute(rel(seq["file"]), rec, w, h, bd, frames)
                        psnr_yuv.write_outputs(os.path.join(runs_dir, rid), res, mse, pf)
                        p = res["peak1020"]
                        row.update({"psnr_y": round(p["avg_of_frame_psnr"]["Y"], 4),
                                    "psnr_u": round(p["avg_of_frame_psnr"]["U"], 4),
                                    "psnr_v": round(p["avg_of_frame_psnr"]["V"], 4),
                                    "psnr_yuv_411": round(p["yuv_411_mse"], 4),
                                    "psnr_yuv_611": round(p["yuv_611_psnr"], 4),
                                    "alignment_best_offset": res["alignment_best_offset"]})
                        if "summary" in e:
                            row["max_abs_psnr_diff_vs_encoder"] = round(max(
                                abs(row["psnr_y"] - e["summary"]["Y"]), abs(row["psnr_u"] - e["summary"]["U"]),
                                abs(row["psnr_v"] - e["summary"]["V"]),
                                abs(row["psnr_yuv_411"] - e["summary"]["YUV"])), 4)

        checks = checks_for(row, e, run, threads, frames, dec_timing, dec_recon, original_sha)
        failed = [k for k, v in checks.items() if not v]
        row["status"] = "ok" if not failed else "failed"
        row["failed_checks"] = " ".join(failed)
        detail.update({"checks": checks, "status": row["status"], "row": row, "finished": now_iso()})
        atomic_write_text(run_json, json.dumps(detail, indent=2))
        write_csv(man, out_dir)
        if failed:
            n_failed += 1
            print(f"    FAILED checks: {failed}", flush=True)
        else:
            n_ok += 1
        print(f"    {row['status']}: enc {row['encode_wall_s']} s (reported {row['encode_reported_s']}), "
              f"dec {row.get('decode_wall_s')} s, {row.get('bitstream_bytes')} B, Y-PSNR {row.get('psnr_y')}", flush=True)

    if not args.dry_run:
        write_csv(man, out_dir)
        print(f"SUMMARY: {n_ok} ok, {n_failed} failed, {len(runs)} in selection", flush=True)
        sys.exit(1 if n_failed else 0)


if __name__ == "__main__":
    main()
