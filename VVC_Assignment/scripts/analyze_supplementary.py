"""Compare the supplementary AC-powered runs (results/supp_ac) with the original full-run measurements.

Original values are only read, never modified. For every supplementary run:
  * bitstream SHA256 / size vs the original, decoded frame count, PSNR vs the original and vs the encoder
  * encode wall, encode reported, decode wall (timing pass) and recon-decode wall times, with
    percentage difference (supplementary - original) / original
  * power exposure: supervisor power samples (2 s) and typeperf CPU counters (5 s) during the run
Timing validity comes from results/supp_ac/supplementary_status.json (AC + Best performance in every sample).

Outputs: results/supp_ac/timing_comparison.csv, supp_comparison.md, supp_summary.json

Usage: python analyze_supplementary.py
"""
import csv
import io
import json
import os
import statistics
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL, SUPP = os.path.join(ROOT, "results", "full"), os.path.join(ROOT, "results", "supp_ac")
TIMES = [("encode_wall_s", "Encode wall (s)"), ("encode_reported_s", "Encode reported (s)"),
         ("decode_wall_s", "Decode wall, timing pass (s)"), ("decode_recon_wall_s", "Decode wall, recon pass (s)")]


def fnum(x):
    return float(x) if x not in ("", None) else None


def atomic_write(path, text):
    with open(path + ".tmp", "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(path + ".tmp", path)


def parse_t(s):
    return datetime.fromisoformat(s).replace(tzinfo=None)


def read_cpu(path):
    """typeperf CSV -> list of (time, perf %, utility %, MHz, thermal C). Thermal zone is reported in kelvin."""
    out = []
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.reader(f))
    for r in rows[1:]:
        try:
            t = datetime.strptime(r[0], "%m/%d/%Y %H:%M:%S.%f")
            vals = [float(v) if v.strip() else None for v in r[1:5]]
        except (ValueError, IndexError):
            continue
        out.append((t, vals[0], vals[1], vals[2], vals[3] - 273.15 if vals[3] is not None else None))
    return out


def read_power(path):
    with open(path, encoding="utf-8") as f:
        return [(parse_t(r["timestamp"]), r["run_id"], r["ac_power"], r["battery_pct"], r["battery_saver"],
                 r["power_mode"]) for r in csv.DictReader(f)]


def power_label(exposure):
    """Describe how much of an original run the full-run monitor saw on battery."""
    if not exposure:
        return "AC"
    mon = exposure["battery_samples"] - exposure.get("started_on_battery", False)
    if exposure.get("started_on_battery") and mon == exposure["samples"]:
        return "battery (whole run)"
    return f"partly battery ({mon} of {exposure['samples']} 30-s samples)"


