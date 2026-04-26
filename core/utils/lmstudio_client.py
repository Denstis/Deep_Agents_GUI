"""
LM Studio Client - HTTP client for interacting with LM Studio server
"""

import logging
from typing import Optional, List
import httpx

logger = logging.getLogger(__name__)


class LMStudioClient:
    """Client for interacting with LM Studio server."""
    
    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url.rstrip("/")
        self.api_key = "lm-studio"  # LM Studio doesn't require a real API key
        logger.debug(f"LMStudioClient initialized with base_url: {self.base_url}")
        
    def get_chat_model(self, model_name: Optional[str] = None, temperature: float = 0.7):
        """Get a ChatOpenAI instance configured for LM Studio."""
        from langchain_openai import ChatOpenAI
        
        logger.info(f"Getting chat model: {model_name or 'local-model'}, temperature: {temperature}")
        return ChatOpenAI(
            base_url=f"{self.base_url}/v1",
            api_key=self.api_key,
            model=model_name or "local-model",
            temperature=temperature,
            streaming=True,
        )
    
    async def check_connection(self) -> bool:
        """Check if LM Studio server is reachable."""
        try:
            logger.debug(f"Checking connection to {self.base_url}/v1/models")
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/models", timeout=5.0)
                connected = response.status_code == 200
                logger.info(f"Connection check result: {connected} (status: {response.status_code})")
                return connected
        except Exception as e:
            logger.error(f"Connection check failed: {str(e)}")
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models from LM Studio."""
        try:
            logger.debug("Fetching available models from LM Studio")
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/models", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    models = [model["id"] for model in data.get("data", [])]
                    logger.info(f"Found {len(models)} models: {models}")
                    return models
        except Exception as e:
            logger.error(f"Failed to get models: {str(e)}")
        return []
    
    async def get_model_info(self, model_id: str) -> dict:
        """Get detailed information about a specific model including max_tokens."""
        try:
            logger.debug(f"Fetching info for model: {model_id}")
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/models/{model_id}", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Model info retrieved: {model_id}")
                    return data
        except Exception as e:
            logger.error(f"Failed to get model info: {str(e)}")
        return {}
