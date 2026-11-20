<!-- Slide number: 1 -->
VVC Encoding and Decoding: Experimental Evaluation
![BQMall test sequence, original frame 100](BQMall frame)
Building VVenC 1.14.0 and VVdeC 3.2.1 on Windows and Linux (WSL2), and measuring the effect of QP and preset on bitrate, quality and runtime
BQMall (832×480, 60 fps), original frame 100
Rabab Khan Rongon
M.Sc. in Computer Science and Engineering (Major: Artificial Intelligence)
Military Institute of Science and Technology (MIST), Bangladesh
Practical assignment for Prof. Kiho, Kyung Hee University  ·  November 2026

### Notes:
Good morning, Professor Kiho. Thank you for this opportunity. My name is Rabab Khan Rongon. I am doing my M.Sc. in Computer Science and Engineering, with a major in Artificial Intelligence, at MIST in Bangladesh. Today I will present my practical assignment on VVC. In short: I built the VVenC encoder and the VVdeC decoder on Windows and on Linux. Then I encoded four test videos with different QP values and presets, decoded them, and measured bitrate, quality and time. All numbers in this talk come from my own result files. When something is only my interpretation, I will say so.

<!-- Slide number: 2 -->
# Assignment Objectives and Workflow
Build the tools, run controlled experiments, and explain the compression–quality–runtime trade-offs
1
2
3
4
5
Build
Encode
Decode
Measure
Compare
VVenC + VVdeC, Windows (MSVC) and Linux (GCC, WSL2)
4 sequences × 8 configurations, QP sweep and preset sweep
VVdeC timing pass and reconstruction pass
Time, bitstream size, PSNR; 65 verified runs
Visual comparison and Windows ↔ Linux bitstream check
Working principles
Every command executed and verified; logs kept for successful and failed attempts
No upstream source changes; exact release commits on both platforms
Measured results, interpretations and hypotheses are labelled separately
Outputs: scripts, run manifests, per-run JSON + logs, CSV tables, figures, phase reports
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
2 / 15

### Notes:
Here is the plan of the work. There were five steps. First, I built the tools. Second, I encoded four sequences with eight settings each. Third, I decoded every bitstream two times: one time only to measure the speed, and one time to write the video for the quality measurement. Fourth, I measured time, file size and PSNR. In total I made 65 runs, and all of them passed my checks. Fifth, I compared the videos visually, and I compared Windows with Linux. I followed some simple rules: I verified every command, I kept all logs, and I did not change the source code.

<!-- Slide number: 3 -->
# VVC, VVenC, VVdeC and YUView
An international video coding standard, plus three open-source tools to encode, decode and inspect it
VVC / H.266
VVenC 1.14.0
VVdeC 3.2.1
YUView 2.14
ITU-T H.266 | ISO/IEC 23090-3 (2020) [1]
Successor of HEVC (H.265)
Block-based hybrid coding; flexible partitioning, new prediction and in-loop filter tools
Target: ≈50% bitrate reduction vs HEVC at similar perceptual quality [2]
Fraunhofer HHI open-source encoder [3]
Presets: faster · fast · medium · slow · slower
Multithreading and SIMD (AVX2 used here)
Used: vvencapp, constant QP
Fraunhofer HHI open-source decoder
Multithreaded, SIMD-optimized
Used: vvdecapp for timing and reconstruction
Open-source YUV and bitstream viewer (IENT, RWTH Aachen) [8]
Side-by-side, comparison and difference views
Used to prepare the visual-comparison workflow
In this study:  original YUV → vvencapp (encode) → .266 bitstream → vvdecapp (decode) → reconstructed YUV → own PSNR script and YUView comparison
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
3 / 15

### Notes:
Now a short introduction to the tools. VVC, also called H.266, is the newest video coding standard from ITU-T and ISO/IEC. It was finished in 2020, and it is the successor of HEVC. According to the overview paper by Bross and colleagues, it targets about fifty percent lower bitrate than HEVC at similar perceptual quality. VVenC is an open-source encoder from Fraunhofer HHI. Its presets, from faster to slower, trade speed for compression. VVdeC is the matching decoder, and YUView is an open-source viewer for raw video. At the bottom you can see how I connected the tools in this study.

