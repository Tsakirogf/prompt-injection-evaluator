# Execution Mode Comparison

| Feature | Batch Mode (`main.py`) | CLI Mode (`executor.py`) |
|---------|------------------------|--------------------------|
| **Command** | `python src/main.py` | `python src/executor.py <model_name>` |
| **Models Evaluated** | ALL models in `models.json` | SINGLE specified model |
| **Test Suite** | Always uses default | Default or custom (optional) |
| **Reports Generated** | Individual + Comparison | Individual only |
| **Use Case** | Full evaluation & comparison | Quick testing, debugging |
| **Speed** | Slower (all models) | Faster (one model) |
| **Best For** | Production runs, benchmarking | Development, iteration |
| **Arguments** | None | Required: model name<br>Optional: test suite path |

## Command Examples

### Batch Mode
```bash
# Run all models with default test suite
python src/main.py
```

### CLI Mode
```bash
# Run single model with default test suite
python src/executor.py gpt2

# Run single model with custom test suite
python src/executor.py gpt2 config/custom_tests.json

# Run different model
python src/executor.py distilgpt2

# Run model with full path name
python src/executor.py TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

## Output Comparison

### Batch Mode Output
```
reports/
├── model1_timestamp.pdf
├── model1_timestamp.xlsx
├── model2_timestamp.pdf
├── model2_timestamp.xlsx
├── model3_timestamp.pdf
├── model3_timestamp.xlsx
├── comparison_report_timestamp.pdf    ← Unique to batch mode
└── comparison_report_timestamp.xlsx   ← Unique to batch mode
```

### CLI Mode Output
```
reports/
├── model_name_timestamp.pdf
└── model_name_timestamp.xlsx
```

## When to Use Each Mode

### Use Batch Mode When:
- Running comprehensive evaluations
- Comparing multiple models
- Generating reports for stakeholders
- Running scheduled/automated tests
- Need cross-model comparison charts

### Use CLI Mode When:
- Testing a new model configuration
- Debugging specific model behavior
- Iterating on test cases
- Quick validation
- Working with custom test suites
- Time/resource constraints
