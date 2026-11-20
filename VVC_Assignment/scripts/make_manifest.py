"""Generate machine-readable experiment manifests (consumed by vvc_runner.py).

Design (per sequence, union of two controlled sweeps, no duplicate runs):
  qp_sweep     : QP in {22, 27, 32, 37}, preset medium
  preset_sweep : preset in {faster, fast, medium, slow, slower}, QP 32
  -> 8 unique (QP, preset) configurations; (32, medium) belongs to both groups.

Usage:
  python make_manifest.py pilot  [--threads 8]                 -> configs/pilot_manifest.json
  python make_manifest.py full   [--threads 8] [--sequences A B] -> configs/full_manifest.json
"""
import argparse
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

QPS = [22, 27, 32, 37]
PRESETS = ["faster", "fast", "medium", "slow", "slower"]
QP_SWEEP_PRESET = "medium"
PRESET_SWEEP_QP = 32

# Every value below was verified in Phase 3 / 4A (see DATASET_NOTES.md, results/phase4a/inspection/).
SEQUENCES = {
    "BasketballPass": {"file": "dataset/BasketballPass_416_240_50_10_420.yuv", "width": 416, "height": 240, "fps": 50,
                       "sha256": "de0dcc61e9ba4d22312effad81517fb3a24ecd883738ec3c66f490f7593ed698",
                       "file_frames": 501, "content_frames": 500},
    "BlowingBubbles": {"file": "dataset/BlowingBubbles_416_240_50_10_420.yuv", "width": 416, "height": 240, "fps": 50,
                       "sha256": "ffe4039fc7cfc034e54258302adcafd6f02a3d77028e566a0f82313a54d180e2",
                       "file_frames": 501, "content_frames": 500},
    "BQMall": {"file": "dataset/BQMall_832_480_60_10_420.yuv", "width": 832, "height": 480, "fps": 60,
               "sha256": "02490741eed0ef8d50016d236e7e98efdf5e3deb9a7cc60aa61c0d55c4e61b52",
               "file_frames": 601, "content_frames": 600},
    "BasketballDrive": {"file": "dataset/BasketballDrive_1920_1080_50_10_420.yuv", "width": 1920, "height": 1080,
                        "fps": 50, "sha256": "1c4cecebc10efb18471ddcb43aa2680c61c6525a8f53b84267a1a04f73eb6334",
                        "file_frames": 501, "content_frames": 500},
}
for s in SEQUENCES.values():
    s.update({"bitdepth": 10, "chroma": "420", "container": "yuv420p10le (16-bit little-endian words)",
              "effective_precision_bits": 8,
              "trailing_frame_note": "last frame is an NTT DOCOMO copyright text card; never encoded"})

PILOT_FRAMES = {"BasketballPass": 64, "BlowingBubbles": 64, "BQMall": 64, "BasketballDrive": 32}


def configs():
    """(qp, preset, groups) for the 8 unique configurations."""
    out = {}
    for qp in QPS:
        out.setdefault((qp, QP_SWEEP_PRESET), []).append("qp_sweep")
    for p in PRESETS:
        out.setdefault((PRESET_SWEEP_QP, p), []).append("preset_sweep")
    return [(qp, p, g) for (qp, p), g in out.items()]


def run_id(seq, frames, qp, preset, threads, suffix=""):
    return f"{seq}_f{frames}_q{qp}_{preset}_t{threads}{suffix}"


