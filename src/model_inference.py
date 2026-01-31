"""
Model Inference Module

Handles loading and running inference on LLM models.
"""
from typing import Dict, Any
import os
import time
from pathlib import Path
import torch
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env in project root
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # python-dotenv not installed, skip
    pass


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
        
        # Remote endpoint configuration
        self.is_remote = model_config.get('remote_type') in ['hf_inference_api', 'hf_inference_endpoint']
        self.remote_type = model_config.get('remote_type')
        self.endpoint_url = model_config.get('endpoint_url')
        self.requires_auth = model_config.get('requires_auth', False)

    def load(self) -> None:
        """Load the model and tokenizer."""
        print(f"    Loading model: {self.model_name}...")
        
        # Handle remote endpoints
        if self.is_remote:
            if not self.endpoint_url:
                raise ValueError(f"Remote model {self.model_name} missing endpoint_url")

            # Check for placeholder URL
            if "REPLACE_WITH" in self.endpoint_url or self.endpoint_url == "":
                raise ValueError(
                    f"Remote model {self.model_name} has placeholder endpoint_url.\n"
                    f"Please update the endpoint_url in config/models.json with your actual endpoint URL."
                )

            # Ensure URL doesn't have trailing slash
            self.endpoint_url = self.endpoint_url.rstrip('/')

            # Get API token from environment or HF cache
            if self.requires_auth:
                token = self._get_hf_token()
                if not token:
                    raise ValueError(
                        "Remote model requires authentication but no Hugging Face token found.\n"
                        "Please check .env file or set HUGGINGFACE_HUB_TOKEN environment variable"
                    )
                self.auth_header = f"Bearer {token}"
            else:
                self.auth_header = None

            print(f"    ✓ Remote endpoint configured: {self.endpoint_url}")
            return

        # Handle local models
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
    
    def _get_hf_token(self) -> str:
        """
        Get Hugging Face token from multiple sources.
        Checks in order: .env file, environment variables, HF cache.

        Returns:
            Token string or None if not found
        """
        # Check .env file first (via HUGGINGFACE_TOKEN)
        token = os.environ.get('HUGGINGFACE_TOKEN')
        if token:
            return token

        # Check standard environment variables
        token = os.environ.get('HUGGINGFACE_HUB_TOKEN') or os.environ.get('HF_TOKEN')
        if token:
            return token

        # Try to get from huggingface_hub cache
        try:
            from huggingface_hub import HfFolder
            token = HfFolder.get_token()
            if token:
                return token
        except ImportError:
            pass

        # Try to read from token file directly (transformers cache location)
        try:
            token_path = os.path.expanduser("~/.huggingface/token")
            if os.path.exists(token_path):
                with open(token_path, 'r') as f:
                    token = f.read().strip()
                    if token:
                        return token
        except Exception:
            pass

        return None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a response from the model.
        
        Args:
            system_prompt: System prompt/instructions
            user_prompt: User's input prompt
        
        Returns:
            Model's generated response
        """
        # Handle remote endpoints
        if self.is_remote:
            return self._generate_remote(system_prompt, user_prompt)

        # Handle local models
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

    def _generate_remote(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        """
        Generate response using remote Hugging Face Inference API.

        Args:
            system_prompt: System prompt/instructions
            user_prompt: User's input prompt
            max_retries: Maximum number of retry attempts

        Returns:
            Model's generated response
        """
        # Check if this is a vLLM endpoint (try chat completions API first)
        is_vllm = self.model_config.get('remote_type') == 'hf_inference_endpoint'

        if is_vllm:
            # Try vLLM OpenAI-compatible chat completions API
            return self._generate_vllm_chat(system_prompt, user_prompt, max_retries)
        else:
            # Use standard HF Inference API format
            return self._generate_hf_inference(system_prompt, user_prompt, max_retries)

    def _generate_vllm_chat(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        """Generate response using vLLM OpenAI-compatible chat completions API."""
        # Prepare request headers
        headers = {"Content-Type": "application/json"}
        if self.auth_header:
            headers["Authorization"] = self.auth_header

        # Use OpenAI chat format for vLLM
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 256,
            "temperature": 0.7
        }

        # Try v1/chat/completions endpoint first
        chat_url = f"{self.endpoint_url}/v1/chat/completions"

        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    chat_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                # If 404, try root endpoint with standard format
                if response.status_code == 404 and attempt == 0:
                    print(f"      Chat API not found, trying standard format...")
                    return self._generate_hf_inference(system_prompt, user_prompt, max_retries)

                # Handle rate limiting (503) and model loading (503)
                if response.status_code == 503:
                    try:
                        error_data = response.json()
                        if "loading" in error_data.get("error", "").lower():
                            wait_time = error_data.get("estimated_time", 20)
                            print(f"      Model is loading, waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                    except:
                        pass
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"      Service unavailable, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue

                # Raise for other error status codes
                response.raise_for_status()

                # Parse OpenAI-format response
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"].strip()

                return str(result).strip()

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"      Request timeout, retrying...")
                    continue
                return "[ERROR] Request timeout after multiple retries"
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"      Request failed: {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return f"[ERROR] Failed to generate response: {str(e)}"
            except Exception as e:
                return f"[ERROR] Unexpected error: {str(e)}"

        return "[ERROR] Failed after maximum retries"

    def _generate_hf_inference(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        """Generate response using standard HF Inference API format."""
        # Format the prompt
        full_prompt = self._format_prompt_remote(system_prompt, user_prompt)

        # Prepare request headers
        headers = {"Content-Type": "application/json"}
        if self.auth_header:
            headers["Authorization"] = self.auth_header

        # Prepare request payload
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 256,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            }
        }

        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.endpoint_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                # Handle rate limiting (503) and model loading (503)
                if response.status_code == 503:
                    try:
                        error_data = response.json()
                        if "loading" in error_data.get("error", "").lower():
                            wait_time = error_data.get("estimated_time", 20)
                            print(f"      Model is loading, waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                    except:
                        pass
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"      Service unavailable, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue

                # Raise for other error status codes
                response.raise_for_status()

                # Parse response
                result = response.json()

                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict) and "generated_text" in result[0]:
                        return result[0]["generated_text"].strip()
                    elif isinstance(result[0], str):
                        return result[0].strip()
                elif isinstance(result, dict) and "generated_text" in result:
                    return result["generated_text"].strip()

                return str(result).strip()

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"      Request timeout, retrying...")
                    continue
                return "[ERROR] Request timeout after multiple retries"
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"      Request failed: {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return f"[ERROR] Failed to generate response: {str(e)}"
            except Exception as e:
                return f"[ERROR] Unexpected error: {str(e)}"

        return "[ERROR] Failed after maximum retries"

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
        if self.tokenizer and hasattr(self.tokenizer, 'apply_chat_template') and self.tokenizer.chat_template:
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
    
    def _format_prompt_remote(self, system_prompt: str, user_prompt: str) -> str:
        """
        Format the prompt for remote API calls.
        Uses appropriate format based on model.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            Formatted prompt string
        """
        # Detect model family from model name
        model_lower = self.model_name.lower()

        # Llama 3.x format
        if 'llama-3' in model_lower or 'llama3' in model_lower:
            return f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

        # Mistral/Mixtral format
        elif 'mistral' in model_lower or 'mixtral' in model_lower:
            return f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]"

        # Default format (simple)
        else:
            return f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"

    def unload(self) -> None:
        """Unload the model to free memory."""
        # Remote endpoints don't need unloading
        if self.is_remote:
            return

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
