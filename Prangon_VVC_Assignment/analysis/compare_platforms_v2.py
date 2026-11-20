"""Phase 6: compare the extra Linux runs with the matching Windows phase-2 runs.
Compares bitstream size + SHA-256, decoded-video SHA-256 + frame count, encoder-reported Y/U/V PSNR and the encoder's
printed configuration (the 'vvenc [notice]' / '[verbose]' parameter lines, with file paths removed)."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p2 = {r["run_id"]: r for r in csv.DictReader(open(ROOT / "results/results_phase2.csv", encoding="utf-8"))}
SUM = re.compile(r"vvenc \[info\]:\s+(\d+)\s+a\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)")


def params(text):
    """Encoder configuration as printed by vvencapp ('vvenc [info]: Name : value' lines, file paths removed) plus the
    command-line options (file arguments removed)."""
    out = []
    for line in text.splitlines():
        m = re.match(r"\S*vvenc \[(?:info|notice|verbose)\]:\s+([A-Za-z][^:]*?)\s+:\s+(.*)$", line)
        if m and not re.search(r"Input File|Bitstream File", m.group(1)):
            out.append(f"{m.group(1).strip()} = {re.sub(r'\\s+', ' ', m.group(2)).strip()}")
    cmd = re.search(r"(?:Command: .*vvencapp(?:\.exe)?\"? |\$ \S*vvencapp )(.*)", text)
    if cmd:
        toks = cmd.group(1).split()
        opts = [f"{a} {b}" for a, b in zip(toks, toks[1:]) if a.startswith("-") and a not in ("-i", "-o")]
        out += [f"cmd {o}" for o in opts]
    return out


res = []
for log in sorted((ROOT / "logs/phase6_linux").glob("*.log")):
    txt = log.read_text(encoding="utf-8", errors="replace")
    rid = log.stem.split("_")[0]
    w = p2[rid]
    wlog = (ROOT / w["log_file"]).read_text(encoding="utf-8", errors="replace")
    wenc = wlog.split("=== DECODE")[0]
    lb = re.search(r"RESULT bitstream_bytes (\d+) bitstream_sha256 (\w+)", txt)
    lr = re.search(r"RESULT recon_bytes (\d+) recon_sha256 (\w+)", txt)
    ls, ws = SUM.search(txt), SUM.search(wenc)
    fsz = int(w["width"]) * int(w["height"]) * 3
    pl, pw = params(txt), params(wenc)
    item = {"run": rid, "config": f"{w['sequence']} QP{w['qp']} {w['preset']}, {w['frames']} frames",
            "windows": {"bytes": int(w["bitstream_bytes"]), "sha256": w["bitstream_sha256"], "recon_sha256": w["recon_sha256"],
                        "frames": float(w["recon_frames"]), "psnr_yuv": [float(w["enc_y_psnr"]), float(w["enc_u_psnr"]), float(w["enc_v_psnr"])]},
            "linux": {"bytes": int(lb.group(1)), "sha256": lb.group(2), "recon_sha256": lr.group(2), "frames": int(lr.group(1)) / fsz,
                      "psnr_yuv": [float(ls.group(3)), float(ls.group(4)), float(ls.group(5))]}}
    W, L = item["windows"], item["linux"]
    diff_params = sorted(set(pl) ^ set(pw))
    item["match"] = {"size": W["bytes"] == L["bytes"], "bitstream_sha256": W["sha256"] == L["sha256"],
                     "recon_sha256": W["recon_sha256"] == L["recon_sha256"], "frames": W["frames"] == L["frames"] == float(w["frames"]),
                     "psnr": W["psnr_yuv"] == L["psnr_yuv"], "encoder_parameters": not diff_params}
    item["n_parameter_lines_compared"] = len(pl)
    item["parameter_differences"] = diff_params
    res.append(item)
    print(item["config"], item["match"], flush=True)
old = json.loads((ROOT / "results/crossplatform.json").read_text(encoding="utf-8"))
out = {"phase6_runs": res, "phase1_checks": old,
       "summary": {"n_new": len(res), "n_new_all_match": sum(all(i["match"].values()) for i in res)}}
(ROOT / "results/crossplatform_v2.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out["summary"]))
