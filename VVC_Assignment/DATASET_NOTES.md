# Dataset Notes

Source: professor-provided Google Drive folder. Naming convention (from the folder's `@name_format` document):
`name_width_height_fps_bitdepth_yuvformat.yuv`.

## Files present in `dataset/` (2026-10-27)
| File | Size (bytes) | Inspected |
|---|---|---|
| BasketballPass_416_240_50_10_420.yuv | 150,059,520 | yes (Phase 3) |
| BlowingBubbles_416_240_50_10_420.yuv | 150,059,520 | not yet |
| BQMall_832_480_60_10_420.yuv | 720,046,080 | not yet |
| BasketballDrive_1920_1080_50_10_420.yuv | 3,116,620,800 | not yet |

## BasketballPass_416_240_50_10_420.yuv — verified properties
Evidence: `results/phase3/BasketballPass_inspection.json`, rendered frames in `results/phase3/frames/`.

| Property | Value | How it was verified |
|---|---|---|
| SHA256 | de0dcc61e9ba4d22312effad81517fb3a24ecd883738ec3c66f490f7593ed698 | computed |
| Sample format | 10-bit in 16-bit little-endian words | every high byte is 0..3 (impossible for 8-bit data) |
| Chroma / plane order | 4:2:0 planar, Y then U then V | rendered frames 0/15/250/499 show correct geometry and colours |
| Resolution | 416x240 | correct image geometry; vertical vs horizontal neighbour differences comparable (24.2 vs 20.4) |
| Value range | Y 64..940, U 192..652, V 412..916 | 10-bit limited (video) range |
| Effective precision | 8-bit content up-shifted by 2 bits | 100% of samples have their two LSBs equal to zero |
| Frame count | 501 frames, 0 trailing bytes | 150,059,520 / 299,520 = 501 exactly |
| Content frames | 500 (indices 0-499) | frame 500 is an NTT DOCOMO copyright-notice text frame (visually inspected) |
| Frame rate | 50 fps | not stored in raw YUV; from filename, confirmed by JVET VTM per-sequence config `cfg/per-sequence/BasketballPass.cfg` (416x240, 50 fps, 500 frames, 8-bit 4:2:0 source) |

Implication for experiments: encode at most the first 500 frames (`-f 500`) so the copyright frame is never coded.