def base_manifest(name, threads):
    return {
        "name": name,
        "manifest_version": 1,
        "tools": {"vvencapp": "src/vvenc/bin/release-static/vvencapp.exe",
                  "vvdecapp": "src/vvdec/bin/release-static/vvdecapp.exe",
                  "vvenc_tag": "v1.14.0", "vvenc_commit": "9428ea8636ae7f443ecde89999d16b2dfc421524",
                  "vvdec_tag": "v3.2.1", "vvdec_commit": "cb1a3efd88b2ebd1141f1a9ca87c774f05de9249"},
        "encoder_common": {"format": "yuv420_10", "qpa": 0, "threads": threads, "verbosity": 4,
                           "extra_args": ["--refreshtype", "cra", "--refreshsec", "1"],
                           "notes": "constant-QP (no rate control); GOP structure = preset default; "
                                    "intra refresh CRA every 1 s; POC0IDR = library default (off)"},
        "decoder_common": {"threads": threads},
        "psnr_definition": {
            "primary_peak": "1020 = 255 << (bitdepth - 8)  (HM/VTM/VVenC convention, vvenc Analyze.h)",
            "secondary_peak": "1023 = 2^bitdepth - 1  (FFmpeg convention, also stored in per-run JSON)",
            "bitdepth": "computed on 10-bit samples of the original file vs 10-bit decoder output",
            "per_component_sequence_value": "arithmetic mean over frames of per-frame PSNR",
            "yuv_combined_primary": "PSNR of 4:1:1 (pixel-count) weighted mean MSE, matches VVenC YUV-PSNR",
            "yuv_combined_secondary": "(6*Y + U + V) / 8 of per-component PSNRs (JVET CTC style)",
            "alignment": "frame i of reconstruction vs frame i of source starting at source frame 0",
        },
        "design": {"qp_sweep": {"qps": QPS, "preset": QP_SWEEP_PRESET},
                   "preset_sweep": {"presets": PRESETS, "qp": PRESET_SWEEP_QP},
                   "shared_run": f"QP {PRESET_SWEEP_QP} / {QP_SWEEP_PRESET} is run once and belongs to both groups"},
        "sequences": SEQUENCES,
        "runs": [],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["pilot", "full"])
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--sequences", nargs="*", default=list(SEQUENCES))
    ap.add_argument("--repeats", type=int, default=1, help="full: timing repeats per config (extra encodes)")
    ap.add_argument("--repeat-sequences", nargs="*", default=None, help="full: sequences that get timing repeats")
    ap.add_argument("--shuffle-seed", type=int, default=None, help="full: seeded random run order")
    ap.add_argument("--warmup", action="store_true", help="full: prepend one short warm-up run (excluded from analysis)")
    a = ap.parse_args()

    if a.kind == "pilot":
        m = base_manifest("pilot", a.threads)
        m["purpose"] = ("Estimate runtime/storage of the full matrix: every unique config on every sequence with a "
                        "reduced frame count, plus repeatability, thread-count and frame-count-linearity checks.")
        for seq in a.sequences:
            f = PILOT_FRAMES[seq]
            for qp, p, g in configs():
                m["runs"].append({"run_id": run_id(seq, f, qp, p, a.threads), "sequence": seq, "frames": f,
                                  "qp": qp, "preset": p, "groups": g})
        if "BasketballPass" in a.sequences:
            base = run_id("BasketballPass", 64, 32, "medium", a.threads)
            for r in (2, 3):
                m["runs"].append({"run_id": base + f"_rep{r}", "sequence": "BasketballPass", "frames": 64, "qp": 32,
                                  "preset": "medium", "groups": ["check_repeatability"], "repeat_of": base})
            m["runs"].append({"run_id": run_id("BasketballPass", 64, 32, "medium", 4), "sequence": "BasketballPass",
                              "frames": 64, "qp": 32, "preset": "medium", "enc_threads": 4,
                              "groups": ["check_thread_count"]})
            m["runs"].append({"run_id": run_id("BasketballPass", 128, 32, "medium", a.threads),
                              "sequence": "BasketballPass", "frames": 128, "qp": 32, "preset": "medium",
                              "groups": ["check_frame_linearity"]})
    else:
        m = base_manifest("full", a.threads)
        repeat_seqs = a.sequences if a.repeat_sequences is None else a.repeat_sequences
        for seq in a.sequences:
            f = SEQUENCES[seq]["content_frames"]
            for qp, p, g in configs():
                rid = run_id(seq, f, qp, p, a.threads)
                m["runs"].append({"run_id": rid, "sequence": seq, "frames": f, "qp": qp, "preset": p, "groups": g})
                for r in range(2, a.repeats + 1 if seq in repeat_seqs else 2):
                    m["runs"].append({"run_id": f"{rid}_rep{r}", "sequence": seq, "frames": f, "qp": qp, "preset": p,
                                      "groups": ["timing_repeat"], "repeat_of": rid})
        if a.shuffle_seed is not None:
            # Spread slow drifts (thermal state, background load) across all configurations.
            # Repeats are kept after their original so a repeat never runs before the run it repeats.
            originals = [r for r in m["runs"] if not r.get("repeat_of")]
            repeats = [r for r in m["runs"] if r.get("repeat_of")]
            random.Random(a.shuffle_seed).shuffle(originals)
            random.Random(a.shuffle_seed + 1).shuffle(repeats)
            m["runs"] = originals + repeats
            m["run_order"] = f"seeded random (seed {a.shuffle_seed}); all repeats after all originals"
        if a.warmup:
            m["runs"].insert(0, {"run_id": "warmup_BasketballPass_f64_q32_faster", "sequence": "BasketballPass",
                                 "frames": 64, "qp": 32, "preset": "faster", "groups": ["warmup"]})

    path = os.path.join(ROOT, "configs", f"{a.kind}_manifest.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(m, fh, indent=2)
    print(f"wrote {path} with {len(m['runs'])} runs")


if __name__ == "__main__":
    main()
