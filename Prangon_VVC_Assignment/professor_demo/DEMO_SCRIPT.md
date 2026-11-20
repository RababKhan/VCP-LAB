# Demo script: live experiment demonstration (about 10 minutes)

**For:** Sadab Khan Prangon, presenting to Prof. Kiho Choi
**Where:** this laptop. Everything needed is in `D:\Korea\Prangon_VVC_Assignment`.

**Before you start:** do the "Before the demo" part of [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md). Have these open:
- one **Windows PowerShell** window, already in the `professor_demo` folder
- File Explorer, in the project folder

Lines marked **SAY** are suggestions. Use your own words, but keep the facts the same.

| Time | Step | |
|---|---|---|
| 0:00 | 0. Introduction (who did what) | must do |
| 0:45 | 1. The original command and log | must do |
| 1:45 | 2. Short encode | must do |
| 3:00 | 3. Decode and frame count | must do |
| 3:45 | 4. Independent PSNR | must do |
| 4:30 | 5. Full reproduction of run A029 (bit-exact) | must do |
| 5:45 | 6. Where the slide 5/6 numbers come from | must do |
| 7:00 | 7. BD-rate (slide 7) | must do |
| 8:00 | 8. YUView, frame 98 | must do |
| 9:15 | 9. Windows vs Linux | skip if short of time |
| 9:45 | 10. Close | |

---

## 0. Introduction (45 s)

**Click / type:** nothing. Show slide 1 or the project folder.

**SAY:**
> "Professor, I would like to show you how the experiment was run and where the numbers in my slides come from.
> I want to be transparent: the original 94 encoder runs were executed by automated scripts. Claude, an AI
> assistant, wrote and ran them on this laptop. Today I am personally reproducing and checking selected steps,
> with the same programs, files and logs. I will not repeat all 94 runs, because some of them take up to
> 55 minutes."

## 1. The original command and log (1 min)

**Click:** in File Explorer, open `logs\phase2\A029_BasketballPass_QP29_faster.log` in Notepad. Show the first lines, then search (Ctrl+F) for `Total Time`.

**What it is:** the complete log of one original run. It records the exact command, the encoder output and the decode and PSNR checks.

**Expected:**
- line 2: `Command: …vvencapp.exe -i …BasketballPass_416_240_50_10_420.yuv -s 416x240 -c yuv420_10 --fps 50 -f 500 -q 29 --preset faster --qpa 0 -t 8 -o …A029….266`
- further down: `Total Time: 8.422 sec.`

**SAY:**
> "Every run has a log like this. This is run A029: BasketballPass, QP 29, preset faster, 500 frames.
> Here is the exact command: 10-bit 4:2:0 input, QP 29, perceptual QP adaptation off (`--qpa 0`) and 8 threads.
> The encoder reported 8.4 seconds. The scripts copied these values into `results\results_phase2.csv`."

## 2. Short encode (1 min 15 s)

**Type:**
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_encode.ps1
```

**What it does:**
1. Prints the encoder version.
2. Encodes the first 32 frames of BasketballPass at QP 29, preset medium, with the same command as the experiment.
3. Measures the bitstream size, bitrate and encoding time.
4. Saves everything in a new folder under `professor_demo\output\`.

**Expected:**
- the magenta line `SHORT DEMO: 32 frames only. This is NOT one of the original 500-frame measurements.`
- a **yellow NOTE**: `Windows refused to start vvencapp.exe … An Application Control policy has blocked this file … Using the Linux build of the same version in WSL instead`
- `vvencapp version 1.14.0 [engine: Linux (WSL2)]`
- `Bitstream size : 20869 bytes`
- `Bitrate : 20869 bytes x 8 / (32 frames / 50 fps = 0.64 s) / 1000 = 260.863 kbps`
- `Encoding time : about 4 s`
- `Encoder PSNR (dB) : Y 37.2215 U 42.2963 V 41.1148`

**Meaning:**
- The bitrate is the file size in bits divided by the video duration.
- The encoder's own bitrate (260.8625) agrees.
- The time is the encoder's "Total Time".

**SAY:**
> "This short run uses only 32 frames, so it is a demonstration, not one of my measurements.
> Since 15 November, Windows Smart App Control blocks the unsigned encoder program. I did not change any security
> setting. Instead, the script uses the Linux build of the same VVenC version. On slide 9 I show that it is
> bit-exact with the Windows build. Because Linux runs in WSL, this time is not comparable with my Windows timings."

*(If no yellow note appears, Windows allowed the encoder again; the engine says `Windows`. That is fine.)*

## 3. Decode and frame count (45 s)

**Type:**
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_decode.ps1
```

