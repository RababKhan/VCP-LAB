#!/usr/bin/env bash
# Linux build verification + cross-platform check for Sadab Khan Prangon's VVC experiment.
# Run inside WSL2 Ubuntu (or Linux) AFTER building in ~/vvc_sadab and AFTER the Windows run (run_experiment.ps1):
#   bash /mnt/d/vvc_sadab/experiment/linux_check.sh
# It encodes BlowingBubbles QP 34 fast (the same settings as Windows run R04) and compares SHA256 values.
# Timing from this script is NOT used for any speed claim (WSL2 reads /mnt/d slowly).
set -u
LX=~/vvc_sadab
WIN=/mnt/d/vvc_sadab
LOG=$WIN/logs
mkdir -p "$LOG" "$LX/out"
ENC=$LX/vvenc/bin/release-static/vvencapp
DEC=$LX/vvdec/bin/release-static/vvdecapp

{
  echo "Recorded: $(date '+%F %T %z')"
  echo "OS: $(. /etc/os-release; echo "$PRETTY_NAME") / kernel $(uname -r)"
  echo "Compiler: $(g++ --version | head -1)"
  echo "CMake: $(cmake --version | head -1)"
  echo "VVenC commit: $(git -C $LX/vvenc log -1 --format='%H %d')"
  echo "VVdeC commit: $(git -C $LX/vvdec log -1 --format='%H %d')"
  "$ENC" --version 2>&1 | head -1
  "$DEC" --version 2>&1 | head -1
} | tee "$LOG/linux_environment.txt"

echo "=== unit tests (this can take a few minutes)"
ctest --test-dir $LX/vvenc/build/release-static --output-on-failure > "$LOG/linux_vvenc_ctest.log" 2>&1; echo "vvenc ctest exit: $?"
ctest --test-dir $LX/vvdec/build/release-static --output-on-failure > "$LOG/linux_vvdec_ctest.log" 2>&1; echo "vvdec ctest exit: $?"
tail -3 "$LOG/linux_vvenc_ctest.log"; tail -3 "$LOG/linux_vvdec_ctest.log"

echo "=== cross-platform encode: BlowingBubbles, 500 frames, QP 34, fast, QPA off, 8 threads"
BS=$LX/out/linux_BlowingBubbles_QP34_fast.266
REC=$LX/out/linux_BlowingBubbles_QP34_fast_rec.yuv
"$ENC" -i $WIN/dataset/BlowingBubbles_416_240_50_10_420.yuv -s 416x240 -c yuv420_10 --fps 50 -f 500 \
       -q 34 --preset fast --qpa 0 -t 8 -o "$BS" > "$LOG/linux_encode_R04.log" 2>&1; echo "encode exit: $?"
"$DEC" -b "$BS" -o "$REC" -t 8 > "$LOG/linux_decode_R04.log" 2>&1; echo "decode exit: $?"

WBS=$WIN/out/R04_BlowingBubbles_QP34_fast.266
WREC=$WIN/out/R04_BlowingBubbles_QP34_fast_rec_416x240_50fps_10bit_420.yuv
{
  echo "Cross-platform check, $(date '+%F %T %z')"
  echo "Linux   bitstream: $(stat -c %s "$BS") bytes  sha256 $(sha256sum "$BS" | cut -d' ' -f1)"
  if [ -f "$WBS" ]; then
    echo "Windows bitstream: $(stat -c %s "$WBS") bytes  sha256 $(sha256sum "$WBS" | cut -d' ' -f1)"
    cmp -s "$BS" "$WBS" && echo "RESULT bitstream: IDENTICAL" || echo "RESULT bitstream: DIFFERENT"
  else
    echo "Windows bitstream not found ($WBS). Run run_experiment.ps1 first."
  fi
  if [ -f "$WREC" ]; then
    cmp -s "$REC" "$WREC" && echo "RESULT decoded video (Linux decoder vs Windows decoder): IDENTICAL" \
                          || echo "RESULT decoded video: DIFFERENT"
  fi
} | tee "$LOG/cross_platform_check.txt"
