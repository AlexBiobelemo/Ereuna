import os
import json
import logging
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatManager:
    """
    Manages the chat interface, generating responses based on provided research content.
    """

    def __init__(self, api_keys: Dict[str, str], model_name: str = "gemini-2.5-flash"):
        self.api_keys = api_keys
        self.model_name = model_name
        self.research_content: str = ""
        self.system_prompt = "You are a helpful assistant that answers questions ONLY based on the provided research content. If the answer is not in the content, state that you don't have enough information."
        
        # Initialize API clients
        self.gemini_client = None
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_api_client()

    def _initialize_api_client(self):
        """Initialize the appropriate API client based on model name."""
        model_prefix = self.model_name.split('-')[0]
        api_key = self.api_keys.get(model_prefix)

        if not api_key:
            logging.warning(f"API key not provided for model prefix: {model_prefix}")
            return

        try:
            if model_prefix == 'gemini':
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.gemini_client = genai
                logging.info("Successfully configured Gemini API for chat")
            elif model_prefix == 'gpt':
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=api_key)
                logging.info("Successfully configured OpenAI API for chat")
            elif model_prefix == 'claude':
                from anthropic import Anthropic
                self.anthropic_client = Anthropic(api_key=api_key)
                logging.info("Successfully configured Anthropic API for chat")
        except Exception as e:
            logging.error(f"Failed to configure API client for {model_prefix}: {e}")

    def load_research_content(self, content: Dict[str, str]):
        """Loads the generated research content for the chatbot to use."""
        if not content:
            logging.warning("No content provided to load")
            return
        
        self.research_content = "\n\n".join([f"## {title}\n{text}" for title, text in content.items()])
        logging.info(f"Research content loaded for chatbot. Length: {len(self.research_content)} characters")

    def generate_chat_response(self, user_query: str) -> str:
        """
        Generates a response to the user's query, strictly based on the loaded research content.
        """
        if not user_query or not user_query.strip():
            return "Please ask a question."
            
        if not self.research_content:
            return "I need research content to be loaded before I can answer questions. Please generate a research report first."

        # Truncate research content if too long (keep last 8000 chars to stay within limits)
        truncated_content = self.research_content[-8000:] if len(self.research_content) > 8000 else self.research_content

        prompt = f"""Based on the following research content, answer the user's question.
If the answer is not directly available in the provided content, state that you don't have enough information in the research to answer.

--- Research Content ---
{truncated_content}
--- End Research Content ---

User's Question: {user_query}

Please provide a clear, concise answer based ONLY on the research content provided above."""
        
        try:
            response_text = ""
            
            if self.model_name.startswith('gemini') and self.gemini_client:
                logging.info(f"Generating chat response with Gemini model: {self.model_name}")
                model = self.gemini_client.GenerativeModel(self.model_name)
                response = model.generate_content(prompt)
                response_text = response.text
                
            elif self.model_name.startswith('gpt') and self.openai_client:
                logging.info(f"Generating chat response with GPT model: {self.model_name}")
                chat_completion = self.openai_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.model_name,
                    timeout=60
                )
                response_text = chat_completion.choices[0].message.content
                
            elif self.model_name.startswith('claude') and self.anthropic_client:
                logging.info(f"Generating chat response with Claude model: {self.model_name}")
                message = self.anthropic_client.messages.create(
                    model=self.model_name,
                    max_tokens=2000,
                    system=self.system_prompt,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    timeout=60
                )
                response_text = message.content[0].text
            else:
                error_msg = f"Model '{self.model_name}' is not supported or API client not initialized."
                logging.error(error_msg)
                return f"Error: {error_msg} Please check your API keys."

            if not response_text or not response_text.strip():
                return "I received an empty response. Please try rephrasing your question."
                
            logging.info("Chat response generated successfully")
            return response_text
            
        except Exception as e:
            logging.error(f"Error generating chat response: {e}", exc_info=True)
            return f"I apologize, but I encountered an error: {str(e)}"
