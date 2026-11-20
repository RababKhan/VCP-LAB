"""Supplementary timing run: B022 (BasketballDrive QP 29 medium) was flagged CHECK because the laptop switched to
battery during that run. This adds one more measurement of the same configuration on AC power, after a warm-up.
B022 itself is kept unchanged in results_phase2.csv."""
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_phase2 as R  # noqa: E402

R.OUT.mkdir(parents=True, exist_ok=True)
R.LOGS.mkdir(parents=True, exist_ok=True)
mon = subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(R.ROOT / "experiment/monitor.ps1"),
                        "-Out", str(R.ROOT / "logs/monitor_phase2.csv")])
R.keep_awake(True)
try:
    with open(R.CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, R.COLS)
        R.warmup("C", R.LOGS / "warmup_C.log")
        R.one_run("C001", "C", "BasketballDrive", 29, "medium", "repeat", "B022 (power-flagged)", w, f)
finally:
    R.keep_awake(False)
    mon.terminate()
