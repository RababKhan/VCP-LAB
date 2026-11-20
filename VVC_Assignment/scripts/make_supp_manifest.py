"""Build configs/supp_ac_manifest.json: supplementary AC-powered timing verification of the four
configurations whose single timing sample in the full run was taken (partly) on battery.

Everything that defines a run (tools, encoder/decoder settings, sequences with file paths and SHA256,
frames, QP, preset) is copied verbatim from configs/full_manifest.json, so the supplementary runs use
exactly the same parameters. Only the run_id gets the suffix "_suppAC" and the field "verifies" names
the original run. A warm-up run (same as the full run's) is placed first, as in the full run.

Usage: python make_supp_manifest.py
"""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINALS = ["warmup_BasketballPass_f64_q32_faster",   # warm-up, as in the full run (not a measurement)
             "BQMall_f600_q32_faster_t8",
             "BasketballDrive_f500_q32_fast_t8",
             "BQMall_f600_q22_medium_t8",
             "BasketballDrive_f500_q32_slower_t8"]     # longest last
SUFFIX = "_suppAC"


def main():
    full = json.load(open(os.path.join(ROOT, "configs", "full_manifest.json"), encoding="utf-8"))
    by_id = {r["run_id"]: r for r in full["runs"]}
    runs = []
    for rid in ORIGINALS:
        r = copy.deepcopy(by_id[rid])
        r["run_id"] = rid + SUFFIX
        r["verifies"] = rid
        runs.append(r)
    seqs = {r["sequence"] for r in runs}
    man = {"name": "supp_ac", "manifest_version": 1,
           "purpose": "supplementary AC-powered timing verification of the battery-affected configurations "
                      "of the full run; original results are not modified",
           "derived_from": "configs/full_manifest.json",
           **{k: copy.deepcopy(full[k]) for k in ("tools", "encoder_common", "decoder_common", "psnr_definition")},
           "sequences": {s: copy.deepcopy(full["sequences"][s]) for s in sorted(seqs)},
           "run_order": "fixed: warm-up first, then shortest to longest",
           "runs": runs}
    out = os.path.join(ROOT, "configs", "supp_ac_manifest.json")
    if os.path.exists(out):
        raise SystemExit(f"{out} exists; not overwriting")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2)
        f.write("\n")
    print(f"wrote {out}: {len(runs)} runs")


if __name__ == "__main__":
    main()
