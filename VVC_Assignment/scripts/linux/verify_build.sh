#!/usr/bin/env bash
# Phase 5: verify the Linux executables (version/help, QP and preset options), record the CMake configuration,
# and run the upstream tests (unit-test programs + ctest). Normal user, no sudo.
# Usage: bash verify_build.sh <log_dir>
set -u
LOGDIR=${1:?log dir}
W=$HOME/vvc_linux
ENC=$W/vvenc/bin/release-static/vvencapp
DEC=$W/vvdec/bin/release-static/vvdecapp

{
  echo "=== executables $(date -Is)"
  for f in $W/vvenc/bin/release-static/* $W/vvdec/bin/release-static/*; do
    echo "$(sha256sum "$f" | cut -d' ' -f1)  $(stat -c %s "$f") bytes  $f"
  done
  echo "--- file / linkage"
  file "$ENC" "$DEC"
  echo "\$ ldd vvencapp"; ldd "$ENC"
  echo "\$ ldd vvdecapp"; ldd "$DEC"
  echo "--- versions"
  echo "\$ vvencapp --version"; "$ENC" --version; echo "exit code: $?"
  echo "\$ vvdecapp --version"; "$DEC" --version; echo "exit code: $?"
  echo "--- CMake cache (key options)"
  for r in vvenc vvdec; do
    echo "[$r]"
    grep -E '^(CMAKE_BUILD_TYPE|CMAKE_CXX_COMPILER|CMAKE_INTERPROCEDURAL|BUILD_SHARED_LIBS|VV(EN|DE)C_[A-Z_]+):' \
      "$W/$r/build/release-static/CMakeCache.txt"
  done
} > "$LOGDIR/phase5_04_executables.log" 2>&1

"$ENC" --help > "$LOGDIR/help/linux_vvencapp_help.txt" 2>&1; echo "vvencapp --help exit code: $?" >> "$LOGDIR/phase5_04_executables.log"
"$ENC" --fullhelp > "$LOGDIR/help/linux_vvencapp_fullhelp.txt" 2>&1; echo "vvencapp --fullhelp exit code: $?" >> "$LOGDIR/phase5_04_executables.log"
"$DEC" --help > "$LOGDIR/help/linux_vvdecapp_help.txt" 2>&1; echo "vvdecapp --help exit code: $?" >> "$LOGDIR/phase5_04_executables.log"

{
  echo "=== upstream tests $(date -Is)"
  echo "--- vvenc_unit_test"; "$W/vvenc/bin/release-static/vvenc_unit_test"; echo "exit code: $?"
  echo "--- vvdec_unit_test"; "$W/vvdec/bin/release-static/vvdec_unit_test"; echo "exit code: $?"
  for r in vvenc vvdec; do
    echo "--- ctest -N ($r): tests registered by upstream CMake"
    (cd "$W/$r/build/release-static" && ctest -N); echo "exit code: $?"
  done
} > "$LOGDIR/phase5_05_unit_tests.log" 2>&1
