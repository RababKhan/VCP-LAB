"""Supervisor for the supplementary AC-powered timing verification (configs/supp_ac_manifest.json).

Measurement itself is unchanged: every run is executed by scripts/vvc_runner.py (--only <run_id>), i.e. the
same encoder/decoder commands, timing and PSNR code as the full run. This script adds an active power guard:

  * preflight: AC power, Windows power mode = Best performance, executables / datasets / manifest checksums,
    disk space, and a fingerprint of results/full (proves the original results stay unchanged)
  * before every run: AC + Best performance, otherwise no further run is launched
  * during every run: AC line status and the effective power mode are polled every POLL_S seconds
    (Win32 GetSystemPowerStatus / PowerGetEffectiveOverlayScheme) and logged; CPU counters are logged
    every 5 s by the built-in typeperf. If AC is lost or the mode changes, the run is stopped
    (taskkill /T), marked INVALID and the experiment stops. Partial files and logs are kept.
  * a completed run counts as valid AC timing only if every power sample during it was AC + Best performance

Status of every run: results/supp_ac/supplementary_status.json (rewritten atomically after each event).

Usage: python run_supplementary_ac.py [--preflight-only] [--manifest PATH] [--simulate-ac-loss-after N]
  --simulate-ac-loss-after N  self-test only: report AC as lost from the N-th power sample on (0 = before the
                              first launch); used to verify the guard without unplugging the charger
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from vvc_runner import POWER_MODES, atomic_write_text, sha256  # noqa: E402

MANIFEST = os.path.join(ROOT, "configs", "supp_ac_manifest.json")
FULL_MANIFEST_SHA = "f96b1ebf3fae61bccb5ada1ad8355b85e5960ea37fcb51d7be4868702199b02b"
EXE_SHA = {"vvencapp": "c74f3b63e331805f3cac74ab1e0849f0c7877fa885de44d32119927425b3160b",
           "vvdecapp": "3f46677abee5bef1c2c272752d6b04222c06a48eaa983b848f623d8dbc2499b6"}
BEST_PERF = "Best performance"
POLL_S = 2
MIN_FREE_GIB = 15
CPU_COUNTERS = [r"\Processor Information(_Total)\% Processor Performance",
                r"\Processor Information(_Total)\% Processor Utility",
                r"\Processor Information(_Total)\Processor Frequency",
                r"\Thermal Zone Information(*)\Temperature"]


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [("ACLineStatus", wt.BYTE), ("BatteryFlag", wt.BYTE), ("BatteryLifePercent", wt.BYTE),
                ("SystemStatusFlag", wt.BYTE), ("BatteryLifeTime", wt.DWORD), ("BatteryFullLifeTime", wt.DWORD)]


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wt.DWORD), ("Data2", wt.WORD), ("Data3", wt.WORD), ("Data4", ctypes.c_ubyte * 8)]

    def __str__(self):
        d4 = bytes(self.Data4)
        return f"{self.Data1:08x}-{self.Data2:04x}-{self.Data3:04x}-{d4[:2].hex()}-{d4[2:].hex()}"


SIMULATE_LOSS_AFTER = None
_samples_taken = 0


def power_sample():
    """(ac: bool|None, battery %, battery saver on, power mode name)."""
    global _samples_taken
    s = SYSTEM_POWER_STATUS()
    ok = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s))
    g = GUID()
    rc = ctypes.windll.powrprof.PowerGetEffectiveOverlayScheme(ctypes.byref(g))
    mode = POWER_MODES.get(str(g), str(g)) if rc == 0 else f"error {rc}"
    ac = {1: True, 0: False}.get(s.ACLineStatus) if ok else None
    if SIMULATE_LOSS_AFTER is not None and _samples_taken >= SIMULATE_LOSS_AFTER:
        ac = False  # self-test only
    _samples_taken += 1
    return ac, s.BatteryLifePercent, bool(s.SystemStatusFlag & 1), mode


def now():
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def tree_fingerprint(path):
    """SHA256 over (relative path, size, sha256) of every file under path."""
    h = hashlib.sha256()
    n = 0
    for p in sorted(glob.glob(os.path.join(path, "**", "*"), recursive=True)):
        if os.path.isfile(p):
            h.update(f"{os.path.relpath(p, path)}|{os.path.getsize(p)}|{sha256(p)}\n".encode())
            n += 1
    return h.hexdigest(), n


def preflight(man):
    checks = {}
    ac, pct, saver, mode = power_sample()
    checks["ac_power"] = (ac is True, f"AC={ac}, battery {pct}%, battery saver {'on' if saver else 'off'}")
    checks["power_mode_best_performance"] = (mode == BEST_PERF, mode)
    full_sha = sha256(os.path.join(ROOT, "configs", "full_manifest.json"))
    checks["full_manifest_unchanged"] = (full_sha == FULL_MANIFEST_SHA, full_sha)
    for k in ("vvencapp", "vvdecapp"):
        h = sha256(os.path.join(ROOT, man["tools"][k]))
        checks[f"{k}_sha256"] = (h == EXE_SHA[k], h)
    for name, s in man["sequences"].items():
        h = sha256(os.path.join(ROOT, s["file"]))
        checks[f"dataset_{name}_sha256"] = (h == s["sha256"], h)
    free = shutil.disk_usage(ROOT).free / 2**30
    checks["disk_free"] = (free >= MIN_FREE_GIB, f"{free:.2f} GiB free (need >= {MIN_FREE_GIB})")
    full_fp = tree_fingerprint(os.path.join(ROOT, "results", "full"))
    checks["results_full_fingerprint"] = (True, f"{full_fp[0]} ({full_fp[1]} files)")
    return checks, full_fp


def main():
    global SIMULATE_LOSS_AFTER, _samples_taken
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=MANIFEST)
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--simulate-ac-loss-after", type=int)
    args = ap.parse_args()
    manifest = os.path.abspath(args.manifest)
    man = json.load(open(manifest, encoding="utf-8"))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    res_dir = os.path.join(ROOT, "results", man["name"])
    os.makedirs(res_dir, exist_ok=True)
    status_path = os.path.join(res_dir, "supplementary_status.json")
    power_log = os.path.join(ROOT, "logs", f"{man['name']}_power_{stamp}.csv")
    cpu_log = os.path.join(ROOT, "logs", f"{man['name']}_cpu_{stamp}.csv")
    console_log = os.path.join(ROOT, "logs", f"{man['name']}_console_{stamp}.log")

    print("PREFLIGHT", flush=True)
    checks, full_fp = preflight(man)
    for k, (ok, info) in checks.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {k}: {info}", flush=True)
    status = {"manifest": os.path.relpath(manifest, ROOT), "manifest_sha256": sha256(manifest), "started": now(),
              "simulated_ac_loss_after": args.simulate_ac_loss_after,
              "preflight": {k: {"pass": ok, "info": info} for k, (ok, info) in checks.items()},
              "results_full_fingerprint_before": full_fp[0], "logs": {
                  "power": os.path.relpath(power_log, ROOT), "cpu": os.path.relpath(cpu_log, ROOT),
                  "console": os.path.relpath(console_log, ROOT)}, "runs": {}, "stopped_reason": None}
    if not all(ok for ok, _ in checks.values()):
        status["stopped_reason"] = "preflight failed"
        atomic_write_text(status_path.replace(".json", f"_preflight_fail_{stamp}.json"), json.dumps(status, indent=2))
        print("PREFLIGHT FAILED: nothing launched", flush=True)
        sys.exit(3)
    if args.preflight_only:
        print("preflight only: nothing launched", flush=True)
        return
    if os.path.exists(status_path):  # keep an earlier attempt's status file
        os.replace(status_path, status_path.replace(".json", f"_before_{stamp}.json"))

    def save():
        atomic_write_text(status_path, json.dumps(status, indent=2))

    save()
    SIMULATE_LOSS_AFTER, _samples_taken = args.simulate_ac_loss_after, 0  # applies after the real preflight
    typeperf = subprocess.Popen(["typeperf", *CPU_COUNTERS, "-si", "5", "-f", "CSV", "-o", cpu_log, "-y"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    plog = open(power_log, "w", encoding="utf-8", newline="")
    plog.write("timestamp,run_id,ac_power,battery_pct,battery_saver,power_mode\n")
    console = open(console_log, "a", encoding="utf-8")

    def sample(rid):
        ac, pct, saver, mode = power_sample()
        plog.write(f"{now()},{rid},{ac},{pct},{saver},{mode}\n")
        plog.flush()
        return ac, mode

    try:
        for run in man["runs"]:
            rid = run["run_id"]
            ac, mode = sample(rid + ":prelaunch")
            entry = {"verifies": run["verifies"], "launched": None, "finished": None, "power_samples": 0,
                     "non_ac_samples": 0, "non_best_perf_samples": 0}
            status["runs"][rid] = entry
            if ac is not True or mode != BEST_PERF:
                entry.update({"result": "NOT LAUNCHED", "timing_valid": False,
                              "reason": f"pre-launch check failed: AC={ac}, mode={mode}"})
                status["stopped_reason"] = entry["reason"]
                save()
                print(f"STOP before {rid}: {entry['reason']}", flush=True)
                break
            entry["launched"] = now()
            save()
            print(f"LAUNCH {rid} (AC, {mode})", flush=True)
            console.write(f"\n=== {entry['launched']} {rid} ===\n")
            console.flush()
            p = subprocess.Popen([sys.executable, "-u", os.path.join(ROOT, "scripts", "vvc_runner.py"), manifest,
                                  "--only", rid], stdout=console, stderr=subprocess.STDOUT)
            abort = None
            while p.poll() is None:
                ac, mode = sample(rid)
                entry["power_samples"] += 1
                entry["non_ac_samples"] += ac is not True
                entry["non_best_perf_samples"] += mode != BEST_PERF
                if ac is not True or mode != BEST_PERF:
                    abort = f"during run: AC={ac}, mode={mode} at {now()}"
                    subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
                    p.wait()
                    break
                time.sleep(POLL_S)
            entry["finished"] = now()
            entry["runner_exit"] = p.returncode
            rj = os.path.join(res_dir, "runs", f"{rid}.json")
            entry["runner_status"] = json.load(open(rj, encoding="utf-8"))["status"] if os.path.exists(rj) else None
            if abort:
                entry.update({"result": "INTERRUPTED", "timing_valid": False, "reason": abort})
                status["stopped_reason"] = f"{rid}: {abort}"
                save()
                print(f"INVALID {rid}: {abort}; experiment stopped (partial files and logs kept)", flush=True)
                break
            valid = (entry["runner_status"] == "ok" and entry["non_ac_samples"] == 0
                     and entry["non_best_perf_samples"] == 0 and entry["power_samples"] > 0)
            entry.update({"result": "COMPLETED" if entry["runner_status"] == "ok" else "FAILED CHECKS",
                          "timing_valid": valid,
                          "reason": "AC + Best performance in every power sample" if valid else
                          f"runner status {entry['runner_status']}, non-AC samples {entry['non_ac_samples']}"})
            save()
            print(f"DONE {rid}: {entry['result']}, timing valid = {valid} ({entry['power_samples']} power samples)",
                  flush=True)
            if entry["runner_status"] != "ok":
                status["stopped_reason"] = f"{rid}: runner checks failed"
                save()
                break
    finally:
        typeperf.terminate()
        plog.close()
        console.close()
        fp_after = tree_fingerprint(os.path.join(ROOT, "results", "full"))
        status["results_full_fingerprint_after"] = fp_after[0]
        status["results_full_unchanged"] = fp_after[0] == full_fp[0]
        status["ended"] = now()
        save()
    n_valid = sum(e.get("timing_valid") is True for e in status["runs"].values())
    print(f"SUMMARY: {n_valid}/{len(man['runs'])} runs with valid AC timing; results/full unchanged = "
          f"{status['results_full_unchanged']}; stopped_reason = {status['stopped_reason']}", flush=True)
    sys.exit(0 if n_valid == len(man["runs"]) else 1)


if __name__ == "__main__":
    main()
