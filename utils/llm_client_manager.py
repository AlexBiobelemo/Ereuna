import logging
from typing import Dict, Any, Optional

import google.genai as genai
import openai
import anthropic
from anthropic import Anthropic, AsyncAnthropic
from openai import OpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)


# Compatibility adapter for google.genai to provide a minimal
# `GenerativeModel(...).generate_content(...)` interface expected
# by the rest of the codebase. This tries multiple call patterns
# supported by different versions of the library.
class _GenaiModelWrapper:
    def __init__(self, module, client_instance, model_name, api_key=None):
        self._module = module
        self._client = client_instance
        self._model_name = model_name
        self._api_key = api_key

    def generate_content(self, messages):
        # Flatten messages into a single prompt string
        parts = []
        for m in messages:
            if isinstance(m, dict):
                if 'parts' in m and isinstance(m['parts'], (list, tuple)):
                    parts.extend([str(p) for p in m['parts']])
                elif 'content' in m:
                    parts.append(str(m['content']))
            else:
                parts.append(str(m))

        prompt_text = "\n".join(parts)

        # Try client.generate(...) if available
        if self._client is not None:
            gen = getattr(self._client, 'generate', None)
            if callable(gen):
                try:
                    resp = gen(model=self._model_name, prompt=prompt_text)
                except TypeError:
                    resp = gen(model=self._model_name, input=prompt_text)
                return _wrap_response(resp)

        # Try module-level generate(...) function
        genf = getattr(self._module, 'generate', None)
        if callable(genf):
            try:
                resp = genf(model=self._model_name, prompt=prompt_text, api_key=self._api_key)
            except TypeError:
                resp = genf(model=self._model_name, input=prompt_text)
            return _wrap_response(resp)

        # Try module-level client() factory
        client_factory = getattr(self._module, 'Client', None) or getattr(getattr(self._module, 'client', None), 'Client', None)
        if client_factory:
            try:
                inst = client_factory(api_key=self._api_key)
            except TypeError:
                inst = client_factory()
            gen = getattr(inst, 'generate', None)
            if callable(gen):
                try:
                    resp = gen(model=self._model_name, prompt=prompt_text)
                except TypeError:
                    resp = gen(model=self._model_name, input=prompt_text)
                return _wrap_response(resp)

        # As a last-resort fallback, try the Google Generative Language REST API
        try:
            import requests

            if not self._api_key:
                raise RuntimeError('No API key available for REST fallback')

            model_id = self._model_name
            # Use the Google Generative Language REST endpoint
            endpoint = f"https://generativelanguage.googleapis.com/v1beta2/models/{model_id}:generate"

            headers = {"Content-Type": "application/json"}
            # Avoid placing API keys in the URL to prevent accidental logging.
            # Prefer Authorization header for REST calls. If this fails for your
            # environment, consider updating to an OAuth bearer token or enabling
            # a dedicated configuration flag.
            if not self._api_key:
                raise RuntimeError('No API key available for REST fallback')
            headers['Authorization'] = f"Bearer {self._api_key}"

            payload = {"prompt": {"text": prompt_text}}

            resp = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # Try common response structures
            text = ""
            if isinstance(data, dict):
                if 'candidates' in data and isinstance(data['candidates'], list) and data['candidates']:
                    cand = data['candidates'][0]
                    text = cand.get('content') or cand.get('text') or ''

                if not text:
                    for key in ('output', 'outputs', 'content', 'text', 'result'):
                        v = data.get(key)
                        if isinstance(v, str) and v:
                            text = v
                            break
                        if isinstance(v, list) and v:
                            text = ' '.join(str(x) for x in v)
                            break
                        if isinstance(v, dict):
                            if 'content' in v:
                                text = v.get('content')
                                break

            if not text:
                # Fallback to stringifying the whole response
                text = str(data)

            return _wrap_response({'text': text})
        except Exception as e:
            # Mask API key in error messages and logs
            err_str = str(e)
            if self._api_key and isinstance(self._api_key, str):
                err_str = err_str.replace(self._api_key, 'REDACTED_API_KEY')
            raise RuntimeError(f"No compatible google.genai generate API found and REST fallback failed: {err_str}")


