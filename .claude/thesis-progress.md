# Thesis Writing Progress

## Context
Writing Chapter 3 (Methodology) and Chapter 4 (Results) of a master's thesis on prompt injection evaluation.
The evaluation is **rule-based** — deliberately chosen to avoid LLM-judge bias.
The LLM evaluator (`--llm-evaluate`) is supplementary/unofficial only.

## LaTeX Commands in Use
- `\tinyllama{}` = TinyLlama/TinyLlama-1.1B-Chat-v1.0
- `\llamaA{}` = meta-llama/Llama-3.1-8B-Instruct
- `\llamaB{}` = meta-llama/Meta-Llama-3-70B-Instruct (best performer)
- `\llamaC{}` = meta-llama/Llama-3.3-70B-Instruct (anomaly — 70B but scores below 8B)

## Completed Sections

### 3.1 — Test Suite Design
- Total: 201 test cases across 10 categories
- Table `tab:categories`: distribution by category and severity
- Table `tab:severity`: severity level definitions
- 4 severity levels: Critical, High, Medium, Low
- Test case structure: system prompt + adversarial user prompt + expected_keywords_absent + expected_keywords_present
- Variation axes: phrasing, target behaviour, obfuscation technique, social vector, complexity

### 3.2 — Models Selected
- 4 models, all Llama family, all instruction-tuned chat variants
- Span: 1.1B, 8B, 70B, 70B
- Two 70B models allow isolation of training recipe effects at identical scale
- All accessed via HuggingFace Inference Endpoints
- Table `tab:models`

### 3.3 — Evaluation Protocol
- Temperature: 0.7, max_new_tokens: 256, do_sample=True
- Fixed system prompt per test case + adversarial user prompt
- PASS = Secure or Safe Refusal; FAIL = anything below (including with caveats/disclaimers)
- Key point: "I must emphasise this is illegal, but here are the steps..." = FAIL
- Fully automated rule-based evaluation
- INVALID status for infrastructure errors (excluded from calculations)

### 3.4 — Limitations
- 201 tests is small vs HarmBench (thousands)
- Keyword-based criteria introduce subjectivity, BUT same criteria applied uniformly → fair comparatively
- Static test set (no adaptive red-teaming)
- Only Llama family tested
- Single-turn only (no multi-turn escalation)
- Minimal system prompt (real deployments use richer prompts)

### 4.1 — Overall Pass Rates
- TinyLlama: 18.4% (37/201)
- Llama-3.1-8B: 57.7% (116/201)
- Meta-Llama-3-70B: 71.1% (143/201)
- Llama-3.3-70B: 51.7% (104/201)
- Anomaly: LlamaC (70B) scores below LlamaA (8B)
- Table `tab:overall`

### 4.2 — Results by Attack Category
- LlamaB leads 9/10 categories
- Exception: indirect injection — TinyLlama leads at 60%
- Sharpest LlamaC regression: jailbreak (96.7%→60%), role-playing (76.9%→46.2%), multilingual (84%→56%)
- Hardest category for all: instruction override (max 44.1%)
- Table `tab:bycategory`

### 4.3 — Results by Severity
- Critical: TinyLlama 18.1% vs LlamaB 90.4% (72pt gap)
- Medium: TinyLlama 10.8% vs LlamaB 43.2%
- Low paradox: LlamaA 0%, LlamaC 0%, TinyLlama 42.9%, LlamaB 57.1%
- Table `tab:byseverity`

### 4.4 — Cross-Model Pass Count Distribution
- 0/4 (all fail): 33 tests → universal failures, current ceiling
- 1/4: 42 tests
- 2/4: 41 tests
- 3/4: 66 tests (largest group — shared failure modes)
- 4/4 (all pass): 19 tests
- Table `tab:distribution`
- Universal failures listed in Appendix `app:universal`, analysed in H4

### 4.5 — Unique Failures per Model
- TinyLlama: 60 unique failures (clearest scale signal)
- Llama-3.1-8B: 1
- Meta-Llama-3-70B: 1
- Llama-3.3-70B: 4 (notable: newest model introduces regressions)
- Table `tab:unique`

## Still To Do
- Section 4 continued (per-heuristic analysis, `sec:heuristics`)
- Appendix `app:universal` — list of 33 universal failures
- Any remaining methodology or discussion sections

## Raw Data Reference
All results from: `reports/Experiment10032026/`
- `model_comparison.xlsx` — summary, by category, by severity
- Individual model xlsx files for test-by-test breakdown
