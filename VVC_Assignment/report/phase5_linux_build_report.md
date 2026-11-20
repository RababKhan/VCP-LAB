# Phase 5: Linux build and cross-platform verification of VVenC / VVdeC

**Status:** completed 2026-11-05. Both codecs built on Linux (Ubuntu 24.04 under WSL2) from the exact commits of the verified Windows build. All upstream tests that can run without extra downloads passed. The 16-frame smoke test produced a **bitstream byte-identical to Windows**, with an identical reconstruction and identical PSNR.
**Scope:** build, tests and the one smoke configuration only. No new experiment matrix was run. No existing Windows file was modified (checked by SHA256 fingerprints, §7).

---

## 1. Environment

### 1.1 Windows host changes for WSL2 (approved by the user)

| Step | Action | Result (verified) |
|---|---|---|
| Pre-check, 2026-11-04 | read-only queries | WSL not installed. CPU virtualization enabled in firmware. VirtualMachinePlatform disabled. |
| Feature install, 19:45 | elevated `wsl.exe --install --no-distribution` (UAC accepted by the user) | VirtualMachinePlatform enabled, WSL 3.0.3 installed. Log: `logs/phase5_wsl_install_20261104_194528.log` |
| First "restart" check, 20:27 | event log, registry, `wsl --status` | **Failed:** no restart had occurred (no boot event after 19:45; reboot still pending). Nothing was installed. The user was asked to use Start > Power > Restart. |
| Real restart | the user, 2026-11-04 22:04:58 (boot type 0x0, full boot) | HypervisorPresent = True, no reboot pending, `wsl --status` reports no virtualization error |
| Distribution | `wsl.exe --install -d Ubuntu-24.04 --no-launch` (no admin needed) | Ubuntu 24.04 LTS on WSL version 2. Log: `logs/phase5_ubuntu_install_20261104_220700.log` |
| Linux account | created by the user interactively (password never shared) | default user `vvcuser` (uid 1000, member of `sudo`). `/etc/wsl.conf`: `[user] default=vvcuser`, `[boot] systemd=true` |

**Side effect:** Windows now runs on top of the Hyper-V hypervisor. All Windows measurements in Phases 3, 4A, 4B and the supplementary run were taken **before** this change. Windows timings measured from now on would be under different conditions.

### 1.2 Linux environment (measured)

| Item | Value |
|---|---|
| Distribution | Ubuntu 24.04.5 LTS (noble) |
| Kernel | 6.18.54.1-microsoft-standard-WSL2 |
| WSL | 3.0.3.0 (WSLg 1.0.79) |
| Resources seen by the VM | 16 logical CPUs, 7.6 GiB RAM (WSL default: half of the host's 15.7 GiB); SIMD flags sse4.1, sse4.2, avx, avx2 |
| Workspace | `/home/vvcuser/vvc_linux` (Linux ext4 filesystem, not `/mnt/d`), 328 MB after build and tests |
| GCC / G++ | 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1) |
| CMake | 3.28.3 (Ubuntu package 3.28.3-1build7) |
| GNU Make | 4.3 |
| Git | 2.43.0 |
| binutils (ld) | 2.42 |
| glibc | 2.39 |
| build-essential | 12.10ubuntu1 |

The only privileged step was the package install: `apt-get install -y --no-install-recommends build-essential cmake git`. It ran as root via `wsl -u root`, because `sudo` would need the user's password interactively. Cloning, building, testing and the smoke test all ran as `vvcuser` without sudo. Log: `logs/phase5_01_linux_deps.log`.

---

## 2. Source code

| Project | Repository | Checked-out commit | Tag at HEAD | `git status` |
|---|---|---|---|---|
| VVenC | https://github.com/fraunhoferhhi/vvenc.git | `9428ea8636ae7f443ecde89999d16b2dfc421524` | v1.14.0 | clean (no modification) |
| VVdeC | https://github.com/fraunhoferhhi/vvdec.git | `cb1a3efd88b2ebd1141f1a9ca87c774f05de9249` | v3.2.1 | clean (no modification) |

Both commits are identical to the Windows build (`SOFTWARE_VERSIONS.md`). The script checks HEAD against the expected hash ("COMMIT CHECK: PASS" in `logs/phase5_02_clone_vvenc.log` and `logs/phase5_02_clone_vvdec.log`). No upstream source file was modified.

---

## 3. Build

