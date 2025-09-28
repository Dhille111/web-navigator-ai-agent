"""
LLM Adapter for local models (GPT4All, Ollama, LLaMA)
Provides a unified interface for different local LLM backends.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized response from LLM"""
    content: str
    model: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None


class BaseLLMAdapter(ABC):
    """Abstract base class for LLM adapters"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM is available"""
        pass


class GPT4AllAdapter(BaseLLMAdapter):
    """Adapter for GPT4All models"""
    
    def __init__(self, model_path: str, model_name: str = "gpt4all"):
        self.model_path = model_path
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the GPT4All model"""
        try:
            from gpt4all import GPT4All
            self.model = GPT4All(self.model_path)
            logger.info(f"Loaded GPT4All model from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load GPT4All model: {e}")
            self.model = None
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using GPT4All"""
        if not self.model:
            raise RuntimeError("GPT4All model not loaded")
        
        try:
            response = self.model.generate(prompt, **kwargs)
            return LLMResponse(
                content=response,
                model=self.model_name,
                response_time=None
            )
        except Exception as e:
            logger.error(f"GPT4All generation failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if GPT4All is available"""
        return self.model is not None


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for Ollama models"""
    
    def __init__(self, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Ollama client"""
        try:
            import ollama
            self.client = ollama.Client(host=self.base_url)
            logger.info(f"Initialized Ollama client for model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            self.client = None
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Ollama"""
        if not self.client:
            raise RuntimeError("Ollama client not initialized")
        
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                **kwargs
            )
            return LLMResponse(
                content=response['response'],
                model=self.model_name,
                tokens_used=response.get('eval_count', None),
                response_time=response.get('total_duration', None)
            )
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        if not self.client:
            return False
        try:
            # Try to list models to check if Ollama is running
            self.client.list()
            return True
        except:
            return False


class LLaMAAdapter(BaseLLMAdapter):
    """Adapter for LLaMA models using transformers"""
    
    def __init__(self, model_path: str, model_name: str = "llama"):
        self.model_path = model_path
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the LLaMA model"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            logger.info(f"Loaded LLaMA model from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load LLaMA model: {e}")
            self.model = None
            self.tokenizer = None
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using LLaMA"""
        if not self.model or not self.tokenizer:
            raise RuntimeError("LLaMA model not loaded")
        
        try:
            import torch
            
            inputs = self.tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=kwargs.get('max_tokens', 512),
                    temperature=kwargs.get('temperature', 0.7),
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the input prompt from the response
            response = response[len(prompt):].strip()
            
            return LLMResponse(
                content=response,
                model=self.model_name,
                response_time=None
            )
        except Exception as e:
            logger.error(f"LLaMA generation failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if LLaMA is available"""
        return self.model is not None and self.tokenizer is not None


class LLMAdapterFactory:
    """Factory for creating LLM adapters"""
    
    @staticmethod
    def create_adapter(llm_type: str, **kwargs) -> BaseLLMAdapter:
        """Create an LLM adapter based on type"""
        if llm_type.lower() == "gpt4all":
            model_path = kwargs.get('model_path', os.getenv('LLM_MODEL_PATH'))
            if not model_path:
                raise ValueError("model_path is required for GPT4All")
            return GPT4AllAdapter(model_path)
        
        elif llm_type.lower() == "ollama":
            model_name = kwargs.get('model_name', os.getenv('LLM_MODEL_NAME', 'llama2'))
            base_url = kwargs.get('base_url', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
            return OllamaAdapter(model_name, base_url)
        
        elif llm_type.lower() == "llama":
            model_path = kwargs.get('model_path', os.getenv('LLM_MODEL_PATH'))
            if not model_path:
                raise ValueError("model_path is required for LLaMA")
            return LLaMAAdapter(model_path)
        
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")


class LLMManager:
    """Manager for LLM operations with fallback support"""
    
    def __init__(self, primary_adapter: BaseLLMAdapter, fallback_adapters: List[BaseLLMAdapter] = None):
        self.primary_adapter = primary_adapter
        self.fallback_adapters = fallback_adapters or []
        self.current_adapter = primary_adapter
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response with fallback support"""
        adapters_to_try = [self.current_adapter] + self.fallback_adapters
        
        for adapter in adapters_to_try:
            if not adapter.is_available():
                logger.warning(f"Adapter {type(adapter).__name__} not available, trying next...")
                continue
            
            try:
                response = adapter.generate(prompt, **kwargs)
                self.current_adapter = adapter
                return response
            except Exception as e:
                logger.warning(f"Adapter {type(adapter).__name__} failed: {e}")
                continue
        
        raise RuntimeError("All LLM adapters failed")
    
    def is_available(self) -> bool:
        """Check if any adapter is available"""
        return any(adapter.is_available() for adapter in [self.current_adapter] + self.fallback_adapters)


# Example usage and configuration
def create_default_llm_manager() -> LLMManager:
    """Create a default LLM manager with fallback support"""
    adapters = []
    
    # Try to create adapters based on environment
    llm_type = os.getenv('LLM_TYPE', 'gpt4all').lower()
    
    try:
        if llm_type == 'gpt4all':
            adapter = LLMAdapterFactory.create_adapter('gpt4all')
            adapters.append(adapter)
        elif llm_type == 'ollama':
            adapter = LLMAdapterFactory.create_adapter('ollama')
            adapters.append(adapter)
        elif llm_type == 'llama':
            adapter = LLMAdapterFactory.create_adapter('llama')
            adapters.append(adapter)
    except Exception as e:
        logger.warning(f"Failed to create primary adapter: {e}")
    
    # Add fallback adapters
    for fallback_type in ['ollama', 'gpt4all']:
        if fallback_type != llm_type:
            try:
                fallback_adapter = LLMAdapterFactory.create_adapter(fallback_type)
                adapters.append(fallback_adapter)
            except Exception as e:
                logger.warning(f"Failed to create fallback adapter {fallback_type}: {e}")
    
    if not adapters:
        raise RuntimeError("No LLM adapters available")
    
    return LLMManager(adapters[0], adapters[1:])


if __name__ == "__main__":
    # Test the LLM adapter
    try:
        manager = create_default_llm_manager()
        if manager.is_available():
            response = manager.generate("Hello, how are you?")
            print(f"Response: {response.content}")
        else:
            print("No LLM adapters available")
    except Exception as e:
        print(f"Error: {e}")
