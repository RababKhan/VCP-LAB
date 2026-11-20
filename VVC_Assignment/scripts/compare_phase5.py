"""Phase 5 cross-platform comparison: Linux (WSL2, GCC 13.3) vs Windows (MSVC 19.44) 16-frame smoke test.

Reads the Linux smoke outputs from the WSL filesystem, copies them into the project (bitstreams/phase5_linux,
recon/phase5_linux) without touching any Windows file, computes PSNR with the same scripts/psnr_yuv.py used
for Windows, and compares bitstream/recon SHA256, sizes, frame counts, PSNR, encoder configuration echo,
per-picture encoder log lines and timing (timing is reported, not benchmarked).

Outputs: results/phase5_linux/ (cross_platform_comparison.json/.md/.csv, *_psnr.json, encoder log diff)

Usage: python compare_phase5.py
"""
import csv
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import psnr_yuv  # noqa: E402
from vvc_runner import parse_decoder, parse_encoder  # noqa: E402

WSL_SMOKE = r"\\wsl.localhost\Ubuntu-24.04\home\vvcuser\vvc_linux\smoke"
TAG = "BasketballPass_f16_QP32_faster_qpa0_t4"
SRC = os.path.join(ROOT, "dataset", "BasketballPass_416_240_50_10_420.yuv")
W, H, BD, N = 416, 240, 10, 16
OUT = os.path.join(ROOT, "results", "phase5_linux")
REPS = ["", "_rep2", "_rep3"]
WIN = {"bs": os.path.join(ROOT, "bitstreams", "smoke", f"{TAG}.266"),
       "rec": os.path.join(ROOT, "recon", "smoke", f"{TAG}_rec.yuv"),
       "enc_log": os.path.join(ROOT, "logs", "phase3_smoke_encode.log"),
       "dec_log": os.path.join(ROOT, "logs", "phase3_smoke_decode.log"),
       "psnr": os.path.join(ROOT, "results", "smoke", f"{TAG}_psnr.json")}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(1 << 22):
            h.update(b)
    return h.hexdigest()


def read_log(p):
    return open(p, encoding="utf-8-sig", errors="replace").read().replace("\r\n", "\n")


def wall(log):
    m = re.search(r"Wall time \(s\): ([\d.]+)", log)
    return float(m.group(1)) if m else None


def exit_code(log):
    m = re.search(r"Exit code: (-?\d+)", log)
    return int(m.group(1)) if m else None


def normalise(log):
    """Encoder log without paths, timestamps, timing and the platform banner, for a line-by-line diff."""
    keep = []
    for line in log.splitlines():
        if line.startswith(("Command:", "Started:", "Exit code:", "Wall time")):
            continue
        if re.search(r"(Input File|Bitstream File)\s+:", line) or "started @" in line or "finished @" in line:
            continue
        line = re.sub(r"Total Time:.*", "Total Time: <t>", line)
        line = re.sub(r"\[ET\s+\d+\s*\]", "[ET <t>]", line)
        line = re.sub(r"version 1\.14\.0 \[.*\]", "version 1.14.0 [<platform>]", line)
        keep.append(line.rstrip())
    return keep