<!-- Slide number: 4 -->
# Development Environments: Windows and Linux
Same release commits, Release builds with upstream defaults, 0 warnings and 0 errors on both platforms

|  | Windows | Linux |
| --- | --- | --- |
| Operating system | Windows 11 Home 10.0.26200 | Ubuntu 24.04.5 LTS on WSL2 (kernel 6.18.54.1) |
| Compiler / build | MSVC 19.44 (VS Build Tools 2022 17.14), CMake 4.4.4 | GCC 13.3.0, CMake 3.28.3, GNU Make 4.3 |
| Configuration | Release, upstream defaults, AVX2 | Release, upstream defaults, AVX2 |
| Build result | 0 warnings, 0 errors | 0 warnings, 0 errors |
| Upstream tests | vvenc_unit_test, vvdec_unit_test: passed | Both unit tests passed; VVenC ctest 39 / 39 passed |
| Source commits | VVenC v1.14.0 (9428ea8), VVdeC v3.2.1 (cb1a3ef) | identical commits, no modification [6] |

Hardware: laptop, Intel Core i7-1260P (12 cores / 16 threads, hybrid P/E cores), 15.7 GB RAM. Linux = WSL2 virtual machine (16 vCPUs, 7.6 GiB RAM), not native Linux.
VVdeC conformance-bitstream tests (251) were not run on either platform; they need a separate JVET download.
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
4 / 15

### Notes:
This slide shows my two build environments. On Windows I used the Microsoft C++ compiler from Visual Studio 2022. On Linux I used Ubuntu 24.04 with GCC 13. Both builds use exactly the same release commits, with no change to the source code, and the default Release settings. Both builds finished with zero warnings and zero errors, and all available tests passed. On Linux I could also run the VVenC test suite: thirty-nine out of thirty-nine passed. One important point: my Linux system is WSL2. This is a small virtual machine on the same laptop. It is not a native Linux installation.

<!-- Slide number: 5 -->
# Dataset and Video Characteristics
Four JVET test sequences, 10-bit 4:2:0 files whose content has 8-bit precision
![BasketballPass, original frame 100](BasketballPass thumbnail)
![BlowingBubbles, original frame 100](BlowingBubbles thumbnail)
![BQMall, original frame 100](BQMall thumbnail)
![BasketballDrive, original frame 100](BasketballDrive thumbnail)
BasketballDrive
1920×1080 · 50 fps · 500 frames
BasketballPass
416×240 · 50 fps · 500 frames
BlowingBubbles
416×240 · 50 fps · 500 frames
BQMall
832×480 · 60 fps · 600 frames
Format: planar YUV 4:2:0, 10-bit little-endian (16-bit words); verified by SHA256 and size checks
All samples have the two least-significant bits = 0 → 8-bit precision content in a 10-bit container
The last frame of each file is a copyright card → excluded; 500 / 500 / 600 / 500 content frames encoded
PSNR: peak 1020 (= 255 << 2, HM / VTM / VVenC convention), mean of per-frame PSNR; YUV-PSNR = 4:1:1 MSE weighting
Thumbnails: original frame 100, rendered from the YUV data (BT.709 assumed for display); BasketballDrive downscaled for display only
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
5 / 15

### Notes:
These are the four test sequences: two small ones at 416 by 240, BQMall at 832 by 480, and BasketballDrive in full HD. Before encoding, I checked every file. The files are 10-bit, but I found that the two lowest bits are always zero. So the real content has only 8-bit precision. I also found that the last frame of each file is a copyright picture, so I did not encode it. For PSNR, I used the peak value 1020. This is the same convention as in the reference software and in VVenC, so my values can be compared directly with the encoder output.

<!-- Slide number: 6 -->
# Experimental Design and Controlled Parameters
One factor at a time: a QP sweep at preset medium and a preset sweep at QP 32

| Sweep | Values | Fixed |
| --- | --- | --- |
| QP sweep | QP 22 · 27 · 32 · 37 | preset medium |
| Preset sweep | faster · fast · medium · slow · slower | QP 32 |
| Unique configurations | 8 per sequence × 4 = 32 | QP 32/medium shared |
| Runs | 1 warm-up + 32 + 32 repeats = 65 | random order |

