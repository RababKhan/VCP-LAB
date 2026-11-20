"""Validate configs/full_manifest.json against the approved Option A design and print a run breakdown.

Approved design: per sequence QP {22,27,32,37} @ medium  U  {faster,fast,medium,slow,slower} @ QP 32
(8 unique configs, 32 in total), all content frames, QPA off, 8 encoder / 8 decoder threads,
CRA refresh every 1 s, 1 warm-up run, 2 extra timing repeats for every config of the two 240p sequences,
seeded random order with every repeat after its original.

Usage: python validate_manifest.py [configs/full_manifest.json]
"""
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_CONFIGS = {(qp, "medium") for qp in (22, 27, 32, 37)} | {(32, p) for p in ("faster", "fast", "medium", "slow", "slower")}
REPEAT_SEQS = {"BasketballPass", "BlowingBubbles"}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "configs", "full_manifest.json")
    m = json.load(open(path, encoding="utf-8"))
    runs = m["runs"]
    problems = []

    def check(cond, msg):
        if not cond:
            problems.append(msg)

    ids = [r["run_id"] for r in runs]
    check(len(ids) == len(set(ids)), "duplicate run_ids")
    warm = [r for r in runs if "warmup" in r.get("groups", [])]
    orig = [r for r in runs if not r.get("repeat_of") and "warmup" not in r.get("groups", [])]
    reps = [r for r in runs if r.get("repeat_of")]
    check(len(warm) == 1 and runs[0] is warm[0], "exactly one warm-up run, placed first")

    c = m["encoder_common"]
    check(c["qpa"] == 0, "QPA must be 0")
    check(c["threads"] == 8 and m["decoder_common"]["threads"] == 8, "threads must be 8 (enc and dec)")
    check(c["format"] == "yuv420_10", "input format yuv420_10")
    check(c.get("extra_args") == ["--refreshtype", "cra", "--refreshsec", "1"], "refresh args")
    check(not any("enc_threads" in r for r in runs), "no per-run thread override")
    check(m["tools"]["vvenc_tag"] == "v1.14.0" and m["tools"]["vvdec_tag"] == "v3.2.1", "tool versions")

    per_seq = {}
    for r in orig:
        seq = m["sequences"][r["sequence"]]
        check(r["frames"] == seq["content_frames"], f"{r['run_id']}: frames != content frames")
        check(r["frames"] < seq["file_frames"], f"{r['run_id']}: would encode the copyright frame")
        per_seq.setdefault(r["sequence"], []).append((r["qp"], r["preset"]))
        want = set()
        if r["preset"] == "medium":
            want.add("qp_sweep")
        if r["qp"] == 32:
            want.add("preset_sweep")
        check(set(r["groups"]) == want, f"{r['run_id']}: groups {r['groups']} != {sorted(want)}")
    for s, cfgs in per_seq.items():
        check(len(cfgs) == 8 and set(cfgs) == EXPECTED_CONFIGS, f"{s}: configs {sorted(cfgs)}")
    check(set(per_seq) == set(m["sequences"]), "all four sequences present")

    pos = {r["run_id"]: i for i, r in enumerate(runs)}
    by_id = {r["run_id"]: r for r in runs}
    rep_count = Counter(r["repeat_of"] for r in reps)
    for r in reps:
        o = by_id.get(r["repeat_of"])
        check(o is not None, f"{r['run_id']}: unknown original")
        if o:
            check(all(r[k] == o[k] for k in ("sequence", "frames", "qp", "preset")), f"{r['run_id']}: differs from original")
            check(pos[r["run_id"]] > pos[o["run_id"]], f"{r['run_id']}: runs before its original")
            check(o["sequence"] in REPEAT_SEQS, f"{r['run_id']}: repeat on non-240p sequence")
    for r in orig:
        n = rep_count.get(r["run_id"], 0)
        check(n == (2 if r["sequence"] in REPEAT_SEQS else 0), f"{r['run_id']}: {n} repeats")

    print(f"manifest: {path}")
    print(f"run order: {m.get('run_order')}")
    print(f"total runs: {len(runs)} = {len(warm)} warm-up + {len(orig)} unique configurations + {len(reps)} timing repeats")
    for s in m["sequences"]:
        o = [r for r in orig if r["sequence"] == s]
        rp = [r for r in reps if by_id[r["repeat_of"]]["sequence"] == s]
        print(f"  {s:16s} {len(o)} configs x {o[0]['frames']} frames, {len(rp)} repeats "
              f"-> {len(o) + len(rp)} encodes, timing samples per config = {1 + len(rp) // len(o)}")
    print(f"qp_sweep runs: {sum('qp_sweep' in r['groups'] for r in orig)}, "
          f"preset_sweep runs: {sum('preset_sweep' in r['groups'] for r in orig)}, "
          f"shared (both): {sum(set(r['groups']) == {'qp_sweep', 'preset_sweep'} for r in orig)}")
    print("RESULT:", "VALID" if not problems else "INVALID")
    for p in problems:
        print("  -", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
