# Speaker notes: Sadab Khan Prangon, VVC assignment

All numbers come from results/results_raw.csv, results/summary.json and results/crossplatform.json. Text in [brackets] (slide 7) must be written by Sadab after his own YUView inspection.

## Slide 1

Good morning, Professor Choi. My name is Sadab Khan Prangon. I am a B.Sc. student in Computer Science and Engineering at IUBAT in Bangladesh, and I expect to graduate in April 2027.

In this short talk I will present the VVC assignment you gave me. I had four goals. First, build the VVenC encoder and the VVdeC decoder on Windows and on Linux. Second, encode raw YUV videos. Third, decode them again. And fourth, measure time, file size, bitrate and PSNR, and look at the decoded video in YUView.

I will first explain the workflow and my setup, then show my results, and finish with what I learned.

## Slide 2

This slide shows the complete pipeline I used.

On the left is the original video. It is a raw YUV file, 10-bit, 4:2:0. A raw file has no header, so I must give the size, frame rate and format myself on the command line.

VVenC compresses it into a .266 bitstream. Here I measure the encoding time and the file size, and from the size I calculate the bitrate. Then VVdeC decodes the bitstream back into a YUV video, and I measure the decoding time.

Finally, I compare the decoded video with the original, frame by frame. This gives the PSNR, and I also look at the frames in YUView. I used the same pipeline on Windows and on Linux.

## Slide 3

Next, the environment. I built VVenC 1.14.0 and VVdeC 3.2.1 from source: on Windows 11 with MSVC 19.44, and on Ubuntu 24.04 in WSL2 with GCC 13.3.

On Linux all 39 VVenC tests and the VVdeC unit test passed. On Windows 32 of 39 passed; the other 7 did not run, because Smart App Control blocked two unsigned test programs. I did not change any security setting.

Then I encoded the same video with the same settings on both systems. In all three checks, the bitstreams and the decoded videos had exactly the same SHA-256 hash. I do not compare speed, because Linux ran in WSL2.

## Slide 4

This is my experiment design. It is small, but it is controlled.

I used two standard test sequences from the provided files: BlowingBubbles at 416 by 240, and BQMall at 832 by 480. Both are 10-bit, 4:2:0 and 10 seconds long.

For each sequence I used four QP values, 24, 29, 34 and 39, and two presets, fast and medium. Two times four times two gives sixteen encodings.

I kept everything else fixed. I turned QP adaptation off, so QP is the only quality control, used eight threads, and ran all runs on the same laptop on AC power, in a shuffled order. I decoded every bitstream three times and kept the median time. I also repeated two encodings to see how much the timing changes.

## Slide 5

Now the first result: what QP does to compression and quality. Each line is one preset, the points are QP 24 to 39, and the bitrate axis is logarithmic.

In my 16 runs, every increase of 5 in QP divided the bitrate by 1.89 to 2.15, about 2.1 times, and the Y-PSNR went down by 2.5 to 3.1 dB. From QP 24 to QP 39 with the medium preset, the bitrate became 9.0 times smaller for BlowingBubbles and 7.7 times smaller for BQMall, and the quality dropped by about 8 dB.

My own PSNR script matched the encoder's PSNR exactly in all 18 runs.

## Slide 6

The second result is about time. Blue is medium, orange is fast.

At the same QP, medium took 2.0 to 4.3 times longer and gave 0.27 to 0.47 dB higher Y-PSNR. But the file size changed by −6.1 to +1.6 percent, so to say how much more efficient medium is, I would need BD-rate.

Decoding took only 0.4 to 2.8 seconds, including writing the file. Encoding was 21 to 192 times slower.

One warning: of my two repeated encodings, one changed by 2.1 percent, the other by 45 percent. So I only trust large time differences. This is one laptop, not a benchmark.

## Slide 7

Numbers are not enough, so I also compared the pictures.

This is frame 432 of BQMall, with the same crop for the original and for QP 24, 29, 34 and 39, medium preset. I chose the frame and the crop with a fixed rule before looking. The hand is moving, so the original is already a little blurred.

The frame PSNR goes down from 39.53 dB at QP 24 to 31.29 dB at QP 39.

[Sadab: after you check these frames in YUView, say here in one or two sentences what you saw, for example where texture or edges are lost.]

These images were rendered from the decoded files by a script; this is not a formal subjective test.

## Slide 8

To conclude, three findings from my own data.

First, QP is the main control. Each step of 5 in QP divided the bitrate by about 2.1 and cost 2.5 to 3.1 dB of Y-PSNR.

Second, at the same QP, the medium preset gave 0.27 to 0.47 dB better quality than fast, but it needed 2.0 to 4.3 times the encoding time, and the file size did not always go down, so a fair comparison needs BD-rate.

Third, Windows and Linux produced exactly the same bitstreams and decoded videos.

I also learned that laptop timing is noisy, so repeated runs are necessary.

My background is in computer vision and deep learning. After this assignment, I am interested in learning-based enhancement of decoded video, for example a small CNN that reduces coding artifacts at high QP. This is only a direction I would like to study, not work I have done.

Thank you very much, Professor Choi. I am happy to answer your questions.
