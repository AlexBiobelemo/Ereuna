"""
Shared utility module for LLM API calls with retry logic.
Provides common logic for making calls to Gemini, OpenAI, and Anthropic APIs.
"""
import time
import random
import logging
from typing import Dict, Any, Optional

import google.genai as genai
import openai
import anthropic

from utils.llm_client_manager import LLMClientManager
from utils.exceptions import (
    APITimeoutError,
    APIRateLimitError,
    APIAuthenticationError,
    APIPermissionError,
    LLMGenerationError
)

logger = logging.getLogger(__name__)

# Backwards-compatible exception references for google.genai
# Some releases expose different exception class names; fall back to generic Exception when not present.
_genai_types = getattr(genai, 'types', genai)
GENAI_BLOCKED_PROMPT_EXCEPTION = getattr(_genai_types, 'BlockedPromptException', Exception)
GENAI_API_ERROR = getattr(genai, 'APIError', getattr(genai, 'Error', Exception))


def make_llm_call_with_retry(
    llm_client_manager: LLMClientManager,
    model_name: str,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_retries: int = 3,
    timeout: int = 60,
    call_type: str = "LLM call"
) -> str:
    """
    Makes an LLM API call with retry logic and exponential backoff with jitter.
    Raises exceptions on failure instead of returning error strings.
    
    Args:
        llm_client_manager: The LLMClientManager instance for API clients.
        model_name: The name of the model to use.
        prompt: The prompt to send to the LLM.
        system_prompt: Optional system prompt for models that support it.
        max_retries: Maximum number of retry attempts.
        timeout: Timeout for API calls in seconds.
        call_type: Descriptive string for the type of LLM call.
    
    Returns:
        str: The response text from the LLM.
    
    Raises:
        LLMGenerationError: When all retries fail or an unrecoverable error occurs.
        APIAuthenticationError: When API authentication fails.
        APIPermissionError: When API permission is denied.
        APIRateLimitError: When rate limit is exceeded.
        APITimeoutError: When API request times out.
    """
    model_prefix = model_name.split('-')[0]
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to generate {call_type} with {model_name} (attempt {attempt + 1}/{max_retries})")
            response_text = ""
            client = llm_client_manager.get_client(model_name)

            if model_prefix == 'gemini' and client:
                # Call Google Gemini API
                model = client.GenerativeModel(model_name)
                messages = [{"role": "user", "parts": [prompt]}]
                response = model.generate_content(messages)
                response_text = response.text
            elif model_prefix == 'gpt' and client:
                # Call OpenAI GPT API
                messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
                messages.append({"role": "user", "content": prompt})
                
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model=model_name,
                    timeout=timeout
                )
                response_text = chat_completion.choices[0].message.content
            elif model_prefix == 'claude' and client:
                # Call Anthropic Claude API
                messages = [{"role": "user", "content": prompt}]
                
                kwargs = {
                    "model": model_name,
                    "max_tokens": 2000,
                    "messages": messages,
                    "timeout": timeout
                }
                if system_prompt:
                    kwargs["system"] = system_prompt
                
                message = client.messages.create(**kwargs)
                response_text = message.content[0].text
            else:
                raise LLMGenerationError(
                    f"Model '{model_name}' is not supported or API client not initialized. Please check your API keys.",
                    model=model_name,
                    section=call_type,
                    attempt=attempt + 1
                )

            if not response_text or not response_text.strip():
                raise LLMGenerationError(
                    f"Empty response received for {call_type}",
                    model=model_name,
                    section=call_type,
                    attempt=attempt + 1
                )
            
            logger.info(f"Successfully generated {call_type} with {model_name}")
            return response_text

        except (GENAI_BLOCKED_PROMPT_EXCEPTION, openai.APITimeoutError, anthropic.APITimeoutError) as e:
            logger.error(f"Timeout error for {call_type} with {model_name}: {e}")
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 0.5)
                logger.info(f"Timeout occurred. Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
            else:
                raise APITimeoutError(provider=model_prefix, model=model_name, timeout=timeout)
        except (GENAI_API_ERROR, openai.APIError, anthropic.APIError) as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "rate" in error_msg:
                logger.error(f"API rate limit/quota error for {call_type} with {model_name}: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2 + random.uniform(0, 0.5)
                    logger.info(f"Rate limit hit. Waiting {wait_time:.2f} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    raise APIRateLimitError(provider=model_prefix, model=model_name)
            elif "api key" in error_msg or "authentication" in error_msg:
                logger.error(f"API key error for {call_type} with {model_name}: {e}")
                raise APIAuthenticationError(provider=model_prefix, model=model_name)
            elif "permission" in error_msg or "forbidden" in error_msg:
                logger.error(f"Permission error for {call_type} with {model_name}: {e}")
                raise APIPermissionError(provider=model_prefix, model=model_name)
            else:
                logger.error(f"Unexpected API error generating {call_type} with {model_name} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt + random.uniform(0, 0.5)
                    logger.info(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    raise LLMGenerationError(
                        f"API error: {e}",
                        model=model_name,
                        section=call_type,
                        attempt=attempt + 1
                    )
        except LLMGenerationError:
            # Re-raise LLMGenerationError as-is
            raise
        except Exception as e:
            error_type = type(e).__name__
            error_msg_str = str(e)
            logger.error(f"Unexpected error generating {call_type} with {model_name} (attempt {attempt + 1}): {error_type} - {error_msg_str}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt + random.uniform(0, 0.5)
                logger.info(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                raise LLMGenerationError(
                    f"{error_type}: {error_msg_str}",
                    model=model_name,
                    section=call_type,
                    attempt=attempt + 1
                )
    
    # If we get here, all retries failed
    raise LLMGenerationError(
        f"Failed to generate {call_type} with {model_name} after {max_retries} attempts",
        model=model_name,
        section=call_type,
        attempt=max_retries
    )


def adapt_prompt_for_model(model_name: str, prompt: str, system_prompt: Optional[str] = None) -> tuple:
    """
    Adapts the prompt format for the specified model.
    
    Args:
        model_name: The name of the model to use.
        prompt: The user prompt.
        system_prompt: Optional system prompt.
    
    Returns:
        Tuple of (messages, kwargs) adapted for the model's API.
    """
    model_prefix = model_name.split('-')[0]
    
    if model_prefix == 'gemini':
        # Gemini uses a simple list format
        messages = [{"role": "user", "parts": [prompt]}]
        return messages, {}
    elif model_prefix == 'gpt':
        # OpenAI uses system/user roles
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages, {}
    elif model_prefix == 'claude':
        # Anthropic uses system separate from messages
        messages = [{"role": "user", "content": prompt}]
        kwargs = {}
        if system_prompt:
            kwargs["system"] = system_prompt
        return messages, kwargs
    else:
        raise ValueError(f"Unsupported model prefix: {model_prefix}")
