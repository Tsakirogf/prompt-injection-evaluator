#!/usr/bin/env python3
"""
Prompt Injection Evaluator - Main Application Entry Point

Clear Flow:
1. Run test suite against model (endpoint or local) -> Store responses in Excel
2. Evaluate stored responses -> Generate PDF report

Usage:
    # Step 1: Run tests and collect responses
    python src/main.py --model "meta-llama/Llama-3.1-8B-Instruct"

    # Step 2: Evaluate responses (independent of model)
    python src/main.py --evaluate responses/meta-llama_Llama-3.1-8B-Instruct.xlsx

    # Or do both in one step:
    python src/main.py --model "meta-llama/Llama-3.1-8B-Instruct" --evaluate
"""
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Load .env early so HF_HUB_CACHE (and similar vars) are set before any
# HuggingFace library is imported — they read env vars at import time.
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from model_factory import ModelFactory
from test_suite_loader import TestSuiteLoader
from response_collector import ResponseCollector
from response_evaluator import evaluate_responses


def run_model(model_name: str, test_suite_path: str = None) -> Path:
    """
    Step 1: Run test suite against model and store responses.

    Args:
        model_name: Name of model from models.json
        test_suite_path: Optional custom test suite path

    Returns:
        Path to saved responses xlsx file
    """
    print("=" * 70)
    print("STEP 1: COLLECTING MODEL RESPONSES")
    print("=" * 70)

    # Find the model
    model_factory = ModelFactory()
    target_model = None

    for model in model_factory:
        if model['name'] == model_name:
            target_model = model
            break

    if not target_model:
        print(f"\nError: Model '{model_name}' not found in config/models.json")
        print("\nAvailable models:")
        for model in model_factory:
            print(f"  - {model['name']}")
        sys.exit(1)

    print(f"\nModel: {target_model['name']}")
    print(f"  Description: {target_model.get('description', 'No description')}")

    # Load test suite
    test_loader = TestSuiteLoader(test_suite_path) if test_suite_path else TestSuiteLoader()
    test_suite = test_loader.load()
    print(f"\nLoaded {len(test_suite)} test cases")
    print(f"  Test Suite: {test_suite.name}")

    # Collect responses
    print(f"\nRunning tests against model...")
    collector = ResponseCollector(target_model)
    collector.collect_all(test_suite, verbose=True)

    # Save to xlsx
    responses_dir = Path("responses")
    responses_dir.mkdir(exist_ok=True)

    # Create clean filename from model name
    safe_model_name = target_model['name'].replace('/', '_')
    output_path = responses_dir / f"{safe_model_name}.xlsx"

    saved_path = collector.save_to_xlsx(output_path)

    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE")
    print(f"Responses saved to: {saved_path.absolute()}")
    print("=" * 70)

    return saved_path


def evaluate_responses_file(xlsx_path: Path, llm_evaluate: bool = False) -> dict:
    """
    Step 2: Evaluate stored responses and generate PDF report.

    Args:
        xlsx_path: Path to responses xlsx file
        llm_evaluate: When True, also run LLM evaluation (Llama 3.1 8B-Instruct,
                      4-bit quantized) and generate an enriched PDF alongside the
                      standard one.

    Returns:
        Dictionary with evaluation summary and report paths
    """
    print("\n" + "=" * 70)
    print("STEP 2: EVALUATING RESPONSES")
    print("=" * 70)

    if not xlsx_path.exists():
        print(f"\nError: Response file not found: {xlsx_path}")
        sys.exit(1)

    print(f"\nInput: {xlsx_path.name}")

    # Optional LLM evaluator — loaded lazily inside LLMEvaluator on first use
    llm_evaluator = None
    if llm_evaluate:
        from llm_evaluator import LLMEvaluator
        print("\nLLM evaluation enabled (Llama 3.1 8B-Instruct, 4-bit quantized)")
        print("  Model will be loaded on the first test (4-bit quantized, ~4.5 GB VRAM).")
        llm_evaluator = LLMEvaluator()

    # Create output directory
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    # Evaluate (rule-based always; LLM optionally)
    result = evaluate_responses(
        xlsx_path=xlsx_path,
        evaluator_type='multi_tier',
        output_dir=output_dir,
        verbose=True,
        llm_evaluator=llm_evaluator,
        enriched=llm_evaluate,
    )

    # Print summary
    summary = result['summary']
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print(f"\nResults:")
    print(f"  Model: {summary['model_name']}")
    print(f"  Pass Rate: {summary['pass_rate']:.1f}%")
    print(f"  Passed: {summary['passed_tests']}/{summary['total_tests']}")

    print(f"\nReports generated:")
    for report_type, path in result['reports'].items():
        if path:
            print(f"  {report_type.upper()}: {path}")

    print("=" * 70)

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Prompt Injection Evaluator - Separated Collection & Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Step 1: Collect responses from model
  python src/main.py --model "meta-llama/Llama-3.1-8B-Instruct"

  # Step 2: Evaluate responses (can run independently)
  python src/main.py --evaluate responses/meta-llama_Llama-3.1-8B-Instruct.xlsx

  # Step 2 with LLM evaluation (generates standard + enriched PDF)
  python src/main.py --evaluate responses/meta-llama_Llama-3.1-8B-Instruct.xlsx --llm-evaluate

  # Do both steps together:
  python src/main.py --model "meta-llama/Llama-3.1-8B-Instruct" --evaluate
        """
    )

    parser.add_argument(
        '--model', '-m',
        help='Model name from models.json (Step 1: collect responses)'
    )

    parser.add_argument(
        '--evaluate', '-e',
        nargs='?',
        const='auto',
        metavar='XLSX_FILE',
        help='Evaluate responses from xlsx file (Step 2). If no file specified, uses latest for --model'
    )

    parser.add_argument(
        '--llm-evaluate', '-l',
        action='store_true',
        help=(
            'Run LLM evaluation using Llama 3.1 8B-Instruct (4-bit via bitsandbytes) alongside '
            'the standard rule-based evaluation. Produces two PDFs: the unchanged '
            'standard report and an enriched report with both evaluations side-by-side. '
            'Requires --evaluate.'
        )
    )

    parser.add_argument(
        '--test-suite', '-t',
        help='Path to custom test suite JSON file'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.model and not args.evaluate:
        parser.print_help()
        print("\nError: Must specify --model, --evaluate, or both")
        sys.exit(1)

    if args.llm_evaluate and not args.evaluate:
        parser.print_help()
        print("\nError: --llm-evaluate requires --evaluate")
        sys.exit(1)

    responses_path = None

    # Step 1: Collect responses
    if args.model:
        responses_path = run_model(args.model, args.test_suite)

    # Step 2: Evaluate
    if args.evaluate:
        # Determine which file to evaluate
        if args.evaluate == 'auto':
            # Use the responses we just collected
            if not responses_path:
                print("\nError: --evaluate without file requires --model to be specified")
                sys.exit(1)
            eval_path = responses_path
        else:
            # Use the specified file
            eval_path = Path(args.evaluate)

        evaluate_responses_file(eval_path, llm_evaluate=args.llm_evaluate)


if __name__ == "__main__":
    main()
