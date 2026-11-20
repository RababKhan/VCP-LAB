# Demo: Windows / Linux bit-exact verification (slide 9)

Generated 2026-11-15 11:24:18 by professor_demo/demo_crossplatform.py. Only saved experiment files were read; nothing in results/, logs/, out/ or presentation/ was changed.

**Result: 25 checks, 25 match, 0 different**

## What 'bit-exact' means

The same encoder source code (VVenC 1.14.0 / VVdeC 3.2.1) was compiled twice: with MSVC 19.44 on Windows and with  
GCC 13.3 on Linux (WSL2 Ubuntu 24.04). The same input and settings were encoded on both. 'Bit-exact' means the two  
output files are identical in every bit, so their SHA-256 fingerprints are identical. Same bitstream -> same decoded  
video -> same PSNR. Encoding SPEED was not compared, because Linux ran inside WSL2.  

## The 8 reported Windows/Linux comparisons - SHA-256 recalculated now from the saved files

1. BasketballPass QP24 slow, 500 frames (run A018)  
   Windows bitstream out/phase2/A018_BasketballPass_QP24_slow.266: 4c5741f69eb3b3dccfa9839ce9b4ddf4a8eca0cdc8d1d52dc225b8c3ed1d4c0c  
   Linux   bitstream out/linux2/A018_BasketballPass_QP24_slow_linux.266: 4c5741f69eb3b3dccfa9839ce9b4ddf4a8eca0cdc8d1d52dc225b8c3ed1d4c0c  
   Decoded YUV (recorded hashes (Linux decoded file is on the WSL disk)): Windows 4c8de67a294def0d... Linux 4c8de67a294def0d...  
2. BasketballPass QP39 faster, 500 frames (run A020)  
   Windows bitstream out/phase2/A020_BasketballPass_QP39_faster.266: 71248828a91ce6e799832c3fb6337b4a3a94a1709e09daca04a11c7bd380aeb3  
   Linux   bitstream out/linux2/A020_BasketballPass_QP39_faster_linux.266: 71248828a91ce6e799832c3fb6337b4a3a94a1709e09daca04a11c7bd380aeb3  
   Decoded YUV (recorded hashes (Linux decoded file is on the WSL disk)): Windows a6c6a441e95f19d6... Linux a6c6a441e95f19d6...  
3. BlowingBubbles QP29 slow, 500 frames (run A021)  
   Windows bitstream out/phase2/A021_BlowingBubbles_QP29_slow.266: 3a3e314c34a2ee61d81704d15bc4937e392ada31949a02707cdf2ef925180e8e  
   Linux   bitstream out/linux2/A021_BlowingBubbles_QP29_slow_linux.266: 3a3e314c34a2ee61d81704d15bc4937e392ada31949a02707cdf2ef925180e8e  
   Decoded YUV (recorded hashes (Linux decoded file is on the WSL disk)): Windows b04f7eba8de9fe68... Linux b04f7eba8de9fe68...  
4. BQMall QP34 faster, 600 frames (run A025)  
   Windows bitstream out/phase2/A025_BQMall_QP34_faster.266: 9b9ff9cca141a96dccd40305f6566665706badd1bb6bc76d588478ded95d0c51  
   Linux   bitstream out/linux2/A025_BQMall_QP34_faster_linux.266: 9b9ff9cca141a96dccd40305f6566665706badd1bb6bc76d588478ded95d0c51  
   Decoded YUV (recorded hashes (Linux decoded file is on the WSL disk)): Windows 4ad809bae7395dbf... Linux 4ad809bae7395dbf...  
5. BasketballDrive QP39 faster, 500 frames (run B019)  
   Windows bitstream out/phase2/B019_BasketballDrive_QP39_faster.266: 220fcf5564bd0cbc34a26c4c15beb56e50a1891a27929f188bf6f5affabe1c4c  
   Linux   bitstream out/linux2/B019_BasketballDrive_QP39_faster_linux.266: 220fcf5564bd0cbc34a26c4c15beb56e50a1891a27929f188bf6f5affabe1c4c  
   Decoded YUV (recorded hashes (Linux decoded file is on the WSL disk)): Windows 9457e345ed5dc8a1... Linux 9457e345ed5dc8a1...  
