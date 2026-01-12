"""
Unit tests for ModelFactory
"""
import sys
import json
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from model_factory import ModelFactory


@pytest.fixture
def sample_config_file():
    """Create a temporary JSON config file for testing."""
    config_data = {
        "models": [
            {
                "name": "test-model-1",
                "description": "Test model 1",
                "requires_auth": False,
                "torch_dtype": "float16"
            },
            {
                "name": "test-model-2",
                "description": "Test model 2",
                "requires_auth": True,
                "torch_dtype": "float32"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink()


def test_model_factory_initialization(sample_config_file):
    """Test that ModelFactory initializes correctly."""
    factory = ModelFactory(sample_config_file)
    assert len(factory) == 2
    assert factory.config_path == Path(sample_config_file)


def test_model_factory_load_models(sample_config_file):
    """Test that models are loaded correctly from JSON."""
    factory = ModelFactory(sample_config_file)
    models = factory.get_all_models()
    
    assert len(models) == 2
    assert models[0]["name"] == "test-model-1"
    assert models[1]["name"] == "test-model-2"


def test_get_next_model(sample_config_file):
    """Test getting models one at a time."""
    factory = ModelFactory(sample_config_file)
    
    model1 = factory.get_next_model()
    assert model1 is not None
    assert model1["name"] == "test-model-1"
    
    model2 = factory.get_next_model()
    assert model2 is not None
    assert model2["name"] == "test-model-2"
    
    model3 = factory.get_next_model()
    assert model3 is None  # No more models


def test_reset(sample_config_file):
    """Test resetting the iterator."""
    factory = ModelFactory(sample_config_file)
    
    # Get both models
    factory.get_next_model()
    factory.get_next_model()
    
    # Reset and get first model again
    factory.reset()
    model = factory.get_next_model()
    assert model["name"] == "test-model-1"


def test_get_model_by_name(sample_config_file):
    """Test retrieving a specific model by name."""
    factory = ModelFactory(sample_config_file)
    
    model = factory.get_model_by_name("test-model-2")
    assert model is not None
    assert model["name"] == "test-model-2"
    assert model["torch_dtype"] == "float32"
    
    # Test non-existent model
    model = factory.get_model_by_name("non-existent")
    assert model is None


def test_iterator(sample_config_file):
    """Test that the factory is iterable."""
    factory = ModelFactory(sample_config_file)
    
    models = list(factory)
    assert len(models) == 2
    assert models[0]["name"] == "test-model-1"
    assert models[1]["name"] == "test-model-2"


def test_file_not_found():
    """Test that FileNotFoundError is raised for missing config."""
    with pytest.raises(FileNotFoundError):
        ModelFactory("/non/existent/path.json")


def test_empty_models():
    """Test that ValueError is raised for empty models list."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"models": []}, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            ModelFactory(temp_path)
    finally:
        Path(temp_path).unlink()


def test_default_config_path():
    """Test using default config path."""
    # This test assumes the default config exists
    project_root = Path(__file__).parent.parent
    default_config = project_root / "config" / "models.json"
    
    if default_config.exists():
        factory = ModelFactory()
        assert factory.config_path == default_config
        assert len(factory) > 0
