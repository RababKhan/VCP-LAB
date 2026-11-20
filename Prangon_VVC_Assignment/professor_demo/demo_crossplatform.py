"""demo_crossplatform.py - Part 6 (slide 9): Windows vs Linux bit-exact verification, from the saved files.

Slide 9 reports EIGHT Windows/Linux comparisons (not all 64 configurations):
  5 full-length phase-6 runs (A018, A020, A021, A025, B019),
  2 full-length phase-1 runs (R04, R15) and 1 short 16-frame smoke test.
For each one this script recalculates, now, the SHA-256 of the saved Windows and Linux bitstreams (and of the decoded
YUV files where both were kept on this disk) and compares them with each other and with results/crossplatform_v2.json.
If a FULL demo run (demo_encode.ps1 -Mode Full) was made with the Linux encoder, it is shown separately at the end
as today's extra example; it is NOT one of the eight reported checks.

Run from the professor_demo folder:   ..\\.venv\\Scripts\\python.exe demo_crossplatform.py
"""
import json
import re

from demo_pyutil import OUT, RES, ROOT, Report, read_csv, rel, sha256

R = Report("demo_crossplatform")
XP = json.loads((RES / "crossplatform_v2.json").read_text(encoding="utf-8"))
P2 = {r["run_id"]: r for r in read_csv(RES / "results_phase2.csv")}

R.h("What 'bit-exact' means")
R.p("The same encoder source code (VVenC 1.14.0 / VVdeC 3.2.1) was compiled twice: with MSVC 19.44 on Windows and with")
R.p("GCC 13.3 on Linux (WSL2 Ubuntu 24.04). The same input and settings were encoded on both. 'Bit-exact' means the two")
R.p("output files are identical in every bit, so their SHA-256 fingerprints are identical. Same bitstream -> same decoded")
R.p("video -> same PSNR. Encoding SPEED was not compared, because Linux ran inside WSL2.")

checks = []
for r in XP["phase6_runs"]:
    run = r["run"]
    m = re.match(r"(\w+) QP(\d+) (\w+), (\d+) frames", r["config"])
    seq, qp, pr, n = m.groups()
    tag = f"{run}_{seq}_QP{qp}_{pr}"
    win_rec = next((ROOT / "out/phase2").glob(f"{tag}_rec_*.yuv"), None)
    llog = (ROOT / "logs/phase6_linux" / f"{tag}.log").read_text(encoding="utf-8", errors="replace")
    lrec = re.search(r"recon_sha256 (\w+)", llog).group(1)
    checks.append(dict(name=f"{seq} QP{qp} {pr}, {n} frames (run {run})", win_bs=ROOT / "out/phase2" / f"{tag}.266",
                       lin_bs=ROOT / "out/linux2" / f"{tag}_linux.266", rec_note=f"Linux decoded-YUV SHA-256 from logs/phase6_linux/{tag}.log",
                       win_rec=win_rec, lin_rec=None, rec_rec=(P2[run]["recon_sha256"], lrec), rec=r))
for r in XP["phase1_checks"]["full_length"]:
    rid = re.search(r"run (R\d+)", r["config"]).group(1)
    seq, qp, pr = re.match(r"(\w+) QP (\d+) (\w+)", r["config"]).groups()
    tag = f"{rid}_{seq}_QP{qp}_{pr}"
    checks.append(dict(name=r["config"].replace(" (Windows run", " (run").rstrip(")") + ")", win_bs=ROOT / "out" / f"{tag}.266",
                       lin_bs=ROOT / "out/linux" / f"{tag}_linux.266", win_rec=next((ROOT / "out").glob(f"{tag}_rec_*.yuv"), None),
                       lin_rec=next((ROOT / "out/linux").glob(f"{tag}_linux_rec_*.yuv"), None), rec=r))
sm = XP["phase1_checks"]["smoke_16_frames"]
checks.append(dict(name="BlowingBubbles QP34 fast, 16 frames (smoke test)", win_bs=ROOT / "out/smoke/smoke_Windows_QP34_fast_f16.266",
                   lin_bs=ROOT / "out/smoke/smoke_Linux_QP34_fast_f16.266",
                   win_rec=ROOT / "out/smoke/smoke_Windows_QP34_fast_f16_rec_416x240_50fps_10bit_420.yuv",
                   lin_rec=ROOT / "out/smoke/smoke_Linux_QP34_fast_f16_rec_416x240_50fps_10bit_420.yuv",
                   rec={"windows": {"sha256": sm["bitstream_sha256"]["Windows"], "recon_sha256": sm["recon_sha256"]["Windows"]},
                        "linux": {"sha256": sm["bitstream_sha256"]["Linux"], "recon_sha256": sm["recon_sha256"]["Linux"]}}))

R.h(f"The {len(checks)} reported Windows/Linux comparisons - SHA-256 recalculated now from the saved files")
rows = []
for i, c in enumerate(checks, 1):
    hw, hl = sha256(c["win_bs"]), sha256(c["lin_bs"])
    same_bs = hw == hl
    as_recorded = hw == c["rec"]["windows"]["sha256"] and hl == c["rec"]["linux"]["sha256"]
    if c.get("lin_rec") and c.get("win_rec"):
        rw, rl = sha256(c["win_rec"]), sha256(c["lin_rec"])
        rec_txt, same_rec = "both files hashed now", rw == rl
    else:
        rw, rl = c["rec_rec"]
        rec_txt, same_rec = "recorded hashes (Linux decoded file is on the WSL disk)", rw == rl
    rows.append([i, c["name"], hw[:16] + "...", hl[:16] + "...", "yes" if same_bs else "NO", "yes" if same_rec else "NO"])
    R.p(f"{i}. {c['name']}")
    R.p(f"   Windows bitstream {rel(c['win_bs'])}: {hw}")
    R.p(f"   Linux   bitstream {rel(c['lin_bs'])}: {hl}")
    R.p(f"   Decoded YUV ({rec_txt}): Windows {rw[:16]}... Linux {rl[:16]}...")
    R.checks += [(f"check {i}: Windows bitstream = Linux bitstream", same_bs), (f"check {i}: decoded YUV identical", same_rec),
                 (f"check {i}: hashes equal those recorded in results/crossplatform_v2.json", as_recorded)]
R.table(["#", "configuration", "Windows SHA-256", "Linux SHA-256", "bitstream identical", "decoded identical"], rows)
R.check(f"all {len(checks)} reported comparisons are bit-exact", all(r[4] == r[5] == "yes" for r in rows))
R.p("The 5 phase-6 runs were also compared on frames, Y/U/V PSNR and 16 encoder parameter lines (all equal, recorded in")
R.p("results/crossplatform_v2.json). Only these 8 configurations were compared across platforms - not all 64.")

# today's extra example (not one of the 8)
runs = sorted(d for d in OUT.glob("*_full") if (d / "run_info.json").exists())
if runs:
    info = json.loads((runs[-1] / "run_info.json").read_text(encoding="utf-8-sig"))
    R.h("Today's extra example (NOT one of the 8 reported checks)")
    R.p(f"Demo run {runs[-1].name}: encoder engine = {info.get('encoder_engine')}; reproduction of original Windows run {info.get('reference_run')}.")
    R.p(f"   today  : {info.get('bitstream_sha256')}")
    R.p(f"   original Windows run: {info.get('original_bitstream_sha256')}")
    R.p("   (shown for information; it does not change the reported 8/8)")
bad = R.save("Demo: Windows / Linux bit-exact verification (slide 9)")
raise SystemExit(1 if bad else 0)
