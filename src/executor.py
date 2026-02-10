"""
Executor Module

Contains the main execution logic for the Prompt Injection Evaluator.

Uses the separated workflow:
- Step 1: ResponseCollector collects model responses
- Step 2: ResponseEvaluator evaluates the collected responses

This separation allows re-evaluation without re-querying expensive models.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from model_factory import ModelFactory
from test_suite_loader import TestSuiteLoader, TestSuite
from report_generator import ReportGenerator
from response_collector import ResponseCollector, CollectedResponse, CollectionMetadata


def _create_collection_metadata(
    model: Dict[str, Any],
    test_suite: TestSuite
) -> CollectionMetadata:
    """Create CollectionMetadata from model and test suite."""
    return CollectionMetadata(
        model_name=model['name'],
        endpoint_url=model.get('endpoint_url'),
        test_suite_name=test_suite.name,
        test_suite_version=test_suite.version,
        started_at=datetime.now().isoformat(),
        completed_at=datetime.now().isoformat(),
        total_tests=len(test_suite)
    )


def _convert_results_to_responses(
    test_results: List[Dict[str, Any]],
    test_suite: TestSuite
) -> List[CollectedResponse]:
    """Convert test results to CollectedResponse objects for saving."""
    responses = []
    for result in test_results:
        test_case = test_suite.get_by_id(result['test_id'])
        response = CollectedResponse(
            test_id=result['test_id'],
            test_name=result['test_name'],
            category=result['category'],
            severity=result['severity'],
            system_prompt=result.get('system_prompt', ''),
            user_prompt=result.get('user_prompt', ''),
            model_response=result.get('output', ''),
            response_timestamp=datetime.now().isoformat(),
            response_time_ms=None,
            error=None if not result.get('output', '').startswith('[ERROR]') else result.get('output'),
            expected_behavior=result.get('expected_behavior', ''),
            protected_secret=test_case.protected_secret if test_case else None,
            expected_keywords_absent=test_case.expected_keywords_absent if test_case else [],
            expected_keywords_present=test_case.expected_keywords_present if test_case else []
        )
        responses.append(response)
    return responses


def evaluate_model(
    model: Dict[str, Any],
    test_suite: TestSuite,
    save_responses: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Evaluate a single model against all test cases using the separated workflow.

    Step 1: Collect responses (expensive)
    Step 2: Evaluate responses (cheap)

    Args:
        model: Model configuration dictionary
        test_suite: TestSuite containing all test cases
        save_responses: Optional path to save collected responses to xlsx file

    Returns:
        Dictionary containing evaluation results for the model
    """
    model_name = model['name']
    print(f"\nEvaluating model: {model_name}")
    print("-" * 70)
    
    # STEP 1: COLLECT RESPONSES
    print("STEP 1: Collecting responses from model...")

    collector = ResponseCollector(model)
    try:
        responses = collector.collect_all(test_suite, verbose=True)
    except Exception as e:
        print(f"\nError during collection: {str(e)}")
        return {
            'model_name': model_name,
            'model_description': model.get('description', ''),
            'test_results': [],
            'stats_by_category': {},
            'stats_by_severity': {},
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'pass_rate': 0.0,
            'error': str(e)
        }
    
    # Save responses if requested
    responses_path = save_responses
    if not responses_path:
        # Default save location
        responses_dir = Path("responses")
        responses_dir.mkdir(exist_ok=True)
        safe_model_name = model_name.replace('/', '_')
        responses_path = responses_dir / f"{safe_model_name}.xlsx"

    saved_path = collector.save_to_xlsx(responses_path)
    print(f"Responses saved to: {saved_path}")

    # STEP 2: EVALUATE RESPONSES
    print("\nSTEP 2: Evaluating responses...")

    from response_evaluator import ResponseEvaluator
    evaluator = ResponseEvaluator(saved_path)
    evaluation_results = evaluator.evaluate_all(verbose=True)

    # Generate reports
    output_dir = Path("reports")
    reports = evaluator.generate_reports(output_dir)

    # Get summary
    summary = evaluator.get_summary()

    # Convert to the expected format for backward compatibility
    test_results = []
    for eval_result in evaluation_results:
        test_results.append({
            'test_id': eval_result['test_id'],
            'test_name': eval_result['test_name'],
            'category': eval_result['category'],
            'severity': eval_result['severity'],
            'passed': eval_result['passed'],
            'output': eval_result.get('model_response', ''),
            'notes': f"Expected behavior: {eval_result.get('expected_behavior', '')}",
            'system_prompt': eval_result.get('system_prompt', ''),
            'user_prompt': eval_result.get('user_prompt', ''),
            'expected_behavior': eval_result.get('expected_behavior', '')
        })

    print(f"\nSummary: {summary['passed_tests']}/{summary['total_tests']} passed ({summary['pass_rate']:.1f}% pass rate)")
    print(f"\nReports generated:")
    print(f"  PDF: {reports['pdf']}")
    print(f"  Excel: {reports['excel']}")

    return {
        'model_name': model_name,
        'model_description': model.get('description', ''),
        'test_results': test_results,
        'stats_by_category': summary['stats_by_category'],
        'stats_by_severity': summary['stats_by_severity'],
        'total_tests': summary['total_tests'],
        'passed_tests': summary['passed_tests'],
        'failed_tests': summary['failed_tests'],
        'pass_rate': summary['pass_rate']
    }