**What it does:**
1. Prints the decoder version.
2. Decodes the bitstream with VVdeC and saves the reconstructed YUV file.
3. Counts the frames from the file size.
4. Decodes 3 more times without an output file and reports the median time.

**Expected:**
- `vvdecapp.exe version 3.2.1 [engine: Windows]`
- `9584640 bytes / (416 x 240 x 1.5 samples x 2 bytes = 299520 bytes per frame) = 32 frames`
- `[MATCH] decoded frame count = 32`
- three decode lines, then `Median decode time: about 0.02 s`

**SAY:**
> "One frame of 10-bit 4:2:0 video at 416×240 has 1.5 samples per pixel, and each sample takes 2 bytes. So the
> file size tells us the number of frames: exactly 32. In the experiment, decoding was timed three times without
> writing a file, so that disk speed does not count, and the median was kept."

## 4. Independent PSNR (45 s)

**Type:**
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_psnr.ps1
```

**What it does:** runs the same checker the experiment used, `experiment\psnr_check.py`, on the original and the decoded YUV. It then compares the result with the PSNR the encoder printed.

**Expected:**
- `Independent : Y 37.2215 U 42.2963 V 41.1148`
- `Largest difference: 0.0000 dB`
- `[MATCH]`

**SAY:**
> "PSNR is 10 times log10 of the peak value squared, divided by the mean squared error. For 10-bit video the peak is
> 1020. It is computed for each frame and averaged. My own script gives exactly the encoder's numbers. In the
> experiment this was checked for all 94 runs, and the largest difference was 0.0000 dB."

## 5. Full reproduction of run A029 (1 min 15 s)

**Type** (three commands, about 25 s in total):
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_encode.ps1 -Mode Full
powershell -ExecutionPolicy Bypass -File .\demo_decode.ps1
powershell -ExecutionPolicy Bypass -File .\demo_psnr.ps1
```

**What it does:** repeats original run A029 with exactly the same settings and all 500 frames. It then compares the size, SHA-256, frame count and PSNR with the saved original values.

**Expected:**
- encode: `[MATCH] bitstream size` and `[MATCH] bitstream SHA-256 (bit-exact reproduction)`, SHA-256 `7f4bc413…aa5a`
- decode: `[MATCH] frame count` and `[MATCH] reconstructed YUV SHA-256 (bit-exact)`
- PSNR: `Y 34.8147 U 39.9791 V 38.2132`, `[MATCH] Y/U/V PSNR equal to the original run`

**Meaning:** SHA-256 is a fingerprint of a file. One different bit changes it completely. The same fingerprint therefore proves that today's result is identical to the original.

**SAY:**
> "This is a full original configuration. The SHA-256 fingerprint of today's bitstream is identical to the one
> recorded on 11 November. So the encoder is deterministic and the result can be reproduced exactly. Only the time
> differs."

## 6. Where the slide 5/6 numbers come from (1 min 15 s)

**Type:**
```powershell
..\.venv\Scripts\python.exe demo_results.py
```
(about 10 s; scroll up slowly)

**What it does:**
- **Part 3:** for the saved run A029, shows for each value the log line, the CSV column and a fresh recalculation from the saved files. The values are encoding time, decoding time, size, bitrate, PSNR, independent PSNR, frames and SHA-256.
- **SSIM / MS-SSIM:** recomputes them for the frames on slide 8.
- **Part 4:** reads the charts directly out of the PowerPoint file and checks every point against `results\config_summary.csv`.

**Expected:**
- sections 1–9, each with `[MATCH]`
- the SSIM table: `BasketballDrive 98 24 38.418 / 38.418 0.92289 / 0.92289 0.98828 / 0.98828 yes`
- `[MATCH] slide 5: all 64 chart points equal results/config_summary.csv (64/64)`
- `[MATCH] slide 6: all 16 chart points …`
- at the end: `RESULT: 31 checks, 31 match, 0 different`

**SAY:**
> "This script traces every value from the log, to the CSV, to the slide. For example, the medium point at QP 29
> for BasketballPass on slide 5 is 403.6 kbps and 35.25 dB. It comes from run A046 and its log file. SSIM compares
> local brightness, contrast and structure. MS-SSIM does this at five scales. Both are recomputed here from the
> decoded files and match the saved values."

## 7. BD-rate, slide 7 (1 min)

**Type:**
```powershell
..\.venv\Scripts\python.exe demo_bdrate.py
```

