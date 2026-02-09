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

## Why Step 1 and Step 2 are Separate

**Step 1 (Collect)** queries the model - this can be expensive and slow.

**Step 2 (Evaluate)** just analyzes the saved responses - this is free and instant.

**Benefit**: You can improve your evaluation logic and re-run Step 2 multiple times without re-querying the model!

## Project Structure

```
prompt-injection-evaluator/
├── config/
│   ├── models.json           # Model configurations
│   └── prompt_cases/         # Test cases (192 total)
├── src/
│   └── main.py               # Main entry point
├── responses/                # Collected model responses
├── reports/                  # Evaluation reports
└── README.md                 # This file
```

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
python src/main.py --help
```

