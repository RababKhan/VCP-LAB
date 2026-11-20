# VVC Assignment: Independent Experiment Guide

**Experimenter:** Sadab Khan Prangon
**Assignment:** VVC encoding and decoding with VVenC and VVdeC, for Prof. Kiho Choi, Video Coding and Processing Lab, Kyung Hee University.

This guide assumes that **nothing has been done yet**. Every result in the presentation must come from the files these steps create on your own computer.

---

## 0. The plan in one picture

```
 2 sequences  x  4 QPs (24, 29, 34, 39)  x  2 presets (fast, medium)  =  16 encodes
     |
     +--> VVenC encodes each YUV file into a .266 bitstream   -> encode time, file size, bitrate, encoder PSNR
     +--> VVdeC decodes each bitstream back to YUV (3 times)  -> decode time
     +--> psnr_check.py compares the decoded YUV with the original -> your own PSNR check
     +--> YUView: look at the original and decoded frames      -> screenshots
 + 2 repeated encodes, to see how much timing changes from run to run
 + 1 cross-platform check: the same encode on Windows and on Linux, compare the bitstream SHA256
```

| Item | Value | Why |
|---|---|---|
| Sequences | **BlowingBubbles** 416x240, 50 fps, 500 frames; **BQMall** 832x480, 60 fps, 600 frames | Two resolutions, two kinds of motion, both 10 s long, both from the provided YUV files |
| Format | 10-bit, 4:2:0 (`yuv420_10`) | This is how the provided files are stored |
| QP | 24, 29, 34, 39 | Steps of 5 cover high to low quality |
| Presets | `fast`, `medium` | Shows the speed versus compression trade-off |
| Fixed settings | `--qpa 0`, `-t 8`, all other options default | QPA off keeps QP constant, so QP is the only quality control |
| Encodes | 16 + 2 repeats = 18 | Small enough to finish in one session |

**Before you start, check:**
- If your files have other names or sizes, use your own values everywhere.
- The file name tells you the format: `name_width_height_fps_bitdepth_chroma.yuv`.
- If your CPU has fewer than 8 threads, change `-t 8` to your thread count and keep it the same for every run.

**Words used in this guide:**
- **QP (quantization parameter):** a higher QP means stronger compression, a smaller file and lower quality.
- **Preset:** how hard the encoder searches. `medium` searches more than `fast`, so it is slower but usually compresses better.
- **PSNR:** a number in dB that tells how close the decoded video is to the original. Higher is better.
- **Bitrate (kbps):** how many kilobits per second of video the bitstream needs.

---

## 1. Install the tools (Windows)

You are making system changes, so do this only on **your own** computer.

| Tool | Where | Check that it works |
|---|---|---|
| Git for Windows | https://git-scm.com/download/win | `git --version` |
| CMake (3.20 or newer) | https://cmake.org/download/ | `cmake --version` |
| Visual Studio 2022 Build Tools, with the workload **"Desktop development with C++"** | https://visualstudio.microsoft.com/downloads/ (under "Tools for Visual Studio") | Open **"Developer PowerShell for VS 2022"** and run `cl` |
| Python 3 and numpy | https://www.python.org/downloads/, then `py -m pip install numpy` | `py -c "import numpy; print(numpy.__version__)"` |
| YUView | https://github.com/IENT/YUView/releases (Windows zip) | Start `YUView.exe` |

Write down every version number in `results/environment.txt`. You will need them for slide 3.

## 2. Get the source code

Open **Developer PowerShell for VS 2022** and run:

```powershell
mkdir D:\vvc_sadab
cd D:\vvc_sadab
git clone --branch v1.14.0 --depth 1 https://github.com/fraunhoferhhi/vvenc.git
git clone --branch v3.2.1  --depth 1 https://github.com/fraunhoferhhi/vvdec.git
git -C vvenc log -1 --format="%H %d"     # write down the commit hash
git -C vvdec log -1 --format="%H %d"
```

