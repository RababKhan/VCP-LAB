# Live experiment demonstration: VVC encoder presets (Sadab Khan Prangon)

This folder shows Prof. Kiho Choi how the experiment was run and where every number in the presentation comes from.
It uses the real project files, scripts, logs and CSV results.

> **Who did what.**
> - **Original experiment (94 encoder runs):** automated scripts, written and executed by Claude (an AI assistant) on this laptop.
> - **This demo:** Sadab personally re-runs and checks selected steps.
>
> The demo does **not** repeat the 94 runs.

**For the meeting, follow [FINAL_LIVE_DEMO_GUIDE.md](FINAL_LIVE_DEMO_GUIDE.md).** It covers every step: command, expected output, slide, what to say, what to do if it fails, and YUView click by click.

Background: [DEMO_SCRIPT.md](DEMO_SCRIPT.md) (the longer speaking script) and [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) (preparation).

## Folder contents

| File | Purpose | Run time |
|---|---|---|
| `demo_encode.ps1` | Shows the encoder version, encodes, writes the VVC bitstream, measures size, bitrate and encoding time | ~5 s short, ~15 s full |
| `demo_decode.ps1` | Shows the decoder version, decodes, saves the reconstructed YUV, checks the frame count, times 3 decodes | ~3 s |
| `demo_psnr.ps1` | Independent Y/U/V PSNR with the experiment's own `experiment/psnr_check.py`, compared with the encoder's value | ~3 s |
| `demo_results.py` | Traces every measured value of a saved run to its log line and CSV column; recomputes SSIM / MS-SSIM; maps slides 5 and 6 to the CSV | ~10 s |
| `demo_bdrate.py` | Walks through one BD-rate step by step; recomputes all 12 BD-rates and compares them with `results/bdrate.csv` and slide 7 | ~3 s |
| `demo_crossplatform.py` | Recomputes the SHA-256 of the saved Windows and Linux files for the 8 comparisons on slide 9 | ~10 s |
| `demo_yuview.ps1` | Opens BasketballDrive (original + QP 24/29/34/39) in YUView and prints the frame and crop to show | ~2 s |
| `demo_common.ps1`, `demo_pyutil.py` | Shared helpers (paths, SHA-256, report writing) | – |
| `SLIDE_DATA_MAPPING.md` | Slide → displayed value → CSV → log → calculation | – |
| `output/` | **Everything the demo writes goes here**, in new time-stamped folders and files | – |

## How to run

Open **Windows PowerShell** and go to this folder:

```powershell
cd D:\Korea\Prangon_VVC_Assignment\professor_demo
powershell -ExecutionPolicy Bypass -File .\demo_encode.ps1               # short demo (32 frames)
powershell -ExecutionPolicy Bypass -File .\demo_decode.ps1
powershell -ExecutionPolicy Bypass -File .\demo_psnr.ps1
powershell -ExecutionPolicy Bypass -File .\demo_encode.ps1 -Mode Full    # reproduce original run A029 (500 frames)
powershell -ExecutionPolicy Bypass -File .\demo_decode.ps1
powershell -ExecutionPolicy Bypass -File .\demo_psnr.ps1
..\.venv\Scripts\python.exe demo_results.py
..\.venv\Scripts\python.exe demo_bdrate.py
..\.venv\Scripts\python.exe demo_crossplatform.py
powershell -ExecutionPolicy Bypass -File .\demo_yuview.ps1
```

**About `-ExecutionPolicy Bypass`:**
- This computer's PowerShell policy is "Restricted", which stops `.ps1` files from running.
- `-ExecutionPolicy Bypass` allows only that one command to run. It does **not** change any system setting.

**Linking the steps:** `demo_decode.ps1` and `demo_psnr.ps1` always use the newest folder in `output/`. To choose another one, add `-RunDir <folder>`.

## The two demo encodes

All demo encodes use BasketballPass (416×240, 10-bit 4:2:0, 50 fps).

| Mode | Settings | What it proves |
|---|---|---|
| **Short** (default) | QP 29, preset medium, **32 frames** | The full workflow, quickly. **This is not one of the original 500-frame measurements.** |
| **Full** (`-Mode Full`) | QP 29, preset faster, **500 frames**: the same settings as original run **A029** | The bitstream and decoded video are **bit-identical** to the saved original (same SHA-256) |

The encoder command is exactly the one in `experiment/run_phase2.py` and in the original logs:

