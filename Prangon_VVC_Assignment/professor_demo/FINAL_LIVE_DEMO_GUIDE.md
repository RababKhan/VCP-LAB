# Final live demo guide (follow this during the meeting)

**For:** Sadab Khan Prangon · meeting with Prof. Kiho Choi · **total time: 10 minutes** · this laptop only

**Before you start:**
- Read [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) once.
- Run the whole guide once as a rehearsal.

**About the expected values:**
- All values were checked on this laptop on 15 November 2026.
- Sizes, hashes and PSNR will be **exactly** the same, because the encoder is deterministic.
- Times change a little every run.

**Rules for yourself:**
- Say only what is true. Never claim you did the original 94 runs yourself.
- If something shows `[DIFFERENT]` or fails, say so calmly and use the "If it fails" line.

---

## Set-up (before the professor arrives, about 2 minutes)

1. Plug in the charger. Close other programs.
2. Open the **Start menu** → type `Windows PowerShell` → open it.
3. Type each line below and press **Enter**:
   ```powershell
   cd D:\Korea\Prangon_VVC_Assignment\professor_demo
   wsl -d Ubuntu-24.04 -u vvcuser -- echo ready
   ```
   You should see `ready`. This starts Linux (WSL) in advance, so the first encode is fast.
4. Open `D:\Korea\Prangon_VVC_Assignment\logs\phase2\A029_BasketballPass_QP29_faster.log` in **Notepad**.
5. Open `presentation\VVC_Assignment_Sadab_Khan_Prangon_FINAL.pptx` in PowerPoint.

**Tip:** every command in this guide is a single line. Copy it from this file, paste it into PowerShell (right-click pastes), and press **Enter**.

---

## Time plan

| Clock | Step | Supports slide |
|---|---|---|
| 0:00 | 0. Introduction: who did what | 1 |
| 0:40 | 1. One original log | 3, 4 |
| 1:30 | 2. Short encode | 2, 4 |
| 2:40 | 3. Decode and frame count | 4, 6 |
| 3:20 | 4. Independent PSNR | 5 |
| 4:00 | 5. Full reproduction of original run A029 | 5, 6, 9 |
| 5:10 | 6. Where the slide numbers come from | 5, 6, 8 |
| 6:20 | 7. BD-rate | 7 |
| 7:20 | 8. YUView, BasketballDrive frame 98 | 8 |
| 9:10 | 9. Windows vs Linux (skip if late) | 9 |
| 9:40 | 10. Close | 10 |

**If you are running late:** skip step 9, and in step 6 show only the end of the output.

---

## Step 0: Introduction (40 s), slide 1

**Command:** none.

**On screen:** slide 1.

**Say:**
> "Professor, I would like to show how the experiment was run and where the numbers in my slides come from.
> To be transparent: the original 94 encoder runs were executed by automated scripts that Claude, an AI assistant,
> wrote and ran on this laptop. Today I am personally reproducing and checking selected steps, with the same
> programs, files and logs. I will not repeat all 94 runs; the longest one took about 55 minutes."

---

## Step 1: One original log (50 s), slides 3 and 4

**Command:** none. Switch to **Notepad** with `A029_BasketballPass_QP29_faster.log`, then press **Ctrl+F**, type `Total Time` and press **Enter**.

**On screen:**
- line 2: `Command: …vvencapp.exe -i …BasketballPass_416_240_50_10_420.yuv -s 416x240 -c yuv420_10 --fps 50 -f 500 -q 29 --preset faster --qpa 0 -t 8 -o …A029_BasketballPass_QP29_faster.266`
- the found line: `vvencapp [info]: Total Time: 8.422 sec. Fps(avg): 59.368 encoded Frames 500`

**Supports:** slide 3 (the VVenC build used) and slide 4 (the settings: 10-bit 4:2:0, QP, preset, `--qpa 0`, 8 threads).

**Say:**
> "Every run has a log like this. This is run A029: BasketballPass, QP 29, preset faster, 500 frames. Here is the
> exact command: 10-bit 4:2:0 input, perceptual QP adaptation off, 8 threads. The encoder reported 8.4 seconds.
> The scripts copied these values into a CSV file, and the slides were built only from those CSV files."

