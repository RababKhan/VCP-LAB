# Demo checklist

## The day before

- [ ] **Read** [DEMO_SCRIPT.md](DEMO_SCRIPT.md) and [SLIDE_DATA_MAPPING.md](SLIDE_DATA_MAPPING.md) once. Be able to explain:
  - the bitrate formula
  - PSNR (peak 1020)
  - what SHA-256 shows
  - BD-rate in your own words
- [ ] **Full rehearsal:** run steps 1–9 once, with a timer. Target: under 10 minutes.
- [ ] **YUView rehearsal (by hand):**
  - Run `demo_yuview.ps1`.
  - Find the properties panel and check that it shows 1920 × 1080, 4:2:0, 10-bit.
  - Find the frame-number box. Check that the first frame is shown as **0**, then go to frame 98.
  - Zoom into the crop area.
  - Write down where these controls are.
  - The scripts can open YUView but cannot click inside it. This part was **not** tested automatically.
- [ ] **Your own observation:** look at frame 98 in YUView yourself. Check that the sentence on slide 8 really matches what you see. If it does not, change the slide text to what you saw.
- [ ] **Disk space:** check that D: has at least 2 GB free (one full demo run writes about 150 MB).
- [ ] **Old output:** delete old test folders in `professor_demo\output\` if you want a clean list. They are demo output only; never delete anything outside `professor_demo\output\`.

## 15 minutes before

- [ ] Laptop on **AC power**, notifications off, other programs closed.
- [ ] **Windows PowerShell** open and in the right folder:
  ```powershell
  cd D:\Korea\Prangon_VVC_Assignment\professor_demo
  ```
- [ ] **WSL warm-up:** the first start can take 10–20 s. Run this once so that the demo encode starts quickly:
  ```powershell
  wsl -d Ubuntu-24.04 -u vvcuser -- echo ready
  ```
- [ ] **Notepad:** `logs\phase2\A029_BasketballPass_QP29_faster.log` open, for step 1.
- [ ] **Deck:** `presentation\VVC_Assignment_Sadab_Khan_Prangon_FINAL.pptx` open on slide 1, in a licensed PowerPoint.
- [ ] **Font size:** the PowerShell font is large enough to read from a distance (right-click the title bar → Properties → Font).

## During the demo: what must appear

| Step | Must see | If not |
|---|---|---|
| 2 Short encode | `Bitstream size : 20869 bytes`. The yellow note about Application Control is normal | Red `ENCODE FAILED`: open `output\<newest>\encode.log`; use `-Engine Linux` |
| 3 Decode | `[MATCH] decoded frame count = 32` | Run `demo_decode.ps1 -Engine Linux` |
| 4 PSNR | `Largest difference: 0.0000 dB`, `[MATCH]` | – |
| 5 Full A029 | three `[MATCH]` lines for bitstream, recon and PSNR | Explain honestly. Then show the saved original with `demo_results.py` |
| 6 Results | `RESULT: 31 checks, 31 match` | Read the `[DIFFERENT]` line aloud; do not hide it |
| 7 BD-rate | `+25.14 %`, `RESULT: 21 checks, 21 match` | – |
| 8 YUView | 5 files in the playlist, frame 98 | The fallback image opens; say "script rendering, not YUView" |
| 9 Cross-platform | `all 8 reported comparisons are bit-exact` | – |

## What you must say (honesty)

- [ ] The original 94 runs were **automated**: scripts written and run by **Claude (an AI assistant)**.
- [ ] Today **you** are reproducing and checking **selected** steps.
- [ ] The short 32-frame encode is a demonstration, **not** one of the measurements.
- [ ] Windows currently blocks the Windows encoder. You used the Linux build of the same version, and you did **not** change security settings.
- [ ] Linux/WSL times are **not** compared with the Windows timings.
- [ ] Windows/Linux was compared for **8** configurations, **not** all 64.
- [ ] The slide 8 images are **script renderings**. The YUView view is shown live.

## After the demo

- [ ] Close YUView.
- [ ] Keep the newest `professor_demo\output\` folder and reports as a record of what was shown.
- [ ] Do **not** run `analysis\analyze_full.py` or the experiment runners. They would overwrite the saved results.
