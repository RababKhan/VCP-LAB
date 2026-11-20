# Speaker notes (10 slides): Sadab Khan Prangon, expanded VVC experiment

All numbers come from results/*.csv and results/*.json. Text in [brackets] (slide 8) must be written by Sadab after his own YUView check. The wording does not claim that Sadab personally ran the automated experiments.

## Slide 1

Good morning, Professor Choi. My name is Sadab Khan Prangon. I am a B.Sc. student in Computer Science and Engineering at IUBAT in Bangladesh.

This talk presents the VVC assignment: building VVenC and VVdeC on Windows and Linux, encoding and decoding test videos, and analysing rate, quality and complexity. The experiment was extended to 64 configurations: four sequences, four QP values and four presets.

I want to be transparent: the builds and runs were executed by automated scripts with the help of an AI assistant, and every log and measurement is kept in the report. My goal today is to explain what the results show and what they do not show.

## Slide 2

This is the pipeline. The original video is a raw 10-bit 4:2:0 YUV file with no header, so the size, frame rate and format must be given on the command line.

VVenC encodes it into a .266 bitstream; here the encoding time and the file size are measured, and the bitrate is computed from the size. VVdeC decodes it again. The decoding time is measured three times without writing an output file, and one extra decode writes the reconstruction.

The reconstruction is compared with the original frame by frame: PSNR for every run, and SSIM and MS-SSIM for selected frames. The same pipeline exists on Windows and Linux.

## Slide 3

VVenC 1.14.0 and VVdeC 3.2.1 were built from source with the same release tags on both systems: on Windows 11 with MSVC 19.44, and on Ubuntu 24.04 in WSL2 with GCC 13.3.

On Linux all 39 VVenC tests and the VVdeC unit test passed. On Windows, 32 of 39 passed; seven could not run because Windows Smart App Control blocked two unsigned test programs. No security setting was changed. The VVdeC conformance tests were not run, because their bitstreams are not part of the source code.

Before the main runs, a 16-frame smoke test passed on both systems. Then 94 encoder runs were made on Windows, and selected configurations were repeated on Linux for a bit-exactness check.

## Slide 4

The experiment design. Four standard sequences: two at 416 by 240, BQMall at 832 by 480, and BasketballDrive at 1080p, each 10 seconds long. Four QP values and four presets give 64 configurations. Sixteen of them came from the first round of the experiment with exactly the same settings, so they were reused.

Because timing on a laptop is noisy, several controls were added: a warm-up before each block, a check for AC power before every run, a random run order with a recorded seed, and a CPU monitor every five seconds. Nine configurations were measured at least four times, and decoding was timed three times without writing a file.

For every run, the PSNR was also checked with an independent script.

## Slide 5

The first result: QP and rate–distortion. Each small chart is one sequence; each line is one preset, and the four points are QP 24 to 39.

Across all 48 QP steps, each increase of 5 in QP divided the bitrate by 1.88 to 2.18, about 2.1 times, and lowered the Y-PSNR by 1.5 to 3.8 dB. The quality loss per step is smallest for BasketballDrive and largest for the small sequences.

The curves of the four presets are almost parallel, with slow on top and faster at the bottom. The independent PSNR check matched the encoder in all 94 runs.

## Slide 6

Preset complexity: the chart shows the median encoding time at QP 29 on a log scale. Each step to a slower preset multiplies the time.

Compared with medium at the same QP, faster needed only 0.08 to 0.16 of the time, fast 0.25 to 0.38, and slow 2.3 to 3.8 times. BasketballDrive at 1080p took up to 1998 seconds per encode at QP 29.

Decoding took only 0.11 to 3.3 seconds.

Timing is now repeatable: the controlled repeats varied by only 0.2 to 2.7 percent. The 45 percent gap in the first round came from a short slow period of the whole laptop at the start.

## Slide 7

Presets give different quality at the same QP, so they are compared with BD-rate against medium, over the four QP points. A piecewise cubic interpolation is integrated over the common quality range; all curves overlapped by more than 90 percent.

Faster needs 25 to 34 percent more bitrate for the same quality, fast 11 to 15 percent more, and slow saves 4.9 to 6.9 percent, but costs about 2.9 to 3.5 times the time.

So each slower preset gives a smaller saving for a larger time cost: diminishing returns. The penalty of faster is larger for the bigger sequences, but with one sequence per resolution this is only a trend.

## Slide 8

For visual quality, frame 98 of BasketballDrive is shown with the same crop for the original and for QP 24 to 39 at the medium preset. The frame and crop were chosen by a fixed rule before looking: the frame with the median quality at QP 39, and the most detailed area of that frame.

From QP 24 to QP 39, the frame PSNR falls from 38.4 to 33.0 dB, SSIM from 0.923 to 0.864, and MS-SSIM from 0.988 to 0.954. The table shows the sequence-level MS-SSIM for all four sequences.

[Sadab: after checking these frames yourself in YUView, describe here in one or two sentences what you saw.]

The images are rendered from the decoded files by a script, and this is not a subjective test.

## Slide 9

The Windows and Linux builds were checked against each other. The same configuration was encoded on both systems, and the bitstream hash, the decoded-video hash, the frame count, the Y, U and V PSNR and the encoder's printed parameters were compared.

In all 8 checks, covering all four sequences and all four presets, the outputs were exactly identical, bit for bit. So the MSVC and GCC builds of VVenC and VVdeC behave the same for these settings.

Speed was not compared, because Linux ran inside WSL2.

## Slide 10

To conclude. First, QP controls the trade-off: about half the bitrate for every 5 QP, at a cost of roughly 1.5 to 4 dB. Second, slower presets are clearly more efficient, but with diminishing returns: slow saves about 5 to 7 percent bitrate for about three times the encoding time. Third, the Windows and Linux builds are bit-exact. Fourth, careful timing control matters: a short slow phase of the laptop produced the earlier 45 percent gap.

What still needs work: more sequences per resolution, the standard CTC QPs, a comparison with VTM, and perceptual metrics like VMAF.

My background is in computer vision and deep learning. A direction I would like to study is learning-based enhancement of decoded video, for example a light CNN that reduces artifacts at high QP. This is a direction, not completed work. Thank you very much, Professor Choi.