6. BlowingBubbles QP 34 fast, 500 frames (run R04)  
   Windows bitstream out/R04_BlowingBubbles_QP34_fast.266: 393e733fd15e0178055b2dc5e8ebc79027f973b56c81fa06e4f8203d788e54d7  
   Linux   bitstream out/linux/R04_BlowingBubbles_QP34_fast_linux.266: 393e733fd15e0178055b2dc5e8ebc79027f973b56c81fa06e4f8203d788e54d7  
   Decoded YUV (both files hashed now): Windows 405648edea2cf744... Linux 405648edea2cf744...  
7. BQMall QP 29 medium, 600 frames (run R15)  
   Windows bitstream out/R15_BQMall_QP29_medium.266: 7c34ef2211c1235826b54c31571eb5d4bd14a07f318176d26e953ac069281122  
   Linux   bitstream out/linux/R15_BQMall_QP29_medium_linux.266: 7c34ef2211c1235826b54c31571eb5d4bd14a07f318176d26e953ac069281122  
   Decoded YUV (both files hashed now): Windows e5fbf487fdce407c... Linux e5fbf487fdce407c...  
8. BlowingBubbles QP34 fast, 16 frames (smoke test)  
   Windows bitstream out/smoke/smoke_Windows_QP34_fast_f16.266: b6cf96c3d9b01c3c533d2328c619b632fcfe2acc9c0aa31a3b789c69510cbcfc  
   Linux   bitstream out/smoke/smoke_Linux_QP34_fast_f16.266: b6cf96c3d9b01c3c533d2328c619b632fcfe2acc9c0aa31a3b789c69510cbcfc  
   Decoded YUV (both files hashed now): Windows 18fa60ceb58daa0c... Linux 18fa60ceb58daa0c...  

| # | configuration | Windows SHA-256 | Linux SHA-256 | bitstream identical | decoded identical |
|---|---|---|---|---|---|
| 1 | BasketballPass QP24 slow, 500 frames (run A018) | 4c5741f69eb3b3dc... | 4c5741f69eb3b3dc... | yes | yes |
| 2 | BasketballPass QP39 faster, 500 frames (run A020) | 71248828a91ce6e7... | 71248828a91ce6e7... | yes | yes |
| 3 | BlowingBubbles QP29 slow, 500 frames (run A021) | 3a3e314c34a2ee61... | 3a3e314c34a2ee61... | yes | yes |
| 4 | BQMall QP34 faster, 600 frames (run A025) | 9b9ff9cca141a96d... | 9b9ff9cca141a96d... | yes | yes |
| 5 | BasketballDrive QP39 faster, 500 frames (run B019) | 220fcf5564bd0cbc... | 220fcf5564bd0cbc... | yes | yes |
| 6 | BlowingBubbles QP 34 fast, 500 frames (run R04) | 393e733fd15e0178... | 393e733fd15e0178... | yes | yes |
| 7 | BQMall QP 29 medium, 600 frames (run R15) | 7c34ef2211c12358... | 7c34ef2211c12358... | yes | yes |
| 8 | BlowingBubbles QP34 fast, 16 frames (smoke test) | b6cf96c3d9b01c3c... | b6cf96c3d9b01c3c... | yes | yes |

**[MATCH]** all 8 reported comparisons are bit-exact  
The 5 phase-6 runs were also compared on frames, Y/U/V PSNR and 16 encoder parameter lines (all equal, recorded in  
results/crossplatform_v2.json). Only these 8 configurations were compared across platforms - not all 64.  

## Today's extra example (NOT one of the 8 reported checks)

Demo run 20261115_112342_full: encoder engine = Linux (WSL2); reproduction of original Windows run A029.  
   today  : 7f4bc4133fa9240ed5c0663f29659af367d7e6dad60215a0390cf6d3f255aa5a  
   original Windows run: 7f4bc4133fa9240ed5c0663f29659af367d7e6dad60215a0390cf6d3f255aa5a  
   (shown for information; it does not change the reported 8/8)  
