# Prompt Injection Evaluator — Project Context

## What It Is
A research tool for evaluating LLM models against **prompt injection attacks** — adversarial inputs designed to hijack a model's behaviour. The goal is to measure how resistant different LLMs are to these attacks, producing quantitative, comparable results.

## Design Decision: Rule-Based Evaluation
The core evaluator is **rule-based** (`multi_tier_evaluator.py`), deliberately chosen to avoid introducing **LLM-judge bias**. Using another LLM to judge whether a model was compromised would risk subjective, inconsistent, or self-serving results. Rule-based evaluation ensures deterministic, reproducible, and impartial scoring.

The optional `--llm-evaluate` flag (local Llama or OpenAI backend) exists purely as a **secondary cross-check** — it is not part of the official evaluation procedure.

## Core Workflow

### Step 1 — Collect (`--model`)
- Sends 192 test cases to the target LLM via HuggingFace Inference Endpoint
- Saves raw responses to `responses/<model_name>.xlsx`
- Expensive (cloud API calls) — run once

### Step 2 — Evaluate (`--evaluate`)
- Runs the **rule-based** multi-tier evaluator over saved responses
- Free and re-runnable without querying the model again
- Outputs per-model **PDF + Excel** reports to `reports/`

### Step 3 — Compare (`generate_comparison.py`)
- Aggregates individual model reports into a side-by-side comparison
- Outputs `reports/model_comparison.pdf` and `reports/model_comparison.xlsx`

## Test Suite
- **192 test cases** in `config/prompt_cases/` (JSON files)
- Attack categories: authority impersonation, hijacking, jailbreak, multilingual, and others
- Each test scored **PASS** (model resisted) or **FAIL** (model was compromised)

## Model Support
- HuggingFace Inference Endpoints (requires `HUGGINGFACE_TOKEN` in `.env`)
- Configured via `config/models.json`

## Project Structure
```
prompt-injection-evaluator/
├── config/
│   ├── models.json               # Model configurations
│   └── prompt_cases/             # 192 test cases (JSON)
├── src/
│   ├── main.py                   # Entry point (Steps 1 & 2)
│   ├── response_collector.py     # Queries models, saves responses
│   ├── multi_tier_evaluator.py   # Rule-based evaluator (official)
│   ├── llm_evaluator.py          # LLM-based evaluator (unofficial, cross-check only)
│   ├── report_generator.py       # PDF/Excel report generation
│   └── ...
├── generate_comparison.py        # Step 3: multi-model comparison
├── responses/                    # Raw model responses (.xlsx)
└── reports/                      # Evaluation reports (PDF + Excel)
```

## Key Principle
> Rule-based evaluation was chosen intentionally to keep scoring **objective, deterministic, and free from LLM-judge bias**. The LLM evaluator is supplementary only.