Command (`scripts/linux/clone_build.sh`):
```
cmake -S <src> -B <src>/build/release-static -DCMAKE_BUILD_TYPE=Release
cmake --build <src>/build/release-static --parallel 8
```
The generator is Unix Makefiles (the CMake default). All other options are upstream defaults. 8 parallel jobs were used instead of 16 because the VM has 7.6 GiB of RAM and link-time optimisation is memory-heavy.

| Project | Configure exit | Build exit | Warnings | Errors | Wall time |
|---|---|---|---|---|---|
| VVenC | 0 | 0 | 0 | 0 | 1.65 min |
| VVdeC | 0 | 0 | 0 | 0 | 0.59 min |

Key CMake cache values (both projects): `CMAKE_BUILD_TYPE=Release`, `BUILD_SHARED_LIBS=OFF`, link-time optimisation `ON`, `WERROR=ON` (warnings are treated as errors), x86 SIMD enabled, no ASan/TSan, tracing off. `VVDEC_ENABLE_BITSTREAM_DOWNLOAD=OFF`.

The Windows build (MSVC) also used upstream defaults with Release. Warning counts are comparable only in the sense that both builds finished with WERROR on.

Logs: `logs/phase5_03_build_vvenc.log`, `logs/phase5_03_build_vvdec.log`.

---

## 4. Build verification

### 4.1 Executables (`logs/phase5_04_executables.log`)

| Executable | Size | SHA256 | Self-reported version |
|---|---|---|---|
| `vvenc/bin/release-static/vvencapp` | 4,652,688 B | `a4263b67…d026` | `vvencapp version 1.14.0`. Banner: `[Linux][GCC 13.3.0][64 bit][SIMD=AVX2]` |
| `vvdec/bin/release-static/vvdecapp` | 2,453,528 B | `cbbcbb14…7f6c` | `vvdecapp version 3.2.1` |
| also built | | | `vvencFFapp`, `vvenc_unit_test`, `vvenclibtest`, `vvencinterfacetest`, `vvdec_unit_test` |

Both apps are ELF x86-64 PIE executables. The codec libraries are linked statically (`BUILD_SHARED_LIBS=OFF`). The system runtime (libstdc++, libm, libgcc_s, libc) is linked dynamically, which is the default on Linux (`ldd` output in the log).

### 4.2 Options (help output)
- `vvencapp --help`, `--fullhelp` and `vvdecapp --help` all exit 0. Saved in `logs/help/linux_*.txt`.
- **Supported QP:** `-q, --qp`: "quantization parameter, QP (0, 1, .. 63)".
- **Supported presets:** `--preset`: faster, fast, medium, slow, slower, medium_lowDecEnergy (default: medium).
- `--qpa` (0 = off, 1 = on) and `-t, --threads` are present.
- **Help text is identical to the Windows build** (`diff` after removing CR line endings). The only differences are the first-line platform banner (`[Linux][GCC 13.3.0]` vs `[Windows][VS 1944]`) and the program name in the vvdecapp usage line (`vvdecapp` vs `vvdecapp.exe`). This holds for `vvencapp --help`, `vvencapp --fullhelp` and `vvdecapp --help`.

### 4.3 Upstream tests

| Test | Linux result | Windows (Phase 2) |
|---|---|---|
| `vvenc_unit_test` | "success: all tests passed!", exit 0 | same |
| `vvdec_unit_test` | "success: all tests passed!", exit 0 | same (after the `cmd /c` re-run) |
| VVenC `ctest`: 39 tests (library API tests, unit test, app tool tests, `faster`/`fast`/`medium`/`slow` preset encodes, rate control 2-pass, and output comparison between `vvencapp` and `vvencFFapp`) | **100% passed, 0 failed of 39** (67.5 s) | not run on Windows |
| VVdeC `ctest` | 252 tests registered: 251 are JVET conformance-bitstream decodes listed as `MISSING:<name>.bit` (the bitstreams are not downloaded by default), plus `vvdec_unit_test` (passed, above) | not run on Windows |

The conformance bitstreams were not downloaded, on either platform. Logs: `logs/phase5_05_unit_tests.log`, `logs/phase5_05b_vvenc_ctest.log`.

---

## 5. Cross-platform smoke test

