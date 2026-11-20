# The 10 most important questions, with simple answers

**Presenter:** Rabab Khan Rongon. **Source:** the 23 questions in `report/phase7_professor_QA.md`.

**How the 10 were chosen:** a video-coding professor is most likely to test four things:
1. understanding of how the codec works (Q1, Q2, Q3 below)
2. whether the measurements can be trusted (Q4, Q5)
3. whether the results are interpreted correctly (Q6–Q8)
4. honesty about scope (Q9, Q10)

The remaining 13 questions are still covered in the Phase 7 document. Every number below comes from the verified result files and is checked by `scripts/audit_claims.py` (28/28 pass).

---

### 1. What does `-q 32` mean? Is every picture coded at QP 32?
**Simple answer:** No. `-q` is a base QP. VVenC uses a hierarchical GOP: lower temporal layers get a lower QP, higher layers a higher QP.

**Technical detail:**
- In BasketballPass at `-q 32`, the IDR picture was coded at QP 27 and the top temporal layer at QP 41–42. In BQMall the IDR picture was at QP 29.
- Averaged over the QP sweep, I pictures were 2.7–3.6 below `-q`, and B pictures 5.7–8.6 above it.
- With QPA off, VVenC still applies a small GOP-level QP adaptation.

### 2. Which PSNR did you use, and how do you know it is correct?
**Simple answer:** Peak value 1020 (255 × 4 for 10-bit), the same convention as HM, VTM and VVenC. The sequence value is the mean of the per-frame PSNR.

**Verification:**
- My own script gave the same PSNR as the encoder in every run (maximum difference 0.0000 dB).
- In the first smoke test it also matched FFmpeg to six decimals.
- I also checked frame alignment: the best offset was 0 in every run.

### 3. Why does the bitrate roughly halve every 5 QP?
**Measured:** at preset medium, each +5 QP divided the bitrate by 1.91–2.35 (median 2.06) and lowered Y-PSNR by 1.45–3.93 dB.

**Why:** in VVC, as in HEVC, the quantizer step size doubles every 6 QP. A larger step means fewer non-zero coefficients and fewer bits. The result is a roughly constant bitrate ratio per QP step, and therefore straight lines on a logarithmic bitrate axis.

### 4. How did you make sure the experiment is reliable?
- **Design:** one factor at a time, fixed settings (constant QP, QPA off, 8 threads, CRA every second), random run order, and automatic checks on every run.
- **Verification:** all 65 runs passed, and all 32 repeated runs gave byte-identical bitstreams.
- **Timing noise:** the median variation of repeated encodes was 2.4%. I do not interpret differences below about 5–10%.
- **Battery incident:** the monitor log showed the laptop on battery for about an hour. I re-measured the four affected settings on AC and kept the original values, clearly marked.

### 5. How reliable are your timing numbers?
- They come from one laptop with a hybrid CPU, in a fixed power mode. They are good for comparing settings with each other, not as a general benchmark.
- The two small sequences have three samples per setting; the two large sequences have one.
- Proper timing would need native Linux, a fixed CPU frequency and many repeats.

### 6. Is the slower preset worth it?
**Measured:** at QP 32, compared with medium, slower needed 14.4–17.1 times the encoding time for only +0.24 to +0.37 dB and 1.5–4.3% smaller files.

**My interpretation:**
- For real-time or large-volume encoding, medium or faster gives most of the benefit.
- For offline archiving, slower may be justified.
- This is one QP only, so it is not a BD-rate comparison. Preset efficiency needs RD curves over several QPs.

### 7. Your reports give 0.24–0.37 dB and 0.84–0.98 dB for the preset gain. Which is right?
**Both are right.** They compare different things, and both are sequence-level values:
- **0.24–0.37 dB:** `medium` → `slower`, over all four sequences.
- **0.84 / 0.98 dB:** `faster` → `slower`, for BasketballPass and BQMall only.

Over all four sequences, `faster` → `slower` is 0.69–0.98 dB.

### 8. You found frames where a faster preset beats a slower one. How is that possible?
**Measured:** in BasketballPass, `medium` had lower frame PSNR than `faster` in 67 of 500 frames.
- In every one of those frames, `faster` had used more bits for that picture.
- In 59 of them, `faster` had coded the picture at a lower slice QP.

So it is a local trade of bits for quality, not "better compression". Over the whole sequence, slower presets give both higher PSNR and smaller files.

**Hypothesis (not tested):** the different motion-filtering settings of `faster` change the encoder's QP adaptation.

### 9. Are Windows and Linux results identical? Is Linux faster?
- **Identity:** for one 16-frame test (QP 32, faster, 4 threads), the MSVC and GCC builds produced a byte-identical bitstream, an identical decoded video and identical PSNR. I have not tested other settings across platforms.
- **Speed:** I cannot say that Linux is faster. The runs were shorter than one second, Linux ran in WSL2, and the conditions were not controlled.

### 10. Did you check visual quality, and does it agree with PSNR?
**What I did:**
- I looked at BasketballPass frame 133 myself: QP 22 was the clearest and QP 37 the most blurred. PSNR and SSIM rank them the same way.
- For the other frames I used automated metrics (frame PSNR, SSIM, difference maps, a detail ratio) and a preliminary inspection.
- This was not a formal subjective test.

**Agreement with PSNR:**
- Large QP differences (about 8–10 dB between QP 22 and 37) are clearly visible.
- Preset differences of a few tenths of a dB are hard to see.
- So PSNR ranks large changes well, but it cannot tell whether a small change is visible.

---

## How this assignment connects to possible future research (directions, not completed work)

This assignment gives me three things that efficient-video-coding research needs:
1. a verified encode–decode–measure pipeline on two platforms
2. an understanding of where encoder time goes (presets, QP)
3. a habit of separating measurement from interpretation

**The measured observation that motivates the research direction:**
- The slower preset costs 14–17× the time of medium for 0.24–0.37 dB.
- Most of the cost of a high-efficiency encoder is therefore in its decision search.

**A natural question, connected to my background in AI and neural-network pruning:** can a small, pruned neural network predict some of these decisions, for example the block partitioning, and so reduce encoding time while keeping the BD-rate loss small?

**What answering it would require:**
- BD-rate against a reference anchor (for example VTM) under common test conditions, measured together with the time saving
- controlled timing
- more sequences

I have **not** proposed or tested such a method. It is a direction I would be interested to study under supervision.
