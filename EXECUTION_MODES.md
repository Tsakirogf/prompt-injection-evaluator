# Execution Modes - Quick Reference

## Two Ways to Run the Evaluator

### 1. Batch Mode (All Models)
**Command:** `python src/main.py`

**What it does:**
- Loads ALL models from `config/models.json`
- Runs all test cases on each model
- Generates individual reports per model
- Creates a comparison report
- Best for: Full evaluation and model comparison

**Example output structure:**
```
reports/
├── distilgpt2_2026-01-24_143022.pdf
├── distilgpt2_2026-01-24_143022.xlsx
├── gpt2_2026-01-24_143055.pdf
├── gpt2_2026-01-24_143055.xlsx
├── TinyLlama_TinyLlama-1.1B-Chat-v1.0_2026-01-24_143130.pdf
├── TinyLlama_TinyLlama-1.1B-Chat-v1.0_2026-01-24_143130.xlsx
├── comparison_report_2026-01-24_143145.pdf
└── comparison_report_2026-01-24_143145.xlsx
```

---

### 2. CLI Mode (Single Model)
**Command:** `python src/executor.py <model_name> [optional_test_suite]`

**What it does:**
- Loads ONLY the specified model
- Runs test cases from default or custom test suite
- Generates reports for that single model only
- Best for: Quick testing, debugging, iterative development

**Examples:**
```bash
# Basic usage - run gpt2 with default test suite
python src/executor.py gpt2

# Run distilgpt2 with default test suite
python src/executor.py distilgpt2

# Run with custom test suite
python src/executor.py gpt2 config/custom_tests.json

# Run TinyLlama (note: use exact name from models.json)
python src/executor.py TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

**Example output structure:**
```
reports/
├── gpt2_2026-01-24_143022.pdf
└── gpt2_2026-01-24_143022.xlsx
```

---

## Implementation Details

### Changes Made:

1. **src/main.py**
   - Entry point for batch mode
   - Calls `run_all_models()` from executor

2. **src/executor.py**
   - Renamed `run_evaluator()` → `run_all_models()` (batch mode)
   - Added `run_single_model(model_name, test_suite_path)` (CLI mode)
   - Added `__main__` block for CLI argument parsing
   - Shows usage help when run without arguments

3. **README.md**
   - Comprehensive documentation for both modes
   - Clear examples and use cases
   - Configuration instructions
   - Project structure overview

### Usage Help:

Run without arguments to see help:
```bash
python src/executor.py
```

Output:
```
Usage: python executor.py <model_name> [test_suite_path]

Example:
  python executor.py gpt2
  python executor.py gpt2 config/test_cases.json

To run all models, use: python main.py
```

---

## Model Configuration

Models must be defined in `config/models.json`. Available models:
- `distilgpt2`
- `gpt2`
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0`

To add more models, edit `config/models.json`:
```json
{
  "models": [
    {
      "name": "model-id-from-huggingface",
      "description": "Model description",
      "requires_auth": false,
      "torch_dtype": "float16"
    }
  ]
}
```

---

## Test Suite Configuration

Default: `config/test_cases.json`

Custom test suites can be provided via CLI:
```bash
python src/executor.py gpt2 path/to/custom_tests.json
```

Test suite must follow the same JSON structure as `config/test_cases.json`.