def _wrap_response(resp):
    # Normalize different response types into an object with `.text`
    from types import SimpleNamespace

    if resp is None:
        return SimpleNamespace(text='')

    # If response is a string
    if isinstance(resp, str):
        return SimpleNamespace(text=resp)

    # If response has attribute 'text'
    text = getattr(resp, 'text', None)
    if text is not None:
        return SimpleNamespace(text=text)

    # If response is a dict-like
    if isinstance(resp, dict):
        # common places: 'output', 'text', 'content'
        for key in ('output', 'text', 'content', 'result'):
            if key in resp:
                val = resp[key]
                if isinstance(val, (list, tuple)):
                    val = ' '.join(str(v) for v in val)
                return SimpleNamespace(text=str(val))

    # Fallback to string conversion
    return SimpleNamespace(text=str(resp))


class _GenaiAdapter:
    """Adapter exposing a `GenerativeModel(name)` factory compatible with older code."""
    def __init__(self, module, api_key=None):
        self._module = module
        self._api_key = api_key

        # Try to instantiate a client if available
        ClientClass = getattr(module, 'Client', None) or getattr(getattr(module, 'client', None), 'Client', None)
        self._client_instance = None
        if ClientClass:
            try:
                self._client_instance = ClientClass(api_key=api_key)
            except TypeError:
                try:
                    self._client_instance = ClientClass()
                except Exception:
                    self._client_instance = None

    def GenerativeModel(self, model_name: str):
        return _GenaiModelWrapper(self._module, self._client_instance, model_name, api_key=self._api_key)

class LLMClientManager:
    """
    Manages the initialization and configuration of various LLM API clients.
    
    Security Note: API keys are stored in memory during the lifetime of this object.
    Use the clear_api_keys() method to securely remove keys from memory when no longer needed.
    """

    def __init__(self, api_keys: Dict[str, str], spinner_update_callback: Optional[Any] = None):
        self._api_keys = api_keys  # Private attribute to discourage direct access
        self.spinner_update_callback = spinner_update_callback
        self.clients = {} # Stores initialized clients
        
    def get_api_keys(self) -> Dict[str, str]:
        """Returns a copy of the API keys (not the original reference)."""
        return self._api_keys.copy()
    
    def clear_api_keys(self):
        """Securely clears API keys from memory."""
        self._api_keys.clear()
        logger.info("API keys cleared from LLMClientManager.")

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
        api_key = self._api_keys.get(model_prefix)

        if not api_key:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Warning: API key not provided for model prefix: {model_prefix}.")
            logger.warning(f"API key not provided for model prefix: {model_prefix}.")
            return

        try:
            if model_prefix == 'gemini':
                # Prefer configuring if available (older API)
                if hasattr(genai, 'configure') and callable(getattr(genai, 'configure')):
                    try:
                        genai.configure(api_key=api_key)
                        self.clients['gemini'] = genai
                        if self.spinner_update_callback:
                            self.spinner_update_callback("Successfully configured Gemini API using genai.configure()")
                        logger.info("Successfully configured Gemini API using genai.configure()")
                    except Exception as e:
                        logger.warning(f"genai.configure failed: {e}. Falling back to adapter.")
                        adapter = _GenaiAdapter(genai, api_key)
                        self.clients['gemini'] = adapter
                else:
                    # Newer google.genai versions may expose a Client class or module-level generate()
                    adapter = _GenaiAdapter(genai, api_key)
                    self.clients['gemini'] = adapter
                    if self.spinner_update_callback:
                        self.spinner_update_callback("Configured Gemini API using compatibility adapter")
                    logger.info("Configured Gemini API using compatibility adapter")
            elif model_prefix == 'gpt':
                self.clients['gpt'] = AsyncOpenAI(api_key=api_key)
                if self.spinner_update_callback:
                    self.spinner_update_callback("Successfully configured OpenAI API")
                logger.info("Successfully configured OpenAI API")
            elif model_prefix == 'claude':
                self.clients['claude'] = AsyncAnthropic(api_key=api_key)
                if self.spinner_update_callback:
                    self.spinner_update_callback("Successfully configured Anthropic API")
                logger.info("Successfully configured Anthropic API")
            else:
                if self.spinner_update_callback:
                    self.spinner_update_callback(f"Warning: No API client configured for model prefix: {model_prefix}")
                logger.warning(f"No API client configured for model prefix: {model_prefix}")
        except Exception as e:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Error: Failed to configure {model_prefix} API: {e}")
            logger.error(f"Failed to configure API client for {model_prefix}: {e}")
