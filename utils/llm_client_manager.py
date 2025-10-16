import logging
from typing import Dict, Any, Optional

import google.generativeai as genai
import openai
import anthropic
from anthropic import Anthropic, AsyncAnthropic
from openai import OpenAI, AsyncOpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LLMClientManager:
    """
    Manages the initialization and configuration of various LLM API clients.
    """

    def __init__(self, api_keys: Dict[str, str], spinner_update_callback: Optional[Any] = None):
        self.api_keys = api_keys
        self.spinner_update_callback = spinner_update_callback
        self.clients = {} # Stores initialized clients

    def get_client(self, model_name: str) -> Optional[Any]:
        """
        Returns an initialized API client for the given model name.
        Initializes the client if it hasn't been already.
        """
        model_prefix = model_name.split('-')[0]
        if model_prefix not in self.clients:
            self._initialize_api_client(model_prefix)
        return self.clients.get(model_prefix)

    def _initialize_api_client(self, model_prefix: str):
        """
        Initializes a specific API client based on the model prefix.
        """
        api_key = self.api_keys.get(model_prefix)

        if not api_key:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Warning: API key not provided for model prefix: {model_prefix}.")
            logging.warning(f"API key not provided for model prefix: {model_prefix}.")
            return

        try:
            if model_prefix == 'gemini':
                genai.configure(api_key=api_key)
                self.clients['gemini'] = genai
                if self.spinner_update_callback:
                    self.spinner_update_callback("Successfully configured Gemini API")
                logging.info("Successfully configured Gemini API")
            elif model_prefix == 'gpt':
                self.clients['gpt'] = AsyncOpenAI(api_key=api_key)
                if self.spinner_update_callback:
                    self.spinner_update_callback("Successfully configured OpenAI API")
                logging.info("Successfully configured OpenAI API")
            elif model_prefix == 'claude':
                self.clients['claude'] = AsyncAnthropic(api_key=api_key)
                if self.spinner_update_callback:
                    self.spinner_update_callback("Successfully configured Anthropic API")
                logging.info("Successfully configured Anthropic API")
            else:
                if self.spinner_update_callback:
                    self.spinner_update_callback(f"Warning: No API client configured for model prefix: {model_prefix}")
                logging.warning(f"No API client configured for model prefix: {model_prefix}")
        except Exception as e:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Error: Failed to configure {model_prefix} API: {e}")
            logging.error(f"Failed to configure API client for {model_prefix}: {e}")
