# Prompt Injection Evaluator

A Python framework for evaluating prompt injection vulnerabilities in Large Language Models (LLMs).

## Features

- 🔒 Comprehensive test suite for prompt injection attacks
- 🤖 Support for multiple models via HuggingFace
- 📊 Automated evaluation with detailed reports (PDF & Excel)
- 🎯 Two execution modes: batch (all models) or single model
- 📈 Category and severity-based analysis

## Setup

1. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure models in `config/models.json` and test cases in `config/test_cases.json`

## Usage

### Method 1: Run All Models (Batch Mode)

Evaluate **all models** defined in `config/models.json` in one run:

```bash
python src/main.py
```

This will:
- Load all models from `config/models.json`
- Run all test cases from `config/test_cases.json` on each model
- Generate individual reports for each model
- Create a comparison report across all models
- Save all reports in the `reports/` directory

**Best for**: Comprehensive evaluation and model comparison

### Method 2: Run Single Model (CLI Mode)

Evaluate a **specific model** via command line:

```bash
python src/executor.py <model_name> [optional: test_suite_path]
```

**Examples:**
```bash
# Run gpt2 model with default test suite
python src/executor.py gpt2

# Run distilgpt2 model with default test suite
python src/executor.py distilgpt2

# Run TinyLlama model with custom test suite
python src/executor.py TinyLlama/TinyLlama-1.1B-Chat-v1.0 config/custom_tests.json
```

This will:
- Load only the specified model from `config/models.json`
- Run all test cases (or custom test suite if provided)
- Generate reports for that single model
- Save reports in the `reports/` directory

**Best for**: Quick testing, debugging specific models, or iterative development

### Available Models

Models are configured in `config/models.json`. To see available models, check that file or run:
```bash
python src/executor.py
```
(without arguments to see usage and available models)

Current default models:
- `distilgpt2` - Ultra-light, fastest model
- `gpt2` - Slightly bigger, stable model
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0` - Small chat-style model

## Configuration

### Adding Models

Edit `config/models.json`:
```json
{
  "models": [
    {
      "name": "model-name-on-huggingface",
      "description": "Description of the model",
      "requires_auth": false,
      "torch_dtype": "float16"
    }
  ]
}
```

### Adding Test Cases

Edit `config/test_cases.json` to add new test cases:
```json
{
  "id": "PI-XXX",
  "name": "Test Name",
  "category": "category_name",
  "description": "What this test evaluates",
  "system_prompt": "System instructions",
  "user_prompt": "User prompt with injection attempt",
  "expected_behavior": "what_should_happen",
  "severity": "critical|high|medium|low"
}
```

## Project Structure

```
prompt-injection-evaluator/
├── config/
│   ├── models.json           # Model configurations
│   └── test_cases.json       # Test suite definitions
├── src/
│   ├── main.py               # Entry point for batch mode (all models)
│   ├── executor.py           # Execution logic + CLI mode entry point
│   ├── evaluator.py          # Evaluation logic
│   ├── model_factory.py      # Model loading
│   ├── model_inference.py    # Model inference wrapper
│   ├── report_generator.py   # Report generation (PDF/Excel)
│   └── test_suite_loader.py  # Test case loader
├── tests/                     # Unit tests
├── reports/                   # Generated evaluation reports (auto-created)
├── requirements.txt           # Project dependencies
└── README.md                  # This file
```

## Reports

Reports are automatically generated in the `reports/` directory with timestamps:

- **Individual Model Reports**: `{model_name}_{timestamp}.pdf` and `.xlsx`
- **Comparison Report**: `comparison_report_{timestamp}.pdf` and `.xlsx`

Reports include:
- Test results for each injection attempt
- Pass/fail status with explanations
- Category and severity breakdowns
- Performance statistics
- Model comparison charts (in comparison report)

## Development

Run tests:
```bash
python -m pytest tests/ -v
```

Run with coverage:
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Categories

- `system_prompt_override` - Attempts to override system instructions
- `secret_extraction` - Data exfiltration attempts
- `jailbreak` - Bypassing content policies
- `indirect_injection` - Injection through user content
- `role_confusion` - Role/identity manipulation
- `delimiter_attack` - Special delimiter exploitation

## Severity Levels

- 🔴 **Critical**: Immediate security threat (secret exposure, full jailbreak)
- 🟠 **High**: Significant policy violation
- 🟡 **Medium**: Moderate security concern
- 🟢 **Low**: Minor issue or edge case

## License

MIT
