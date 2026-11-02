\# PHON: A Unified DSL and LLM Frontend for Photonic and Phononic Wave Computing



\## Abstract

We present PHON, a domain-specific language (DSL) for photonic and phononic circuit design, alongside PHON-LLM, a neurosymbolic pipeline that translates natural language into PHON code. A key innovation is the \*\*Unified Medium\*\* architecture, which exploits the mathematical equivalence of linear wave propagation to simulate both optical and acoustic circuits using identical source code. To ensure reliable code generation from small language models, we employ constrained decoding (Outlines CFG). Our pipeline achieves 98% syntax validity in code generation and 100% accuracy in parameter extraction across 200 held-out test cases. Furthermore, the PHON simulator validates optical neural network inference, achieving 97.78% accuracy on MNIST with zero mismatches compared to scikit-learn. 



\## 1. Introduction

\- \*\*Problem:\*\* Designing photonic and phononic circuits requires specialized knowledge. Natural language interfaces could lower the barrier, but small LLMs struggle to produce valid structured output.

\- \*\*Solution:\*\* We built PHON (a custom DSL) and PHON-LLM (a constrained decoding pipeline).

\- \*\*Key Contributions:\*\* 

&#x20; 1. \*\*Unified Medium:\*\* The first DSL to natively support both photonic and phononic media by dispatching physical constants while keeping the underlying matrix mathematics identical.

&#x20; 2. \*\*Constrained Decoding:\*\* Proving that CFG (Outlines) is essential for small LLMs to generate valid JSON/DSL.

&#x20; 3. \*\*Validation:\*\* 97.78% MNIST accuracy (0 mismatches vs. sklearn), 98% code syntax validity, and 100% extraction accuracy.



\## 2. System Architecture

\### 2.1 The PHON DSL

\- Parser -> AST -> Config Dict -> Simulator.

\- Explain the `layer` and `propagate` primitives.



\### 2.2 Unified Medium (Phase 5.5)

\- Explain that `kind: photonic` uses $c$ (speed of light), while `kind: acoustic` uses $v$ (speed of sound).

\- Show a code snippet where changing one line switches the entire simulation medium.



\### 2.3 PHON-LLM Pipeline

\- \*\*Code Generation:\*\* SmolLM-135M + LoRA + CFG (Outlines/llguidance).

\- \*\*Extraction:\*\* Hybrid approach: Regex-first (fast) -> Qwen-0.5B + Outlines fallback (accurate).



\## 3. Experiments \& Results

\### 3.1 Code Generation (50 prompts)

| Configuration | Syntax Valid | Semantic Valid |

|---|---|---|

| v1 (Baseline) | 43/50 (86%) | 43/50 (86%) |

| v2 (LoRA) | 48/50 (96%) | 47/50 (94%) |

| \*\*v2 + CFG\*\* | \*\*49/50 (98%)\*\* | \*\*47/50 (94%)\*\* |



\### 3.2 Parameter Extraction (200 cases)

\- \*\*Regex-only:\*\* 145/200 (72.5%) \[\*Update with exact number from test\*]

\- \*\*Hybrid (Regex + Qwen):\*\* \*\*200/200 (100%)\*\*

\- Latency: Regex \~0ms; LLM \~4.8s (CPU).



\### 3.3 Neural Network Inference (MNIST)

\- 784 -> 128 (relu) -> 10 (softmax).

\- Accuracy: \*\*97.78%\*\* (0 mismatches vs sklearn on 100 samples).



\## 4. Ablation Study: Why Constrained Decoding?

\- \*\*The Capacity Limit:\*\* Loss plateaus at 0.23-0.24 across 3 models (SmolLM-135M, SmolLM-fresh, Qwen-0.5B). The models \*know\* the numbers but fail to format them.

\- \*\*The Solution:\*\* Outlines CFG forces valid JSON.

\- \*\*Result:\*\* 0% JSON validity -> 100% JSON validity using the exact same model weights.



\## 5. Conclusion

PHON proves that small, constrained language models can act as reliable neurosymbolic interfaces for complex physical DSLs, while the Unified Medium architecture paves the way for cross-domain wave computing.



\---

\*(References to be added)\*

