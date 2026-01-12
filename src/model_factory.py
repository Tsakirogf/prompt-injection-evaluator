"""
Model Factory Module

Provides a factory for loading pretrained model configurations from JSON
and returning them one at a time.
"""
import json
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List


class ModelFactory:
    """
    Factory for managing and iterating through pretrained model configurations.
    
    This class reads model configurations from a JSON file and provides
    methods to access them one at a time or all at once.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ModelFactory.
        
        Args:
            config_path: Path to the JSON configuration file.
                        If None, uses default config/models.json
        """
        if config_path is None:
            # Default to config/models.json in project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "models.json"
        
        self.config_path = Path(config_path)
        self._models: List[Dict[str, Any]] = []
        self._current_index = 0
        self._load_models()
    
    def _load_models(self) -> None:
        """Load model configurations from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Model configuration file not found: {self.config_path}"
            )
        
        with open(self.config_path, 'r') as f:
            data = json.load(f)
        
        self._models = data.get('models', [])
        
        if not self._models:
            raise ValueError(
                f"No models found in configuration file: {self.config_path}"
            )
    
    def get_next_model(self) -> Optional[Dict[str, Any]]:
        """
        Get the next model configuration.
        
        Returns:
            Dictionary containing model configuration, or None if no more models.
        """
        if self._current_index >= len(self._models):
            return None
        
        model = self._models[self._current_index]
        self._current_index += 1
        return model
    
    def reset(self) -> None:
        """Reset the iterator to start from the beginning."""
        self._current_index = 0
    
    def get_all_models(self) -> List[Dict[str, Any]]:
        """
        Get all model configurations.
        
        Returns:
            List of all model configuration dictionaries.
        """
        return self._models.copy()
    
    def get_model_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific model configuration by name.
        
        Args:
            name: The model name to search for.
        
        Returns:
            Dictionary containing model configuration, or None if not found.
        """
        for model in self._models:
            if model.get('name') == name:
                return model.copy()
        return None
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate through all models.
        
        Returns:
            Iterator over model configurations.
        """
        return iter(self._models)
    
    def __len__(self) -> int:
        """Return the number of models in the configuration."""
        return len(self._models)
    
    def __repr__(self) -> str:
        """String representation of the factory."""
        return (
            f"ModelFactory(config_path='{self.config_path}', "
            f"models={len(self._models)})"
        )
