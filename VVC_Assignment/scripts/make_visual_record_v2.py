"""Phase 6: write visual/phase6/visual_evaluation_record_v2.csv (the v1 record in visual/ is left unchanged).

Per (sequence, frame, variant) row, three clearly separated evidence types:
  * automated_metrics        - measured by scripts/analyze_visual.py (visual/phase6/tables/frame_metrics.csv)
  * user_confirmed_observation - only what the user stated (2026-11-05): BasketballPass frame 133,
                                 "QP22 appeared clearest and QP37 appeared blurriest"
  * claude_preliminary_visual_interpretation - Claude's inspection of the rendered crops (v1 notes); NOT confirmed

Usage: python make_visual_record_v2.py   (refuses to overwrite)
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V1 = os.path.join(ROOT, "visual", "visual_evaluation_record.csv")
MET = os.path.join(ROOT, "visual", "phase6", "tables", "frame_metrics.csv")
OUT = os.path.join(ROOT, "visual", "phase6", "visual_evaluation_record_v2.csv")
USER = {("BasketballPass", "133", "22", "medium"): "Appeared clearest of QP22/QP32/QP37 (user statement, 2026-11-05).",
        ("BasketballPass", "133", "37", "medium"): "Appeared blurriest of QP22/QP32/QP37 (user statement, 2026-11-05).",
        ("BasketballPass", "133", "32", "medium"): "Not individually stated by the user (user ranked QP22 clearest, QP37 blurriest)."}


def main():
    if os.path.exists(OUT):
        raise SystemExit(f"{OUT} exists; not overwriting")
    v1 = {(r["sequence"], r["frame_index"], r["qp"], r["preset"]): r for r in csv.DictReader(open(V1, encoding="utf-8"))}
    rows = []
    for m in csv.DictReader(open(MET, encoding="utf-8")):
        k = (m["sequence"], m["frame_index"], m["qp"], m["preset"])
        r = v1[k]
        auto = (f"frame Y-PSNR {float(m['frame_psnr_y']):.2f} dB, SSIM-Y {float(m['frame_ssim_y']):.4f}, "
                f"mean|dY| {float(m['frame_mae_y']):.2f}, |dY|>16 in {float(m['frame_pct_absdiff_gt16']):.1f}% of pixels, "
                f"detail ratio {float(m['frame_detail_ratio']):.3f}; crop Y-PSNR {float(m['crop_psnr_y']):.2f} dB, "
                f"crop detail ratio {float(m['crop_detail_ratio']):.3f}")
        rows.append({"sequence": k[0], "frame_index": k[1], "frame_rule": r["frame_rule"], "qp": k[2], "preset": k[3],
                     "frame_y_psnr_db": m["frame_psnr_y"], "sequence_y_psnr_db": r["sequence_y_psnr_db"],
                     "bitstream_bytes": r["bitstream_bytes"], "crop_xywh_zoom": r["crop_xywh_zoom"],
                     "automated_metrics": auto,
                     "user_confirmed_observation": USER.get(k, ""),
                     "claude_preliminary_visual_interpretation": r["claude_preliminary_observation"],
                     "evidence_status": "user-confirmed (partial) + automated" if k in USER and "Not individually" not in USER[k]
                     else "automated metrics + preliminary interpretation (not user-confirmed)"})
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT}: {len(rows)} rows; user-confirmed rows: {sum(r['evidence_status'].startswith('user') for r in rows)}")


if __name__ == "__main__":
    main()
