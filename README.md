# Prompt Injection Evaluator

Test LLM models for prompt injection vulnerabilities.

## Quick Start

### Step 1: Collect Responses
Run test suite against your model and save responses:

```bash
python src/main.py --model "meta-llama/Llama-3.1-8B-Instruct"
```

Output: `responses/meta-llama_Llama-3.1-8B-Instruct.xlsx`

### Step 2: Evaluate Responses
Evaluate the collected responses and generate reports:

```bash
python src/main.py --evaluate responses/meta-llama_Llama-3.1-8B-Instruct.xlsx
```

Output:
- `reports/meta-llama_Llama-3.1-8B-Instruct_multi_tier.pdf`
- `reports/meta-llama_Llama-3.1-8B-Instruct_multi_tier.xlsx`

### Or Do Both at Once

```bash
python src/main.py --model "meta-llama/Llama-3.1-8B-Instruct" --evaluate
```

### Step 3: Generate Model Comparison Report

Compare multiple evaluated models side-by-side:

#### Option A: Compare ALL models in reports/ directory
```bash
python generate_comparison.py
```

This will automatically find and compare all `.xlsx` files in the `reports/` directory (excluding response files and previous comparison reports).

#### Option B: Compare specific models only
```bash
python generate_comparison.py --models "meta-llama/Llama-3.1-8B-Instruct" "meta-llama/Meta-Llama-3-70B-Instruct"
```

#### Option C: Specify custom output directory
```bash
python generate_comparison.py --output custom_reports/
```

**Output Files:**
- `reports/model_comparison.pdf` - Visual comparison report with tables and charts
- `reports/model_comparison.xlsx` - Detailed comparison data in Excel format

**Example Console Output:**
```
GENERATING MODEL COMPARISON REPORT
======================================================================

Found 5 model evaluation reports:
  - distilgpt2
  - gpt2
  - meta-llama_Llama-3.1-8B-Instruct
  - meta-llama_Meta-Llama-3-70B-Instruct
  - gpt-oss-20b-exj

Loading evaluation results...
  Loading distilgpt2.xlsx... OK (27/192 passed)
  Loading gpt2.xlsx... OK (34/192 passed)
  Loading meta-llama_Llama-3.1-8B-Instruct.xlsx... OK (92/192 passed)
  Loading meta-llama_Meta-Llama-3-70B-Instruct.xlsx... OK (121/192 passed)
  Loading gpt-oss-20b-exj.xlsx... OK (0/153 passed)

======================================================================
COMPARISON SUMMARY
======================================================================

Model                                               Pass Rate   Passed
----------------------------------------------------------------------
meta-llama/Meta-Llama-3-70B-Instruct                    63.0% 121/192
meta-llama/Llama-3.1-8B-Instruct                        47.9%  92/192
gpt2                                                    17.7%  34/192
distilgpt2                                              14.1%  27/192
gpt-oss-20b-exj                                          0.0%   0/153

======================================================================
✅ Comparison report generated successfully!
======================================================================
```

## Installation

```bash
pip install -r requirements.txt
```

For remote models, create `.env` file:
```
HUGGINGFACE_TOKEN=your_token_here
```

## Configuration

### Models
Edit `config/models.json` to add models:

```json
{
  "models": [
    {
      "name": "meta-llama/Llama-3.1-8B-Instruct",
      "description": "Llama model via HF endpoint",
      "requires_auth": true,
      "remote_type": "hf_inference_endpoint",
      "endpoint_url": "https://your-endpoint.aws.endpoints.huggingface.cloud",
      "endpoint_namespace": "your_namespace",
      "endpoint_name": "your-endpoint-name"
    }
  ]
}
```

### Test Cases
Test cases are in `config/prompt_cases/`:
- `authority_impersonation.json`
- `hijacking.json`
- `jailbreak.json`
- `multilingual.json`
- And more...

## Understanding Results

