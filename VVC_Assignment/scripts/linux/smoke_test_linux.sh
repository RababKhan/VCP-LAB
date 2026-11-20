#!/usr/bin/env bash
# Phase 5 Linux smoke test, mirroring scripts/smoke_test.ps1 (Phase 3, Windows): encode 16 frames of
# BasketballPass (QP 32, preset faster, QPA off, 4 threads), decode with VVdeC (-o, 4 threads).
# Encoder/decoder arguments are identical to the Windows run; only the file paths differ.
# The input is copied into the Linux filesystem and its SHA256 checked. The run is repeated REPEATS times
# to check that Linux output is deterministic (run 1 is the reference smoke result).
# Usage: bash smoke_test_linux.sh <windows_project_dir_as_/mnt_path>
set -u
PROJ=${1:?project dir}
W=$HOME/vvc_linux
ENC=$W/vvenc/bin/release-static/vvencapp
DEC=$W/vvdec/bin/release-static/vvdecapp
SRC_WIN="$PROJ/dataset/BasketballPass_416_240_50_10_420.yuv"
IN=$W/data/BasketballPass_416_240_50_10_420.yuv
WANT_SHA=de0dcc61e9ba4d22312effad81517fb3a24ecd883738ec3c66f490f7593ed698
TAG=BasketballPass_f16_QP32_faster_qpa0_t4
OUT=$W/smoke
LOGS=$PROJ/logs
REPEATS=3
mkdir -p "$W/data" "$OUT"

{
  echo "=== input copy $(date -Is)"
  if [ ! -f "$IN" ]; then cp "$SRC_WIN" "$IN"; echo "copied $SRC_WIN -> $IN (exit $?)"; else echo "already present: $IN"; fi
  sha=$(sha256sum "$IN" | cut -d' ' -f1)
  echo "sha256: $sha"; echo "expect: $WANT_SHA"
  if [ "$sha" = "$WANT_SHA" ]; then echo "INPUT CHECK: PASS"; else echo "INPUT CHECK: FAIL"; fi
  echo "size: $(stat -c %s "$IN") bytes"
} > "$LOGS/phase5_06_smoke_input.log" 2>&1
grep -q "INPUT CHECK: PASS" "$LOGS/phase5_06_smoke_input.log" || { echo "input checksum mismatch"; exit 2; }

timed() {  # timed <log> <cmd...>: same log layout as the Windows Invoke-Timed helper
  local log=$1; shift
  { echo "Command: $*"; echo "Started: $(date '+%Y-%m-%d %H:%M:%S.%3N %:z')"; } > "$log"
  local t0 t1 rc
  t0=$(date +%s.%N)
  "$@" >> "$log" 2>&1; rc=$?
  t1=$(date +%s.%N)
  { echo "Exit code: $rc"; echo "Wall time (s): $(echo "$t0 $t1" | awk '{printf "%.3f", $2-$1}')"; } >> "$log"
  return $rc
}

for i in $(seq 1 $REPEATS); do
  sfx=$([ "$i" -eq 1 ] && echo "" || echo "_rep$i")
  bs=$OUT/${TAG}${sfx}.266
  rec=$OUT/${TAG}${sfx}_rec.yuv
  timed "$LOGS/phase5_07_smoke_encode${sfx}.log" "$ENC" -i "$IN" -s 416x240 -c yuv420_10 --fps 50 -f 16 \
        -q 32 --preset faster --qpa 0 -t 4 -v 4 -o "$bs"
  e=$?
  timed "$LOGS/phase5_07_smoke_decode${sfx}.log" "$DEC" -b "$bs" -o "$rec" -t 4
  d=$?
  echo "run $i: encode exit $e, decode exit $d, bitstream $(stat -c %s "$bs") B sha256 $(sha256sum "$bs" | cut -d' ' -f1), recon $(stat -c %s "$rec") B sha256 $(sha256sum "$rec" | cut -d' ' -f1)"
done