def run_all_models(simulate: bool = True):
    """
    Execute the prompt injection evaluation workflow for ALL models.
    
    Runs all models defined in models.json configuration file.
    This function orchestrates the entire evaluation process.
    """
    print("🔒 Prompt Injection Evaluator - Running All Models")
    print("=" * 70)
    
    # Load models
    model_factory = ModelFactory()
    print(f"\n✓ Loaded {len(model_factory)} models from configuration")
    
    # Load test cases
    test_loader = TestSuiteLoader()
    test_suite = test_loader.load()
    print(f"✓ Loaded {len(test_suite)} test cases from suite: {test_suite.name}")
    print(f"  Version: {test_suite.version}")
    print(f"  Description: {test_suite.description}")
    
    # Display models
    print(f"\n📋 Available Models:")
    print("-" * 70)
    for idx, model in enumerate(model_factory, 1):
        print(f"  {idx}. {model['name']}")
        print(f"     {model['description']}")
    
    # Display test cases summary
    print(f"\n🧪 Test Cases:")
    print("-" * 70)
    for test_case in test_suite:
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(test_case.severity, '⚪')
        
        print(f"  {severity_emoji} [{test_case.id}] {test_case.name}")
        print(f"     Category: {test_case.category} | Severity: {test_case.severity}")
        print(f"     {test_case.description}")
        print()
    
    # Display statistics
    print("📊 Test Suite Statistics:")
    print("-" * 70)
    categories = {}
    severities = {}
    
    for test_case in test_suite:
        categories[test_case.category] = categories.get(test_case.category, 0) + 1
        severities[test_case.severity] = severities.get(test_case.severity, 0) + 1
    
    print(f"  Categories: {', '.join(f'{k}({v})' for k, v in categories.items())}")
    print(f"  Severities: {', '.join(f'{k}({v})' for k, v in severities.items())}")
    
    # Run evaluation for each model
    print("\n🚀 Starting Evaluation:")
    print("=" * 70)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_model_results = []
    
    for model in model_factory:
        if simulate:
            # Create simulated results to avoid heavy model loads during tests
            test_results = []
            stats_by_category = {}
            stats_by_severity = {}

            for tc in test_suite:
                passed = False
                output = "[SIMULATED OUTPUT]"
                result = {
                    'test_id': tc.id,
                    'test_name': tc.name,
                    'category': tc.category,
                    'severity': tc.severity,
                    'passed': passed,
                    'output': output,
                    'notes': f'Expected behavior: {tc.expected_behavior}',
                    'system_prompt': tc.system_prompt,
                    'user_prompt': tc.get_user_prompt(),
                    'expected_behavior': tc.expected_behavior
                }
                test_results.append(result)

                # Update stats
                stats_by_category.setdefault(tc.category, {'passed': 0, 'failed': 0, 'total': 0})
                stats_by_category[tc.category]['total'] += 1
                stats_by_category[tc.category]['failed'] += 1

                stats_by_severity.setdefault(tc.severity, {'passed': 0, 'failed': 0, 'total': 0})
                stats_by_severity[tc.severity]['total'] += 1
                stats_by_severity[tc.severity]['failed'] += 1

            total_tests = len(test_results)
            passed_tests = sum(1 for r in test_results if r['passed'])
            failed_tests = total_tests - passed_tests
            pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

            model_result = {
                'model_name': model.get('name'),
                'model_description': model.get('description', ''),
                'test_results': test_results,
                'stats_by_category': stats_by_category,
                'stats_by_severity': stats_by_severity,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'pass_rate': pass_rate
            }
        else:
            model_result = evaluate_model(model, test_suite)

        all_model_results.append(model_result)
    
    # Generate reports for each model
    print("\n📝 Generating Individual Model Reports:")
    print("-" * 70)
    
    report_generator = ReportGenerator()
    
    for model_result in all_model_results:
        model_name = model_result['model_name']
        print(f"\n  {model_name}:")
        
        # Metadata for the report
        metadata = {
            'Model': model_name,
            'Description': model_result['model_description'],
            'Date': timestamp,
            'Test Suite': test_suite.name,
            'Version': test_suite.version,
            'Total Tests': model_result['total_tests'],
            'Passed': model_result['passed_tests'],
            'Failed': model_result['failed_tests'],
            'Pass Rate': f"{model_result['pass_rate']:.1f}%"
        }
        
        # Generate both PDF and Excel reports
        reports = report_generator.generate_reports(
            model_name, 
            model_result['test_results'], 
            metadata,
            stats_by_category=model_result['stats_by_category'],
            stats_by_severity=model_result['stats_by_severity']
        )
        
        print(f"    ✓ PDF:   {reports['pdf']}")
        print(f"    ✓ Excel: {reports['excel']}")
    
    # Generate comparison report
    print("\n📊 Generating Model Comparison Report:")
    print("-" * 70)
    
    comparison_report = report_generator.generate_comparison_report(
        all_model_results,
        test_suite,
        timestamp
    )
    
    print(f"  ✓ PDF:   {comparison_report['pdf']}")
    print(f"  ✓ Excel: {comparison_report['excel']}")
    
    print("\n" + "=" * 70)
    print("✅ Evaluation complete! All reports generated successfully.")
    print(f"📂 Reports saved in: {report_generator.output_dir.absolute()}")
    print("\n📈 Model Performance Summary:")
    print("-" * 70)
    for model_result in all_model_results:
        print(f"  {model_result['model_name']:40} {model_result['passed_tests']:3}/{model_result['total_tests']:3} passed ({model_result['pass_rate']:5.1f}%)")
    print("=" * 70)


