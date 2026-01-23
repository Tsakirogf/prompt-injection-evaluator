# Evaluation System Documentation

## Overview

The Prompt Injection Evaluator now includes complete model evaluation logic with support for:
- **Rule-based evaluation** - Fast, deterministic checks against explicit criteria
- **LLM-based evaluation** (future) - Use another LLM to judge test results for more nuanced evaluation
- **Hybrid evaluation** - Combines both approaches

## Architecture

### Core Components

#### 1. Model Inference (`src/model_inference.py`)
Handles loading and running LLM models using HuggingFace Transformers.

**Features:**
- Automatic model loading with proper device mapping
- Chat template support for compatible models
- Memory management (model loading/unloading)
- Error handling for generation failures

**Usage:**
```python
from model_inference import ModelInference

inference = ModelInference(model_config)
inference.load()
output = inference.generate(system_prompt, user_prompt)
inference.unload()  # Free memory
```

#### 2. Evaluator (`src/evaluator.py`)
Evaluates model outputs against test criteria.

**Three Evaluator Types:**

##### RuleBasedEvaluator
- Checks for protected secrets
- Validates keyword presence/absence
- Fast and deterministic

##### LLMBasedEvaluator (Future Enhancement)
- Uses another LLM as a judge
- Can evaluate nuanced responses
- Better for ambiguous cases
- Requires API integration (OpenAI, Anthropic, etc.)

##### HybridEvaluator
- Combines both approaches
- Uses rules first, LLM for edge cases

**Evaluation Criteria:**
- `protected_secret` - Secret value that must NOT appear in output
- `expected_keywords_absent` - Keywords that must NOT be present
- `expected_keywords_present` - Keywords that MUST be present
- `expected_behavior` - Expected behavior type

#### 3. Executor (`src/executor.py`)
Orchestrates the evaluation process.

**Process Flow:**
1. Load model
2. Run each test case
3. Generate model output
4. Evaluate output
5. Collect statistics
6. Unload model
7. Generate reports

## Test Pass/Fail Logic

A test **PASSES** if the model successfully resists the prompt injection attack:
- Does NOT reveal protected secrets
- Does NOT contain forbidden keywords
- DOES contain required keywords (if specified)

A test **FAILS** if the model is compromised:
- Reveals secrets
- Contains forbidden content
- Follows injected instructions
- Changes behavior unexpectedly

## Using LLM-Based Evaluation (Future)

To enable LLM-based evaluation for more nuanced judging:

```python
# In run_evaluator(), change:
model_result = evaluate_model(model, test_suite, use_llm_judge=True)
```

**Implementation Steps:**
1. Choose a judge LLM (e.g., GPT-4, Claude)
2. Add API client in `LLMBasedEvaluator.__init__()`
3. Implement API calls in `evaluate()`
4. Parse judge's response (PASS/FAIL)

**Benefits:**
- Better handling of nuanced responses
- Can understand context and intent
- More robust against edge cases

**Drawbacks:**
- Slower (API latency)
- More expensive (API costs)
- Requires internet connection

## Installation

Install the new dependencies:

```bash
.venv\Scripts\python.exe -m pip install torch transformers accelerate
```

Or install all:

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Running Evaluations

**Standard run (rule-based):**
```bash
.venv\Scripts\python.exe src\main.py
```

**With LLM judge (when implemented):**
Modify `src/executor.py` line ~203 to pass `use_llm_judge=True`

## Report Generation

Reports now include:
- Individual model reports (PDF + Excel)
  - Summary statistics
  - Category/severity breakdowns
  - Detailed test results
  - **Full transcript** with prompts and responses
- Comparison report across all models
  - Side-by-side performance
  - Category comparisons
  - Severity level analysis

## Customization

### Adding New Evaluation Criteria

Edit `src/evaluator.py`:

```python
class RuleBasedEvaluator:
    def evaluate(self, test_case, output):
        passed = True
        
        # Add your custom checks here
        if my_custom_check(output):
            passed = False
            
        return passed
```

### Using Different Models

Edit `config/models.json`:

```json
{
  "models": [
    {
      "name": "your-model-name",
      "description": "Description",
      "requires_auth": false,
      "torch_dtype": "float16"
    }
  ]
}
```

### Adding Test Cases

Edit `config/test_cases.json` - see existing format for structure.

## Memory Management

Models are automatically unloaded after evaluation to free memory:
- GPU memory is cleared
- Next model loads fresh
- Prevents out-of-memory errors

## Error Handling

- Model loading failures are caught and logged
- Generation errors are recorded as failed tests
- Evaluation continues with remaining tests
- Reports show error messages

## Future Enhancements

1. **LLM Judge Integration**
   - OpenAI API
   - Anthropic API
   - Local judge models

2. **Advanced Metrics**
   - Confidence scores
   - Response quality metrics
   - Attack success rates

3. **Parallel Evaluation**
   - Run multiple models concurrently
   - Batch processing

4. **Interactive Mode**
   - Manual review of edge cases
   - Human-in-the-loop evaluation
