"""
Test Suite Loader Service

Loads and manages test cases for prompt injection evaluation.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import warnings


@dataclass
class TestCase:
    """
    Represents a single test case for prompt injection evaluation.
    """
    id: str
    name: str
    category: str
    description: str
    system_prompt: str
    user_prompt: str
    expected_behavior: str
    severity: str
    user_prompt_template: Optional[str] = None
    page_content: Optional[str] = None
    protected_secret: Optional[str] = None
    expected_keywords_absent: List[str] = field(default_factory=list)
    expected_keywords_present: List[str] = field(default_factory=list)
    
    def get_user_prompt(self) -> str:
        """
        Get the final user prompt, applying template if needed.
        
        Returns:
            The formatted user prompt string.
        """
        if self.user_prompt_template and self.page_content:
            return self.user_prompt_template.format(page_content=self.page_content)
        return self.user_prompt


@dataclass
class TestSuite:
    """
    Represents a complete test suite with metadata.
    """
    name: str
    version: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    
    def get_by_id(self, test_id: str) -> Optional[TestCase]:
        """Get a test case by its ID."""
        for test_case in self.test_cases:
            if test_case.id == test_id:
                return test_case
        return None
    
    def get_by_category(self, category: str) -> List[TestCase]:
        """Get all test cases in a specific category."""
        return [tc for tc in self.test_cases if tc.category == category]
    
    def get_by_severity(self, severity: str) -> List[TestCase]:
        """Get all test cases with a specific severity level."""
        return [tc for tc in self.test_cases if tc.severity == severity]
    
    def __len__(self) -> int:
        """Return the number of test cases."""
        return len(self.test_cases)
    
    def __iter__(self):
        """Iterate through test cases."""
        return iter(self.test_cases)


class TestSuiteLoader:
    """
    Service for loading test suites from JSON configuration files.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the TestSuiteLoader.
        
        Args:
            config_path: Path to the JSON configuration file.
                        If None, uses default config/test_cases.json
        """
        if config_path is None:
            # If a directory of per-category prompt case files exists, load them all and merge.
            project_root = Path(__file__).parent.parent
            dir_path = project_root / "config" / "prompt_cases"
            primary = project_root / "config" / "prompt_injection_cases.json"
            fallback = project_root / "config" / "test_cases.json"

            if dir_path.exists() and dir_path.is_dir():
                config_path = dir_path
            elif primary.exists():
                config_path = primary
            elif fallback.exists():
                warnings.warn(
                    "Default test cases filename 'config/test_cases.json' is deprecated; found and loading it as a fallback. Please rename to 'config/prompt_injection_cases.json' or create 'config/prompt_cases/' directory.",
                    DeprecationWarning
                )
                config_path = fallback
            else:
                # Prefer directory path by default
                config_path = dir_path

        self.config_path = Path(config_path)
        self._test_suite: Optional[TestSuite] = None
    
    def load(self) -> TestSuite:
        """
        Load the test suite from JSON file.
        
        Returns:
            TestSuite object containing all test cases.
        
        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If JSON is invalid or missing required fields.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Test cases configuration file not found: {self.config_path}"
            )
        
        if self.config_path.is_dir():
            # Merge all JSON files in directory
            merged_suite = TestSuite(name='Merged Prompt Cases', version='1.0', description='Merged per-category prompt cases')
            files = sorted([p for p in self.config_path.iterdir() if p.suffix.lower() == '.json'])
            if not files:
                raise ValueError(f"No JSON files found in directory: {self.config_path}")

            for p in files:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Merge metadata (concatenate names/descriptions)
                suite_info = data.get('test_suite', {})
                merged_suite.name = merged_suite.name + ' / ' + suite_info.get('name', '')
                merged_suite.description = (merged_suite.description + ' ' + suite_info.get('description', '')).strip()

                test_cases_data = data.get('test_cases', [])
                for tc_data in test_cases_data:
                    test_case = TestCase(
                        id=tc_data['id'],
                        name=tc_data['name'],
                        category=tc_data['category'],
                        description=tc_data['description'],
                        system_prompt=tc_data.get('system_prompt', ''),
                        user_prompt=tc_data.get('user_prompt', ''),
                        expected_behavior=tc_data.get('expected_behavior', ''),
                        severity=tc_data.get('severity', 'low'),
                        user_prompt_template=tc_data.get('user_prompt_template'),
                        page_content=tc_data.get('page_content'),
                        protected_secret=tc_data.get('protected_secret'),
                        expected_keywords_absent=tc_data.get('expected_keywords_absent', []),
                        expected_keywords_present=tc_data.get('expected_keywords_present', [])
                    )
                    merged_suite.test_cases.append(test_case)

            self._test_suite = merged_suite
            return merged_suite
        else:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Parse test suite metadata
            suite_info = data.get('test_suite', {})
            test_suite = TestSuite(
                name=suite_info.get('name', 'Unnamed Test Suite'),
                version=suite_info.get('version', '1.0'),
                description=suite_info.get('description', '')
            )

            # Parse test cases
            test_cases_data = data.get('test_cases', [])
            if not test_cases_data:
                raise ValueError(
                    f"No test cases found in configuration: {self.config_path}"
                )

            for tc_data in test_cases_data:
                test_case = TestCase(
                    id=tc_data['id'],
                    name=tc_data['name'],
                    category=tc_data['category'],
                    description=tc_data['description'],
                    system_prompt=tc_data['system_prompt'],
                    user_prompt=tc_data.get('user_prompt', ''),
                    expected_behavior=tc_data['expected_behavior'],
                    severity=tc_data['severity'],
                    user_prompt_template=tc_data.get('user_prompt_template'),
                    page_content=tc_data.get('page_content'),
                    protected_secret=tc_data.get('protected_secret'),
                    expected_keywords_absent=tc_data.get('expected_keywords_absent', []),
                    expected_keywords_present=tc_data.get('expected_keywords_present', [])
                )
                test_suite.test_cases.append(test_case)

        self._test_suite = test_suite
        return test_suite
    
    def get_test_suite(self) -> TestSuite:
        """
        Get the loaded test suite.
        
        Returns:
            TestSuite object. Loads it if not already loaded.
        """
        if self._test_suite is None:
            return self.load()
        return self._test_suite
    
    def reload(self) -> TestSuite:
        """
        Force reload the test suite from disk.
        
        Returns:
            Newly loaded TestSuite object.
        """
        self._test_suite = None
        return self.load()
    
    def __repr__(self) -> str:
        """String representation of the loader."""
        loaded = "loaded" if self._test_suite else "not loaded"
        return f"TestSuiteLoader(config_path='{self.config_path}', status={loaded})"
