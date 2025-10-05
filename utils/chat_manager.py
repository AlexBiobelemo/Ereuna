import os
import json
import logging
from typing import Dict, List, Optional, Any
from utils.research_generator import ResearchGenerator # Assuming ResearchGenerator can be adapted for chat

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatManager:
    """
    Manages the chat interface, generating responses based on provided research content.
    """

    def __init__(self, api_keys: Dict[str, str], model_name: str = "gemini-2.5-flash"):
        self.api_keys = api_keys
        self.model_name = model_name
        self.research_content: str = ""
        self.research_generator = ResearchGenerator(
            topic="Chat based on research", # Dummy topic for ResearchGenerator
            keywords=[],
            research_questions=[],
            api_keys=self.api_keys,
            system_prompt="You are a helpful assistant that answers questions ONLY based on the provided research content. If the answer is not in the content, state that you don't have enough information.",
            model_name=self.model_name
        )

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

        prompt = f"""
        Based on the following research content, answer the user's question.
        If the answer is not directly available in the provided content, state that you don't have enough information in the research to answer.

        --- Research Content ---
        {self.research_content}
        --- End Research Content ---

        User's Question: {user_query}
        """
        
        try:
            response = self.research_generator.generate_section(
                section_name="Chat Response", # Dummy section name
                additional_prompt=prompt
            )
            return response
        except Exception as e:
            logging.error(f"Error generating chat response: {e}")
            return "I apologize, but I encountered an error while trying to generate a response."
