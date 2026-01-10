import streamlit as st
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._api_keys = self._load_api_keys()
        self._default_model = self._load_default_model()
        self._available_models = self._load_available_models()
        logger.info("ConfigManager initialized.")

    def _load_api_keys(self) -> Dict[str, str]:
        """Loads API keys from Streamlit secrets."""
        api_keys = {
            "gemini": st.secrets.get("GEMINI_API_KEY", ""),
            "gpt": st.secrets.get("OPENAI_API_KEY", ""),
            "claude": st.secrets.get("ANTHROPIC_API_KEY", "")
        }
        # Filter out empty keys for better management
        return {k: v for k, v in api_keys.items() if v}

    def _load_default_model(self) -> str:
        """Loads the default model name from Streamlit secrets or provides a fallback."""
        return st.secrets.get("DEFAULT_LLM_MODEL", "gemini-2.5-flash")

    def _load_available_models(self) -> Dict[str, Any]:
        """
        Loads available models and their configurations from Streamlit secrets.
        Expected format in secrets.toml:
        [models.gemini]
        gemini-2.5-flash = { display_name = "Gemini 2.5 Flash", provider = "gemini" }
        gemini-1.5-pro = { display_name = "Gemini 1.5 Pro", provider = "gemini" }

        [models.openai]
        gpt-4o = { display_name = "GPT-4o", provider = "gpt" }
        gpt-3.5-turbo = { display_name = "GPT-3.5 Turbo", provider = "gpt" }

        [models.anthropic]
        claude-3-opus-20240229 = { display_name = "Claude 3 Opus", provider = "claude" }
        
        In production, fails loudly if secrets are missing. In development, uses hardcoded fallbacks.
        """
        available_models = {}
        if "models" in st.secrets:
            for provider_key, models_dict in st.secrets["models"].items():
                for model_id, model_info in models_dict.items():
                    available_models[model_id] = {
                        "display_name": model_info.get("display_name", model_id),
                        "provider": model_info.get("provider", provider_key)
                    }
        
        # Fail loudly if no models are found in secrets (production mode)
        if not available_models:
            is_development = os.environ.get("STREAMLIT_ENV", "production").lower() == "development"
            if is_development:
                logger.warning("No LLM models found in st.secrets. Using hardcoded defaults (development mode only).")
                available_models = {
                    "gemini-2.5-pro": {"display_name": "Gemini 2.5 Pro", "provider": "gemini"},
                    "gemini-2.5-flash": {"display_name": "Gemini 2.5 Flash", "provider": "gemini"},
                    "gemini-3-pro": {"display_name": "Gemini 3 Pro", "provider": "gemini"},
                    "gemini-3-flash": {"display_name": "Gemini 3 Flash", "provider": "gemini"},
                    "gpt-5.2": {"display_name": "GPT-5.2", "provider": "gpt"},
                    "gpt-5.1": {"display_name": "GPT-5.1", "provider": "gpt"},
                    "gpt-5": {"display_name": "GPT-5", "provider": "gpt"},
                    "gpt-5-pro": {"display_name": "GPT-5 Pro", "provider": "gpt"},
                    "gpt-5-mini": {"display_name": "GPT-5 Mini", "provider": "gpt"},
                    "claude-sonnet-4-20250514": {"display_name": "Claude Sonnet 4", "provider": "claude"},
                    "claude-opus-4-20250514": {"display_name": "Claude Opus 4", "provider": "claude"},
                    "claude-3-5-sonnet-20241022": {"display_name": "Claude 3.5 Sonnet", "provider": "claude"},
                }
            else:
                raise ValueError(
                    "No LLM models found in st.secrets. "
                    "Please configure [models] section in your secrets.toml file. "
                    "Set STREAMLIT_ENV=development to use fallbacks."
                )
        return available_models

    def get_api_keys(self) -> Dict[str, str]:
        if not hasattr(self, '_api_keys') or self._api_keys is None:
            self._api_keys = self._load_api_keys()
        return self._api_keys

    def get_default_model(self) -> str:
        if not hasattr(self, '_default_model') or self._default_model is None:
            self._default_model = self._load_default_model()
        return self._default_model

    def get_available_models(self) -> Dict[str, Any]:
        if not hasattr(self, '_available_models') or self._available_models is None:
            self._available_models = self._load_available_models()
        return self._available_models

    def get_model_provider(self, model_name: str):
        model_info = self._available_models.get(model_name)
        return model_info.get("provider") if model_info else None

    def get_model_display_name(self, model_name: str):
        model_info = self._available_models.get(model_name)
        return model_info.get("display_name") if model_info else model_name
