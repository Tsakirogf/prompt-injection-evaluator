"""
Unit tests for TestSuiteLoader
"""
import sys
import json
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from test_suite_loader import TestSuiteLoader, TestSuite, TestCase


@pytest.fixture
def sample_test_cases_file():
    """Create a temporary JSON test cases file for testing."""
    config_data = {
        "test_suite": {
            "name": "Sample Test Suite",
            "version": "1.0",
            "description": "Test suite for testing"
        },
        "test_cases": [
            {
                "id": "TEST-001",
                "name": "Test Case 1",
                "category": "test_category",
                "description": "First test case",
                "system_prompt": "System prompt 1",
                "user_prompt": "User prompt 1",
                "expected_behavior": "refuse",
                "severity": "high",
                "expected_keywords_absent": ["secret", "password"]
            },
            {
                "id": "TEST-002",
                "name": "Test Case 2",
                "category": "test_category",
                "description": "Second test case",
                "system_prompt": "System prompt 2",
                "user_prompt_template": "Template: {page_content}",
                "page_content": "Page content here",
                "expected_behavior": "accept",
                "severity": "medium",
                "protected_secret": "SECRET123",
                "expected_keywords_present": ["valid", "response"]
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink()


def test_test_suite_loader_initialization(sample_test_cases_file):
    """Test that TestSuiteLoader initializes correctly."""
    loader = TestSuiteLoader(sample_test_cases_file)
    assert loader.config_path == Path(sample_test_cases_file)
    assert loader._test_suite is None


def test_load_test_suite(sample_test_cases_file):
    """Test loading test suite from JSON."""
    loader = TestSuiteLoader(sample_test_cases_file)
    test_suite = loader.load()
    
    assert isinstance(test_suite, TestSuite)
    assert test_suite.name == "Sample Test Suite"
    assert test_suite.version == "1.0"
    assert len(test_suite) == 2


def test_test_cases_loaded_correctly(sample_test_cases_file):
    """Test that test cases are parsed correctly."""
    loader = TestSuiteLoader(sample_test_cases_file)
    test_suite = loader.load()
    
    test_case = test_suite.test_cases[0]
    assert test_case.id == "TEST-001"
    assert test_case.name == "Test Case 1"
    assert test_case.category == "test_category"
    assert test_case.system_prompt == "System prompt 1"
    assert test_case.user_prompt == "User prompt 1"
    assert test_case.expected_behavior == "refuse"
    assert test_case.severity == "high"
    assert "secret" in test_case.expected_keywords_absent


def test_test_case_with_template(sample_test_cases_file):
    """Test test case with user_prompt_template."""
    loader = TestSuiteLoader(sample_test_cases_file)
    test_suite = loader.load()
    
    test_case = test_suite.test_cases[1]
    assert test_case.user_prompt_template == "Template: {page_content}"
    assert test_case.page_content == "Page content here"
    assert test_case.protected_secret == "SECRET123"
    
    # Test get_user_prompt method
    formatted_prompt = test_case.get_user_prompt()
    assert formatted_prompt == "Template: Page content here"


def test_get_by_id(sample_test_cases_file):
    """Test retrieving test case by ID."""
    loader = TestSuiteLoader(sample_test_cases_file)
    test_suite = loader.load()
    
    test_case = test_suite.get_by_id("TEST-002")
    assert test_case is not None
    assert test_case.name == "Test Case 2"
    
    # Test non-existent ID
    test_case = test_suite.get_by_id("NONEXISTENT")
    assert test_case is None


def test_get_by_category(sample_test_cases_file):
    """Test retrieving test cases by category."""
    loader = TestSuiteLoader(sample_test_cases_file)
    test_suite = loader.load()
    
    cases = test_suite.get_by_category("test_category")
    assert len(cases) == 2


def test_get_by_severity(sample_test_cases_file):
    """Test retrieving test cases by severity."""
    loader = TestSuiteLoader(sample_test_cases_file)
    test_suite = loader.load()
    
    high_cases = test_suite.get_by_severity("high")
    assert len(high_cases) == 1
    assert high_cases[0].id == "TEST-001"
    
    medium_cases = test_suite.get_by_severity("medium")
    assert len(medium_cases) == 1
    assert medium_cases[0].id == "TEST-002"


def test_test_suite_iteration(sample_test_cases_file):
    """Test that test suite is iterable."""
    loader = TestSuiteLoader(sample_test_cases_file)
    test_suite = loader.load()
    
    cases = list(test_suite)
    assert len(cases) == 2
    assert cases[0].id == "TEST-001"
    assert cases[1].id == "TEST-002"


def test_get_test_suite(sample_test_cases_file):
    """Test get_test_suite method (loads if needed)."""
    loader = TestSuiteLoader(sample_test_cases_file)
    
    # Should load automatically
    test_suite = loader.get_test_suite()
    assert test_suite is not None
    assert len(test_suite) == 2
    
    # Should return cached version
    test_suite2 = loader.get_test_suite()
    assert test_suite is test_suite2


def test_reload(sample_test_cases_file):
    """Test reload functionality."""
    loader = TestSuiteLoader(sample_test_cases_file)
    
    test_suite1 = loader.load()
    test_suite2 = loader.reload()
    
    # Should be different objects
    assert test_suite1 is not test_suite2
    # But with same content
    assert len(test_suite1) == len(test_suite2)


def test_file_not_found():
    """Test that FileNotFoundError is raised for missing config."""
    loader = TestSuiteLoader("/non/existent/path.json")
    with pytest.raises(FileNotFoundError):
        loader.load()


def test_empty_test_cases():
    """Test that ValueError is raised for empty test cases."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"test_suite": {"name": "Empty"}, "test_cases": []}, f)
        temp_path = f.name
    
    try:
        loader = TestSuiteLoader(temp_path)
        with pytest.raises(ValueError):
            loader.load()
    finally:
        Path(temp_path).unlink()


def test_default_config_path():
    """Test using default config path."""
    project_root = Path(__file__).parent.parent
    default_config = project_root / "config" / "test_cases.json"
    
    if default_config.exists():
        loader = TestSuiteLoader()
        assert loader.config_path == default_config
        test_suite = loader.load()
        assert len(test_suite) > 0
