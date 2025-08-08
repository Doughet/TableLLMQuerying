"""
OpenAI LLM Service Implementation.

This module provides a concrete implementation of the LLM service interface
for OpenAI's API (compatible with OpenAI, Azure OpenAI, and other OpenAI-compatible APIs).
"""

import logging
import requests
import json
from typing import Dict, Any, List, Optional

from ..llm_service import LLMService, LLMResponse

logger = logging.getLogger(__name__)


class OpenAILLMService(LLMService):
    """OpenAI API implementation of the LLM service."""
    
    def __init__(self, api_key: str, model_id: str = "gpt-3.5-turbo", base_url: str = "https://api.openai.com/v1", **kwargs):
        """
        Initialize OpenAI LLM service.
        
        Args:
            api_key: OpenAI API key
            model_id: Model identifier (default: gpt-3.5-turbo)
            base_url: Base URL for OpenAI API (or compatible service)
            **kwargs: Additional configuration
        """
        super().__init__(api_key=api_key, model_id=model_id, base_url=base_url, **kwargs)
        self.api_key = api_key
        self.model_id = model_id
        self.base_url = base_url.rstrip('/')
        self.timeout = kwargs.get('timeout', 30)
        self.organization = kwargs.get('organization')  # Optional for OpenAI
        
        logger.info(f"OpenAILLMService initialized with model {model_id}")
    
    def generate_completion(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using OpenAI chat completions endpoint."""
        messages = [{"role": "user", "content": prompt}]
        return self.generate_chat_completion(messages, **kwargs)
    
    def generate_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Generate chat completion using OpenAI API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Add organization header if provided
            if self.organization:
                headers["OpenAI-Organization"] = self.organization
            
            payload = {
                "model": self.model_id,
                "messages": messages,
                "max_tokens": kwargs.get('max_tokens', 500),
                "temperature": kwargs.get('temperature', 0.1)
            }
            
            # Add any additional parameters
            for key, value in kwargs.items():
                if key not in ['max_tokens', 'temperature']:
                    payload[key] = value
            
            url = f"{self.base_url}/chat/completions"
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            if not content:
                return LLMResponse(
                    content="",
                    success=False,
                    error="Empty response from API",
                    metadata={"response": result}
                )
            
            return LLMResponse(
                content=content,
                success=True,
                metadata={
                    "model": self.model_id,
                    "usage": result.get("usage", {}),
                    "response_id": result.get("id", ""),
                    "finish_reason": result.get("choices", [{}])[0].get("finish_reason", "")
                }
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request failed: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=f"API request failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI LLM service: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        if not self.api_key:
            return False
        
        try:
            # Test with a minimal request
            test_response = self.generate_completion("test", max_tokens=1, temperature=0)
            return test_response.success
        except Exception:
            return False