# 5-minute version: speaking outline

**Presenter:** Rabab Khan Rongon. Use this if Prof. Kiho asks for a short explanation.

**With slides:** use `VVC_Experimental_Evaluation_Prof_Kiho_5min.pptx` (7 slides). These are slides 1, 6, 8, 10, 11, 12 and 14 of the full deck, renumbered. The full script is in `speaker_notes_5min.md` (about 505 words, 4–5 minutes at a calm pace).

**Without slides:** use the same six points as a verbal answer.

| Time | Slide (5-min deck) | Message, in one sentence | Number to remember |
|---|---|---|---|
| 0:00–0:30 | 1 Title | Who I am and what I did: built VVenC and VVdeC on Windows and Linux, then ran a controlled experiment | — |
| 0:30–1:20 | 2 Design | One factor at a time: QP 22–37 at medium, 5 presets at QP 32; 65 runs, all verified | 65/65 ok; 32/32 repeats identical |
| 1:20–2:00 | 3 QP results | +5 QP roughly halves the bitrate and costs about 1.5–4 dB | ÷2.06 per +5 QP; −1.45 to −3.93 dB |
| 2:00–2:45 | 4 Presets | Slower presets cost much more time for a small gain; this is not BD-rate | slower = 14–17× medium time for +0.24 to +0.37 dB |
| 2:45–3:30 | 5 Visual | Large QP differences are visible; I confirmed BasketballPass frame 133 myself; not a formal subjective test | frame 133: 40.79 → 30.55 dB |
| 3:30–4:10 | 6 Windows vs Linux | Byte-identical bitstream for one 16-frame test; WSL2; no speed claim | 10,069 B, SHA256 `5037d075…` |
| 4:10–5:00 | 7 Conclusion | Next steps: BD-rate, native-Linux timing, perceptual metrics; research idea: small pruned networks for faster encoder decisions | "directions, not results" |

**Three sentences to say even if time is very short:**
1. "QP is the main control: each +5 QP roughly halves the bitrate and costs about 1.5 to 4 dB of PSNR."
2. "Slower presets give only a few tenths of a dB at QP 32, but they need 14 to 17 times the encoding time of medium. To compare preset efficiency properly I would need BD-rate over several QPs."
3. "All 65 runs were verified, repeated runs were byte-identical, and a 16-frame test gave identical bitstreams on Windows and Linux."
