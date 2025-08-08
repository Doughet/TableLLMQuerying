"""
Example: Creating a Custom LLM Service

This example shows how to create a custom LLM service that can be plugged
into the table querying system. This example implements a local Ollama service.
"""

import logging
import requests
from typing import Dict, Any, List

from src.services.llm_service import LLMService, LLMResponse

logger = logging.getLogger(__name__)


class OllamaLLMService(LLMService):
    """
    Custom LLM service for Ollama (local LLM server).
    
    This demonstrates how to implement the LLMService interface
    for a custom LLM provider.
    """
    
    def __init__(self, model_id: str = "llama2", base_url: str = "http://localhost:11434", **kwargs):
        """
        Initialize Ollama LLM service.
        
        Args:
            model_id: Model name in Ollama (e.g., 'llama2', 'mistral')
            base_url: Ollama server URL
            **kwargs: Additional configuration
        """
        super().__init__(model_id=model_id, base_url=base_url, **kwargs)
        self.model_id = model_id
        self.base_url = base_url.rstrip('/')
        self.timeout = kwargs.get('timeout', 60)  # Ollama can be slower
        
        logger.info(f"OllamaLLMService initialized with model {model_id} at {base_url}")
    
    def generate_completion(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using Ollama API."""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model_id,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', 0.1),
                    "num_predict": kwargs.get('max_tokens', 500)
                }
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("response", "").strip()
            
            if not content:
                return LLMResponse(
                    content="",
                    success=False,
                    error="Empty response from Ollama",
                    metadata={"response": result}
                )
            
            return LLMResponse(
                content=content,
                success=True,
                metadata={
                    "model": self.model_id,
                    "eval_count": result.get("eval_count", 0),
                    "eval_duration": result.get("eval_duration", 0)
                }
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=f"API request failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Ollama LLM service: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    def generate_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        Generate chat completion using Ollama.
        
        Note: Ollama doesn't have native chat completions, so we convert
        messages to a single prompt.
        """
        # Convert messages to single prompt
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        full_prompt = "\n\n".join(prompt_parts)
        
        return self.generate_completion(full_prompt, **kwargs)
    
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            
            return any(self.model_id in name for name in model_names)
        except Exception:
            return False


def example_usage():
    """Example of how to use the custom Ollama service."""
    
    # Import the service factory
    from src.services.service_factory import ServiceFactory, ServiceConfig
    
    # Register the custom service
    ServiceFactory.register_llm_service("ollama", OllamaLLMService)
    
    # Create configuration for the custom service
    config = ServiceConfig(
        llm_service_type="ollama",
        llm_model_id="llama2",  # or "mistral", "codellama", etc.
        llm_base_url="http://localhost:11434",
        llm_timeout=60,
        db_service_type="sqlite",
        db_path="tables.db"
    )
    
    # Create services
    try:
        llm_service, db_service = ServiceFactory.create_services(config)
        
        # Test the LLM service
        response = llm_service.generate_completion("Hello, how are you?")
        if response.success:
            print(f"LLM Response: {response.content}")
        else:
            print(f"LLM Error: {response.error}")
        
        # The services can now be used with the table processing system
        print("Custom Ollama LLM service is ready to use!")
        
    except Exception as e:
        print(f"Error creating services: {e}")


if __name__ == "__main__":
    # Run the example
    example_usage()