Controlled parameters
Constant QP (no rate control)
QPA off (--qpa 0)
8 encoder and 8 decoder threads
CRA refresh every 1 s (intra period 48 / 64), GOP 32
All content frames (500 / 600)
AC power, Windows mode "Best performance", 30 s system monitor
Same tools, inputs and checksums for every run
Timing repeats: 2 extra runs for each configuration of the two 240p sequences (3 samples, median reported)
Verification: 65 / 65 runs passed all checks; 32/32 repeats byte-identical
Run order randomized (seed 2026) so that slow drifts do not align with one factor
Battery incident: 64 min on battery → 4 single-sample configurations re-measured on AC (originals kept, flagged)
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
6 / 15

### Notes:
My design changes one factor at a time. For the QP sweep, I used QP 22, 27, 32 and 37 with preset medium. For the preset sweep, I used all five presets with QP 32. This gives eight settings per sequence, and thirty-two in total. To measure timing noise, I repeated every setting of the two small sequences two more times. With one warm-up run, this makes 65 runs, in random order. All other parameters were fixed. During the run, the laptop was unplugged for about one hour. My monitoring log showed this, so I measured the four affected settings again on AC power. I kept the original values and marked them clearly.

<!-- Slide number: 7 -->
# Encoding and Decoding Pipeline
Every run is encoded, decoded twice and verified automatically before its result is accepted
Original YUV
10-bit 4:2:0
vvencapp
VVenC encoder
Bitstream
.266 (VVC)
vvdecapp
timing pass + recon pass
Reconstructed YUV
same format
PSNR + checks
results.csv
Example (BQMall, QP 32, medium):
vvencapp -i BQMall_832_480_60_10_420.yuv -s 832x480 -c yuv420_10 --fps 60 -f 600 -q 32 --preset medium --qpa 0 -t 8 -v 4 --refreshtype cra --refreshsec 1 -o out.266
vvdecapp -b out.266 -t 8            (timing pass, no output)
vvdecapp -b out.266 -o rec.yuv -t 8  (reconstruction for PSNR)
Automatic checks per run
Exit codes = 0; picture and decoded-frame counts = input frames
Encoder echo: QPA disabled, rate control "QP n", 8 threads, 10-bit input
Independent PSNR = encoder PSNR (max difference 0.0000 dB); FFmpeg cross-check in the Phase 3 smoke test
Frame alignment: best offset 0 in every run
Repeats: SHA256 byte-identical bitstreams (32/32)
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
7 / 15

### Notes:
This is the pipeline for every run. The encoder reads the original video and writes a VVC bitstream. Then the decoder runs two times. The first time, it writes nothing; this gives a clean decoding time. The second time, it writes the reconstructed video. My own script then computes the PSNR against the original. I accept a run only when all checks pass. For example, the frame counts must be correct, the encoder must report the expected settings, and my PSNR must be equal to the encoder's PSNR. The largest difference was 0.0000 dB. Repeated runs gave byte-identical bitstreams.

<!-- Slide number: 8 -->
# QP vs Bitrate and PSNR
QP is the main rate–quality control: +5 QP roughly halves the bitrate and costs 1.45–3.93 dB
![Line chart: bitrate in kbps (log scale) versus QP 22 to 37 for four sequences, preset medium](QP vs bitrate chart)
![Line chart: Y-PSNR versus QP 22 to 37 for four sequences, preset medium](QP vs Y-PSNR chart)
Conditions
Preset medium, QPA off, 8 threads, sequence level (all frames)
÷2.06
bitrate per +5 QP (median)
range 1.91–2.35 over 12 steps
1.45–3.93 dB
Y-PSNR loss per +5 QP
peak 1020, mean of per-frame PSNR
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
8 / 15

### Notes:
Now the results. These charts show the QP sweep at preset medium. On the left, the bitrate axis is logarithmic, and the lines are almost straight. This means that each step of plus five QP divides the bitrate by about 2.06, in a range from 1.91 to 2.35. On the right you see the quality. Each plus five QP step costs between 1.45 and 3.93 dB of Y-PSNR. These values are for the whole sequence, using all frames. So QP is the main control for the balance between bitrate and quality.

