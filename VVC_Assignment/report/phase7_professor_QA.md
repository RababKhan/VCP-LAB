# Likely questions from Prof. Kiho, with suggested answers

The answers use only measured project data, or they state clearly when something is an interpretation or a hypothesis. Numbers refer to the Phase 4B full run (`results/full/`) unless another source is named.

**Labels used below:**
- **[M]** measured
- **[I]** interpretation
- **[H]** hypothesis, not tested
- **[U]** user-confirmed observation

---

## A. Basics and tools

**Q1. What does `-q 32` actually mean in VVenC? Is every picture coded at QP 32?**

No. `-q` is a base QP.
- **[M]** VVenC applies hierarchical QP offsets. At `-q 32` in BasketballPass, the IDR picture was coded at slice QP 27 and the highest temporal layer (TId 5) at QP 41–42. In BQMall the IDR picture was at QP 29.
- **[M]** The average slice QP of I pictures was 2.7–3.6 below `-q`, and that of B pictures 5.7–8.6 above it (QP sweep, preset medium).
- **[M]** With `--qpa 0`, VVenC still enables GOP-wise QP adaptation (`m_GOPQPA = 1`; `vvencCfg.cpp`, lines 1555–1558). This can move a GOP's QP by ±1.

**Q2. Why did you disable QPA?**
- QPA (perceptual QP adaptation) changes QPs per block to optimise a perceptual (XPSNR-based) target. That would make PSNR-based comparison between configurations less direct.
- With QPA off, rate control is "QP n", and every run's configuration echo confirms that.

**Q3. Why random access with CRA every second, and why did the first IDR appear at POC 15 or 31?**
- **CRA every second:** a common streaming-like setting (`--refreshtype cra --refreshsec 1`). It gives an intra period of 48 (50 fps) or 64 (60 fps), with GOP size 32.
- **[M]** **First IDR at POC 15 / 31:** these are the observed positions. Since VVenC 1.10.0 the default `poc0idr` is off, so the first key picture is placed later in the GOP structure.

**Q4. Which PSNR definition did you use? Does it match the encoder?**
- **[M]** Peak value 1020 (= 255 << 2), the HM/VTM/VVenC convention. The sequence value is the mean of per-frame PSNR. YUV-PSNR is the PSNR of the 4:1:1 pixel-weighted MSE.
- **[M]** My independent script matched the encoder's own PSNR with a maximum difference of 0.0000 dB in all runs. It also matched FFmpeg to 6 decimals in Phase 3.
- Alternative conventions are stored too: peak 1023, PSNR of the average MSE, and 6:1:1 weighting.

**Q5. The input is 10-bit. Is it real 10-bit content?**
- **[M]** No. In all four files the two least-significant bits of every sample are 0. The content is 8-bit precision shifted into a 10-bit container.
- **[I]** Results therefore describe 10-bit coding of 8-bit-precision content, not true 10-bit detail.

**Q6. Why did you exclude the last frame?**
- **[M]** The last frame of each file is an NTT DOCOMO copyright card, not part of the scene.
- I encoded only the content frames: 500 / 500 / 600 / 500.

---

## B. Experimental design and reliability

**Q7. How many runs, and why 65?**
- **Design:** 8 unique configurations per sequence (QP 22/27/32/37 at medium, plus faster/fast/slow/slower at QP 32; QP 32 / medium is shared), × 4 sequences = 32.
- **Repeats:** 2 extra timing repeats for each configuration of the two 240p sequences = 32 repeats.
- **Warm-up:** 1 warm-up run.
- **Total:** 65 runs, in randomized order (seed 2026).

**Q8. How do you know the results are correct?**

**[M]** Every run passed automatic checks:
- exit codes
- frame counts
- the encoder's configuration echo (QPA disabled, QP, 8 threads, 10-bit input)
- PSNR recomputed independently and equal to the encoder value
- frame alignment offset 0
- for repeats: SHA256-identical bitstreams (32/32)

In a final audit, 26 key numerical claims were recomputed from the CSV files (26/26 pass after corrections; see the audit report).

**Q9. How reliable are your timing numbers?**
- **[M]** Repeated encodes had a median coefficient of variation of 2.4% (16 configurations × 3 samples). The range was 0.4–5.3%, excluding one outlier.
- **[I]** Differences below about 5–10% between single runs should not be interpreted.
- The two large sequences have only one timing sample per configuration.
- All timing comes from one laptop with a hybrid CPU.

**Q10. What happened with the battery?**
- **[M]** The 30-second monitor showed the laptop on battery from 14:27 to 15:31 (about 64 minutes). Power-saving behaviour was not part of the design.
  - Bitstreams were not affected: all repeats are byte-identical.
  - One repeat (BasketballPass, slower) was 26% slower; the median protects that configuration.
- **Re-measurement:** four single-sample configurations were re-measured on AC under an active power guard.
  - Three agreed within −2.8% to +0.9%.
  - BQMall QP 32 `faster` was 18.7% faster on AC (13.65 s → 11.10 s).
- **[H]** That difference may come from short-term turbo power limits on battery. This was not verified.
- **Data handling:** original values were kept and flagged.

**Q11. Is your Windows timing comparable with future measurements?**
- Not directly. Enabling WSL2 activated the Windows hypervisor (2026-11-04 22:04). All Windows measurements were taken before that change.

---

## C. Results

