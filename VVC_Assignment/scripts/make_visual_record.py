"""Phase 6: write visual/visual_evaluation_record.csv: one row per (sequence, frame, variant).

Columns with measured values (frame Y-PSNR, sequence PSNR, bitstream size, crop position) come from
visual/frame_selection.json, visual/sample_manifest.json and visual/rendered/crops.json.
`claude_preliminary_observation` holds what Claude saw in the rendered, zoomed crops (visual/rendered/*_crop.png);
it is NOT a confirmed result. `user_confirmed_observation` is left empty for the user's own YUView inspection,
and `status` stays "pending user confirmation" until the user fills it.

Usage: python make_visual_record.py   (refuses to overwrite an existing record)
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIS = os.path.join(ROOT, "visual")

# Claude's preliminary notes from the zoomed crops (crop position: crops.json). Keys: (sequence, frame rule, variant).
NOTES = {
    ("BasketballPass", "intra_first_idr", "QP22_medium"): "Very close to the original; wood-panel grain only slightly smoother.",
    ("BasketballPass", "intra_first_idr", "QP32_medium"): "Wood-panel grain largely smoothed; jersey stripes and '18' still sharp.",
    ("BasketballPass", "intra_first_idr", "QP37_medium"): "Wood texture flattened; stripes softer; smear near lower edge of the shorts; '18' still legible.",
    ("BasketballPass", "intra_first_idr", "QP32_faster"): "Hard to distinguish from medium/slower at 4x zoom.",
    ("BasketballPass", "intra_first_idr", "QP32_slower"): "Hard to distinguish from medium/faster at 4x zoom.",
    ("BasketballPass", "typical_qp32_medium", "QP22_medium"): "Close to original; slight softening of the ball lettering.",
    ("BasketballPass", "typical_qp32_medium", "QP32_medium"): "Ball and shorts number blurred/smeared; arm edges soft; jacket texture lost.",
    ("BasketballPass", "typical_qp32_medium", "QP37_medium"): "Strong degradation: ball shape smeared, shorts number nearly lost, blotchy smeared patches in the moving leg region.",
    ("BasketballPass", "typical_qp32_medium", "QP32_faster"): "Ball shows more distortion/colour smear than medium and slower.",
    ("BasketballPass", "typical_qp32_medium", "QP32_slower"): "Similar to medium; ball possibly slightly cleaner (uncertain).",
    ("BasketballPass", "worst_qp37_medium", "QP22_medium"): "Thin vertical line and small grey object on the wall still visible but softened.",
    ("BasketballPass", "worst_qp37_medium", "QP32_medium"): "Thin line and small grey object lost; wood texture smoothed; jersey lettering softened.",
    ("BasketballPass", "worst_qp37_medium", "QP37_medium"): "Jersey lettering heavily distorted with colour bleeding; arm and background blurred.",
    ("BasketballPass", "worst_qp37_medium", "QP32_faster"): "Thin line/grey object lost (as medium); slightly more mottled texture on the arm/background.",
    ("BasketballPass", "worst_qp37_medium", "QP32_slower"): "Thin line/grey object lost; no clear visible difference from medium. Note: frame PSNR faster > medium here.",
    ("BQMall", "intra_first_idr", "QP22_medium"): "Very close to the original.",
    ("BQMall", "intra_first_idr", "QP32_medium"): "Hair and face texture of the woman smoothed; poster texture smoothed; glasses still visible.",
    ("BQMall", "intra_first_idr", "QP37_medium"): "Face features blurred, glasses barely visible, poster detail mostly lost; dark pillar area blotchy.",
    ("BQMall", "intra_first_idr", "QP32_faster"): "Hard to distinguish from medium/slower at 3x zoom.",
    ("BQMall", "intra_first_idr", "QP32_slower"): "Hard to distinguish from medium/faster at 3x zoom.",
    ("BQMall", "typical_qp32_medium", "QP22_medium"): "Knit texture of the dark jacket mostly retained.",
    ("BQMall", "typical_qp32_medium", "QP32_medium"): "Knit texture replaced by a smooth surface with streaks.",
    ("BQMall", "typical_qp32_medium", "QP37_medium"): "Knit and red-sweater texture gone (flat); hand blurred.",
    ("BQMall", "typical_qp32_medium", "QP32_faster"): "Knit texture lost as in medium; slightly more smear on hand/face.",
    ("BQMall", "typical_qp32_medium", "QP32_slower"): "Knit texture lost as in medium; differences small.",
    ("BQMall", "worst_qp37_medium", "QP22_medium"): "Close to original; slight softening of the moving woman's bag pattern.",
    ("BQMall", "worst_qp37_medium", "QP32_medium"): "Moving woman smeared at bag/arm (ghost-like blob at the arm); handbag pattern lost.",
    ("BQMall", "worst_qp37_medium", "QP37_medium"): "Strong smearing of the moving woman; boy's face edge blurred; striped shirt partly preserved.",
    ("BQMall", "worst_qp37_medium", "QP32_faster"): "More smearing near the woman's arm; striped shirt slightly distorted.",
    ("BQMall", "worst_qp37_medium", "QP32_slower"): "Arm region looks somewhat cleaner than faster/medium (tentative).",
}


def main():
    out = os.path.join(VIS, "visual_evaluation_record.csv")
    if os.path.exists(out):
        raise SystemExit(f"{out} exists; not overwriting (user observations may be in it)")
    sel = json.load(open(os.path.join(VIS, "frame_selection.json"), encoding="utf-8"))
    crops = json.load(open(os.path.join(VIS, "rendered", "crops.json"), encoding="utf-8"))
    man = json.load(open(os.path.join(VIS, "sample_manifest.json"), encoding="utf-8"))["samples"]
    seqinfo = {(m["sequence"], f"QP{m['qp']}_{m['preset']}"): m for m in man if m["role"] != "original"}
    rows = []
    for seq, info in sel.items():
        for rule, idx in info["frames"].items():
            c = crops[f"{seq}/{rule}"]
            for var, by_rule in info["per_frame_y_psnr"].items():
                fpsnr = by_rule[rule]
                m = seqinfo[(seq, var)]
                rows.append({"sequence": seq, "frame_index": idx, "frame_rule": rule, "qp": m["qp"], "preset": m["preset"],
                             "frame_y_psnr_db": fpsnr, "sequence_y_psnr_db": m["psnr_y"],
                             "sequence_yuv_psnr_db": m["psnr_yuv_411"], "bitstream_bytes": m["bitstream_bytes"],
                             "bitrate_kbps": m["bitrate_kbps"],
                             "crop_xywh_zoom": f"{c['crop_x']},{c['crop_y']},{c['crop_w']},{c['crop_h']},{c['zoom']}x",
                             "claude_preliminary_observation": NOTES.get((seq, rule, var), ""),
                             "user_confirmed_observation": "", "status": "pending user confirmation"})
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}: {len(rows)} rows, {sum(bool(r['claude_preliminary_observation']) for r in rows)} with preliminary notes")


if __name__ == "__main__":
    main()