<!-- Slide number: 9 -->
# QP vs Encoding Time
Lower QP means more coded detail and longer encoding; decoding stays two orders of magnitude faster
![Line chart: encoding time in seconds (log scale) versus QP for four sequences, preset medium](QP vs encoding time chart)
2.7–3.7×
encoding time QP 22 vs QP 37
preset medium, 4 sequences
133–333×
encoding vs decoding time
medium; decode timing pass without output
2.4%
median CV of repeated encodes
16 configurations × 3 samples (240p)
Windows, i7-1260P laptop, 8 threads, Best performance mode. Encoder-reported time, median of samples.
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
9 / 15

### Notes:
QP also changes the encoding time. QP 22 took 2.7 to 3.7 times longer than QP 37, because the encoder codes and searches more detail. Decoding is much cheaper. At preset medium, encoding took 133 to 333 times longer than decoding. The full HD video decoded at about 134 to 220 frames per second. I repeated the encodes of the small sequences, and the median variation was 2.4 percent. So I do not interpret small timing differences between single runs. All timings come from one laptop, so they are not a general benchmark.

<!-- Slide number: 10 -->
# Preset vs Compression Efficiency and Runtime
Slower presets buy small gains at large cost: slower takes 14–17× the time of medium for +0.24 to +0.37 dB
![Line chart: encoding time in seconds (log scale) versus preset faster to slower at QP 32 for four sequences](Preset vs encoding time chart)

| Preset vs medium | Encoding time | ΔY-PSNR | Bitstream size |
| --- | --- | --- | --- |
| faster | 0.11–0.13× | −0.66 to −0.45 dB | +6.3 to +13.8% |
| fast | 0.27–0.30× | −0.44 to −0.26 dB | −0.6 to +4.6% |
| slow | 3.2–3.7× | +0.13 to +0.19 dB | −3.5 to −1.3% |
| slower | 14.4–17.1× | +0.24 to +0.37 dB | −4.3 to −1.5% |

QP 32, sequence level, ranges over the 4 sequences. BQMall faster: 0.115× (run on battery) vs 0.094× (AC re-measurement).
Read with care
One QP per preset → not a BD-rate comparison
BlowingBubbles fast: 0.58% smaller than medium but −0.44 dB
Frame level: medium below faster in 13.4% of BasketballPass frames, always with more bits spent by faster
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
10 / 15

### Notes:
This slide is about presets, at QP 32. The encoding time grows very fast. Compared with medium, slower needed 14 to 17 times more time. But it gained only 0.24 to 0.37 dB, and the files were only 1.5 to 4.3 percent smaller. Faster needed about 0.11 to 0.13 times the time of medium, and lost 0.45 to 0.66 dB. I want to be careful here. These results are at one QP only, so they are not a BD-rate comparison. Also, at frame level, a faster preset sometimes has higher PSNR than a slower one. But in every such frame, the faster preset had used more bits.

<!-- Slide number: 11 -->
# Visual Quality Comparison: Original, QP 22, QP 32, QP 37
Observer-confirmed for BasketballPass frame 133: QP 22 clearest, QP 37 blurriest — PSNR and SSIM rank the same way
BasketballPass, frame 133 — observer-confirmed: QP 22 clearest, QP 37 blurriest
Notes
Same crop window for all panels; pixel-repetition zoom (4× / 3×)
Frame-level Y-PSNR and SSIM-Y [5] (simplified 8×8 window)
BQMall row: automated metrics + preliminary interpretation
Not a formal subjective study (no BT.500 setup, no MOS)
Display: BT.709 assumed
![BasketballPass frame 133, enlarged crop, original](BasketballPass f133 original)
![BasketballPass frame 133, enlarged crop, QP22 medium](BasketballPass f133 QP22_medium)
![BasketballPass frame 133, enlarged crop, QP32 medium](BasketballPass f133 QP32_medium)
![BasketballPass frame 133, enlarged crop, QP37 medium](BasketballPass f133 QP37_medium)
Original
QP 22: 40.79 dB · SSIM 0.976
QP 32: 33.28 dB · SSIM 0.908
QP 37: 30.55 dB · SSIM 0.845
BQMall, frame 42 — lowest QP 37 frame; automated metrics + preliminary interpretation
![BQMall frame 42, enlarged crop, original](BQMall f42 original)
![BQMall frame 42, enlarged crop, QP22 medium](BQMall f42 QP22_medium)
![BQMall frame 42, enlarged crop, QP32 medium](BQMall f42 QP32_medium)
![BQMall frame 42, enlarged crop, QP37 medium](BQMall f42 QP37_medium)
Original
QP 22: 38.28 dB · SSIM 0.969
QP 32: 32.31 dB · SSIM 0.917
QP 37: 29.58 dB · SSIM 0.864
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
11 / 15