def side(bs, rec, enc_log_p, dec_log_p):
    el, dl = read_log(enc_log_p), read_log(dec_log_p)
    e, d = parse_encoder(el), parse_decoder(dl)
    frame_bytes = (W * H + 2 * (W // 2) * (H // 2)) * 2
    return {"bitstream_sha256": sha256(bs), "bitstream_bytes": os.path.getsize(bs),
            "recon_sha256": sha256(rec), "recon_bytes": os.path.getsize(rec),
            "recon_frames": os.path.getsize(rec) / frame_bytes,
            "encode_exit": exit_code(el), "decode_exit": exit_code(dl),
            "encode_wall_s": wall(el), "encode_reported_s": e["total_time_s"],
            "decode_wall_s": wall(dl), "decode_reported_s": d["reported_s"], "decoded_frames": d["frames"],
            "encoder_pictures": e["pictures"], "encoder_summary": e.get("summary"),
            "intra": e["intra"], "banner": next((l for l in el.splitlines() if "version 1.14.0" in l), ""),
            "notice": e["notice"]}, el


def main():
    os.makedirs(OUT, exist_ok=True)
    bs_dir, rec_dir = os.path.join(ROOT, "bitstreams", "phase5_linux"), os.path.join(ROOT, "recon", "phase5_linux")
    os.makedirs(bs_dir, exist_ok=True)
    os.makedirs(rec_dir, exist_ok=True)
    res = {"source": SRC, "source_sha256": sha256(SRC), "windows": {}, "linux": {}}

    win, win_log = side(WIN["bs"], WIN["rec"], WIN["enc_log"], WIN["dec_log"])
    wp = json.load(open(WIN["psnr"], encoding="utf-8-sig"))
    win["psnr_peak1020"] = wp["peak1020"]["avg_of_frame_psnr"] | {"YUV_411": wp["peak1020"]["yuv_411_mse"]}
    res["windows"] = win

    lin_logs = {}
    for r in REPS:
        bs = os.path.join(bs_dir, f"{TAG}{r}.266")
        rec = os.path.join(rec_dir, f"{TAG}{r}_rec.yuv")
        for src, dst in ((os.path.join(WSL_SMOKE, f"{TAG}{r}.266"), bs), (os.path.join(WSL_SMOKE, f"{TAG}{r}_rec.yuv"), rec)):
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            assert sha256(src) == sha256(dst), f"copy mismatch {dst}"
        s, lin_logs[r] = side(bs, rec, os.path.join(ROOT, "logs", f"phase5_07_smoke_encode{r}.log"),
                              os.path.join(ROOT, "logs", f"phase5_07_smoke_decode{r}.log"))
        pr, mse, pf = psnr_yuv.compute(SRC, rec, W, H, BD, N)
        psnr_yuv.write_outputs(os.path.join(OUT, f"{TAG}{r}_linux"), pr, mse, pf)
        s["psnr_peak1020"] = pr["peak1020"]["avg_of_frame_psnr"] | {"YUV_411": pr["peak1020"]["yuv_411_mse"]}
        s["alignment_best_offset"] = pr["alignment_best_offset"]
        res["linux"][r or "run1"] = s

    L = res["linux"]["run1"]
    notice_diff = {k: (win["notice"].get(k), L["notice"].get(k)) for k in sorted(set(win["notice"]) | set(L["notice"]))
                   if win["notice"].get(k) != L["notice"].get(k) and k not in ("Input File", "Bitstream File")}
    log_diff = list(difflib.unified_diff(normalise(win_log), normalise(lin_logs[""]), "windows_encode", "linux_encode",
                                         lineterm="", n=0))
    with open(os.path.join(OUT, "encoder_log_diff_windows_vs_linux.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log_diff) + "\n" if log_diff else "(no differences after removing paths, timestamps, timing and banner)\n")
    res["checks"] = {
        "linux_runs_deterministic_bitstream": len({v["bitstream_sha256"] for v in res["linux"].values()}) == 1,
        "linux_runs_deterministic_recon": len({v["recon_sha256"] for v in res["linux"].values()}) == 1,
        "bitstream_identical_windows_linux": win["bitstream_sha256"] == L["bitstream_sha256"],
        "recon_identical_windows_linux": win["recon_sha256"] == L["recon_sha256"],
        "bitstream_bytes_equal": win["bitstream_bytes"] == L["bitstream_bytes"],
        "recon_frames_16_both": win["recon_frames"] == 16 and L["recon_frames"] == 16,
        "decoded_frames_16_both": win["decoded_frames"] == 16 and L["decoded_frames"] == 16,
        "exit_codes_zero_both": all(x == 0 for x in (win["encode_exit"], win["decode_exit"], L["encode_exit"], L["decode_exit"])),
        "psnr_identical_windows_linux": win["psnr_peak1020"] == L["psnr_peak1020"],
        "linux_psnr_matches_encoder_log": all(abs(L["psnr_peak1020"][c] - L["encoder_summary"][c]) < 5e-5 for c in "YUV"),
        "encoder_config_echo_identical": not notice_diff,
        "encoder_log_identical_after_normalisation": not log_diff,
    }
    res["encoder_config_differences"] = notice_diff
    res["encoder_log_diff_lines"] = len(log_diff)
    with open(os.path.join(OUT, "cross_platform_comparison.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=str)

    rows = [("Encode exit code", win["encode_exit"], L["encode_exit"]),
            ("Decode exit code", win["decode_exit"], L["decode_exit"]),
            ("Encoder pictures", win["encoder_pictures"], L["encoder_pictures"]),
            ("Decoded frames (decoder log)", win["decoded_frames"], L["decoded_frames"]),
            ("Recon bytes", win["recon_bytes"], L["recon_bytes"]),
            ("Recon frames (bytes / 299,520)", win["recon_frames"], L["recon_frames"]),
            ("Bitstream bytes", win["bitstream_bytes"], L["bitstream_bytes"]),
            ("Bitstream SHA256", win["bitstream_sha256"], L["bitstream_sha256"]),
            ("Recon SHA256", win["recon_sha256"], L["recon_sha256"]),
            ("Y-PSNR (dB, peak 1020)", win["psnr_peak1020"]["Y"], L["psnr_peak1020"]["Y"]),
            ("U-PSNR (dB)", win["psnr_peak1020"]["U"], L["psnr_peak1020"]["U"]),
            ("V-PSNR (dB)", win["psnr_peak1020"]["V"], L["psnr_peak1020"]["V"]),
            ("YUV-PSNR (dB, 4:1:1 MSE)", win["psnr_peak1020"]["YUV_411"], L["psnr_peak1020"]["YUV_411"]),
            ("Encoder-reported kbps", win["encoder_summary"]["kbps"], L["encoder_summary"]["kbps"]),
            ("Intra pictures (POC:type)", win["intra"], L["intra"]),
            ("Encode wall time (s)", win["encode_wall_s"], L["encode_wall_s"]),
            ("Encode reported time (s)", win["encode_reported_s"], L["encode_reported_s"]),
            ("Decode wall time (s)", win["decode_wall_s"], L["decode_wall_s"]),
            ("Decode reported time (s)", win["decode_reported_s"], L["decode_reported_s"])]
    buf = io.StringIO()
    wr = csv.writer(buf)
    wr.writerow(["metric", "windows", "linux_run1"])
    wr.writerows(rows)
    with open(os.path.join(OUT, "cross_platform_comparison.csv"), "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())
    md = ["| Metric | Windows (MSVC) | Linux (GCC, WSL2) | Same? |", "|---|---|---|---|"]
    for name, a, b in rows:
        same = "n/a (not a benchmark)" if "time" in name else ("yes" if a == b else "**no**")
        md.append(f"| {name} | {a} | {b} | {same} |")
    md += ["", "Linux repeats (determinism):", "",
           "| Linux run | Bitstream SHA256 | Recon SHA256 | Encode wall (s) | Encode reported (s) | Decode wall (s) |",
           "|---|---|---|---|---|---|"]
    for k, v in res["linux"].items():
        md.append(f"| {k} | {v['bitstream_sha256'][:16]}… | {v['recon_sha256'][:16]}… | {v['encode_wall_s']} | "
                  f"{v['encode_reported_s']} | {v['decode_wall_s']} |")
    md += ["", "Checks:", ""] + [f"- {k}: {v}" for k, v in res["checks"].items()]
    with open(os.path.join(OUT, "cross_platform_comparison.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
