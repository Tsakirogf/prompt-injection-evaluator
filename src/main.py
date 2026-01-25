#!/usr/bin/env python3
"""
Prompt Injection Evaluator - Main Application Entry Point

Runs all models from models.json configuration file.
"""
from executor import run_all_models


def main():
    """Main entry point - runs all models from models.json."""
    run_all_models(simulate=True)


if __name__ == "__main__":
    main()
