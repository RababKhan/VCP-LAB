#!/usr/bin/env bash
# Phase 5: clone VVenC/VVdeC at the exact commits of the verified Windows build and build them in Release mode
# inside the Linux filesystem (~/vvc_linux). Run as the normal user (no sudo).
# Usage: bash clone_build.sh <log_dir>     (log_dir: where the per-step logs are written)
set -u
LOGDIR=${1:?log dir}
W=$HOME/vvc_linux
mkdir -p "$W" "$LOGDIR"
JOBS=8   # parallel build jobs (16 logical CPUs but only ~7.6 GiB RAM in the VM; LTO links are memory-heavy)

declare -A URL=([vvenc]=https://github.com/fraunhoferhhi/vvenc.git [vvdec]=https://github.com/fraunhoferhhi/vvdec.git)
declare -A COMMIT=([vvenc]=9428ea8636ae7f443ecde89999d16b2dfc421524 [vvdec]=cb1a3efd88b2ebd1141f1a9ca87c774f05de9249)
declare -A TAG=([vvenc]=v1.14.0 [vvdec]=v3.2.1)

fail=0
for r in vvenc vvdec; do
  log="$LOGDIR/phase5_02_clone_$r.log"
  {
    echo "=== clone $r $(date -Is) as $(whoami) in $W"
    if [ -d "$W/$r/.git" ]; then echo "repository already present (not re-cloned)"
    else echo "\$ git clone ${URL[$r]} $W/$r"; git clone "${URL[$r]}" "$W/$r"; echo "clone exit code: $?"; fi
    echo "\$ git -C $W/$r checkout --detach ${COMMIT[$r]}"
    git -C "$W/$r" checkout --detach "${COMMIT[$r]}"; echo "checkout exit code: $?"
    head=$(git -C "$W/$r" rev-parse HEAD)
    echo "HEAD: $head"
    echo "expected: ${COMMIT[$r]}"
    echo "tags at HEAD: $(git -C "$W/$r" tag --points-at HEAD | tr '\n' ' ')"
    echo "describe: $(git -C "$W/$r" describe --tags)"
    echo "git status --porcelain (empty = unmodified):"; git -C "$W/$r" status --porcelain; echo "[end status]"
    if [ "$head" = "${COMMIT[$r]}" ]; then echo "COMMIT CHECK: PASS"; else echo "COMMIT CHECK: FAIL"; fi
  } > "$log" 2>&1
  grep -q "COMMIT CHECK: PASS" "$log" || { echo "commit check failed for $r"; fail=1; }
done
[ $fail -eq 0 ] || exit 2

for r in vvenc vvdec; do
  src="$W/$r"; bld="$src/build/release-static"
  log="$LOGDIR/phase5_03_build_$r.log"
  {
    echo "=== $r Linux build $(date -Is) as $(whoami)"
    echo "Source: $src"
    echo "Commit: $(git -C "$src" rev-parse HEAD) ($(git -C "$src" describe --tags))"
    echo "Compiler: $(g++ --version | head -1); $(cmake --version | head -1)"
    echo "Generator: Unix Makefiles (CMake default), CMAKE_BUILD_TYPE=Release, all other options = upstream defaults"
    echo "--- configure"
    echo "\$ cmake -S $src -B $bld -DCMAKE_BUILD_TYPE=Release"
    cmake -S "$src" -B "$bld" -DCMAKE_BUILD_TYPE=Release; echo "configure exit code: $?"
    echo "--- build"
    echo "\$ cmake --build $bld --parallel $JOBS"
    t0=$(date +%s.%N)
    cmake --build "$bld" --parallel $JOBS; rc=$?
    t1=$(date +%s.%N)
    echo "build exit code: $rc  (wall time $(echo "$t0 $t1" | awk '{printf "%.2f", ($2-$1)/60}') min)"
    echo "--- produced executables"
    find "$src/bin" -type f -perm -u+x -printf '%p  %s bytes  %TY-%Tm-%Td %TH:%TM\n' 2>/dev/null | sort
  } > "$log" 2>&1
  echo "$r: $(grep -E 'configure exit code|build exit code' "$log" | tr '\n' ' ')"
  echo "$r: compiler warnings (lines matching 'warning:'): $(grep -c 'warning:' "$log"); errors ('error:'): $(grep -c 'error:' "$log")"
done
