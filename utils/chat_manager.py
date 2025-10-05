import os
import json
import logging
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from openai import OpenAI
from anthropic import Anthropic

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
        self._initialize_api_client()

    def _initialize_api_client(self):
        """Initialize the appropriate API client based on model name."""
        self.gemini_client = None
        self.openai_client = None
        self.anthropic_client = None

        model_prefix = self.model_name.split('-')[0]
        api_key = self.api_keys.get(model_prefix)

        if not api_key:
            logging.warning(f"API key not provided for model prefix: {model_prefix}")
            return

        if model_prefix == 'gemini':
            try:
                genai.configure(api_key=api_key)
                self.gemini_client = genai
                logging.info("Successfully configured Gemini API for chat")
            except Exception as e:
                logging.error(f"Failed to configure Gemini API: {e}")
        elif model_prefix == 'gpt':
            try:
                self.openai_client = OpenAI(api_key=api_key)
                logging.info("Successfully configured OpenAI API for chat")
            except Exception as e:
                logging.error(f"Failed to configure OpenAI API: {e}")
        elif model_prefix == 'claude':
            try:
                self.anthropic_client = Anthropic(api_key=api_key)
                logging.info("Successfully configured Anthropic API for chat")
            except Exception as e:
                logging.error(f"Failed to configure Anthropic API: {e}")

    def load_research_content(self, content: Dict[str, str]):
        """Loads the generated research content for the chatbot to use."""
        self.research_content = "\n\n".join([f"## {title}\n{text}" for title, text in content.items()])
        logging.info("Research content loaded for chatbot.")

    def generate_chat_response(self, user_query: str) -> str:
        """
        Generates a response to the user's query, strictly based on the loaded research content.
        """
        if not self.research_content:
            return "I need research content to be loaded before I can answer questions."

        prompt = f"""Based on the following research content, answer the user's question.
If the answer is not directly available in the provided content, state that you don't have enough information in the research to answer.

--- Research Content ---
{self.research_content}
--- End Research Content ---

User's Question: {user_query}

Please provide a clear, concise answer based ONLY on the research content provided above."""
        
        try:
            response_text = ""
            
            if self.model_name.startswith('gemini') and self.gemini_client:
                model = self.gemini_client.GenerativeModel(self.model_name)
                response = model.generate_content(prompt)
                response_text = response.text
                
            elif self.model_name.startswith('gpt') and self.openai_client:
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
                return f"Error: Unsupported model '{self.model_name}' or API client not initialized."

            return response_text if response_text else "I apologize, but I couldn't generate a response."
            
        except Exception as e:
            logging.error(f"Error generating chat response: {e}")
            return "I apologize, but I encountered an error while trying to generate a response."