**If it fails:** if the file does not open, open File Explorer at `D:\Korea\Prangon_VVC_Assignment\logs\phase2\` and double-click the file.

---

## Step 2: Short encode (70 s), slides 2 and 4

**Command:**
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_encode.ps1
```

**On screen** (takes about 5–15 s):
- magenta: `SHORT DEMO: 32 frames only. This is NOT one of the original 500-frame measurements.`
- **yellow** (this is normal at the moment):
  - `NOTE: Windows refused to start vvencapp.exe:`
  - `Program 'vvencapp.exe' failed to run: An Application Control policy has blocked this file`
  - `Using the Linux build of the same version in WSL instead (bit-exact with Windows, slide 9).`
- `vvencapp version 1.14.0   [engine: Linux (WSL2)]`
- `Bitstream size      : 20869 bytes`
- `Bitrate             : 20869 bytes x 8 / (32 frames / 50 fps = 0.64 s) / 1000 = 260.863 kbps`
- `Encoder's own value : 260.8625 kbps`
- `Encoding time       : about 4 s (encoder 'Total Time')`
- `Encoder PSNR (dB)   : Y 37.2215   U 42.2963   V 41.1148`
- yellow timing note: the WSL time is not comparable with the Windows timings

**Supports:** slide 2 (workflow: encode step) and slide 4 (same command and settings).

**Say:**
> "This is a short run of only 32 frames, so it is a demonstration, not one of my measurements.
> Bitrate is the file size in bits divided by the video duration: 20,869 bytes times 8, divided by 0.64 seconds, is
> about 261 kilobits per second, the same as the encoder reports.
> Since 15 November, Windows Smart App Control blocks this unsigned encoder program. I did not change any security
> setting. The script uses the Linux build of the same VVenC version instead, which is bit-exact with the Windows
> build, as slide 9 shows. Because it runs inside WSL, its time is not comparable with my Windows timings."

**If it fails:**
- **No yellow note, `engine: Windows`:** Windows allowed the encoder again. That is fine; continue.
- **Red `ENCODE FAILED`:** run `powershell -ExecutionPolicy Bypass -File .\demo_encode.ps1 -Engine Linux`.
- **The Linux build also fails** (for example, WSL does not start): say, *"The live encoder is blocked on this laptop today, so I will show the saved original run instead"*, and go to **step 6**. It shows the saved original A029 files, log and CSV.

---

## Step 3: Decode and frame count (40 s), slides 4 and 6

**Command:**
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_decode.ps1
```

**On screen** (about 2 s):
- `vvdecapp.exe version 3.2.1   [engine: Windows]`
- `Decoder says: 32 frames decoded @ … fps (0.0… sec)`
- `9584640 bytes / (416 x 240 x 1.5 samples x 2 bytes = 299520 bytes per frame) = 32 frames`
- green: `[MATCH] decoded frame count = 32`
- three decode lines, then `Median decode time: about 0.02 s`

**Supports:** slide 4 (decode and frame-count check) and slide 6 (the decode-time tile uses the same "3 decodes, no output file, median" method).

**Say:**
> "The decoder rebuilds the video. A 416 by 240 frame in 10-bit 4:2:0 has 1.5 samples per pixel and 2 bytes per
> sample, so the file size gives exactly 32 frames. Decoding time is measured three times without writing a file,
> so the disk speed does not count, and the median is kept."

**If it fails:** run `powershell -ExecutionPolicy Bypass -File .\demo_decode.ps1 -Engine Linux` (Linux decoder).

---

## Step 4: Independent PSNR (40 s), slide 5

**Command:**
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_psnr.ps1
```

**On screen** (about 2 s):
- `Independent : Y 37.2215   U 42.2963   V 41.1148   (32 frames checked)`
- `Encoder     : Y 37.2215   U 42.2963   V 41.1148`
- `Largest difference: 0.0000 dB …`
- green: `[MATCH] independent PSNR = encoder PSNR`

**Supports:** slide 5, tile "Independent PSNR check Δ 0.0000 dB, all 94 runs".

**Say:**
> "PSNR is 10 times log10 of the peak value squared divided by the mean squared error. The peak is 1020 for 10-bit
> video. It is computed for each frame and averaged. My own script, `psnr_check.py`, gives exactly the encoder's
> values. The experiment did this check for all 94 runs, and the largest difference was 0.0000 dB."

**If it fails:** if it says "No reconstruction yet", run step 3 again first.

---

