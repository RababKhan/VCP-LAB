# Visual quality evaluation: summary

**VVenC 1.14.0 / VVdeC 3.2.1, random access, QPA off, 8 threads.** Sequences: BasketballPass (416×240) and BQMall (832×480). Six frames were chosen by fixed rules: the first IDR picture, a typical frame, and the worst frame at QP 37. Each was compared at full-frame size and as an enlarged crop of the same region, with luma difference maps on a fixed scale.

**QP (preset medium, QP 22 / 32 / 37)**
- **Rate:** the bitstream shrinks 8.2–8.6× from QP 22 to QP 37.
- **Quality:** frame Y-PSNR drops 7.9–10.2 dB, and SSIM-Y drops from 0.965–0.989 to 0.780–0.929.
- **Detail:** high-frequency detail falls to 39–70% of the original.
- **Visible artefacts:** loss of texture and thin structures at QP 32. At QP 37, strong blurring and smearing of moving objects (ball, lettering, people) and blurred faces. Moving content degrades much more than intra pictures, which is consistent with hierarchical slice QPs. For `-q 32` the IDR picture is coded at slice QP 27 (BasketballPass) or 29 (BQMall), and the top temporal layer at QP 41–42.
- **Observer confirmation:** the observer confirmed this for BasketballPass frame 133 (QP 22 clearest, QP 37 blurriest). The other visual statements come from an automated analysis with image inspection and have not been confirmed by an observer.

**Preset (QP 32: faster / medium / slower)**
- **Sequence level** (BasketballPass / BQMall):
  - **faster → slower:** +0.84 / +0.98 dB Y-PSNR, 13.1% / 14.6% fewer bytes.
  - **medium → slower:** +0.37 / +0.33 dB, 2.2% / 4.3% fewer bytes.
  - Both are sequence-level values. The Phase 4B figure "+0.24 to +0.37 dB" (originally written as +0.38, corrected in the audit) is medium → slower over all four sequences.
- **Frame level** (six selected frames, faster → slower): 0.24–1.31 dB. In the enlarged crops they are only noticeable for `faster` in motion regions. Medium vs slower (0.15–0.59 dB) is not clearly distinguishable.
- **Slower is not always better per frame.** Medium is below faster in 13.4% of BasketballPass frames. In **every** such case the faster preset spent more bits on that picture, mostly because it coded the picture at a lower slice QP.
- **Why the slice QP differs (hypothesis from reading the source code; not verified at run time):** with QPA off, VVenC still enables GOP-wise QP adaptation and block-importance QP offsets derived from MCTF, and `faster` uses different MCTF and motion-search settings. **[measured]** Medium and slower share those settings and had identical slice QPs in every picture.

**Takeaway**
- Large PSNR differences (QP) are clearly visible.
- Preset differences at a fixed QP are mostly numerical and are better judged by rate–distortion (bits and PSNR together) than by eye.
- The fair way to compare presets is BD-rate over several QPs.

**Limitations**
- There was no formal subjective test (no BT.500 setup, no MOS).
- The images were enlarged still frames, so temporal artefacts were not assessed.
- SSIM is a simplified 8×8-window version.
- Colour was displayed assuming BT.709.
