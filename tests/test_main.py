"""
Unit tests for main module
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import main


def test_main():
    """Test that main function runs without errors."""
    try:
        main()
        assert True
    except Exception as e:
        assert False, f"main() raised an exception: {e}"