### Notes:
Here is the visual comparison. These are enlarged crops of the same region, made from the real video data. The top row is BasketballPass, frame 133. I looked at this frame myself: QP 22 is the clearest, and QP 37 is the most blurred. PSNR and SSIM give the same order. The bottom row is BQMall, frame 42, which was the worst frame at QP 37. For this row, my statements come from the metrics and a preliminary inspection. This was not a formal subjective test. One more point: between QP 22 and QP 37, these frames differ by 8.7 to 10.2 dB, which is easy to see. Preset differences are much smaller, and much harder to see.

<!-- Slide number: 12 -->
# Cross-Platform Verification: Windows vs Linux
The MSVC and GCC builds produced a byte-identical bitstream for the tested configuration

| 16-frame smoke test | Windows (MSVC 19.44) | Linux (GCC 13.3, WSL2) | Result |
| --- | --- | --- | --- |
| Bitstream size | 10,069 B | 10,069 B | identical |
| Bitstream SHA256 | 5037d0750588ac5f… | 5037d0750588ac5f… | identical |
| Reconstruction SHA256 | 17dda8aee3708c15… | 17dda8aee3708c15… | identical |
| Decoded frames | 16 | 16 | identical |
| Y / U / V PSNR (dB) | 34.2535 / 39.7084 / 38.5279 | 34.2535 / 39.7084 / 38.5279 | identical |
| Linux repeats (3 runs) | – | same SHA256 in all runs | deterministic |

Scope and caveats
Verified for one 16-frame configuration only
Linux = Ubuntu 24.04 in WSL2, not native
No speed claim: sub-second runs, different compilers, VM, day and power state
Other presets, QPs, thread counts and long sequences: not tested across platforms
Configuration: BasketballPass 416×240, 16 frames, QP 32, preset faster, QPA off, 4 threads (same command on both platforms)
Encoder per-picture log lines (POC, slice QP, bits, PSNR) are also identical; only the speed (fps) lines differ.
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
12 / 15

### Notes:
To verify the Linux build, I repeated my 16-frame test from the Windows phase, with exactly the same command. The result: the bitstream, the decoded video and the PSNR are byte-for-byte identical, and all three Linux repeats are identical too. This means that, for this test, the MSVC build and the GCC build made the same encoding decisions. I did not assume this before the test. But please note the limits. This is only one short configuration, and Linux ran in WSL2. I also do not compare speed, because the runs were shorter than one second and the conditions were not controlled.

<!-- Slide number: 13 -->
# Key Findings, Limitations and Lessons Learned
Measured findings
Limitations
Lessons learned
+5 QP: bitrate ÷2.06 (median); Y-PSNR −1.45 to −3.93 dB
slower vs medium: 14.4–17.1× time for +0.24 to +0.37 dB and 1.5–4.3% smaller files
Encoding 133–333× slower than decoding
Deterministic output: 32/32 repeats identical; Windows = Linux for the smoke test
Presets compared at one QP → no BD-rate
Laptop timing: hybrid CPU; 1 sample for the two large sequences; 64-min battery incident
8-bit content in a 10-bit container
Linux via WSL2; cross-platform identity for one configuration
Visual evaluation informal; one observer-confirmed observation
Verify independently: own PSNR tool, SHA256, frame alignment
Control and monitor the environment (power mode, AC, temperature)
-q is a base QP: hierarchy and GOP-level adaptation change slice QPs
Keep logs, manifests and fingerprints; label interpretations
Bottom line:  QP sets the rate–quality operating point; the preset decides how much encoder time is spent to reach it. A fair preset comparison needs BD-rate over several QPs.
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
13 / 15

