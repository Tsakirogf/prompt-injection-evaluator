"""
Executor Module

Contains the main execution logic for the Prompt Injection Evaluator.
"""
from datetime import datetime
from typing import List, Dict, Any
from model_factory import ModelFactory
from test_suite_loader import TestSuiteLoader, TestCase, TestSuite
from report_generator import ReportGenerator
from model_inference import ModelInference
from evaluator import RuleBasedEvaluator, LLMBasedEvaluator, HybridEvaluator


def evaluate_model(model: Dict[str, Any], test_suite: TestSuite, use_llm_judge: bool = False) -> Dict[str, Any]:
    """
    Evaluate a single model against all test cases.
    
    Args:
        model: Model configuration dictionary
        test_suite: TestSuite containing all test cases
        use_llm_judge: Whether to use LLM-based evaluation (default: False, uses rule-based)
    
    Returns:
        Dictionary containing evaluation results for the model
    """
    model_name = model['name']
    print(f"\n🔬 Evaluating model: {model_name}")
    print("-" * 70)
    
    # Initialize model inference
    model_inference = ModelInference(model)
    try:
        model_inference.load()
    except Exception as e:
        print(f"\n  ✗ Failed to load model: {str(e)}")
        print(f"    Skipping evaluation for {model_name}")
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
    
    # Initialize evaluator
    if use_llm_judge:
        evaluator = LLMBasedEvaluator()
        print(f"    Using LLM-based evaluation")
    else:
        evaluator = RuleBasedEvaluator()
        print(f"    Using rule-based evaluation")
    
    test_results = []
    stats_by_category = {}
    stats_by_severity = {}
    
    for idx, test_case in enumerate(test_suite, 1):
        print(f"  [{idx}/{len(test_suite)}] Running test: {test_case.id} - {test_case.name}", end="")
        
        try:
            # Generate model output
            output = model_inference.generate(
                test_case.system_prompt,
                test_case.get_user_prompt()
            )
            
            # Evaluate the output
            passed = evaluator.evaluate(test_case, output)
            
        except Exception as e:
            output = f"[ERROR] {str(e)}"
            passed = False
        
        result = {
            'test_id': test_case.id,
            'test_name': test_case.name,
            'category': test_case.category,
            'severity': test_case.severity,
            'passed': passed,
            'output': output,
            'notes': f'Expected behavior: {test_case.expected_behavior}',
            'system_prompt': test_case.system_prompt,
            'user_prompt': test_case.get_user_prompt(),
            'expected_behavior': test_case.expected_behavior
        }
        test_results.append(result)
        
        # Update statistics by category
        if test_case.category not in stats_by_category:
            stats_by_category[test_case.category] = {'passed': 0, 'failed': 0, 'total': 0}
        stats_by_category[test_case.category]['total'] += 1
        if passed:
            stats_by_category[test_case.category]['passed'] += 1
        else:
            stats_by_category[test_case.category]['failed'] += 1
        
        # Update statistics by severity
        if test_case.severity not in stats_by_severity:
            stats_by_severity[test_case.severity] = {'passed': 0, 'failed': 0, 'total': 0}
        stats_by_severity[test_case.severity]['total'] += 1
        if passed:
            stats_by_severity[test_case.severity]['passed'] += 1
        else:
            stats_by_severity[test_case.severity]['failed'] += 1
        
        status = " ✓" if passed else " ✗"
        print(status)
    
    # Unload model to free memory
    model_inference.unload()
    print(f"  ✓ Model unloaded")
    
    # Calculate overall statistics
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['passed'])
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n  Summary: {passed_tests}/{total_tests} passed ({pass_rate:.1f}% pass rate)")
    
    return {
        'model_name': model_name,
        'model_description': model.get('description', ''),
        'test_results': test_results,
        'stats_by_category': stats_by_category,
        'stats_by_severity': stats_by_severity,
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'pass_rate': pass_rate
    }


def run_evaluator():
    """
    Execute the prompt injection evaluation workflow.
    
    This function orchestrates the entire evaluation process,
    keeping the main entry point clean.
    """
    print("🔒 Prompt Injection Evaluator")
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
