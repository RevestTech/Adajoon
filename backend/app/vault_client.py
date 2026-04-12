"""
Railway Vault Python Client

Drop this file into your Python application and use it to fetch secrets.

Installation:
    pip install requests

Usage:
    from vault_client import VaultClient
    
    vault = VaultClient()
    DATABASE_URL = vault.get("myapp:database_url")
    API_KEY = vault.get("myapp:api_key")
"""

import os
import sys
from typing import Optional
import requests


class VaultClient:
    """Client for Railway KMac Vault."""
    
    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 5
    ):
        """
        Initialize vault client.
        
        Args:
            url: Vault URL (defaults to VAULT_URL env var)
            token: Auth token (defaults to VAULT_TOKEN env var)
            timeout: Request timeout in seconds
        """
        self.base_url = url or os.getenv("VAULT_URL", "http://vault.railway.internal:9999")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.timeout = timeout
        
        if not self.token:
            raise ValueError("VAULT_TOKEN environment variable or token parameter required")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Verify connection on init
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify vault is accessible."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            if not response.ok:
                raise ConnectionError(f"Vault health check failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Cannot connect to vault: {e}")
    
    def get(self, key: str) -> str:
        """
        Get secret value from vault.
        
        Args:
            key: Secret key (e.g., "myapp:database_url")
            
        Returns:
            Secret value as string
            
        Raises:
            KeyError: If key not found
            ConnectionError: If vault unreachable
        """
        try:
            response = requests.get(
                f"{self.base_url}/get/{key}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                raise KeyError(f"Secret not found: {key}")
            
            response.raise_for_status()
            return response.json()["value"]
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to get secret {key}: {e}")
    
    def set(self, key: str, value: str) -> None:
        """
        Store secret in vault.
        
        Args:
            key: Secret key
            value: Secret value
            
        Raises:
            ConnectionError: If vault unreachable
        """
        try:
            response = requests.post(
                f"{self.base_url}/set",
                headers=self.headers,
                json={"key": key, "value": value},
                timeout=self.timeout
            )
            response.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to set secret {key}: {e}")
    
    def delete(self, key: str) -> None:
        """
        Delete secret from vault.
        
        Args:
            key: Secret key to delete
            
        Raises:
            ConnectionError: If vault unreachable
        """
        try:
            response = requests.post(
                f"{self.base_url}/delete/{key}",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to delete secret {key}: {e}")
    
    def list(self) -> list[str]:
        """
        List all secret keys.
        
        Returns:
            List of secret keys
            
        Raises:
            ConnectionError: If vault unreachable
        """
        try:
            response = requests.get(
                f"{self.base_url}/list",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["keys"]
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to list secrets: {e}")
    
    def has(self, key: str) -> bool:
        """
        Check if secret exists.
        
        Args:
            key: Secret key to check
            
        Returns:
            True if exists, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/has/{key}",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["exists"]
            
        except requests.exceptions.RequestException:
            return False


# Convenience function for quick usage
def load_secrets(prefix: str = "") -> dict:
    """
    Load all secrets with optional prefix into a dictionary.
    
    Args:
        prefix: Optional key prefix filter (e.g., "myapp:")
        
    Returns:
        Dictionary of key-value pairs
        
    Example:
        secrets = load_secrets("myapp:")
        DATABASE_URL = secrets["myapp:database_url"]
    """
    vault = VaultClient()
    keys = vault.list()
    
    if prefix:
        keys = [k for k in keys if k.startswith(prefix)]
    
    return {key: vault.get(key) for key in keys}


# Example usage
if __name__ == "__main__":
    # Example 1: Basic usage
    vault = VaultClient()
    
    # Set a secret
    vault.set("test:hello", "world")
    
    # Get a secret
    value = vault.get("test:hello")
    print(f"Secret value: {value}")
    
    # List all secrets
    keys = vault.list()
    print(f"All keys: {keys}")
    
    # Check if exists
    exists = vault.has("test:hello")
    print(f"Exists: {exists}")
    
    # Delete secret
    vault.delete("test:hello")
    
    print("✅ All operations successful!")
    
    # Example 2: Load all app secrets at startup
    print("\nLoading application secrets...")
    try:
        app_secrets = load_secrets("myapp:")
        print(f"Loaded {len(app_secrets)} secrets for myapp")
        
        # Use them
        # DATABASE_URL = app_secrets.get("myapp:database_url")
        # API_KEY = app_secrets.get("myapp:api_key")
        
    except Exception as e:
        print(f"Failed to load secrets: {e}")
        sys.exit(1)
