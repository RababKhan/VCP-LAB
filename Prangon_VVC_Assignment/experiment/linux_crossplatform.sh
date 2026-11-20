#!/usr/bin/env bash
# Phase 4: run full-length configurations with the Linux (GCC, WSL2) build that match Windows runs, so the outputs
# can be compared (size, SHA-256, frame count, decoded-video hash, PSNR). Timing here is NOT used for any claim.
#   R04 = BlowingBubbles QP 34 fast (500 frames);  R15 = BQMall QP 29 medium (600 frames)
set -u
LX=~/vvc_sadab; P=/mnt/d/Korea/Prangon_VVC_Assignment; OUT=$P/out/linux; LOG=$P/logs/11_linux_crossplatform.log
mkdir -p "$OUT"
ENC=$LX/vvenc/bin/release-static/vvencapp; DEC=$LX/vvdec/bin/release-static/vvdecapp
echo "=== Linux cross-platform runs $(date '+%F %T %z') (automated by Claude)" > "$LOG"
run() {  # id seq file w h fps frames qp preset
  local id=$1 seq=$2 f=$3 w=$4 h=$5 fps=$6 n=$7 qp=$8 pr=$9
  local bs=$OUT/${id}_${seq}_QP${qp}_${pr}_linux.266 rec=$OUT/${id}_${seq}_QP${qp}_${pr}_linux_rec_${w}x${h}_${fps}fps_10bit_420.yuv
  echo "--- $id $seq QP $qp $pr" >> "$LOG"
  echo "\$ $ENC -i $P/dataset/$f -s ${w}x${h} -c yuv420_10 --fps $fps -f $n -q $qp --preset $pr --qpa 0 -t 8 -o $bs" >> "$LOG"
  "$ENC" -i "$P/dataset/$f" -s ${w}x${h} -c yuv420_10 --fps $fps -f $n -q $qp --preset $pr --qpa 0 -t 8 -o "$bs" > "$OUT/${id}_encode.log" 2>&1
  echo "encode exit: $?" >> "$LOG"; grep -E "^\S*vvenc \[info\]:\s+[0-9]+\s+a " "$OUT/${id}_encode.log" >> "$LOG"
  "$DEC" -b "$bs" -o "$rec" -t 8 > "$OUT/${id}_decode.log" 2>&1
  echo "decode exit: $?" >> "$LOG"
  echo "bitstream $(stat -c %s "$bs") bytes sha256 $(sha256sum "$bs" | cut -d' ' -f1)" >> "$LOG"
  echo "recon $(stat -c %s "$rec") bytes sha256 $(sha256sum "$rec" | cut -d' ' -f1)" >> "$LOG"
}
run R04 BlowingBubbles BlowingBubbles_416_240_50_10_420.yuv 416 240 50 500 34 fast
run R15 BQMall BQMall_832_480_60_10_420.yuv 832 480 60 600 29 medium
echo "done $(date '+%F %T %z')" >> "$LOG"
cat "$LOG"