### Notes:
Let me summarize. First, QP is the main control of bitrate and quality. Second, slower presets cost a lot of time for a small gain. Third, decoding is more than one hundred times faster than encoding. Fourth, the encoder output was deterministic. The main limitations are: presets were compared at one QP only, the timing comes from one laptop, the content is 8-bit, Linux was WSL2, and the visual evaluation was informal. For me, the main lessons were: check every number independently, monitor the test environment, and remember that the QP option is only a base QP, because the encoder adapts the QP of each picture.

<!-- Slide number: 14 -->
# Conclusion and Possible Future Research Directions
The tools are built and verified on two platforms, and the main VVC trade-offs are quantified with checked data
Towards efficient video coding research (directions, not completed work)
Conclusion
VVenC 1.14.0 and VVdeC 3.2.1 built from unmodified release commits on Windows and Linux (WSL2); all available tests passed
65 verified runs: QP controls rate and quality; slower presets cost much more time for small gains
Encoder output deterministic and, for the tested configuration, identical across compilers
Visual inspection agrees with PSNR for large QP steps; preset differences are mostly numerical
BD-rate study
Presets over QP 22–37 and more sequences vs a VTM anchor: BD-rate [4] together with time saving
1
Controlled timing
Native Linux, fixed CPU frequency and affinity, many repeats; this pipeline as the baseline
2
Perceptual quality
VMAF / XPSNR / MS-SSIM and a small formal subjective test (ITU-R BT.500) [7]
3
Efficient encoding (AI background)
Open question: can small, pruned networks predict encoder decisions (e.g. partitioning) and cut the 14–17× slower-preset time at a small BD-rate loss?
4
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
14 / 15

### Notes:
To conclude: I built and verified both tools on two platforms, and I measured the main trade-offs with checked data. On the right are possible next steps. These are directions, not completed work. The first step would be a BD-rate study of the presets over several QPs. Second, controlled timing on native Linux. Third, perceptual metrics and a small formal viewing test. Finally, my background is in AI and neural-network pruning. My measurements show that the slower preset costs 14 to 17 times the time of medium. So one research question could be: can a small, pruned network predict some encoder decisions, and save time with only a small BD-rate loss? Thank you very much. I am happy to answer your questions.

<!-- Slide number: 15 -->
# References
[1] ITU-T Rec. H.266 | ISO/IEC 23090-3, Versatile Video Coding, 2020.
[2] B. Bross et al., "Overview of the Versatile Video Coding (VVC) Standard and its Applications," IEEE Trans. Circuits Syst. Video Technol., vol. 31, no. 10, pp. 3736–3764, Oct. 2021, doi:10.1109/TCSVT.2021.3101953.
[3] A. Wieckowski et al., "VVenC: An Open and Optimized VVC Encoder Implementation," Proc. IEEE ICME Workshops (ICMEW), Shenzhen, 2021, doi:10.1109/ICMEW53276.2021.9455944.
[4] G. Bjøntegaard, "Calculation of Average PSNR Differences between RD-curves," ITU-T SG16 Q.6 (VCEG), Doc. VCEG-M33, 2001.
[5] Z. Wang, A. C. Bovik, H. R. Sheikh, E. P. Simoncelli, "Image Quality Assessment: From Error Visibility to Structural Similarity," IEEE Trans. Image Process., vol. 13, no. 4, pp. 600–612, 2004.
[6] VVenC and VVdeC source code: github.com/fraunhoferhhi/vvenc (v1.14.0), github.com/fraunhoferhhi/vvdec (v3.2.1).
[7] ITU-R Rec. BT.500, Methodologies for the subjective assessment of the quality of television images.
[8] YUView: github.com/IENT/YUView (v2.14).
VVC encoding and decoding: experimental evaluation  ·  VVenC 1.14.0 / VVdeC 3.2.1
15 / 15

### Notes:
This slide lists the standard, the papers and the software that I used. All data, scripts and reports are in my project folder, and I can share them if needed.
