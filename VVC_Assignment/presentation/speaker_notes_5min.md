# Speaker notes: 5-minute version (7 slides)

Use VVC_Experimental_Evaluation_Prof_Kiho_5min.pptx (slides 1, 6, 8, 10, 11, 12 and 14 of the full deck).
Total: 505 words; at a calm 110-125 words per minute this is about 4-5 minutes plus pauses.

## Slide 1: VVC Encoding and Decoding: Experimental Evaluation  (~82 words, about 0.7 min)

Good morning, Professor Kiho. I am Rabab Khan Rongon, an M.Sc. student in Computer Science and Engineering, with a major in Artificial Intelligence, at MIST in Bangladesh. In the next five minutes I will show what I did in the VVC assignment. I built the VVenC encoder and the VVdeC decoder on Windows and on Linux, I ran a controlled experiment with four test videos, and I analysed bitrate, quality and encoding time. All numbers come from my own verified result files.

## Slide 2: Experimental Design and Controlled Parameters  (~102 words, about 0.8 min)

My experiment changes one factor at a time. In the QP sweep, I used QP 22, 27, 32 and 37 with preset medium. In the preset sweep, I used the five presets, from faster to slower, with QP 32. With timing repeats and one warm-up run, I made 65 runs in random order. Every run passed automatic checks: correct frame counts, the expected encoder settings, and PSNR equal to the encoder's own value. Repeated runs gave identical bitstreams. When the laptop ran on battery for about one hour, my logs showed it, and I measured the affected settings again on AC power.

## Slide 3: QP vs Bitrate and PSNR  (~61 words, about 0.5 min)

This is the main result. The bitrate axis is logarithmic, and the lines are almost straight. Each plus five QP step divides the bitrate by about 2.06, and it costs 1.45 to 3.93 dB of Y-PSNR. This is true for all four sequences, from 240p to full HD. So QP is the main control of the balance between bitrate and quality.

## Slide 4: Preset vs Compression Efficiency and Runtime  (~63 words, about 0.5 min)

Presets mainly change the encoding time. Compared with medium, slower needed 14 to 17 times more time, but it gained only 0.24 to 0.37 dB, and the files were only 1.5 to 4.3 percent smaller. So the slower presets buy a small gain at a large cost. But this is a result at one QP only, so it is not a BD-rate comparison.

## Slide 5: Visual Quality Comparison: Original, QP 22, QP 32, QP 37  (~64 words, about 0.5 min)

Here you see enlarged crops from the real video data. In BasketballPass frame 133, I checked myself: QP 22 is the clearest, and QP 37 is the most blurred. PSNR and SSIM give the same order. Preset differences at the same QP are much smaller, and they are hard to see. I want to be clear that this was not a formal subjective test.

## Slide 6: Cross-Platform Verification: Windows vs Linux  (~57 words, about 0.5 min)

Finally, I verified the Linux build. For a 16-frame test with the same command, Windows and Linux produced byte-identical bitstreams, identical decoded video and identical PSNR. This is only one short configuration, and Linux ran in WSL2, not natively. I also make no speed claim, because the test was too short and the conditions were not controlled.

## Slide 7: Conclusion and Possible Future Research Directions  (~76 words, about 0.6 min)

To conclude, the tools are built and verified, and the main trade-offs are measured with checked data. Next steps would be a BD-rate study over several QPs, controlled timing on native Linux, and perceptual quality metrics. With my background in AI and network pruning, one direction I would like to explore is small, pruned networks that predict encoder decisions, to reduce the time of the slower presets. These are ideas, not results. Thank you very much.
