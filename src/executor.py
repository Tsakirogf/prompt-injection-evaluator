"""
Executor Module

Contains the main execution logic for the Prompt Injection Evaluator.
"""
from datetime import datetime
from model_factory import ModelFactory
from test_suite_loader import TestSuiteLoader
from report_generator import ReportGenerator


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
    
    # Generate reports for each model
    print("\n📝 Generating Reports:")
    print("-" * 70)
    
    report_generator = ReportGenerator()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for model in model_factory:
        model_name = model['name']
        print(f"  Generating reports for: {model_name}")
        
        # Create sample test results (placeholder - will be replaced with actual evaluation)
        test_results = []
        for test_case in test_suite:
            test_results.append({
                'test_id': test_case.id,
                'test_name': test_case.name,
                'category': test_case.category,
                'severity': test_case.severity,
                'passed': False,  # Placeholder - will be determined by actual evaluation
                'output': 'Sample output (evaluation not yet implemented)',
                'notes': f'Expected behavior: {test_case.expected_behavior}'
            })
        
        # Metadata for the report
        metadata = {
            'Model': model_name,
            'Date': timestamp,
            'Test Suite': test_suite.name,
            'Version': test_suite.version,
            'Total Tests': len(test_results)
        }
        
        # Generate both PDF and Excel reports
        reports = report_generator.generate_reports(model_name, test_results, metadata)
        
        print(f"    ✓ PDF:   {reports['pdf']}")
        print(f"    ✓ Excel: {reports['excel']}")
    
    print("\n" + "=" * 70)
    print("✅ Setup complete! Reports generated successfully.")
    print(f"📂 Reports saved in: {report_generator.output_dir.absolute()}")
    print("=" * 70)