- You can choose a newer release tag. If you do, write it down and use it on both Windows and Linux.
- Copy the provided YUV files into `D:\vvc_sadab\dataset\`.
- Copy this `experiment` folder, including all four files, to `D:\vvc_sadab\experiment\`.

## 3. Build VVenC and VVdeC on Windows

```powershell
cd D:\vvc_sadab
cmake -S vvenc -B vvenc\build -G "Visual Studio 17 2022" -A x64
cmake --build vvenc\build --config Release --parallel
cmake -S vvdec -B vvdec\build -G "Visual Studio 17 2022" -A x64
cmake --build vvdec\build --config Release --parallel
```

**Where the programs should appear:** `vvenc\bin\release-static\vvencapp.exe` and `vvdec\bin\release-static\vvdecapp.exe`. If they are somewhere else, search with `Get-ChildItem -Recurse -Filter vvencapp.exe`.

**Verify the build** (save each output into `logs\`):

```powershell
mkdir logs, results
.\vvenc\bin\release-static\vvencapp.exe --version  *>&1 | Tee-Object logs\win_vvenc_version.log
.\vvdec\bin\release-static\vvdecapp.exe --version  *>&1 | Tee-Object logs\win_vvdec_version.log
ctest --test-dir vvenc\build -C Release --output-on-failure *>&1 | Tee-Object logs\win_vvenc_ctest.log
ctest --test-dir vvdec\build -C Release --output-on-failure *>&1 | Tee-Object logs\win_vvdec_ctest.log
```

Look for **"100% tests passed"** at the end of each `ctest` log. If a test fails, keep the log and report it honestly. Do not hide it.

> **If Windows refuses to run `vvdecapp.exe` or `vvencapp.exe`** (for example, a "Smart App Control" or "blocked" message): Windows 11 can block programs you compiled yourself, because they have no digital signature.
> - Do **not** switch off security settings just for this.
> - Write the message down, use the Linux build (step 4) for the blocked tool, and say so in your presentation.

## 4. Build on Linux (WSL2 Ubuntu 24.04, or a real Linux PC)

If you do not have WSL yet:
- Open PowerShell **as administrator** and run `wsl --install -d Ubuntu-24.04`.
- Restart the computer, then create your Ubuntu user name and password.
- Never share that password with anyone.

In the Ubuntu terminal:

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake git
mkdir -p ~/vvc_sadab && cd ~/vvc_sadab
git clone --branch v1.14.0 --depth 1 https://github.com/fraunhoferhhi/vvenc.git
git clone --branch v3.2.1  --depth 1 https://github.com/fraunhoferhhi/vvdec.git
cmake -S vvenc -B vvenc/build/release-static -DCMAKE_BUILD_TYPE=Release
cmake --build vvenc/build/release-static --parallel 8
cmake -S vvdec -B vvdec/build/release-static -DCMAKE_BUILD_TYPE=Release
cmake --build vvdec/build/release-static --parallel 8
```

