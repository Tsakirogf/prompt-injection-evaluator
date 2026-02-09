"""
Hugging Face Endpoint Manager

Manages lifecycle (pause/resume) of Hugging Face Inference Endpoints
to minimize costs by only running endpoints when needed.
"""
import os
import time
import requests
from pathlib import Path
from typing import Optional

# Load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass


class EndpointManager:
    """Manages HuggingFace Inference Endpoint lifecycle."""

    def __init__(self, endpoint_name: str, namespace: str = "tsakirogf"):
        """
        Initialize endpoint manager.

        Args:
            endpoint_name: Name of the endpoint (e.g., 'llama-3-1-8b-instruct-log')
            namespace: HF namespace/username (default: 'tsakirogf')
        """
        self.endpoint_name = endpoint_name
        self.namespace = namespace
        self.api_base = "https://api.endpoints.huggingface.cloud/v2/endpoint"
        self.token = self._get_token()

    @classmethod
    def from_url(cls, endpoint_url: str, namespace: str = "tsakirogf"):
        """
        Create EndpointManager by finding the endpoint that matches the given URL.

        Args:
            endpoint_url: The endpoint URL (e.g., 'https://wacdy6ihswnfwbk1.us-east-1...')
            namespace: HF namespace/username

        Returns:
            EndpointManager instance or None if not found
        """
        # Create temporary instance to access helper methods
        temp = cls.__new__(cls)
        temp.namespace = namespace
        temp.api_base = "https://api.endpoints.huggingface.cloud/v2/endpoint"
        temp.token = temp._get_token()

        # List all endpoints and find match
        endpoints = temp._list_all_endpoints()
        for endpoint in endpoints:
            if endpoint.get('url') == endpoint_url:
                endpoint_name = endpoint.get('name')
                print(f"  ✓ Found endpoint name: {endpoint_name}")
                return cls(endpoint_name, namespace)

        print(f"  ⚠️  Could not find endpoint matching URL: {endpoint_url}")
        return None

    def _get_token(self) -> str:
        """Get HF token from environment."""
        token = (
            os.environ.get('HUGGINGFACE_TOKEN') or
            os.environ.get('HUGGINGFACE_HUB_TOKEN') or
            os.environ.get('HF_TOKEN')
        )
        if not token:
            raise ValueError("No Hugging Face token found. Check .env file.")
        return token

    def _list_all_endpoints(self) -> list:
        """List all endpoints in the namespace."""
        url = f"{self.api_base}/{self.namespace}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result if isinstance(result, list) else result.get('items', [])
        except Exception as e:
            print(f"⚠️  Failed to list endpoints: {e}")
            return []

    def _get_status(self) -> Optional[dict]:
        """Get current endpoint status."""
        url = f"{self.api_base}/{self.namespace}/{self.endpoint_name}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Failed to get endpoint status: {e}")
            return None

    def is_running(self) -> bool:
        """Check if endpoint is currently running."""
        status = self._get_status()
        if not status:
            return False

        state = status.get('status', {}).get('state', '').lower()
        return state == 'running'

    def resume(self, wait: bool = True, max_wait: int = 120) -> bool:
        """
        Resume (start) the endpoint.

        Args:
            wait: If True, wait for endpoint to be running
            max_wait: Maximum seconds to wait

        Returns:
            True if successful, False otherwise
        """
        if self.is_running():
            print(f"  ✓ Endpoint already running")
            return True

        print(f"  ▶ Resuming endpoint: {self.endpoint_name}...")
        url = f"{self.api_base}/{self.namespace}/{self.endpoint_name}/resume"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.post(url, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"  ✓ Resume request sent")

            if not wait:
                return True

            # Wait for endpoint to be running
            print(f"  ⏳ Waiting for endpoint to start (max {max_wait}s)...")
            start_time = time.time()

            while time.time() - start_time < max_wait:
                if self.is_running():
                    elapsed = int(time.time() - start_time)
                    print(f"  ✓ Endpoint running (took {elapsed}s)")
                    return True
                time.sleep(5)

            print(f"  ⚠️  Timeout waiting for endpoint to start")
            return False

        except Exception as e:
            print(f"  ✗ Failed to resume endpoint: {e}")
            return False

    def pause(self) -> bool:
        """
        Pause (stop) the endpoint to save costs.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_running():
            print(f"  ✓ Endpoint already paused")
            return True

        print(f"  ⏸ Pausing endpoint: {self.endpoint_name}...")
        url = f"{self.api_base}/{self.namespace}/{self.endpoint_name}/pause"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.post(url, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"  ✓ Endpoint paused (billing stopped)")
            return True

        except Exception as e:
            print(f"  ✗ Failed to pause endpoint: {e}")
            return False


def extract_endpoint_name(endpoint_url: str) -> Optional[str]:
    """
    Extract endpoint name from URL.

    Example:
        'https://llama-3-1-8b-instruct-log.us-east-1.aws.endpoints.huggingface.cloud'
        -> 'llama-3-1-8b-instruct-log'
    """
    try:
        # Extract subdomain (endpoint name)
        parts = endpoint_url.split('.')
        if len(parts) > 0 and 'https://' in parts[0]:
            name = parts[0].replace('https://', '')
            return name
    except Exception:
        pass
    return None

