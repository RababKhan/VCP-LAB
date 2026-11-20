#!/usr/bin/env bash
# Phase 6: extra Windows/Linux checks with the Linux (GCC, WSL2) build. Input is read from /mnt/d; outputs are written
# to the Linux home (~/vvc_sadab/xp) and the bitstreams are copied back for comparison. Timing is not used.
# Each argument line: RUNID SEQ FILE W H FPS N QP PRESET
set -u
LX=~/vvc_sadab; P=/mnt/d/Korea/Prangon_VVC_Assignment; XP=$LX/xp; LOG=$P/logs/phase6_linux
mkdir -p "$XP" "$LOG" "$P/out/linux2"
ENC=$LX/vvenc/bin/release-static/vvencapp; DEC=$LX/vvdec/bin/release-static/vvdecapp
while read -r id seq f w h fps n qp pr; do
  [ -z "$id" ] && continue
  tag=${id}_${seq}_QP${qp}_${pr}
  bs=$XP/${tag}_linux.266; rec=$XP/${tag}_linux_rec.yuv
  { echo "=== $tag (Linux) $(date '+%F %T %z')"
    echo "\$ $ENC -i $P/dataset/$f -s ${w}x${h} -c yuv420_10 --fps $fps -f $n -q $qp --preset $pr --qpa 0 -t 8 -o $bs"
    "$ENC" -i "$P/dataset/$f" -s ${w}x${h} -c yuv420_10 --fps $fps -f $n -q $qp --preset $pr --qpa 0 -t 8 -o "$bs" 2>&1
    echo "encode exit: $?"
    echo "\$ $DEC -b $bs -o $rec -t 8"
    "$DEC" -b "$bs" -o "$rec" -t 8 2>&1 | tail -3
    echo "decode exit: ${PIPESTATUS[0]}"
    echo "RESULT bitstream_bytes $(stat -c %s "$bs") bitstream_sha256 $(sha256sum "$bs" | cut -d' ' -f1)"
    echo "RESULT recon_bytes $(stat -c %s "$rec") recon_sha256 $(sha256sum "$rec" | cut -d' ' -f1)"
  } > "$LOG/$tag.log" 2>&1
  cp "$bs" "$P/out/linux2/"   # the Linux reconstruction stays in ~/vvc_sadab/xp (WSL disk); its SHA-256 is logged
  grep RESULT "$LOG/$tag.log"
done
echo "done $(date '+%F %T %z')"
