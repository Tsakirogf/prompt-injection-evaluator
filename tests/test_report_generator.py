"""
Unit tests for ReportGenerator
"""
import sys
from pathlib import Path
import tempfile
import shutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from report_generator import ReportGenerator


@pytest.fixture
def temp_report_dir():
    """Create a temporary directory for reports."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_test_results():
    """Sample test results for report generation."""
    return [
        {
            'test_id': 'TEST-001',
            'test_name': 'System Override Test',
            'category': 'system_override',
            'severity': 'high',
            'passed': True,
            'output': 'Model correctly refused to reveal system prompt.',
            'notes': 'Good security posture'
        },
        {
            'test_id': 'TEST-002',
            'test_name': 'Secret Extraction Test',
            'category': 'secret_extraction',
            'severity': 'critical',
            'passed': False,
            'output': 'API_KEY=SECRET123 - model revealed the secret!',
            'notes': 'Security vulnerability detected'
        }
    ]


@pytest.fixture
def sample_metadata():
    """Sample metadata for reports."""
    return {
        'Model': 'test-model-1',
        'Date': '2026-01-12',
        'Test Suite': 'Security Tests',
        'Version': '1.0'
    }


@pytest.fixture
def sample_stats():
    """Sample statistics for reports."""
    return {
        'stats_by_category': {
            'system_override': {'passed': 1, 'failed': 0, 'total': 1},
            'secret_extraction': {'passed': 0, 'failed': 1, 'total': 1}
        },
        'stats_by_severity': {
            'high': {'passed': 1, 'failed': 0, 'total': 1},
            'critical': {'passed': 0, 'failed': 1, 'total': 1}
        }
    }


def test_report_generator_initialization(temp_report_dir):
    """Test that ReportGenerator initializes correctly."""
    generator = ReportGenerator(temp_report_dir)
    assert generator.output_dir == Path(temp_report_dir)
    assert generator.output_dir.exists()


def test_sanitize_filename():
    """Test filename sanitization."""
    generator = ReportGenerator()
    
    assert generator.sanitize_filename("model/name") == "model_name"
    assert generator.sanitize_filename("Model\\Name") == "Model_Name"
    assert generator.sanitize_filename("model-1.0") == "model-1.0"
    assert generator.sanitize_filename("model@#$%name") == "modelname"


def test_generate_pdf_report(temp_report_dir, sample_test_results, sample_metadata, sample_stats):
    """Test PDF report generation."""
    generator = ReportGenerator(temp_report_dir)
    
    pdf_path = generator.generate_pdf_report(
        "test-model",
        sample_test_results,
        sample_metadata,
        sample_stats['stats_by_category'],
        sample_stats['stats_by_severity']
    )
    
    assert pdf_path.exists()
    assert pdf_path.suffix == '.pdf'
    assert pdf_path.name == 'test-model.pdf'
    assert pdf_path.stat().st_size > 0


def test_generate_excel_report(temp_report_dir, sample_test_results, sample_metadata, sample_stats):
    """Test Excel report generation."""
    generator = ReportGenerator(temp_report_dir)
    
    excel_path = generator.generate_excel_report(
        "test-model",
        sample_test_results,
        sample_metadata,
        sample_stats['stats_by_category'],
        sample_stats['stats_by_severity']
    )
    
    assert excel_path.exists()
    assert excel_path.suffix == '.xlsx'
    assert excel_path.name == 'test-model.xlsx'
    assert excel_path.stat().st_size > 0


def test_generate_reports(temp_report_dir, sample_test_results, sample_metadata, sample_stats):
    """Test generating both PDF and Excel reports."""
    generator = ReportGenerator(temp_report_dir)
    
    reports = generator.generate_reports(
        "test-model",
        sample_test_results,
        sample_metadata,
        sample_stats['stats_by_category'],
        sample_stats['stats_by_severity']
    )
    
    assert 'pdf' in reports
    assert 'excel' in reports
    assert reports['pdf'].exists()
    assert reports['excel'].exists()


def test_model_name_with_slashes(temp_report_dir, sample_test_results):
    """Test report generation with model name containing slashes."""
    generator = ReportGenerator(temp_report_dir)
    
    reports = generator.generate_reports(
        "company/model-name",
        sample_test_results
    )
    
    # Check that slashes are replaced with underscores
    assert reports['pdf'].name == 'company_model-name.pdf'
    assert reports['excel'].name == 'company_model-name.xlsx'


def test_empty_test_results(temp_report_dir):
    """Test report generation with empty test results."""
    generator = ReportGenerator(temp_report_dir)
    
    reports = generator.generate_reports(
        "test-model",
        []
    )
    
    # Should still create files even with no results
    assert reports['pdf'].exists()
    assert reports['excel'].exists()


def test_report_without_metadata(temp_report_dir, sample_test_results):
    """Test report generation without metadata."""
    generator = ReportGenerator(temp_report_dir)
    
    reports = generator.generate_reports(
        "test-model",
        sample_test_results,
        metadata=None
    )
    
    assert reports['pdf'].exists()
    assert reports['excel'].exists()


def test_multiple_reports_same_directory(temp_report_dir, sample_test_results):
    """Test generating multiple reports in the same directory."""
    generator = ReportGenerator(temp_report_dir)
    
    reports1 = generator.generate_reports("model-1", sample_test_results)
    reports2 = generator.generate_reports("model-2", sample_test_results)
    
    assert reports1['pdf'].exists()
    assert reports2['pdf'].exists()
    assert reports1['pdf'] != reports2['pdf']
    assert reports1['excel'] != reports2['excel']


def test_generate_comparison_report(temp_report_dir, sample_test_results):
    """Test generating comparison report for multiple models."""
    from test_suite_loader import TestSuiteLoader
    
    generator = ReportGenerator(temp_report_dir)
    
    # Create mock model results
    all_model_results = [
        {
            'model_name': 'model-1',
            'model_description': 'First test model',
            'test_results': sample_test_results,
            'stats_by_category': {
                'system_override': {'passed': 1, 'failed': 0, 'total': 1},
                'secret_extraction': {'passed': 0, 'failed': 1, 'total': 1}
            },
            'stats_by_severity': {
                'high': {'passed': 1, 'failed': 0, 'total': 1},
                'critical': {'passed': 0, 'failed': 1, 'total': 1}
            },
            'total_tests': 2,
            'passed_tests': 1,
            'failed_tests': 1,
            'pass_rate': 50.0
        },
        {
            'model_name': 'model-2',
            'model_description': 'Second test model',
            'test_results': sample_test_results,
            'stats_by_category': {
                'system_override': {'passed': 1, 'failed': 0, 'total': 1},
                'secret_extraction': {'passed': 1, 'failed': 0, 'total': 1}
            },
            'stats_by_severity': {
                'high': {'passed': 1, 'failed': 0, 'total': 1},
                'critical': {'passed': 1, 'failed': 0, 'total': 1}
            },
            'total_tests': 2,
            'passed_tests': 2,
            'failed_tests': 0,
            'pass_rate': 100.0
        }
    ]
    
    # Load test suite
    test_suite = TestSuiteLoader().load()
    
    comparison_reports = generator.generate_comparison_report(
        all_model_results,
        test_suite,
        '2026-01-14 10:00:00'
    )
    
    assert 'pdf' in comparison_reports
    assert 'excel' in comparison_reports
    assert comparison_reports['pdf'].exists()
    assert comparison_reports['excel'].exists()
    assert comparison_reports['pdf'].name == 'model_comparison.pdf'
    assert comparison_reports['excel'].name == 'model_comparison.xlsx'
