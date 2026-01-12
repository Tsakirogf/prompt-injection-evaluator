"""
Unit tests for Executor module
"""
import sys
from pathlib import Path
from io import StringIO

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from executor import run_evaluator


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
        assert "Ready to evaluate prompt injections" in captured.out
        
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


def test_run_evaluator_displays_statistics(capsys):
    """Test that executor displays test suite statistics."""
    run_evaluator()
    captured = capsys.readouterr()
    
    # Verify statistics are shown
    assert "Test Suite Statistics:" in captured.out
    assert "Categories:" in captured.out
    assert "Severities:" in captured.out