### 5.1 Configuration
The settings are identical to the Phase 3 Windows smoke test (`scripts/smoke_test.ps1`); only the paths differ (`scripts/linux/smoke_test_linux.sh`):
```
vvencapp -i <BasketballPass_416_240_50_10_420.yuv> -s 416x240 -c yuv420_10 --fps 50 -f 16 -q 32 --preset faster --qpa 0 -t 4 -v 4 -o <bs>.266
vvdecapp -b <bs>.266 -o <rec>.yuv -t 4
```
- **Input:** the input YUV was copied into the Linux filesystem. Its SHA256 `de0dcc61…d593ed698` matches the dataset value (`logs/phase5_06_smoke_input.log`).
- **Repeats:** the Linux run was repeated 3 times to check determinism. Run 1 is the reference.
- **PSNR:** the Linux reconstruction was copied back to the project (`recon/phase5_linux/`, copy verified by SHA256). PSNR was computed with the same `scripts/psnr_yuv.py` used for Windows (`scripts/compare_phase5.py`).

### 5.2 Results (measured)

| Metric | Windows (MSVC 19.44, Phase 3) | Linux (GCC 13.3, WSL2) | Same? |
|---|---|---|---|
| Encode / decode exit codes | 0 / 0 | 0 / 0 | yes |
| Encoder pictures / decoded frames | 16 / 16 | 16 / 16 | yes |
| Reconstruction size | 4,792,320 B (= 16 × 299,520) | 4,792,320 B | yes |
| Bitstream size | 10,069 B | 10,069 B | yes |
| **Bitstream SHA256** | `5037d0750588ac5fe0b02a7aa4fa038709ea4fd4364b6b27adf5b7890a20e1bb` | `5037d0750588ac5fe0b02a7aa4fa038709ea4fd4364b6b27adf5b7890a20e1bb` | **yes, byte-identical** |
| **Reconstruction SHA256** | `17dda8aee3708c15df5cc7134bb613371fdcf70c2aa9db931f923c6ef3c699cb` | `17dda8aee3708c15df5cc7134bb613371fdcf70c2aa9db931f923c6ef3c699cb` | **yes** |
| Y / U / V PSNR (dB, peak 1020) | 34.2535 / 39.7084 / 38.5279 | 34.2535 / 39.7084 / 38.5279 | yes (identical to full double precision) |
| YUV-PSNR (4:1:1 MSE) | 35.1826 | 35.1826 | yes |
| PSNR from the independent script vs the encoder log | match | match (< 5·10⁻⁵ dB) | yes |
| Bitrate (encoder-reported) | 251.725 kbps | 251.725 kbps | yes |
| Intra pictures | POC 15 IDR_W_RADL | POC 15 IDR_W_RADL | yes |
| Frame alignment (best offset) | 0 | 0 | yes |

- **Linux determinism:** all 3 Linux runs gave the same bitstream and reconstruction SHA256.
- **Encoder configuration echo:** every `vvenc [notice]` configuration line is identical apart from file paths. Examples: Threads "4 (parallel frames: 4)", Rate control "QP 32", Perceptual optimization "Disabled", GOP size 32, Intra period 48, profile main_10, level 2.1.
- **Full encoder log:** after removing paths, timestamps, timing fields and the platform banner, the logs differ in exactly two lines. Both are the encoder's speed statistics: `fps= 46.5` on Windows vs `fps= 82.1` on Linux. All 16 per-picture lines (POC, temporal layer, NAL type, slice type, QP, bits, per-picture Y/U/V PSNR, reference lists) are identical. File: `results/phase5_linux/encoder_log_diff_windows_vs_linux.txt`.

### 5.3 Timing (recorded, not a benchmark)

| | Windows (Phase 3, 2026-10-27, one run) | Linux runs 1 / 2 / 3 (2026-11-05) |
|---|---|---|
| Encode, reported | 0.345 s | 0.196 / 0.197 / 0.189 s |
| Encode, wall | 0.452 s | 0.251 / 0.242 / 0.234 s |
| Decode, wall | 0.055 s | 0.025 / 0.020 / 0.022 s |

**These numbers must not be read as "Linux is faster than Windows."** The conditions were not controlled:
- compiler (MSVC vs GCC) and C runtime
- OS and scheduler; Linux ran inside a WSL2 VM with 7.6 GiB RAM
- the Windows run used an unknown power mode (Phase 3 predates the power-mode checks); the Linux run's power mode was not recorded
- a different day, and after the hypervisor was enabled
- Windows: 1 sample; Linux: 3 samples
- the input files were on different filesystems
- the runs are sub-second, so start-up and I/O are a large share of the time

A fair comparison would need the same machine state, power mode, input location, many repeats and longer sequences. That was not part of this phase.

---

## 6. Findings (measured vs interpretation)

