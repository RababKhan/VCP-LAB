# Verification checklist: expanded experiment (v2)

**Status (2026-11-11):**
- **Done:** phases 1–7.
  - Audit: 614 checks, all passed.
  - 64/64 configurations and 94 encoder runs.
  - BD-rate, timing reliability, visual metrics, 8/8 Windows = Linux checks.
  - 10-slide deck.
- **Who did it:** Claude (AI assistant), with automated scripts. Details: `results/EXPERIMENT_REPORT_v2.md`.
- **Personally verified by Sadab:** nothing yet.

## Automated checks (done, evidence in `logs/` and `results/`)
- [x] Input SHA-256 for all 4 sequences matches the provided files (`logs/00_setup_provenance.log`)
- [x] Phase-1 audit: 614/614 checks (`results/audit_phase1.json`)
- [x] 64/64 configurations measured
- [x] 93 runs OK, 1 flagged (B022, battery during the run; re-timed as C001), 0 failed
- [x] Independent PSNR = encoder PSNR in all runs (max difference 0.0000 dB); frame counts correct
- [x] Repeated encodes give identical bitstreams (all repeated configurations)
- [x] BD-rate passes all validity checks (4 points, monotonic, overlap ≥ 93 %); PCHIP and polynomial agree within 0.14 %
- [x] SSIM implementation matches scikit-image (4/4 sequences)
- [x] Windows = Linux bit-exact in 8/8 configurations (bitstream, decoded video, frames, PSNR, 16 parameter lines)
- [x] The 45 % timing gap was investigated: early-run slow state; phase-2 repeats CV 0.2–2.7 %

## Must be done by Sadab before presenting
- [ ] **YUView inspection:**
  - Open the files in `visual/yuview/` with `tools/YUView/YUView.exe`.
  - Check the format in Properties.
  - Look at BasketballDrive frame 98, and at least one other sequence.
  - Frame numbers and crop areas: `visual/v2/selection.json`.
- [ ] Take 2–4 YUView screenshots into `visual/yuview_screenshots/`.
- [ ] Write his own one- or two-sentence observation on slide 8 and in its notes (replace `[Sadab: …]`).
- [ ] Re-run at least one configuration himself and compare its SHA-256 with `results/results_all_runs.csv`.
- [ ] Understand and be able to explain:
  - BD-rate (method, anchor, why same-QP comparison is not enough)
  - timing reliability (R04 story)
  - the limitations
- [ ] Decide how to tell Prof. Choi that the runs were executed with an AI assistant. The deck already states it on slide 1.

## Practical
- [ ] **Licensed PowerPoint:** open `presentation/VVC_Assignment_Sadab_Khan_Prangon_v2_10slides.pptx` in a licensed PowerPoint and check all 10 slides.
  - The native charts on slides 5–7 could not be rendered on this computer ("Unlicensed Product").
  - The layout was checked with a wireframe render; the file passed the validator.
- [ ] **Fonts:** install Roboto Slab and Source Sans Pro on the presenting computer.
- [ ] **Rehearse:** use `presentation/speaker_notes_v2_10slides.md` (about 1,130 words, about 7–8 minutes).
- [ ] **Disk:** D: has about 6 GB free. These files are regenerable from the bitstreams and can be deleted only if you approve:
  - `out/phase2/_scratch_*` (3.6 GB)
  - `out/phase2/_visual_*` (11.6 GB; needed for the BasketballDrive YUView check)

## Known limitations to state if asked
- One laptop (hybrid CPU, Balanced plan): times are relative. CPU temperature was not recordable.
- One sequence each at 832×480 and 1080p: the resolution trend cannot be separated from content.
- QPs 24/29/34/39 are not the CTC set; the BD-rate anchor is medium, not VTM.
- Visual results are metrics plus script renderings; no subjective test.
- 7 Windows VVenC unit tests were blocked (Smart App Control); VVdeC conformance tests were not run.