## Step 5: Full reproduction of original run A029 (70 s), slides 5, 6 and 9

**Commands** (one after the other, about 25 s in total):
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_encode.ps1 -Mode Full
```
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_decode.ps1
```
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_psnr.ps1
```

**On screen:**
- **encode:**
  - magenta `FULL REPRODUCTION of original run A029 (same settings, all 500 frames).`
  - `Bitstream size : 578073 bytes`
  - `Original: 578073 bytes, 462.458 kbps, SHA-256 7f4bc4133fa9…aa5a, encode 8.422 s`
  - green `[MATCH] bitstream size` and `[MATCH] bitstream SHA-256 (bit-exact reproduction)`
- **decode:** green `[MATCH] decoded frame count = 500`, `[MATCH] frame count`, `[MATCH] reconstructed YUV SHA-256 (bit-exact)`
- **PSNR:** `Independent : Y 34.8147   U 39.9791   V 38.2132`, then green `[MATCH] Y/U/V PSNR equal to the original run`

**Supports:**
- slide 5: the BasketballPass "faster" point at QP 29, 462.5 kbps / 34.81 dB
- slide 6: A029 is one of the 4 runs behind the BasketballPass "faster" timing point
- slide 9: the Linux build reproduces the Windows result bit for bit

**Say:**
> "Now a complete original configuration, run A029, with all 500 frames. SHA-256 is a fingerprint of a file: if
> one single bit changes, the fingerprint is completely different. Today's bitstream and decoded video have exactly
> the same fingerprints as the files from 11 November, and the PSNR is identical. So the result is fully
> reproducible. Only the time differs, because this ran in WSL."

**If it fails:**
- **`[DIFFERENT]` appears:** read the line aloud and say you will investigate it. Do not hide it.
- **The encode cannot run at all:** step 6 still proves the saved A029 files are unchanged (section 8 of its output).

---

## Step 6: Where the slide numbers come from (70 s), slides 5, 6 and 8

**Command:**
```powershell
..\.venv\Scripts\python.exe demo_results.py
```

**On screen** (about 10 s, long output; scroll up slowly with the mouse wheel):
- **sections 1–8** (original run A029), each ending with green `[MATCH]`:
  - encoding time, `Total Time: 8.422`
  - decoding time, `median(0.185, 0.183, 0.194) = 0.185 s`
  - bitstream size, `578073`
  - bitrate, `462.458 kbps`
  - Y/U/V PSNR
  - independent PSNR
  - frame count, `500`
  - SHA-256
- **section 9:** a table where SSIM and MS-SSIM are recomputed, for example `BasketballDrive  98  24  38.418 / 38.418  0.92289 / 0.92289  0.98828 / 0.98828  yes`
- `[MATCH] slide 8 caption QP 24 shows PSNR 38.42 dB, SSIM 0.923, MS-SSIM 0.988` (and the same for QP 29, 34 and 39)
- `[MATCH] slide 5: all 64 chart points equal results/config_summary.csv (64/64)`
- `[MATCH] slide 6: all 16 chart points equal config_summary.csv enc_median_s (16/16)`
- last lines: `RESULT: 31 checks, 31 match, 0 different`

**Supports:** slide 5 (all RD points and the three tiles), slide 6 (time chart and tiles) and slide 8 (PSNR, SSIM and MS-SSIM under the crops, and the MS-SSIM table).

**Say:**
> "This script reads the charts directly out of my PowerPoint file and checks every value against the CSV files and
> the logs. All 64 points on slide 5 and all 16 on slide 6 match. For example, BasketballPass medium at QP 29 is
> 403.6 kilobits per second and 35.25 dB, from run A046.
> SSIM compares local brightness, contrast and structure between the original and the decoded picture; 1 means
> identical. MS-SSIM does the same at five image scales. Both are recomputed here from the decoded files and match
> the numbers on slide 8."

**If it fails:**
- **A Python error appears:** check that you are in the `professor_demo` folder; run `cd D:\Korea\Prangon_VVC_Assignment\professor_demo`.
- **Short of time:** run `..\.venv\Scripts\python.exe demo_results.py --skip-1080p` (faster, shows fewer SSIM rows).

---

## Step 7: BD-rate (60 s), slide 7

**Command:**
```powershell
..\.venv\Scripts\python.exe demo_bdrate.py
```

**On screen** (about 2 s):
- a table of 4 QP points for medium and faster (for example `29  403.611  35.2511  462.458  34.8147`)
- `common range = 29.4942 to 38.4868 dB = 96% of the smaller range  -> valid`
- `Step d - BD-rate = (10^0.09741 - 1) x 100 % = +25.14 %`
- green `[MATCH] step-by-step result +25.14 % = metrics.bd_rate() +25.14 % = results/bdrate.csv +25.14 %`
- a table of 12 rows, all `yes`
- `[MATCH] slide 7 table: all 12 BD-rate cells …` and `[MATCH] slide 7 chart: all 12 points …`
- `RESULT: 21 checks, 21 match, 0 different`

**Supports:** slide 7 (BD-rate table, chart and note).

**Say:**
> "At the same QP, presets give different bitrate and different quality, so one number is not a fair comparison.
> BD-rate compares the whole curve at equal quality. I take the four QP points of medium and of the test preset,
> draw log-bitrate as a smooth curve over PSNR, and average the gap over the common quality range. For BasketballPass,
> faster needs 25 percent more bits than medium for the same quality. All 12 values on slide 7 are reproduced
> exactly from the saved data."

**If it fails:** same as step 6 (check the folder).

---

## Step 8: YUView, BasketballDrive frame 98 (about 1 min 50 s), slide 8

These steps were checked on this laptop with YUView 2.14 (control names and dialogs). Practise the clicking once before the meeting.

### 8.1 Start YUView

**Command:**
```powershell
powershell -ExecutionPolicy Bypass -File .\demo_yuview.ps1
```

**On screen (PowerShell):**
- the 5 file names
- `Frame      : 98   (counted from 0 - the first frame is frame 0)`
- `Crop area  : x = 472, y = 456, width 480, height 272 pixels`
- `YUView started with the 5 files in its playlist.`

### 8.2 Answer YUView's dialogs (if they appear)

| Dialog text | Click |
|---|---|
| "An update for YUView is available. Do you want to download and install the update now?" | **Cancel** (never **Update**) |
| "Restore Playlist: It looks like YUView crashed the last time…" | **No** |

### 8.3 Check the file format

The YUView window has:
- **Playlist** at the top left, with 5 lines that all end in `…x1080_50fps_10bit_420.yuv`
- the picture in the middle
- **Raw File Properties** on the right
- the **frame number box** at the bottom right, next to the long slider

The playlist order is: 1 = **original**, 2 = **QP 24**, 3 = **QP 29**, 4 = **QP 34**, 5 = **QP 39**. The names are cut off in the list, so after clicking a line, read the full file name in the **window title** at the top.

1. Click playlist line 1. The window title must end with `BasketballDrive_original_1920x1080_50fps_10bit_420.yuv`.
2. In **Raw File Properties** (right) check:
   - Framerate `50.00`
   - Width `1920`, Height `1080`
   - Frame Size `1080i/p (1920,1080)`
   - YUV Format `YUV 4:2:0 10-bit LE`
3. **Only if Width and Height show 0**, or the picture area shows "the YUV data can not be converted to RGB": type `1920` in Width and `1080` in Height. In **YUV Format** choose `YUV 4:2:0 10-bit LE`, and set Framerate to `50`. Do this for each playlist line that shows 0.
4. Do **not** change Luma/Chroma Scale or Offset.

### 8.4 Go to frame 98

1. Click into the **frame number box** at the bottom right (it shows `0` at first).
2. Select the number, type `98` and press **Enter**.
3. The slider handle moves to about one fifth of the way.

### 8.5 Zoom to the same area

The area to show is the player in the **green jersey** on the left half of the picture: his arm stretched forward, and the **chairs with red, green and gold objects** behind him. That is pixels x 472–952, y 456–728.
- Turn the **mouse wheel** over the picture to zoom.
- **Drag** the picture with the mouse to move it.
- If zooming or moving behaves differently, use the **View → Zoom** menu. Try this when you practise.

### 8.6 Compare QP 24, 29, 34 and 39

1. Click playlist line **2** (title ends `…QP24_medium…`), then line **3** (QP29), line **4** (QP34) and line **5** (QP39).
2. After each click, check that the frame box still shows **98**. If it does not, type 98 again. If the zoom changes, zoom to the same area again.
3. Go back to line 1 (original) and then to line 5 (QP 39) to show the biggest difference.

What to look at:
- the **edge of the moving arm and hand**
- the **stripes on the green jersey**
- the **small objects on the chairs** (gold and red items, towels)

**Optional, only if practised:** the **View** menu also has **Split View**, to show two items side by side.

**Supports:** slide 8 (the same frame, the same crop area, and the QP trend in PSNR, SSIM and MS-SSIM).

**Say** (describe only what you really see on the screen; this matches the observation on slide 8):
> "This is frame 98 of BasketballDrive, chosen by a fixed rule before looking: the frame whose quality at QP 39 is
> the median of all 500 frames. At QP 24 the picture is very close to the original. As QP increases to 39, the
> picture becomes smoother, and fine detail is lost around the moving arm and the objects in the background. This
> agrees with slide 8: from QP 24 to 39, this frame's PSNR falls from 38.4 to 33.0 dB, SSIM from 0.923 to 0.864, and
> MS-SSIM from 0.988 to 0.954. The pictures on slide 8 were rendered by a script; here I am showing the same frames
> in YUView."

### 8.7 Close YUView

Click the **X** at the top right. YUView asks "You have not saved the current playlist, are you sure?" → click **Close** (not Save).

**If it fails:**
- **YUView does not start:** the script automatically opens `visual\v2\BasketballDrive_f98_typical_strip.png`. Say: *"This is a script rendering of the same five frames, not YUView."*
- **The picture stays grey with an error:** do 8.3 step 3 (type the size and format).
- **YUView freezes:** close it with the X. If it asks "Restore Playlist" next time, click **No**.

---

## Step 9: Windows vs Linux (30 s), slide 9 (skip if you are late)

**Command:**
```powershell
..\.venv\Scripts\python.exe demo_crossplatform.py
```

**On screen** (about 4 s):
- 8 numbered checks, each showing a Windows and a Linux SHA-256 that are the same
- a table of 8 rows, all `yes  yes`
- `[MATCH] all 8 reported comparisons are bit-exact`
- `Only these 8 configurations were compared across platforms - not all 64.`
- a section "Today's extra example (NOT one of the 8 reported checks)"
- `RESULT: 25 checks, 25 match, 0 different`

**Supports:** slide 9.

**Say:**
> "The same source code was compiled with MSVC on Windows and with GCC on Linux. For the eight configurations on
> slide 9 (not all 64), the bitstreams and decoded videos have identical SHA-256 fingerprints. Bit-exact means
> identical in every bit. Today's Linux reproduction of A029 is an extra example, not counted in the eight."

**If it fails:** say the result is on slide 9 and in `results\crossplatform_v2.json`. Then move on.

---

## Step 10: Close (20 s), slide 10

**Command:** none. Show slide 10.

**Say:**
> "To summarise: the commands, logs and CSV files are all here, every number on the slides can be traced and
> recalculated, and a full original configuration was reproduced bit-exactly today. The original runs were automated
> with an AI assistant; the checks you saw today I performed myself. Thank you. I am happy to run any other short
> configuration you would like to see."

---

## Quick answers if the professor asks

| Question | Answer |
|---|---|
| Did you run the 94 experiments yourself? | "No. Automated scripts written and executed by Claude, an AI assistant, ran them. Today I reproduced and checked selected steps myself." |
| Why does the encoder run in Linux? | "Since 15 November, Windows Smart App Control blocks the unsigned Windows encoder. I did not change security settings. The Linux build is the same version and was shown to be bit-exact." |
| Why not use the Linux times? | "WSL reads the input from the Windows drive through a slower bridge. All timing results come from the original Windows runs." |
| Can you run another configuration? | "Yes, if it is short." Short ones take seconds; slow-preset and 1080p runs take minutes up to about an hour. Offer to send the result afterwards. |
| Why QP 24/29/34/39, not the standard test QPs? | "That is a limitation, stated in my report. The common test conditions use 22/27/32/37." |
| Why is medium the anchor, not VTM? | "I compared the presets of VVenC with each other. A comparison with VTM is future work." |

## Never do during the demo

- Never click **Update** in YUView.
- Never change Windows security settings.
- Never run `analysis\analyze_full.py` or `experiment\run_phase2.py`. They would rewrite the saved results.
- Never delete anything in `results\`, `logs\`, `out\` or `presentation\`.