Each test gets **PASS** or **FAIL**:
- **PASS**: Model successfully resisted the prompt injection attack
- **FAIL**: Model was compromised (followed malicious instructions, leaked secrets, etc.)

Example output:
```
Results:
  Model: meta-llama/Llama-3.1-8B-Instruct
  Pass Rate: 68.2%
  Passed: 131/192
```

## Workflow Overview

**Step 1 (Collect)** - Queries the model and saves responses
- Can be expensive and slow (especially for cloud endpoints)
- Saves responses to `responses/` directory as Excel files
- Run with: `python src/main.py --model "model-name"`

**Step 2 (Evaluate)** - Analyzes saved responses and generates individual reports
- Free and instant (no model queries)
- Can be run multiple times with improved evaluation logic
- Generates PDF and Excel reports for each model
- Run with: `python src/main.py --evaluate responses/model-name.xlsx`

**Step 3 (Compare)** - Creates comparison reports across multiple models
- Reads existing evaluation reports from `reports/` directory
- Generates side-by-side comparison PDF and Excel
- Shows which models are most secure against prompt injection
- Run with: `python generate_comparison.py`

**Benefits of this workflow:**
1. ✅ Collect responses once (expensive operation)
2. ✅ Re-evaluate multiple times for free (improve evaluation logic)
3. ✅ Compare all models easily (no re-collection needed)
4. ✅ Save time and money on cloud API calls

## Project Structure

```
prompt-injection-evaluator/
├── config/
│   ├── models.json           # Model configurations
│   └── prompt_cases/         # Test cases (192 total)
├── src/
│   ├── main.py               # Main entry point (Steps 1 & 2)
│   ├── response_collector.py # Collects model responses
│   ├── response_evaluator.py # Evaluates responses
│   ├── report_generator.py   # Generates PDF/Excel reports
│   └── ...
├── generate_comparison.py    # Step 3: Generate comparison reports
├── responses/                # Collected model responses (.xlsx)
├── reports/                  # Evaluation and comparison reports
│   ├── model_name.pdf        # Individual model PDF report
│   ├── model_name.xlsx       # Individual model Excel data
│   ├── model_comparison.pdf  # Multi-model comparison PDF
│   └── model_comparison.xlsx # Multi-model comparison Excel
└── README.md                 # This file
```

## Complete Example Workflow

```bash
# 1. Collect responses from multiple models
python src/main.py --model "meta-llama/Llama-3.1-8B-Instruct"
python src/main.py --model "meta-llama/Meta-Llama-3-70B-Instruct"
python src/main.py --model "gpt2"

# 2. Evaluate all models (if not done automatically with --evaluate flag)
python src/main.py --evaluate responses/meta-llama_Llama-3.1-8B-Instruct.xlsx
python src/main.py --evaluate responses/meta-llama_Meta-Llama-3-70B-Instruct.xlsx
python src/main.py --evaluate responses/gpt2.xlsx

# 3. Generate comparison report
python generate_comparison.py

# OR: Compare only specific models
python generate_comparison.py --models "meta-llama/Llama-3.1-8B-Instruct" "meta-llama/Meta-Llama-3-70B-Instruct"
```

**Result:** You now have:
- ✅ Individual detailed reports for each model
- ✅ Side-by-side comparison showing which model is most secure
- ✅ All data in both PDF (human-readable) and Excel (data analysis) formats

## Troubleshooting

**"Model not found"**
- Check model name matches `config/models.json` exactly

**"Response file not found"**
- Run Step 1 first to collect responses

**Endpoint issues**
- Verify `HUGGINGFACE_TOKEN` in `.env`
- Check endpoint URL in `models.json`

## Help

```bash
# Main application help (Steps 1 & 2)
python src/main.py --help

# Comparison report help (Step 3)
python generate_comparison.py --help
```

**Need help?**
- Check the examples above
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify `.env` file contains `HUGGINGFACE_TOKEN` for remote models
- Make sure you've run Steps 1 & 2 before running Step 3

