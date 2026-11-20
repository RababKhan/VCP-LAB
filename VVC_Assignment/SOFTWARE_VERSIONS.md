# Software Versions and Build Configuration

All values below were read from the actual tools/repositories on 2026-10-27 (see `logs/`).

## Host
| Item | Value |
|---|---|
| OS | Windows 11 Home Single Language 10.0.26200 (64-bit) |
| CPU | Intel Core i7-1260P (12 cores / 16 threads, AVX2) |
| RAM | 15.7 GB |

## Codec sources
| Project | Repository | Tag | Commit |
|---|---|---|---|
| VVenC | https://github.com/fraunhoferhhi/vvenc.git | v1.14.0 | 9428ea8636ae7f443ecde89999d16b2dfc421524 |
| VVdeC | https://github.com/fraunhoferhhi/vvdec.git | v3.2.1 (branch `release-3.2.1`) | cb1a3efd88b2ebd1141f1a9ca87c774f05de9249 |

Latest stable release tags were used instead of `master` for reproducibility. No upstream source file was modified (`git status` clean).

## Windows toolchain
| Tool | Version | Source |
|---|---|---|
| Visual Studio Build Tools 2022 | 17.14.37806.7 (winget `Microsoft.VisualStudio.2022.BuildTools` 17.14.42) | Microsoft, via winget |
| MSVC compiler (cl.exe) | 19.44.35229 for x64 (toolset 14.44.35207) | VS Build Tools |
| Windows SDK | 10.0.26100.0 | VS Build Tools |
| CMake | 4.4.4 (portable zip, SHA256 verified) | https://github.com/Kitware/CMake/releases/tag/v4.4.4 |
| Git | 2.55.0.windows.5 | pre-installed |
| Python | 3.12.10 (user scope) | python.org, via winget `Python.Python.3.12` |
| FFmpeg | n9.0.2-36-g6882969ce9-20261026 (BtbN `ffmpeg-n9.0-latest-win64-gpl-9.0.zip`, SHA256 verified) | https://github.com/BtbN/FFmpeg-Builds |
| YUView | v2.14 (`YUView-Win.zip`, SHA256 34D1F04B4930E83C3D0845F523CB5955E79C1684B641EF2AFD3D9B051997F353) | https://github.com/IENT/YUView/releases/tag/v2.14 |

VS components installed: `Microsoft.VisualStudio.Workload.VCTools` (required set), `Microsoft.VisualStudio.Component.VC.Tools.x86.x64`, `Microsoft.VisualStudio.Component.Windows11SDK.26100` (no `--includeRecommended`).

## Build configuration (Windows)
- Generator: `Visual Studio 17 2022`, platform `x64`, configuration `Release`
- Command: `scripts/build_windows.ps1` (`cmake -S <src> -B <src>/build/release-static -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release`, then `cmake --build ... --config Release --parallel`)
- All other CMake options are upstream defaults (static libs, x86 SIMD on, LTO on, warnings-as-errors on).
- Build result: 0 warnings, 0 errors for both projects. Wall time: VVenC 4.24 min, VVdeC 1.28 min.

## Unit tests (upstream test programs)
- `vvenc_unit_test.exe`: "success: all tests passed!", exit 0 (`logs/phase2_10_unit_tests.log`)
- `vvdec_unit_test.exe`: 12/12 suites, "success: all tests passed!", exit 0 (`logs/phase2_11_vvdec_unit_test_rerun.log`). The first attempt in `phase2_10` ran no tests ("Unknown argument" printed); it was re-run via `cmd /c`.

## Executables
| Executable | Self-reported version |
|---|---|
| `src/vvenc/bin/release-static/vvencapp.exe` | `vvencapp version 1.14.0` — banner `[Windows][VS 1944][64 bit][SIMD=AVX2]` |
| `src/vvenc/bin/release-static/vvencFFapp.exe` | 1.14.0 (full-feature expert app) |
| `src/vvdec/bin/release-static/vvdecapp.exe` | `vvdecapp.exe version 3.2.1` |
