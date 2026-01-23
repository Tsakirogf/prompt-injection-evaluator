"""
Model Inference Module

Handles loading and running inference on LLM models.
"""
from typing import Dict, Any, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


class ModelInference:
    """
    Handles model loading and inference for evaluation.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize model inference.
        
        Args:
            model_config: Model configuration dictionary
        """
        self.model_config = model_config
        self.model_name = model_config['name']
        self.model = None
        self.tokenizer = None
        self.pipe = None
        
    def load(self) -> None:
        """Load the model and tokenizer."""
        print(f"    Loading model: {self.model_name}...")
        
        # Determine torch dtype
        dtype_str = self.model_config.get('torch_dtype', 'float16')
        torch_dtype = torch.float16 if dtype_str == 'float16' else torch.float32
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        
        # Set padding token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch_dtype,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Create text generation pipeline
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            return_full_text=False
        )
        
        print(f"    ✓ Model loaded successfully")
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a response from the model.
        
        Args:
            system_prompt: System prompt/instructions
            user_prompt: User's input prompt
        
        Returns:
            Model's generated response
        """
        if self.pipe is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        
        # Format the prompt
        full_prompt = self._format_prompt(system_prompt, user_prompt)
        
        try:
            # Generate response
            result = self.pipe(full_prompt)
            output = result[0]['generated_text'].strip()
            return output
        except Exception as e:
            return f"[ERROR] Failed to generate response: {str(e)}"
    
    def _format_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """
        Format the prompt based on model requirements.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
        
        Returns:
            Formatted prompt string
        """
        # Check if model has a chat template
        if hasattr(self.tokenizer, 'apply_chat_template') and self.tokenizer.chat_template:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            try:
                return self.tokenizer.apply_chat_template(
                    messages, 
                    tokenize=False,
                    add_generation_prompt=True
                )
            except Exception:
                # Fall back to simple format if chat template fails
                pass
        
        # Simple format for models without chat templates
        return f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
    
    def unload(self) -> None:
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            del self.tokenizer
            del self.pipe
            self.model = None
            self.tokenizer = None
            self.pipe = None
            
            # Clear CUDA cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
