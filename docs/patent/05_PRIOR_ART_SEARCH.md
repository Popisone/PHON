# Prior Art Search (Preliminary)

Date: 2026-10-30
Status: DRAFT - for attorney review
Related: 01_TECHNICAL_DESCRIPTION.md, 02_CLAIMS_DRAFT.md

---

## CRITICAL: Public Disclosure Timeline

PHON is publicly released on GitHub at https://github.com/Popisone/PHON

Release timeline:
- v0.4.0 released 2026-10-29 (compressor, channel, compress, transmit, REST API, C export, ONNX)
- v0.5.0 released 2026-10-29 (for loops, ONNX Runtime API)
- v0.6.0-docs released 2026-10-30 (this patent documentation)

Intended priority date: 2026-10-30

JURISDICTION ANALYSIS:

United States (USPTO):
- Grace period: 12 months from inventor own disclosure (35 U.S.C. 102(b)(1)(A))
- Status: FILING DEADLINE = 2027-10-29
- Recommendation: viable, must file before 2027-10-29

European Patent Office (EPO):
- Grace period: NONE for inventor own publication (Art. 55 EPC exceptions do NOT cover ordinary publication)
- Status: NOVELTY LIKELY DESTROYED for all matter publicly disclosed 2026-10-29
- Recommendation: NOT viable for the core invention as of 2026-10-29

PCT (Patent Cooperation Treaty):
- Follows national rules for grace period after entering national phase
- Status: depends on designated states

STRATEGY RECOMMENDATION:
1. File USPTO utility application before 2027-10-29
2. Focus claims on novel matter NOT in v0.4.0 / v0.5.0 releases (v0.6+ features)
3. Consider defensive publication strategy for EPO
4. Consider trade secret for future developments

---

## 1. Prior Art Categories

The invention should be compared against prior art in:

1.1 Phononic computing hardware
- Phononic crystal logic gates
- Acoustic wave interference devices
- Surface acoustic wave (SAW) filters and multiplexers

1.2 Design automation for wave-based computing
- Photonic circuit design languages (GDSII, IPKISS, Luceda)
- Phononic / mechanical circuit design tools
- SPICE-like simulators for non-electrical domains

1.3 DSL and compiler design for hardware
- Hardware description languages (Verilog, VHDL, Chisel, MyHDL)
- High-level synthesis (HLS) tools
- Domain-specific languages for analog design

1.4 Machine learning surrogates for physics simulation
- Neural network surrogates for FDTD / FEM
- Gaussian process regression for design space exploration

1.5 Data compression and transmission in wave-based systems
- Photonic data compression
- Acoustic data transmission protocols

---

## 2. Search Keywords

For Google Patents, Espacenet, USPTO Full-Text, WIPO Patentscope:

- phononic computing
- phononic integrated circuit
- acoustic wave logic gate
- phonon interference logic
- surface acoustic wave DSL
- declarative hardware description language
- compiler for wave-based computing
- phononic data compression
- acoustic data transmission
- machine learning surrogate FDTD

---

## 3. Candidate Patents to Check

Table to be filled by attorney during formal search:

| Patent Number | Title | Assignee | Filed | Status |
|---|---|---|---|---|
| US 2020/008976 A1 | (to verify) | (TBD) | (TBD) | (TBD) |
| US 2019/012345 A1 | (to verify) | (TBD) | (TBD) | (TBD) |
| (TBD) | (TBD) | Intel | (TBD) | (TBD) |
| (TBD) | (TBD) | GlobalFoundries | (TBD) | (TBD) |
| (TBD) | (TBD) | imec | (TBD) | (TBD) |

---

## 4. Academic Literature to Check

Recent reviews and papers (2023-2025) on phononic computing:

- Search Google Scholar, arXiv, IEEE Xplore
- Keywords: phononic computing review, acoustic wave computing, phonon logic gate
- Key venues: Nature Photonics, Nature Electronics, Physical Review Applied, IEEE Transactions on Ultrasonics

---

## 5. Novelty Analysis (Preliminary)

What we believe is novel about PHON (subject to prior art search):

A. Three-level declarative DSL (Medium / Components / Flow) for phononic circuits
B. Physics-consistent simulator for logic verification at 24,092x speedup vs FDTD
C. Compression mechanism (freq_out = freq_in / ratio) as first-class language primitive
D. Transmission mechanism (speed = bandwidth * 100 Gbps) as first-class language primitive
E. Machine learning surrogate with R^2 = 1.0000 trained on PHON-generated data
F. Unified pipeline: source -> LALR parser -> JSON -> simulator -> ONNX/C

What is likely NOT novel (publicly disclosed before or widely known):
- Wave interference as a logic primitive (well-known in photonics)
- DSLs for hardware description (many exist)
- ML surrogates for physics simulation (many exist)

Strongest claims are likely A, C, D, and F.

---

## 6. Recommendation

Proposed filing strategy (to be confirmed by attorney):

Primary:
- USPTO utility application before 2027-10-29
- Focus on claims 1, 3, 4, 5, 6, 7 from 02_CLAIMS_DRAFT.md
- Use doctrine of equivalents where possible

Secondary:
- PCT application (reserves options for non-EP jurisdictions)
- Consider Japan, South Korea, China (large semiconductor industries)

EPO:
- NOT recommended at this time (grace period does not apply)
- Alternative: defensive publication to prevent others from patenting

---

## 7. Search Log (for attorney)

| Date | Database | Query | Results | Notes |
|---|---|---|---|---|
| (TBD) | Google Patents | (TBD) | (TBD) | (TBD) |
| (TBD) | Espacenet | (TBD) | (TBD) | (TBD) |
| (TBD) | USPTO Full-Text | (TBD) | (TBD) | (TBD) |
| (TBD) | Google Scholar | (TBD) | (TBD) | (TBD) |

---

## 8. Action Items

1. Attorney to perform formal search (Section 7)
2. Attorney to review Section 5 (novelty analysis)
3. Attorney to confirm filing strategy in Section 6
4. Inventor to provide technical clarifications as needed
5. If EPO is desired despite disclosure, explore:
   - Whether any claimed feature was NOT in the GitHub releases
   - Whether the GitHub repo can be taken private (does NOT restore novelty at EPO)
   - Whether the disclosure was under confidentiality (unlikely - public GitHub)
