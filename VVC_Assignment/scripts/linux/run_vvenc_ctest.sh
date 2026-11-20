#!/usr/bin/env bash
# Phase 5: run the self-contained upstream VVenC ctest suite (39 tests; uses test data shipped in the repo).
# VVdeC's ctest conformance tests need the JVET conformance bitstreams, which upstream does not download by
# default (VVDEC_ENABLE_BITSTREAM_DOWNLOAD=OFF), so they are not run here; vvdec_unit_test is run separately.
# Usage: bash run_vvenc_ctest.sh <log_dir>
set -u
LOGDIR=${1:?log dir}
B=$HOME/vvc_linux/vvenc/build/release-static
{
  echo "=== vvenc ctest $(date -Is) as $(whoami)"
  echo "\$ cd $B && ctest --output-on-failure"
  t0=$(date +%s)
  (cd "$B" && ctest --output-on-failure); rc=$?
  echo "ctest exit code: $rc  (wall time $(( $(date +%s) - t0 )) s)"
} > "$LOGDIR/phase5_05b_vvenc_ctest.log" 2>&1
tail -8 "$LOGDIR/phase5_05b_vvenc_ctest.log"
