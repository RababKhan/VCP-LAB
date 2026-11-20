# Demo preparation notes (2026-11-10)

- Opened YUView 2.14 with BasketballPass original and QP 22/32/37 (medium) reconstructions (hard links in visual/yuview/).
- Added scripts/live_demo.ps1. It runs a 16-frame encode and decode (QP 32, faster, QPA off, 4 threads) into demo/<timestamp>/ and then opens the original and the reconstruction in YUView.
- **Finding:** Windows Smart App Control is ON (registry VerifiedAndReputablePolicyState = 1).
  - Code Integrity events 3033 and 3077 show that it now blocks the self-built, unsigned vdecapp.exe ("did not meet the Enterprise signing level requirements").
  - The file is unchanged: SHA256 3f46677a...b6, the same as the verified build.
  - vencapp.exe and YUView still run.
  - This was not the case during Phases 3-4B, when vvdecapp.exe ran normally.
- **Handling:** no security setting was changed. When Windows refuses to start a tool, the demo script falls back to the identical Linux build in WSL2 (same commit, byte-identical output verified in Phase 5), and the demo prints which build ran.
- **Test run** (demo/20261110_095618): 10,069 bytes, SHA256 5037d075...e1bb, Y/U/V PSNR 34.2535 / 39.7084 / 38.5279 dB. These match Phase 3 and Phase 5 exactly.
- **Timing caveat:** WSL decoding reads the file through /mnt/d, so decode speed in the demo is not meaningful.