| Statement | Basis |
|---|---|
| VVenC 1.14.0 and VVdeC 3.2.1 build on Linux (GCC 13.3) from the unmodified upstream commits, with 0 warnings and 0 errors | Measured |
| All available upstream tests pass on Linux (2 unit-test programs + 39 VVenC ctest tests) | Measured |
| For this configuration (16 frames, QP 32, `faster`, QPA off, 4 threads), the Windows/MSVC and Linux/GCC builds produce byte-identical bitstreams and reconstructions | Measured (SHA256) |
| The two builds therefore make identical encoding decisions for this input and configuration | Direct consequence of identical bitstreams |
| The encoders would also match for other presets, QPs, thread counts or longer sequences | **Not tested.** This is not claimed. |
| Linux being faster | **Not established** (§5.3) |

Cross-platform identity was not assumed in advance. The comparison was set up to document a difference had one appeared.

---

## 7. Preservation of Windows data (measured)
- `results/full/` SHA256 fingerprint: `44eb11e4…2c47` (136 files). Identical to the value recorded before and after the supplementary run.
- `results/smoke/` and `results/supp_ac/` were only read.
- Windows smoke bitstream, reconstruction and encode log are unchanged (timestamps 2026-10-27 19:37:11; the bitstream SHA256 is unchanged).
- Windows executables are unchanged (`vvencapp.exe` `c74f3b63…160b`, `vvdecapp.exe` `3f46677a…b6`).
- All Phase 5 outputs went to new locations: `logs/phase5_*`, `logs/help/linux_*`, `results/phase5_linux/`, `bitstreams/phase5_linux/`, `recon/phase5_linux/`, `scripts/linux/`, `scripts/compare_phase5.py`, and the WSL home directory.

---

## 8. Limitations
1. **One configuration.** Cross-platform identity is shown only for the 16-frame smoke configuration (4 threads). The Phase 4B matrix (500–600 frames, 8 threads, CRA refresh) was not re-encoded on Linux.
2. **WSL2, not native Linux.** Linux runs in a lightweight Hyper-V VM on the same laptop. Bitstream results should not depend on this; timing does.
3. **One compiler per platform.** Only GCC 13.3 on Linux and only MSVC 19.44 on Windows. Clang was not tested.
4. **Conformance tests not run.** The VVdeC JVET conformance tests (251) need a separate download of the conformance bitstreams. They were not run on either platform.
5. **The upstream test sets differ between platforms.** Windows ran the two unit-test programs; Linux ran those plus VVenC ctest.
6. **Timing is not a benchmark** (§5.3).
7. **Hypervisor now active on Windows** (§1.1). This does not affect any recorded result, but it changes the conditions for any future Windows timing.

---

## 9. Reproducing
From Windows (PowerShell), with Ubuntu-24.04 installed and the default user created:
```
wsl -d Ubuntu-24.04 -u root -- bash /mnt/d/Korea/VVC_Assignment/scripts/linux/install_deps.sh
wsl -d Ubuntu-24.04 -- bash /mnt/d/Korea/VVC_Assignment/scripts/linux/check_env.sh
wsl -d Ubuntu-24.04 -- bash /mnt/d/Korea/VVC_Assignment/scripts/linux/clone_build.sh /mnt/d/Korea/VVC_Assignment/logs
wsl -d Ubuntu-24.04 -- bash /mnt/d/Korea/VVC_Assignment/scripts/linux/verify_build.sh /mnt/d/Korea/VVC_Assignment/logs
wsl -d Ubuntu-24.04 -- bash /mnt/d/Korea/VVC_Assignment/scripts/linux/run_vvenc_ctest.sh /mnt/d/Korea/VVC_Assignment/logs
wsl -d Ubuntu-24.04 -- bash /mnt/d/Korea/VVC_Assignment/scripts/linux/smoke_test_linux.sh /mnt/d/Korea/VVC_Assignment
.venv\Scripts\python.exe scripts\compare_phase5.py
```

**Logs:**
- `logs/phase5_environment_notes.md`
- `logs/phase5_wsl_install_*.log`
- `logs/phase5_ubuntu_install_*.log`
- `logs/phase5_01_linux_deps.log`
- `logs/phase5_02_clone_*.log`
- `logs/phase5_03_build_*.log`
- `logs/phase5_04_executables.log`
- `logs/phase5_05_unit_tests.log`
- `logs/phase5_05b_vvenc_ctest.log`
- `logs/phase5_06_smoke_input.log`
- `logs/phase5_07_smoke_*.log`
- `logs/phase5_08_compare.log`

**Results:** `results/phase5_linux/` (`cross_platform_comparison.json/.md/.csv`, per-run PSNR JSON/CSV, encoder log diff).