def run_single_model(model_name: str, test_suite_path: str = None):
    """
    Execute evaluation for a single model specified via command line.
    
    Args:
        model_name: Name of the model to evaluate (must exist in models.json)
        test_suite_path: Optional path to a custom test suite JSON file
    """
    print(f"🔒 Prompt Injection Evaluator - Single Model Mode")
    print("=" * 70)
    print(f"  Model: {model_name}")
    if test_suite_path:
        print(f"  Test Suite: {test_suite_path}")
    print("=" * 70)
    
    # Load models and find the requested model
    model_factory = ModelFactory()
    target_model = None
    
    for model in model_factory:
        if model['name'] == model_name:
            target_model = model
            break
    
    if not target_model:
        print(f"\n❌ Error: Model '{model_name}' not found in models.json")
        print("\nAvailable models:")
        for model in model_factory:
            print(f"  - {model['name']}")
        return 1
    
    print(f"\n✓ Found model: {target_model['name']}")
    print(f"  Description: {target_model['description']}")
    
    # Load test cases
    test_loader = TestSuiteLoader(test_suite_path) if test_suite_path else TestSuiteLoader()
    test_suite = test_loader.load()
    print(f"\n✓ Loaded {len(test_suite)} test cases from suite: {test_suite.name}")
    print(f"  Version: {test_suite.version}")
    print(f"  Description: {test_suite.description}")
    
    # Display test cases summary
    print(f"\n🧪 Test Cases:")
    print("-" * 70)
    for test_case in test_suite:
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(test_case.severity, '⚪')
        
        print(f"  {severity_emoji} [{test_case.id}] {test_case.name}")
        print(f"     Category: {test_case.category} | Severity: {test_case.severity}")
    
    # Run evaluation
    print("\n🚀 Starting Evaluation:")
    print("=" * 70)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    model_result = evaluate_model(target_model, test_suite)
    
    # Generate reports
    print("\n📝 Generating Reports:")
    print("-" * 70)
    
    report_generator = ReportGenerator()
    
    # Metadata for the report
    metadata = {
        'Model': model_result['model_name'],
        'Description': model_result['model_description'],
        'Date': timestamp,
        'Test Suite': test_suite.name,
        'Version': test_suite.version,
        'Total Tests': model_result['total_tests'],
        'Passed': model_result['passed_tests'],
        'Failed': model_result['failed_tests'],
        'Pass Rate': f"{model_result['pass_rate']:.1f}%"
    }
    
    # Generate both PDF and Excel reports
    reports = report_generator.generate_reports(
        model_result['model_name'], 
        model_result['test_results'], 
        metadata,
        stats_by_category=model_result['stats_by_category'],
        stats_by_severity=model_result['stats_by_severity']
    )
    
    print(f"  ✓ PDF:   {reports['pdf']}")
    print(f"  ✓ Excel: {reports['excel']}")
    
    print("\n" + "=" * 70)
    print("✅ Evaluation complete! Reports generated successfully.")
    print(f"📂 Reports saved in: {report_generator.output_dir.absolute()}")
    print("\n📈 Performance Summary:")
    print("-" * 70)
    print(f"  Model: {model_result['model_name']}")
    print(f"  Passed: {model_result['passed_tests']}/{model_result['total_tests']} ({model_result['pass_rate']:.1f}%)")
    print(f"  Failed: {model_result['failed_tests']}/{model_result['total_tests']}")
    print("=" * 70)
    
    return 0


def run_evaluator():
    """Compatibility wrapper expected by the tests. Runs the evaluator in simulation mode to keep test runs fast."""
    return run_all_models(simulate=True)


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python executor.py <model_name> [test_suite_path]")
        print("\nExample:")
        print("  python executor.py gpt2")
        print("  python executor.py gpt2 config/test_cases.json")
        print("\nTo run all models, use: python main.py")
        sys.exit(1)
    
    model_name = sys.argv[1]
    test_suite_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    exit_code = run_single_model(model_name, test_suite_path)
    sys.exit(exit_code)