Then run the check script. It saves versions, test results and a cross-platform bitstream check into `D:\vvc_sadab\logs\`:

```bash
bash /mnt/d/vvc_sadab/experiment/linux_check.sh
```

**Important:** the build and tests are kept in your Linux home folder because that is faster. Timing measured in WSL2 is **not** a fair speed comparison with Windows, so do not claim that Linux is faster or slower.

## 5. Try one encode and decode by hand (to understand each option)

```powershell
cd D:\vvc_sadab
mkdir out
.\vvenc\bin\release-static\vvencapp.exe -i dataset\BlowingBubbles_416_240_50_10_420.yuv -s 416x240 -c yuv420_10 --fps 50 -f 500 -q 34 --preset fast --qpa 0 -t 8 -o out\test_QP34_fast.266
.\vvdec\bin\release-static\vvdecapp.exe -b out\test_QP34_fast.266 -o out\test_QP34_fast_rec.yuv -t 8
```

| Option | Meaning |
|---|---|
| `-i` | input YUV file |
| `-s 416x240 -c yuv420_10 --fps 50` | picture size, 10-bit 4:2:0, frame rate. A raw YUV file has no header, so you must give these yourself |
| `-f 500` | number of frames to encode |
| `-q 34 --preset fast` | base QP and encoder preset |
| `--qpa 0` | QP adaptation off, so QP stays constant |
| `-t 8` | number of threads |
| `-o` (encoder) | output bitstream (`.266`) |
| `-b` / `-o` (decoder) | input bitstream / output decoded YUV |

**What to look for in the encoder output:**
```
vvenc [info]:   Total Frames |   Bitrate     Y-PSNR    U-PSNR    V-PSNR    YUV-PSNR
vvenc [info]:          500    a     ....       ....      ....      ....      ....      <- bitrate (kbps) and PSNR (dB)
vvencapp [info]: Total Time: ... sec.                                                 <- encoding time
```
**In the decoder output:** `500 frames decoded @ ... fps (... sec)`. This is the decoding time.

## 6. Run the full experiment

Close other programs, plug in the charger, and keep the same Windows power mode for all runs. Then:

```powershell
cd D:\vvc_sadab
powershell -ExecutionPolicy Bypass -File experiment\run_experiment.ps1 -Root D:\vvc_sadab
```

**What the script does:**
1. Runs the 16 configurations in a shuffled but repeatable order, plus 2 repeated encodes. Shuffling stops "later runs were hotter or slower" from looking like a preset effect.
2. Saves the full console output of every run in `logs\runs\`.
3. Decodes each bitstream **3 times** and keeps the median decode time.
4. Runs `psnr_check.py` on the decoded file and compares the result with the encoder's own PSNR.
5. Writes one row per run into **`results\results_raw.csv`** (same columns as `results_template.csv`). It also saves `results\environment.txt` (CPU, Windows version, power state).

**Disk space:** about 8 GB for the decoded `.yuv` files. They are kept so that you can open them in YUView.

**Time:** usually between a few seconds and a few minutes per encode on a laptop. `medium` is slower than `fast`, and BQMall is slower than BlowingBubbles.

**If a run fails:** the script writes `status = FAILED` and continues. Do not delete failed rows; report them.

**Which time to use:**
- *Encoding time* = the encoder's own "Total Time" (column `encode_time_s`).
- *Wall time* includes starting the program and is also saved.
- *Decoding time* = the median of the 3 decodes.

## 7. Check the PSNR independently

`run_experiment.ps1` already does this. To run it by hand:

```powershell
py experiment\psnr_check.py dataset\BlowingBubbles_416_240_50_10_420.yuv out\test_QP34_fast_rec.yuv 416 240 500
```

**How PSNR is calculated:**
- PSNR uses peak = 1020 (that is, 255 x 4, for 10-bit video). This is the convention used by HM, VTM and VVenC.
- PSNR is calculated for every frame and then averaged.

**What to check:**
- The result should match the encoder's Y/U/V-PSNR to about 0.01 dB.
- If it does not, check the frame count and the YUV format before using any number.

## 8. Inspect the video in YUView and take screenshots

1. Open YUView. Use **File -> Open** (or drag and drop) to open the original file and two decoded files: QP 24 medium and QP 39 medium of the same sequence.
2. For each file, check **Properties**: width/height, `YUV 4:2:0`, `10 bit`, frame rate. YUView guesses these from the file name, so name your decoded files like `..._416x240_50fps_10bit_420.yuv`, or set them by hand.
3. Choose **one frame number** and use it for every file. Write it down.
4. Use **View -> Split view** to put the original and the decoded frame side by side. Zoom into an area with fine detail, such as edges, text or texture.
5. Take screenshots with **Win + Shift + S** and save them into `screenshots\` with clear names, for example `BlowingBubbles_f200_original_vs_QP39_medium.png`.
6. Write down in one or two sentences what **you** see (for example: "QP 39 looks blurred at the edges"). Only write what you actually saw.

## 9. What to send back for the presentation

| File | Used on slide |
|---|---|
| `results\results_raw.csv` | 5, 6, 8 |
| `results\environment.txt` and the version numbers from step 1 | 3 |
| `logs\win_*_ctest.log`, `logs\linux_*` and `logs\cross_platform_check.txt` | 3 |
| 2 to 4 YUView screenshots, with the frame number and your own observation | 7 |
| Any failure or blocking message | 3 (stated honestly) |

You can record the measurements by hand in **`results_template.csv`** (open it in Excel). It has one row for each planned run and the same columns that the script writes.
