# Figures (to be drawn by a patent illustrator)

**FIG. 1 — System architecture.** Three horizontal layers: Medium (silicon / LiNbO3 with temperature annotation), Components (five boxes: resonator, waveguide, detector, compressor, channel), Flow (six arrows: emit, interfere, capture, compress, transmit, for-loop). Arrows point downward from Flow to Components to Medium.

**FIG. 2 — Compiler pipeline.** Left-to-right flow: Source file `.phon` -> Lexer (token stream icon) -> Parser LALR (tree icon) -> Semantic analyzer (magnifier + checkmark) -> Emitter (curly-brace icon JSON) -> Simulator (wave icon) -> Output vector.

**FIG. 3 — Physics of interference.** Two amplitude vectors A1, A2 originating from a common point, with angle delta_phi = phi1 - phi2 between them. A dashed resultant vector of magnitude sqrt(A1^2 + A2^2 + 2*A1*A2*cos(delta_phi)). Two inset plots: (a) delta_phi = 0, showing constructive sum; (b) delta_phi = pi, showing cancellation.

**FIG. 4 — Compression mechanism.** A block labeled "Compressor (ratio R)" with input arrow labeled "freq_in" and output arrow labeled "freq_out = freq_in / R". Below: two frequency-domain magnitude plots, before (peak at freq_in) and after (peak at freq_in / R).

**FIG. 5 — Transmission mechanism.** A block labeled "Channel (bandwidth B GHz)" with input pulse and output pulse train. Annotated: "speed = B * 100 Gbps". Below: a time-domain plot of pulses with rate labeled.

**FIG. 6 — ML surrogate pipeline.** Five boxes connected left-to-right: "PHON simulator (N samples)" -> "Feature engineering" -> "Random Forest training" -> "ONNX export" -> three parallel deployment boxes: "REST API (FastAPI)", "C header (MCU)", "ONNX Runtime (C#/Web)".

**FIG. 7 — Performance comparison.** Bar chart on log scale. Three bars: "FDTD 697 ms/run", "PHON (cached) 0.029 ms/run", "ML inference 1.55 us/batch". Annotations: "24,092x" over FDTD bar, "321x" over PHON bar.

**FIG. 8 — Register8 example.** Eight resonator circles labeled r0..r7 (top row), eight parallel waveguides labeled bus0..bus7 (middle row), eight detector squares labeled d0..d7 (bottom row). An arrow labeled "capture 0xB5" enters from the left, and an arrow labeled "read back 0xB5" exits to the right.
