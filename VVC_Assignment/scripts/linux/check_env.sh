#!/usr/bin/env bash
# Phase 5: read-only check of the WSL2 Ubuntu environment (user, home, OS, tools). Changes nothing
# except creating and removing one test file in $HOME.
echo "whoami=$(whoami) uid=$(id -u) groups=$(id -nG)"
echo "HOME=$HOME"
grep -E '^(PRETTY_NAME|VERSION_ID|VERSION_CODENAME)=' /etc/os-release
echo "kernel: $(uname -r)"
t="$HOME/.phase5_write_test_$$"
if echo ok > "$t" && [ "$(cat "$t")" = ok ]; then echo "home writable: yes"; else echo "home writable: NO"; fi
rm -f "$t"
df -h "$HOME" | tail -1
echo "nproc: $(nproc)"
free -g | head -2
for c in gcc g++ cmake git make ninja python3 sha256sum; do
  printf '%-10s %s\n' "$c" "$(command -v "$c" || echo MISSING)"
done
echo "--- /etc/wsl.conf:"; cat /etc/wsl.conf 2>/dev/null || echo "(none)"
echo "--- PID 1: $(ps -p 1 -o comm=)"
