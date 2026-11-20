#!/usr/bin/env bash
# Phase 5: install the minimal Linux build dependencies for VVenC/VVdeC (must run as root; this is the only
# privileged step). Packages: build-essential (gcc, g++, make, libc6-dev), cmake, git.
# Usage (from Windows): wsl -d Ubuntu-24.04 -u root -- bash /mnt/d/Korea/VVC_Assignment/scripts/linux/install_deps.sh
set -u
export DEBIAN_FRONTEND=noninteractive
echo "=== install_deps.sh $(date -Is) as $(whoami)"
echo "--- apt-get update"
apt-get update; echo "apt-get update exit code: $?"
echo "--- apt-get install -y --no-install-recommends build-essential cmake git"
apt-get install -y --no-install-recommends build-essential cmake git; rc=$?
echo "apt-get install exit code: $rc"
echo "--- installed package versions"
dpkg-query -W -f='${Package} ${Version}\n' build-essential gcc g++ gcc-13 g++-13 make cmake git libc6-dev binutils 2>&1
echo "--- tool versions"
gcc --version | head -1; g++ --version | head -1; make --version | head -1; cmake --version | head -1
git --version; ld --version | head -1; ldd --version | head -1
echo "--- CPU flags seen by the guest (SIMD)"
grep -o -w -E 'sse4_1|sse4_2|avx|avx2|avx512f' /proc/cpuinfo | sort | uniq -c
exit $rc