**What it does:**
1. Shows how the 4 QP points of medium and of faster give one BD-rate.
2. Recomputes all 12 BD-rates with the experiment's own `analysis\metrics.py`.
3. Compares them with `results\bdrate.csv` and with slide 7.

**Expected:**
- the table of 4 + 4 points
- `common range = 29.4942 to 38.4868 dB = 96% …`
- `BD-rate = (10^0.09741 - 1) x 100 % = +25.14 %`
- all 12 rows `yes`, and `RESULT: 21 checks, 21 match, 0 different`

**SAY:**
> "At the same QP, presets give different bitrate and different quality, so I cannot compare one number. BD-rate
> compares the whole curves at equal quality. log10(bitrate) is interpolated with a piecewise cubic curve over PSNR
> and integrated over the common quality range. For BasketballPass, faster needs 25 percent more bits than medium for
> the same quality. All 12 values are reproduced exactly."

## 8. YUView, frame 98 (1 min 15 s)

**Type:**
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_yuview.ps1
```
YUView opens with 5 files in its playlist: the original, then QP 24, 29, 34 and 39. If YUView asks about an **update, click Cancel**. If it asks to **Restore Playlist, click No**. The step-by-step YUView instructions are in [FINAL_LIVE_DEMO_GUIDE.md](FINAL_LIVE_DEMO_GUIDE.md), step 8.

**Click:**
1. In the playlist, click the first file (`…original…`). In YUView's properties panel, check that the size is 1920 × 1080 and the format is YUV 4:2:0, 10-bit. If the panel is hidden, open it from the **View** menu. If YUView guessed wrongly, correct it there. (Rehearse this once, see the checklist.)
2. Go to **frame 98** with the frame number box or slider at the bottom (the first frame is 0).
3. Zoom (mouse wheel) into the area the script printed: x 472, y 456, 480 × 272. This is the running player's arm and the chairs behind him.
4. Click each QP file in turn. Check that the frame number is still 98.

**SAY** (only what you actually see; the sentence below is the observation on slide 8):
> "QP 24 is very close to the original. As QP rises to 39, the picture gets smoother and loses fine detail around
> the moving arm and the objects in the background. This matches the falling PSNR, SSIM and MS-SSIM on slide 8.
> The images on slide 8 were rendered by a script; here we see the same frames in YUView."

*If YUView does not start:* the script opens the script-rendered image instead. Say: "This is a script rendering of the same frames, not YUView."

## 9. Windows vs Linux, slide 9 (30 s, skip if short of time)

**Type:**
```powershell
..\.venv\Scripts\python.exe demo_crossplatform.py
```

**Expected:** a table of 8 rows, all `yes yes`, then `[MATCH] all 8 reported comparisons are bit-exact` and `RESULT: 25 checks, 25 match`.

**SAY:**
> "The same source code was compiled with MSVC on Windows and with GCC on Linux. For the 8 configurations on slide 9
> (not all 64), the bitstreams and decoded videos have identical SHA-256. 'Bit-exact' means identical in every bit.
> Today's Linux reproduction of A029 is a ninth example, but it is not counted in the 8."

## 10. Close (15 s)

**SAY:**
> "To summarise: the commands, logs and CSV files are all here. Every value on the slides can be traced back and
> recalculated, and a full original configuration was reproduced bit-exactly today. The original runs were
> automated with an AI assistant; the checks I showed today I performed myself. Thank you. I am happy to run any
> other configuration you would like to see."

---

## Questions the professor may ask

| Question | Short honest answer |
|---|---|
| "Did you run the 94 experiments yourself?" | "No. They were run by automated scripts that Claude, an AI assistant, wrote and executed. I have now reproduced and checked selected steps myself, as you saw." |
| "Why is the encoder running in Linux?" | "Since 15 November, Windows Smart App Control blocks the unsigned Windows `vvencapp.exe`. I did not change security settings. The Linux build is the same version and was shown to be bit-exact (slide 9)." |
| "Why not use the Linux time?" | "WSL reads the input from the Windows drive through a slower file bridge. Timing results come only from the original Windows runs." |
| "Can you run another configuration?" | Yes, if it is short: e.g. `-Mode Full` takes about 15 s. Longer ones (slow preset, 1080p) take minutes to an hour. Offer to send the result afterwards. |
| "Why QP 24/29/34/39 and not the CTC QPs?" | "That is a limitation; it is stated in the report. The CTC QPs are 22/27/32/37." |
| "Why is the anchor medium and not VTM?" | "I compared the presets with each other. Comparing with VTM would be future work." |
