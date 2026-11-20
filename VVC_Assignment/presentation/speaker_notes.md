# Speaker notes: full talk (15 slides, 12-15 minutes)

Presenter: Rabab Khan Rongon. The same text is stored in the .pptx speaker notes. Short sentences, simple words; numbers come from the verified result files.
Total: 1493 words; at a calm 110-125 words per minute this is about 12-14 minutes plus pauses.

## Slide 1: VVC Encoding and Decoding: Experimental Evaluation  (~101 words, about 0.8 min)

Good morning, Professor Kiho. Thank you for this opportunity. My name is Rabab Khan Rongon. I am doing my M.Sc. in Computer Science and Engineering, with a major in Artificial Intelligence, at MIST in Bangladesh. Today I will present my practical assignment on VVC. In short: I built the VVenC encoder and the VVdeC decoder on Windows and on Linux. Then I encoded four test videos with different QP values and presets, decoded them, and measured bitrate, quality and time. All numbers in this talk come from my own result files. When something is only my interpretation, I will say so.

## Slide 2: Assignment Objectives and Workflow  (~104 words, about 0.9 min)

Here is the plan of the work. There were five steps. First, I built the tools. Second, I encoded four sequences with eight settings each. Third, I decoded every bitstream two times: one time only to measure the speed, and one time to write the video for the quality measurement. Fourth, I measured time, file size and PSNR. In total I made 65 runs, and all of them passed my checks. Fifth, I compared the videos visually, and I compared Windows with Linux. I followed some simple rules: I verified every command, I kept all logs, and I did not change the source code.

## Slide 3: VVC, VVenC, VVdeC and YUView  (~101 words, about 0.8 min)

Now a short introduction to the tools. VVC, also called H.266, is the newest video coding standard from ITU-T and ISO/IEC. It was finished in 2020, and it is the successor of HEVC. According to the overview paper by Bross and colleagues, it targets about fifty percent lower bitrate than HEVC at similar perceptual quality. VVenC is an open-source encoder from Fraunhofer HHI. Its presets, from faster to slower, trade speed for compression. VVdeC is the matching decoder, and YUView is an open-source viewer for raw video. At the bottom you can see how I connected the tools in this study.

## Slide 4: Development Environments: Windows and Linux  (~102 words, about 0.8 min)

This slide shows my two build environments. On Windows I used the Microsoft C++ compiler from Visual Studio 2022. On Linux I used Ubuntu 24.04 with GCC 13. Both builds use exactly the same release commits, with no change to the source code, and the default Release settings. Both builds finished with zero warnings and zero errors, and all available tests passed. On Linux I could also run the VVenC test suite: thirty-nine out of thirty-nine passed. One important point: my Linux system is WSL2. This is a small virtual machine on the same laptop. It is not a native Linux installation.

## Slide 5: Dataset and Video Characteristics  (~104 words, about 0.9 min)

These are the four test sequences: two small ones at 416 by 240, BQMall at 832 by 480, and BasketballDrive in full HD. Before encoding, I checked every file. The files are 10-bit, but I found that the two lowest bits are always zero. So the real content has only 8-bit precision. I also found that the last frame of each file is a copyright picture, so I did not encode it. For PSNR, I used the peak value 1020. This is the same convention as in the reference software and in VVenC, so my values can be compared directly with the encoder output.

## Slide 6: Experimental Design and Controlled Parameters  (~113 words, about 0.9 min)

My design changes one factor at a time. For the QP sweep, I used QP 22, 27, 32 and 37 with preset medium. For the preset sweep, I used all five presets with QP 32. This gives eight settings per sequence, and thirty-two in total. To measure timing noise, I repeated every setting of the two small sequences two more times. With one warm-up run, this makes 65 runs, in random order. All other parameters were fixed. During the run, the laptop was unplugged for about one hour. My monitoring log showed this, so I measured the four affected settings again on AC power. I kept the original values and marked them clearly.

## Slide 7: Encoding and Decoding Pipeline  (~99 words, about 0.8 min)

This is the pipeline for every run. The encoder reads the original video and writes a VVC bitstream. Then the decoder runs two times. The first time, it writes nothing; this gives a clean decoding time. The second time, it writes the reconstructed video. My own script then computes the PSNR against the original. I accept a run only when all checks pass. For example, the frame counts must be correct, the encoder must report the expected settings, and my PSNR must be equal to the encoder's PSNR. The largest difference was 0.0000 dB. Repeated runs gave byte-identical bitstreams.