```
vvencapp -i <input.yuv> -s 416x240 -c yuv420_10 --fps 50 -f <frames> -q <QP> --preset <preset> --qpa 0 -t 8 -o <out.266>
vvdecapp -b <out.266> -o <recon.yuv> -t 8        (decode with output: frame count, PSNR)
vvdecapp -b <out.266> -t 8                       (3 timing decodes without output; the median is kept)
```

## Important: Windows now blocks the encoder program

On **15 November 2026**, Windows Application Control (Smart App Control) started refusing to run `vvenc\bin\release-static\vvencapp.exe`:

> "An Application Control policy has blocked this file"

- The same file ran normally for all experiments on 11 November.
- The decoder `vvdecapp.exe`, Python and YUView still run.
- No security setting was changed. Smart App Control can only be switched off for the whole PC, so do not do this for the demo.

**What the scripts do:**
- `demo_encode.ps1` first tries the Windows encoder.
- If Windows blocks it, the script prints a yellow note and runs the **Linux build of the same VVenC 1.14.0** in WSL2 (Ubuntu 24.04).
- Slide 9 already shows that this build gives bit-identical results.
- Tested on 15 November 2026: the Linux build reproduced original run A029 exactly (bitstream SHA-256 `7f4bc413…aa5a`).

**What not to use:**
- **Do not compare encoding times** from the Linux build with the original Windows times. WSL reads the input from D: through a slower file bridge (15.0 s vs 8.4 s for A029).
- **`vvencFFapp.exe` is not a replacement.** It still runs, but it has different defaults. With the same options its bitstream differed (577,807 vs 578,073 bytes).

## Expected results (tested on 15 November 2026)

| Step | Expected output |
|---|---|
| Short encode | 20,869 bytes; 260.863 kbps; Y/U/V PSNR 37.2215 / 42.2963 / 41.1148 dB; SHA-256 `9588cc94…3789`. Encoding about 4 s (Linux build) |
| Short decode | 32 frames; reconstruction SHA-256 `a1cb966a…e346` |
| Short PSNR | independent = encoder, difference 0.0000 dB |
| Full encode (A029) | 578,073 bytes; SHA-256 `7f4bc413…aa5a`. Shows [MATCH] for size and SHA-256 |
| Full decode | 500 frames; reconstruction SHA-256 `2df48646…2a25` = original. Shows [MATCH] |
| Full PSNR | Y 34.8147, U 39.9791, V 38.2132 = original. Shows [MATCH] |
| `demo_results.py` | 31 checks, 31 match |
| `demo_bdrate.py` | 21 checks, 21 match (BasketballPass faster vs medium: +25.14 %) |
| `demo_crossplatform.py` | 25 checks, 25 match (8/8 comparisons bit-exact) |

**Repeatable outputs:** the encoder is deterministic, so sizes, hashes and PSNR come out the same every time.
- Encoding and decoding **times** change slightly every run.
- The short demo was tested only with the Linux build. If the Windows encoder works again and gives a different hash, report it honestly; do not hide it.

## What the demo never does

- **Experiment files:** it never writes to `results/`, `logs/`, `out/`, `dataset/`, `visual/`, `experiment/`, `analysis/` or `presentation/`.
  - Every script only reads them.
  - Test on 15 November 2026: all 11,567 project files outside `professor_demo/` had the same size and modification time before and after the tests. All 398 CSV, log, script, deck and bitstream files also had the same SHA-256.
- **Other limits:** it does not re-run the 94 experiments, does not run `analysis/analyze_full.py` (that script would rewrite the CSV files), does not change any security setting, and does not delete anything.

## If something fails

| Problem | Safe alternative |
|---|---|
| Windows blocks `vvencapp.exe` | Automatic: the script uses the Linux build. You can force it with `-Engine Linux` |
| WSL does not start | Skip the live encode. Run `demo_results.py`, which shows the **saved** original run A029 (log, CSV, file hashes), and say honestly that the live encode is blocked on this laptop |
| Windows blocks `vvdecapp.exe` | Automatic: the script uses the Linux decoder. Or use `-Engine Linux` |
| YUView does not start | `demo_yuview.ps1` opens `visual/v2/BasketballDrive_f98_typical_strip.png` instead. Say clearly that it is a script rendering, not YUView |
| Disk space | The output of one full run is about 150 MB. Old `output/` folders can be deleted after the demo. They are demo output only |
