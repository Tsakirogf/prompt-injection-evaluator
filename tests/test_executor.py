"""
Unit tests for Executor module
"""
import sys
from pathlib import Path
from io import StringIO

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from executor import run_evaluator, evaluate_model
from model_factory import ModelFactory
from test_suite_loader import TestSuiteLoader


def test_run_evaluator(capsys):
    """Test that run_evaluator executes without errors."""
    try:
        run_evaluator()
        captured = capsys.readouterr()
        
        # Verify output contains expected content
        assert "Prompt Injection Evaluator" in captured.out
        assert "Loaded" in captured.out
        assert "models from configuration" in captured.out
        assert "test cases" in captured.out
        assert "Evaluation complete" in captured.out
        
    except Exception as e:
        assert False, f"run_evaluator() raised an exception: {e}"


def test_run_evaluator_displays_models(capsys):
    """Test that executor displays model information."""
    run_evaluator()
    captured = capsys.readouterr()
    
    # Check that it shows model details
    assert "Available Models:" in captured.out
    assert "distilgpt2" in captured.out or "gpt2" in captured.out


def test_run_evaluator_displays_test_cases(capsys):
    """Test that executor displays test case information."""
    run_evaluator()
    captured = capsys.readouterr()
    
    # Verify test cases are displayed
    assert "Test Cases:" in captured.out
    assert "Category:" in captured.out
    assert "Severity:" in captured.out


def test_evaluate_model():
    """Test that evaluate_model function works correctly."""
    # Load test data
    model_factory = ModelFactory()
    test_suite = TestSuiteLoader().load()
    
    # Get first model
    model = model_factory.get_next_model()
    
    # Evaluate the model
    result = evaluate_model(model, test_suite)
    
    # Verify result structure
    assert 'model_name' in result
    assert 'test_results' in result
    assert 'stats_by_category' in result
    assert 'stats_by_severity' in result
    assert 'total_tests' in result
    assert 'passed_tests' in result
    assert 'failed_tests' in result
    assert 'pass_rate' in result
    
    # Verify statistics
    assert result['total_tests'] == len(test_suite)
    assert result['passed_tests'] + result['failed_tests'] == result['total_tests']


def test_run_evaluator_displays_statistics(capsys):
    """Test that executor displays test suite statistics."""
    run_evaluator()
    captured = capsys.readouterr()
    
    # Verify statistics are shown
    assert "Test Suite Statistics:" in captured.out
    assert "Categories:" in captured.out
    assert "Severities:" in captured.out
