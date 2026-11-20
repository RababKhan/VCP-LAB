# VCP-LAB: VVC encoder experiments

This repository holds two separate VVC (H.266) encoding projects. Both use VVenC 1.14.0 and VVdeC 3.2.1.

| Folder | Project |
|---|---|
| [`VVC_Assignment/`](VVC_Assignment/) | Rabab Khan Rongon's VVC assignment |
| [`Prangon_VVC_Assignment/`](Prangon_VVC_Assignment/) | Sadab Khan Prangon's VVC assignment: 4 sequences × 4 QPs × 4 presets, BD-rate, timing reliability, Windows/Linux check |

Each folder has its own documentation. For Prangon_VVC_Assignment, see:
- `Prangon_VVC_Assignment/results/EXPERIMENT_REPORT_v2.md`
- `Prangon_VVC_Assignment/MISSING_EVIDENCE_CHECKLIST.md`
- `Prangon_VVC_Assignment/professor_demo/README.md`

These documents record that the experiment runs were automated with an AI assistant (Claude). They also record which steps were checked by hand.

## What is not in this repository

| Left out | Why | How to get it back |
|---|---|---|
| `*.yuv` (raw and decoded video, tens of GB) | Far too large for git | Decode the saved `.266` bitstreams with VVdeC. Their SHA-256 values are listed in the results CSV files |
| `*/dataset/` (JVET test sequences BasketballPass, BlowingBubbles, BQMall, BasketballDrive) | Too large, and not ours to redistribute | Obtain them from the JVET test-sequence distribution |
| `.venv/`, `__pycache__/` | Machine-specific Python environments | Python 3.12 with numpy, scipy, matplotlib, scikit-image, python-pptx |
| ffmpeg / ffplay / ffprobe executables and the ffmpeg zip | Larger than GitHub's 100 MB file limit | Download ffmpeg separately |
| Build output of VVenC/VVdeC (`bin/`, `build/`, `lib/`) | Generated files inside the codec source folders | Build the codecs from the submodules, as described below |

## Codec sources (git submodules)

`Prangon_VVC_Assignment/vvenc`, `Prangon_VVC_Assignment/vvdec`, `VVC_Assignment/src/vvenc` and `VVC_Assignment/src/vvdec` are submodules. They point to the exact Fraunhofer HHI commits that were used:

- VVenC `9428ea8636ae7f443ecde89999d16b2dfc421524` (v1.14.0): https://github.com/fraunhoferhhi/vvenc
- VVdeC `cb1a3efd88b2ebd1141f1a9ca87c774f05de9249` (v3.2.1): https://github.com/fraunhoferhhi/vvdec

```
git clone --recurse-submodules https://github.com/RababKhan/VCP-LAB.git
```