def main():
    status = json.load(open(os.path.join(SUPP, "supplementary_status.json"), encoding="utf-8"))
    full_rows = {r["run_id"]: r for r in csv.DictReader(open(os.path.join(FULL, "results.csv"), encoding="utf-8"))}
    full_flags = json.load(open(os.path.join(FULL, "analysis_summary.json"), encoding="utf-8"))
    bat_runs = full_flags.get("runs_with_battery_samples", {})
    cpu = read_cpu(os.path.join(ROOT, status["logs"]["cpu"]))
    power = read_power(os.path.join(ROOT, status["logs"]["power"]))

    comp, summary_runs = [], {}
    for rid, st in status["runs"].items():
        orig_id = st["verifies"]
        o = full_rows[orig_id]
        rj = os.path.join(SUPP, "runs", f"{rid}.json")
        s = json.load(open(rj, encoding="utf-8"))["row"] if os.path.exists(rj) else None
        entry = {"run_id": rid, "original_run_id": orig_id, "supervisor_result": st.get("result"),
                 "timing_valid_ac": st.get("timing_valid"), "reason": st.get("reason"),
                 "original_power_exposure": bat_runs.get(orig_id, "AC throughout")}
        if s is None:
            summary_runs[rid] = entry
            continue
        is_warm = "warmup" in o["groups"]
        entry.update({
            "runner_status": s["status"],
            "bitstream_sha256_identical": s["bitstream_sha256"] == o["bitstream_sha256"],
            "bitstream_bytes": [int(o["bitstream_bytes"]), s["bitstream_bytes"]],
            "decoded_frames_ok": s.get("recon_frames_ok") is True,
            "psnr_identical_to_original": all(fnum(o[k]) == s.get(k) for k in
                                              ("psnr_y", "psnr_u", "psnr_v", "psnr_yuv_411")),
            "max_abs_psnr_diff_vs_encoder": s.get("max_abs_psnr_diff_vs_encoder"),
            "intra_pocs_identical": s.get("intra_pocs") == o["intra_pocs"],
            "vvenc_version_identical": s.get("vvenc_version") == o["vvenc_version"],
            "vvdec_version_identical": s.get("vvdec_version") == o["vvdec_version"],
            "settings_identical": all(str(s.get(k)) == o[k] for k in
                                      ("frames", "qp", "preset", "qpa", "enc_threads", "dec_threads",
                                       "gop_size", "intra_period")),
        })
        t0 = parse_t(st["launched"])
        t1 = parse_t(st["finished"])
        win = [c for c in cpu if t0 <= c[0] <= t1]
        perf = [c[1] for c in win if c[1] is not None]
        temp = [c[4] for c in win if c[4] is not None]
        pw = [p for p in power if p[1] == rid]
        entry["power_monitor"] = {"power_samples": len(pw), "ac_samples": sum(p[2] == "True" for p in pw),
                                  "best_perf_samples": sum(p[5] == "Best performance" for p in pw),
                                  "battery_pct_range": [min(int(p[3]) for p in pw), max(int(p[3]) for p in pw)] if pw else None,
                                  "battery_saver_samples": sum(p[4] == "True" for p in pw)}
        entry["cpu_monitor"] = {"samples": len(win),
                                "perf_pct_median": round(statistics.median(perf), 1) if perf else None,
                                "perf_pct_min": round(min(perf), 1) if perf else None,
                                "perf_pct_max": round(max(perf), 1) if perf else None,
                                "samples_perf_below_80": sum(p < 80 for p in perf),
                                "thermal_zone_C_max": round(max(temp), 1) if temp else None}
        for key, label in TIMES:
            ov, sv = fnum(o.get(key)), s.get(key)
            diff = 100 * (sv - ov) / ov if ov and sv is not None else None
            comp.append({"configuration": orig_id, "warmup": is_warm, "metric": key,
                         "original": ov, "original_power": power_label(bat_runs.get(orig_id)),
                         "supplementary_ac": sv, "supplementary_timing_valid": st.get("timing_valid"),
                         "diff_pct": round(diff, 2) if diff is not None else None})
        summary_runs[rid] = entry

    buf = io.StringIO()
    if comp:
        w = csv.DictWriter(buf, fieldnames=list(comp[0]))
        w.writeheader()
        w.writerows(comp)
        atomic_write(os.path.join(SUPP, "timing_comparison.csv"), buf.getvalue())

    md = ["# Supplementary AC-powered timing verification (generated by scripts/analyze_supplementary.py)", "",
          "Original = full run (results/full, unchanged). Supplementary = results/supp_ac. "
          "Diff = (supplementary - original) / original.", "",
          "| Configuration | Metric | Original (s) | Original power | Supplementary, AC (s) | Valid AC timing | Diff |",
          "|---|---|---|---|---|---|---|"]
    for c in comp:
        md.append(f"| {c['configuration']}{' (warm-up)' if c['warmup'] else ''} | {c['metric']} | {c['original']} | "
                  f"{c['original_power']} | {c['supplementary_ac']} | {c['supplementary_timing_valid']} | "
                  f"{c['diff_pct']:+.2f}% |" if c["diff_pct"] is not None else
                  f"| {c['configuration']} | {c['metric']} | {c['original']} | {c['original_power']} | "
                  f"{c['supplementary_ac']} | {c['supplementary_timing_valid']} | n/a |")
    md += ["", "| Supplementary run | Result | Valid AC timing | Bitstream SHA256 identical | PSNR identical | "
               "Decoded frames ok | Power samples (AC / total) | CPU perf % median (min) | Thermal zone max °C |",
           "|---|---|---|---|---|---|---|---|---|"]
    for rid, e in summary_runs.items():
        pm, cm = e.get("power_monitor", {}), e.get("cpu_monitor", {})
        md.append(f"| {rid} | {e['supervisor_result']} | {e['timing_valid_ac']} | {e.get('bitstream_sha256_identical')} | "
                  f"{e.get('psnr_identical_to_original')} | {e.get('decoded_frames_ok')} | "
                  f"{pm.get('ac_samples')} / {pm.get('power_samples')} | "
                  f"{cm.get('perf_pct_median')} ({cm.get('perf_pct_min')}) | {cm.get('thermal_zone_C_max')} |")
    atomic_write(os.path.join(SUPP, "supp_comparison.md"), "\n".join(md) + "\n")
    out = {"stopped_reason": status.get("stopped_reason"), "results_full_unchanged": status.get("results_full_unchanged"),
           "runs": summary_runs}
    atomic_write(os.path.join(SUPP, "supp_summary.json"), json.dumps(out, indent=2, default=str))
    print("\n".join(md))
    ok = all(e.get("timing_valid_ac") and e.get("bitstream_sha256_identical") for e in summary_runs.values())
    sys.exit(0 if ok and len(summary_runs) == len(status["runs"]) else 1)


if __name__ == "__main__":
    main()
