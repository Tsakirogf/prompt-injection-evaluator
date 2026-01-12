# Prompt Injection Evaluator

A Python project for evaluating prompt injection vulnerabilities.

## Setup

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main application:
```bash
python src/main.py
```

## Project Structure

```
prompt-injection-evaluator/
├── src/
│   └── main.py          # Main application entry point
├── tests/
│   └── test_main.py     # Unit tests
├── requirements.txt     # Project dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Development

Run tests:
```bash
python -m pytest tests/
```

## License

MIT