**Q12. How does bitrate depend on QP?**
- **[M]** At preset medium, each +5 QP step divided the bitrate by 1.91–2.35 (median 2.06) and lowered Y-PSNR by 1.45–3.93 dB.
- **[I]** An approximate halving per +5 to +6 QP is the behaviour expected when the quantizer step size doubles every 6 QP.

**Q13. Is the slower preset worth it?**
- **[M]** At QP 32, sequence level, `slower` vs `medium`: 14.4–17.1× the encoding time for +0.24 to +0.37 dB Y-PSNR and 1.5–4.3% smaller files.
- **[I]** For time-sensitive use, medium or faster presets give most of the efficiency. For archival or offline encoding, slower presets may be justified.
- **[I]** This is **not** a BD-rate result. It is a single-QP comparison, so size and quality change together.

**Q14. Your Phase 4B and Phase 6 reports give different numbers for the preset gain (0.24–0.37 dB vs 0.84–0.98 dB). Which is right?**

Both are correct; they compare different things. Both are sequence-level values.

| Report | Comparison | Sequences | Y-PSNR gain | Size reduction |
|---|---|---|---|---|
| Phase 4B | `medium` → `slower` | all 4 | +0.24 to +0.37 dB | 1.5–4.3% |
| Phase 6 | `faster` → `slower` | BasketballPass, BQMall | +0.84 / +0.98 dB | 13.1% / 14.6% |

- Phase 4B gives `faster` → `slower` over all 4 sequences as +0.69 to +0.98 dB and 7.4–15.3%.
- Separately, the Phase 6 **frame-level** spread (six selected frames, `faster` → `slower`) is 0.24–1.31 dB.
- During the audit, the Phase 4B upper bound was corrected from "+0.38" to "+0.37" (the measured value is 0.3747).

**Q15. You said a faster preset sometimes beats a slower one. How?**
- **[M]** In BasketballPass, `medium` had a lower frame PSNR than `faster` in 67 of 500 frames (13.4%).
  - In **all 67**, `faster` had spent more bits on that picture.
  - In 59 of them, `faster` coded the picture at a lower slice QP.
  - Overall, `faster` and `medium` used different slice QPs in 138 of 500 pictures, while `medium` and `slower` used identical slice QPs in every picture.
- **[H]** This may be caused by preset-specific MCTF and motion-search settings (faster: MCTFSpeed 4, SearchRange 128). They feed block-importance mapping and GOP-level QP adaptation. This comes from reading the source code; it was not instrumented.

**Q16. How much faster is decoding than encoding?**
- **[M]** At preset medium, encoding took 133–333× longer than decoding (decode timing pass without output).
- **[M]** 1080p decoded at about 134–220 fps, and 240p at about 1,400–3,100 fps, with 8 threads (preset medium).

**Q17. Did you see the quality differences visually?**
- **[U]** BasketballPass frame 133: QP 22 appeared clearest and QP 37 blurriest. This is my own confirmed observation.
- **[M]** The other frames were evaluated with automated metrics: frame PSNR, SSIM-Y, mean and maximum absolute difference, difference maps and a detail-retention ratio.
- **[I]** In enlarged crops, QP 32 loses fine texture and QP 37 smears moving objects. Preset differences (0.24–1.31 dB per frame) are hard to see; medium vs slower is not clearly distinguishable.
- This was **not** a formal subjective test: no BT.500 setup and no MOS.

**Q18. Does PSNR agree with what you see?**
- **[M]** For the large QP steps, PSNR, SSIM and the detail ratio all fall monotonically, consistent with the visible blurring.
- **[I]** For presets, PSNR differences of a few tenths of a dB exist without a clearly visible difference at normal viewing. PSNR is good at ranking large changes but not at telling whether a small change is visible. Perceptual metrics or a subjective test would be needed for that.

---

## D. Cross-platform

**Q19. Are Windows and Linux outputs identical?**
- **[M]** For the 16-frame smoke test (BasketballPass, QP 32, faster, QPA off, 4 threads), the MSVC and GCC builds produced byte-identical bitstreams (SHA256 `5037d075…e1bb`, 10,069 B) and identical reconstructions and PSNR.
- **[M]** The encoder's per-picture log lines are also identical.
- **[I]** This shows identical encoding decisions for this configuration only. Other presets, QPs, thread counts and long sequences were not compared across platforms.

**Q20. Is Linux faster than Windows?**
- I cannot say. The Linux smoke encode took 0.19 s and the Windows one 0.35 s, but these are sub-second runs with different compilers, a WSL2 VM, different days and power states, and one Windows sample. It is not a controlled benchmark.

**Q21. Why WSL2 and not native Linux?**
- It was the practical way to build and test on the same laptop without repartitioning.
- For bitstream correctness it is sufficient.
- For timing it is not a substitute for native Linux. That is a limitation, and it is listed under future work.

---

## E. Research direction

**Q22. What would you do next?**
1. A BD-rate study of the presets over QP 22–37 and more sequences, against a VTM anchor under JVET common test conditions.
2. Controlled timing on native Linux (fixed frequency, CPU affinity, many repeats).
3. Perceptual metrics (VMAF, XPSNR, MS-SSIM) and a small BT.500-style subjective test.
4. **[H]** Connected to my background in neural-network pruning: lightweight learned models that predict encoder decisions such as CU partitioning, to reduce the encoding time of the slower presets while keeping most of their efficiency.

**Q23. What was the most important lesson?**
- To verify every number independently and to label interpretation separately from measurement.
- Two concrete examples:
  - The battery incident was found only because the system monitor was logged.
  - The final audit caught two overstated or imprecise figures before the presentation.
