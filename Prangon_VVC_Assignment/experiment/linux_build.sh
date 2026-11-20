#!/usr/bin/env bash
# Linux build for Sadab's experiment: clone the same tags into ~/vvc_sadab and build Release with GCC.
set -u
LX=~/vvc_sadab; LOG=/mnt/d/Korea/Prangon_VVC_Assignment/logs/build
mkdir -p "$LX" "$LOG"; cd "$LX"
for spec in "vvenc v1.14.0" "vvdec v3.2.1"; do
  set -- $spec; n=$1; tag=$2; L=$LOG/03_linux_build_$n.log
  { echo "=== $n Linux build $(date '+%F %T %z')"
    echo "Compiler: $(g++ --version | head -1); $(cmake --version | head -1)"
    [ -d $n ] || git clone --branch $tag --depth 1 https://github.com/fraunhoferhhi/$n.git $n 2>&1
    echo "Commit: $(git -C $n log -1 --format='%H %d')"
    echo "\$ cmake -S $n -B $n/build/release-static -DCMAKE_BUILD_TYPE=Release"
    cmake -S $n -B $n/build/release-static -DCMAKE_BUILD_TYPE=Release 2>&1; echo "configure exit: $?"
    s=$(date +%s); echo "\$ cmake --build $n/build/release-static --parallel 8"
    cmake --build $n/build/release-static --parallel 8 2>&1; echo "build exit: $?; build wall time $(( $(date +%s) - s )) s"
  } > "$L"
  tail -2 "$L"
done
ls -la $LX/vvenc/bin/release-static/ $LX/vvdec/bin/release-static/ | grep -E 'vvencapp|vvdecapp'