## Slide 8: QP vs Bitrate and PSNR  (~91 words, about 0.8 min)

Now the results. These charts show the QP sweep at preset medium. On the left, the bitrate axis is logarithmic, and the lines are almost straight. This means that each step of plus five QP divides the bitrate by about 2.06, in a range from 1.91 to 2.35. On the right you see the quality. Each plus five QP step costs between 1.45 and 3.93 dB of Y-PSNR. These values are for the whole sequence, using all frames. So QP is the main control for the balance between bitrate and quality.

## Slide 9: QP vs Encoding Time  (~93 words, about 0.8 min)

QP also changes the encoding time. QP 22 took 2.7 to 3.7 times longer than QP 37, because the encoder codes and searches more detail. Decoding is much cheaper. At preset medium, encoding took 133 to 333 times longer than decoding. The full HD video decoded at about 134 to 220 frames per second. I repeated the encodes of the small sequences, and the median variation was 2.4 percent. So I do not interpret small timing differences between single runs. All timings come from one laptop, so they are not a general benchmark.

## Slide 10: Preset vs Compression Efficiency and Runtime  (~107 words, about 0.9 min)

This slide is about presets, at QP 32. The encoding time grows very fast. Compared with medium, slower needed 14 to 17 times more time. But it gained only 0.24 to 0.37 dB, and the files were only 1.5 to 4.3 percent smaller. Faster needed about 0.11 to 0.13 times the time of medium, and lost 0.45 to 0.66 dB. I want to be careful here. These results are at one QP only, so they are not a BD-rate comparison. Also, at frame level, a faster preset sometimes has higher PSNR than a slower one. But in every such frame, the faster preset had used more bits.

## Slide 11: Visual Quality Comparison: Original, QP 22, QP 32, QP 37  (~118 words, about 1.0 min)

Here is the visual comparison. These are enlarged crops of the same region, made from the real video data. The top row is BasketballPass, frame 133. I looked at this frame myself: QP 22 is the clearest, and QP 37 is the most blurred. PSNR and SSIM give the same order. The bottom row is BQMall, frame 42, which was the worst frame at QP 37. For this row, my statements come from the metrics and a preliminary inspection. This was not a formal subjective test. One more point: between QP 22 and QP 37, these frames differ by 8.7 to 10.2 dB, which is easy to see. Preset differences are much smaller, and much harder to see.

## Slide 12: Cross-Platform Verification: Windows vs Linux  (~102 words, about 0.8 min)

To verify the Linux build, I repeated my 16-frame test from the Windows phase, with exactly the same command. The result: the bitstream, the decoded video and the PSNR are byte-for-byte identical, and all three Linux repeats are identical too. This means that, for this test, the MSVC build and the GCC build made the same encoding decisions. I did not assume this before the test. But please note the limits. This is only one short configuration, and Linux ran in WSL2. I also do not compare speed, because the runs were shorter than one second and the conditions were not controlled.

## Slide 13: Key Findings, Limitations and Lessons Learned  (~106 words, about 0.9 min)

Let me summarize. First, QP is the main control of bitrate and quality. Second, slower presets cost a lot of time for a small gain. Third, decoding is more than one hundred times faster than encoding. Fourth, the encoder output was deterministic. The main limitations are: presets were compared at one QP only, the timing comes from one laptop, the content is 8-bit, Linux was WSL2, and the visual evaluation was informal. For me, the main lessons were: check every number independently, monitor the test environment, and remember that the QP option is only a base QP, because the encoder adapts the QP of each picture.

## Slide 14: Conclusion and Possible Future Research Directions  (~122 words, about 1.0 min)

To conclude: I built and verified both tools on two platforms, and I measured the main trade-offs with checked data. On the right are possible next steps. These are directions, not completed work. The first step would be a BD-rate study of the presets over several QPs. Second, controlled timing on native Linux. Third, perceptual metrics and a small formal viewing test. Finally, my background is in AI and neural-network pruning. My measurements show that the slower preset costs 14 to 17 times the time of medium. So one research question could be: can a small, pruned network predict some encoder decisions, and save time with only a small BD-rate loss? Thank you very much. I am happy to answer your questions.

## Slide 15: References  (~30 words, about 0.2 min)

This slide lists the standard, the papers and the software that I used. All data, scripts and reports are in my project folder, and I can share them if needed.
