#!/usr/bin/env bash
# Linux verification: versions + unit tests for Sadab's build in ~/vvc_sadab
LX=~/vvc_sadab; LOG=/mnt/d/Korea/Prangon_VVC_Assignment/logs/build
{ echo "=== Linux environment $(date '+%F %T %z')"
  echo "OS: $(. /etc/os-release; echo "$PRETTY_NAME") / kernel $(uname -r)"
  echo "Compiler: $(g++ --version | head -1)"; echo "CMake: $(cmake --version | head -1)"
  echo "VVenC commit: $(git -C $LX/vvenc log -1 --format='%H %d')"; echo "VVdeC commit: $(git -C $LX/vvdec log -1 --format='%H %d')"
  $LX/vvenc/bin/release-static/vvencapp --version 2>&1 | head -1
  $LX/vvdec/bin/release-static/vvdecapp --version 2>&1 | head -1
  echo "sha256 vvencapp $(sha256sum $LX/vvenc/bin/release-static/vvencapp | cut -d' ' -f1)"
  echo "sha256 vvdecapp $(sha256sum $LX/vvdec/bin/release-static/vvdecapp | cut -d' ' -f1)"
} > $LOG/07_linux_environment.log 2>&1
cat $LOG/07_linux_environment.log
ctest --test-dir $LX/vvenc/build/release-static --output-on-failure > $LOG/08_linux_ctest_vvenc.log 2>&1; echo "vvenc ctest exit $?: $(grep -E 'tests passed' $LOG/08_linux_ctest_vvenc.log)"
{ echo "=== vvdec_unit_test (Linux) $(date '+%F %T %z')"; $LX/vvdec/bin/release-static/vvdec_unit_test 2>&1 | tail -15; echo "exit: ${PIPESTATUS[0]}"; } > $LOG/09_linux_vvdec_unit_test.log
tail -4 $LOG/09_linux_vvdec_unit_test.log
