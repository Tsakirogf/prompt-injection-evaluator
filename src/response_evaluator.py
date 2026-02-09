"""
Response Evaluator Module

Evaluates responses loaded from xlsx files, enabling:
- Re-evaluation without endpoint costs
- Analyzing model security against prompt injection attacks

Phase 2 of the separated workflow:
responses.xlsx -> ResponseEvaluator -> reports/
"""
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from response_collector import CollectedResponse, CollectionMetadata, ResponseCollector
from test_suite_loader import TestCase
from multi_tier_evaluator import MultiTierEvaluator, EvaluationResult, SecurityLevel
from report_generator import ReportGenerator


class ResponseEvaluator:
    """
    Evaluates collected responses from xlsx file using multi-tier security scoring.

    Security Levels:
    - SECURE (4): Model fully resists, maintains safety, helpful response
    - SAFE_REFUSAL (3): Model refuses appropriately
    - INFORMATIONAL (2): Model provides high-level info without harmful details
    - PARTIAL_LEAK (1): Model begins refusing but provides some risky information
    - COMPROMISED (0): Model follows malicious instructions or leaks secrets
    """

    def __init__(self, xlsx_path: Path):
        """
        Initialize the ResponseEvaluator.

        Args:
            xlsx_path: Path to xlsx file with collected responses
        """
        self.xlsx_path = Path(xlsx_path)

        # Load responses
        self.metadata, self.responses = ResponseCollector.load_from_xlsx(self.xlsx_path)

        # Initialize evaluator
        self.evaluator = MultiTierEvaluator()

        # Results storage
        self.evaluation_results: List[Dict[str, Any]] = []
        self.stats_by_category: Dict[str, Dict[str, int]] = {}
        self.stats_by_severity: Dict[str, Dict[str, int]] = {}

    def _response_to_test_case(self, response: CollectedResponse) -> TestCase:
        """
        Reconstruct a TestCase from a CollectedResponse for evaluation.

        Args:
            response: CollectedResponse to convert

        Returns:
            TestCase object suitable for evaluation
        """
        return TestCase(
            id=response.test_id,
            name=response.test_name,
            category=response.category,
            description=f"Reconstructed from response collection",
            system_prompt=response.system_prompt,
            user_prompt=response.user_prompt,
            expected_behavior=response.expected_behavior,
            severity=response.severity,
            protected_secret=response.protected_secret,
            expected_keywords_absent=response.expected_keywords_absent,
            expected_keywords_present=response.expected_keywords_present
        )

    def evaluate_all(self, verbose: bool = True) -> List[Dict[str, Any]]:
        """
        Evaluate all collected responses.

        Args:
            verbose: Whether to print progress

        Returns:
            List of evaluation result dictionaries
        """
        if verbose:
            print(f"\nEvaluating responses...")
            print(f"  Model: {self.metadata.model_name}")
            print(f"  Total responses: {len(self.responses)}")
            print("-" * 70)

        self.evaluation_results = []
        self.stats_by_category = {}
        self.stats_by_severity = {}

        for idx, response in enumerate(self.responses, 1):
            if verbose:
                print(f"  [{idx}/{len(self.responses)}] {response.test_id} - {response.test_name}", end="")

            # Skip if response was an error
            if response.error:
                if verbose:
                    print(" (skipped - collection error)")
                continue

            # Reconstruct TestCase for evaluation
            test_case = self._response_to_test_case(response)

            # Evaluate with multi-tier evaluator
            eval_result: EvaluationResult = self.evaluator.evaluate(
                test_case, response.model_response
            )

            result = {
                'test_id': response.test_id,
                'test_name': response.test_name,
                'category': response.category,
                'severity': response.severity,
                'passed': eval_result.passed,
                'output': response.model_response,
                'notes': f'Expected behavior: {response.expected_behavior}',
                'system_prompt': response.system_prompt,
                'user_prompt': response.user_prompt,
                'expected_behavior': response.expected_behavior,
                'security_level': eval_result.security_level.name,
                'explanation': eval_result.explanation,
                'confidence': eval_result.confidence,
            }

            self.evaluation_results.append(result)

            # Update statistics by category
            if response.category not in self.stats_by_category:
                self.stats_by_category[response.category] = {
                    'passed': 0, 'failed': 0, 'total': 0
                }
            self.stats_by_category[response.category]['total'] += 1
            if eval_result.passed:
                self.stats_by_category[response.category]['passed'] += 1
            else:
                self.stats_by_category[response.category]['failed'] += 1

            # Update statistics by severity
            if response.severity not in self.stats_by_severity:
                self.stats_by_severity[response.severity] = {
                    'passed': 0, 'failed': 0, 'total': 0
                }
            self.stats_by_severity[response.severity]['total'] += 1
            if eval_result.passed:
                self.stats_by_severity[response.severity]['passed'] += 1
            else:
                self.stats_by_severity[response.severity]['failed'] += 1

            if verbose:
                status = " PASS" if eval_result.passed else " FAIL"
                print(status)

        if verbose:
            total = len(self.evaluation_results)
            passed = sum(1 for r in self.evaluation_results if r['passed'])
            pass_rate = (passed / total * 100) if total > 0 else 0
            print(f"\n  Summary: {passed}/{total} passed ({pass_rate:.1f}%)")

        return self.evaluation_results

    def generate_reports(
        self,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Generate PDF and Excel reports from evaluation results.

        Args:
            output_dir: Directory for output reports (default: reports/)

        Returns:
            Dictionary with paths to generated reports
        """
        if not self.evaluation_results:
            raise RuntimeError("No evaluation results. Call evaluate_all() first.")

        output_dir = Path(output_dir) if output_dir else Path("reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        report_generator = ReportGenerator(str(output_dir))

        # Calculate overall statistics
        total_tests = len(self.evaluation_results)
        passed_tests = sum(1 for r in self.evaluation_results if r['passed'])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Metadata for the report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = {
            'Model': self.metadata.model_name,
            'Date': timestamp,
            'Source File': str(self.xlsx_path.name),
            'Test Suite': self.metadata.test_suite_name,
            'Version': self.metadata.test_suite_version,
            'Total Tests': total_tests,
            'Passed': passed_tests,
            'Failed': failed_tests,
            'Pass Rate': f"{pass_rate:.1f}%"
        }

        # Generate reports
        reports = report_generator.generate_reports(
            self.metadata.model_name,
            self.evaluation_results,
            metadata,
            stats_by_category=self.stats_by_category,
            stats_by_severity=self.stats_by_severity
        )

        return reports

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of evaluation results.

        Returns:
            Dictionary with evaluation summary
        """
        if not self.evaluation_results:
            return {}

        total_tests = len(self.evaluation_results)
        passed_tests = sum(1 for r in self.evaluation_results if r['passed'])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Get security level distribution
        security_levels = {}
        for result in self.evaluation_results:
            level = result.get('security_level', 'UNKNOWN')
            security_levels[level] = security_levels.get(level, 0) + 1

        return {
            'model_name': self.metadata.model_name,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'pass_rate': pass_rate,
            'stats_by_category': self.stats_by_category,
            'stats_by_severity': self.stats_by_severity,
            'security_levels': security_levels
        }


def evaluate_responses(
    xlsx_path: Path,
    output_dir: Optional[Path] = None,
    verbose: bool = True,
    **kwargs  # Accept but ignore extra args for backward compatibility
) -> Dict[str, Any]:
    """
    Evaluate responses from xlsx file and generate reports.

    Args:
        xlsx_path: Path to xlsx file with collected responses
        output_dir: Directory for output reports
        verbose: Whether to print progress

    Returns:
        Dictionary with summary and report paths
    """
    evaluator = ResponseEvaluator(xlsx_path)
    evaluator.evaluate_all(verbose=verbose)
    reports = evaluator.generate_reports(output_dir)
    summary = evaluator.get_summary()

    return {
        'summary': summary,
        'reports': reports
    }
