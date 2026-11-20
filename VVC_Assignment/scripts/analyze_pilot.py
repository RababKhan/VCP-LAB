"""Turn pilot measurements into runtime / storage estimates for the full matrix.

Extrapolation model (stated, then checked by the pilot itself):
  full_time = (measured time / pilot frames) * content frames
The 'check_frame_linearity' run (BasketballPass 128 vs 64 frames) tests this model.

Usage: python analyze_pilot.py [results/pilot/results.csv]
Writes results/pilot/pilot_estimates.csv and results/pilot/pilot_summary.json
"""
import csv
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_manifest import SEQUENCES  # noqa: E402


def f(x):
    return float(x) if x not in ("", None) else None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "pilot", "results.csv")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    by_id = {r["run_id"]: r for r in rows}
    summary = {"runs": len(rows), "all_exit_zero": all(r["encode_exit"] == "0" and r["decode_exit"] == "0" for r in rows)}

    # Integrity checks across all non-repeat runs.
    main_rows = [r for r in rows if not r["repeat_of"]]
    summary["recon_frames_all_ok"] = all(r["recon_frames_ok"] == "True" for r in main_rows)
    summary["alignment_all_zero"] = all(r["alignment_best_offset"] == "0" for r in main_rows)
    summary["max_abs_psnr_diff_vs_encoder"] = max(f(r["max_abs_psnr_diff_vs_encoder"]) for r in main_rows)
    summary["max_abs_bitrate_diff_vs_encoder_kbps"] = max(
        abs(f(r["bitrate_kbps"]) - f(r["encoder_reported_kbps"])) for r in main_rows)
    summary["ac_power_all_runs"] = all(r["ac_power"] == "True" for r in rows)
    summary["power_plans"] = sorted({r["power_plan"] for r in rows})

    # Repeatability (same config three times).
    base = next((r for r in rows if r["groups"] == "qp_sweep+preset_sweep" and r["sequence"] == "BasketballPass"
                 and r["frames"] == "64" and r["enc_threads"] == "8"), None)
    reps = [base] + [r for r in rows if r["repeat_of"] == (base or {}).get("run_id")]
    if base and len(reps) > 1:
        def stats(key):
            v = [f(r[key]) for r in reps]
            return {"values": v, "mean": statistics.mean(v), "stdev": statistics.stdev(v),
                    "cv_percent": 100 * statistics.stdev(v) / statistics.mean(v)}
        summary["repeatability"] = {
            "run_ids": [r["run_id"] for r in reps],
            "bitstreams_identical": len({r["bitstream_sha256"] for r in reps}) == 1,
            "encode_wall_s": stats("encode_wall_s"), "encode_reported_s": stats("encode_reported_s"),
            "decode_wall_s": stats("decode_wall_s"),
        }

    # Timing reference for the base config = median of its repeats (the first run can be an outlier).
    med_wall = statistics.median(f(r["encode_wall_s"]) for r in reps) if base else None
    med_rep = statistics.median(f(r["encode_reported_s"]) for r in reps) if base else None

    # Thread count (t4 vs t8, same config).
    t4 = next((r for r in rows if r["groups"] == "check_thread_count"), None)
    if base and t4:
        summary["thread_count"] = {
            "encode_wall_s": {"t8_median_of_3": med_wall, "t4_single": f(t4["encode_wall_s"])},
            "encode_reported_s": {"t8_median_of_3": med_rep, "t4_single": f(t4["encode_reported_s"])},
            **{k: {"t8": base[k], "t4": t4[k]} for k in ("bitstream_bytes", "psnr_y", "psnr_yuv_411", "parallel_frames")},
            "bitstreams_identical": base["bitstream_sha256"] == t4["bitstream_sha256"],
        }

    # Frame-count linearity (128 vs 64 frames).
    lin = next((r for r in rows if r["groups"] == "check_frame_linearity"), None)
    if base and lin:
        p64 = med_rep / 64
        p128 = f(lin["encode_reported_s"]) / 128
        summary["frame_linearity"] = {
            "enc_reported_s_per_frame_f64_median_of_3": p64, "enc_reported_s_per_frame_f128": p128,
            "ratio_f128_over_f64": p128 / p64,
            "enc_reported_s_per_frame_f64_first_run": f(base["encode_reported_s"]) / 64,
            "bytes_per_frame_f64": f(base["bitstream_bytes"]) / 64,
            "bytes_per_frame_f128": f(lin["bitstream_bytes"]) / 128,
        }

    # Full-matrix estimates from the 8 unique configs per sequence.
    est = []
    for r in rows:
        if r["groups"] not in ("qp_sweep", "preset_sweep", "qp_sweep+preset_sweep") or r["enc_threads"] != "8":
            continue
        seq = SEQUENCES[r["sequence"]]
        n_pilot, n_full = int(r["frames"]), seq["content_frames"]
        scale = n_full / n_pilot
        frame_bytes = seq["width"] * seq["height"] * 3 // 2 * 2
        est.append({
            "sequence": r["sequence"], "qp": int(r["qp"]), "preset": r["preset"], "groups": r["groups"],
            "pilot_frames": n_pilot, "full_frames": n_full,
            "pilot_enc_wall_s": f(r["encode_wall_s"]), "pilot_enc_reported_s": f(r["encode_reported_s"]),
            "pilot_dec_wall_s": f(r["decode_wall_s"]), "pilot_dec_recon_wall_s": f(r["decode_recon_wall_s"]),
            "pilot_enc_fps_reported": n_pilot / f(r["encode_reported_s"]),
            "est_full_enc_wall_s": f(r["encode_wall_s"]) * scale,
            "est_full_dec_wall_s": (f(r["decode_wall_s"]) + f(r["decode_recon_wall_s"])) * scale,
            "est_full_bitstream_bytes": f(r["bitstream_bytes"]) * scale,
            "full_recon_bytes": n_full * frame_bytes,
        })
    out_csv = os.path.join(os.path.dirname(path), "pilot_estimates.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(est[0]))
        wr.writeheader()
        wr.writerows(est)

    per_seq = {}
    for e in est:
        s = per_seq.setdefault(e["sequence"], {"configs": 0, "enc_h": 0.0, "dec_h": 0.0, "bitstream_MB": 0.0, "recon_GB": 0.0})
        s["configs"] += 1
        s["enc_h"] += e["est_full_enc_wall_s"] / 3600
        s["dec_h"] += e["est_full_dec_wall_s"] / 3600
        s["bitstream_MB"] += e["est_full_bitstream_bytes"] / 1e6
        s["recon_GB"] += e["full_recon_bytes"] / 1e9
    summary["full_matrix_estimate_per_sequence"] = per_seq
    summary["full_matrix_estimate_total"] = {k: sum(v[k] for v in per_seq.values())
                                             for k in ("configs", "enc_h", "dec_h", "bitstream_MB", "recon_GB")}
    per_preset = {}
    for e in est:
        if "preset_sweep" in e["groups"]:
            per_preset.setdefault(e["preset"], {})[e["sequence"]] = round(e["est_full_enc_wall_s"] / 60, 1)
    summary["est_full_enc_minutes_by_preset_qp32"] = per_preset

    with open(os.path.join(os.path.dirname(path), "pilot_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
