import os
import json
import logging
import re
from typing import Dict, List, Optional, Any

from utils.web_scraper import WebScraper # Import the WebScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatManager:
    """
    Manages the chat interface, generating responses based on provided research content.
    """

    def __init__(self, api_keys: Dict[str, str], model_name: str = "gemini-2.5-flash", timeout: int = 60):
        self.api_keys = api_keys
        self.model_name = model_name
        self.research_content: str = ""
        self.timeout = timeout
        self.system_prompt = (
            "You are a helpful research assistant. Your primary goal is to answer questions based on the provided research content. "
            "If a question cannot be answered using the given content, you may use your broader knowledge to answer, but always prioritize the provided research content. "
            "If you use external knowledge, clearly state that the information is not from the provided research."
        )
        
        # Initialize API clients
        self.gemini_client = None
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_api_client()
        self.web_scraper = WebScraper(timeout=self.timeout) # Initialize WebScraper

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
        Generates a response to the user's query, prioritizing loaded research content,
        but expanding to broader knowledge or web search if necessary.
        """
        if not user_query or not user_query.strip():
            return "Please ask a question."
            
        # Initial prompt to prioritize research content
        initial_prompt = f"""Based on the following research content, answer the user's question.
If the answer is not directly available in the provided content, state that you don't have enough information in the research to answer, but then attempt to answer using your broader knowledge.
If you use external knowledge, clearly state that the information is not from the provided research.

--- Research Content ---
{self.research_content if self.research_content else "No specific research content loaded."}
--- End Research Content ---

User's Question: {user_query}

Please provide a clear, concise answer. Prioritize information from the research content. If you use external knowledge, clearly state that it is not from the provided research."""

        try:
            response_text = self._get_llm_response(initial_prompt)

            # Check if the response indicates lack of information from the report
            # and if a web search might be beneficial.
            # This is a simplified check; more sophisticated NLP could be used.
            if "not available in the research" in response_text.lower() or "don't have enough information" in response_text.lower():
                logging.info("Initial response indicates lack of specific research content. Attempting web search.")
                search_query = f"{user_query} research" # Refine search query
                web_results = self.web_scraper.search_academic_sources(search_query, num_results=3)
                
                if web_results:
                    scraped_content = []
                    for result in web_results:
                        content = self.web_scraper.scrape_text_from_url(result['url'])
                        if content:
                            scraped_content.append(f"Source: {result['title']} ({result['url']})\nContent: {content[:1000]}...") # Truncate content
                    
                    if scraped_content:
                        web_search_prompt = f"""Based on the following web search results and your broader knowledge, answer the user's question.
Clearly state that this information is from external sources and not the original research report.

--- Web Search Results ---
{"\n\n".join(scraped_content)}
--- End Web Search Results ---

User's Question: {user_query}

Please provide a clear, concise answer, explicitly mentioning that this information is from external sources."""
                        response_text = self._get_llm_response(web_search_prompt)
                        if "not from the provided research" not in response_text.lower():
                            response_text = "The following information is from external sources and not from the provided research: " + response_text
            
            if not response_text or not response_text.strip():
                return "I received an empty response. Please try rephrasing your question."
                
            logging.info("Chat response generated successfully")
            return response_text
            
        except Exception as e:
            logging.error(f"Error generating chat response: {e}", exc_info=True)
            return f"I apologize, but I encountered an error: {str(e)}"

    def _get_llm_response(self, prompt: str) -> str:
        """Helper method to get response from the appropriate LLM."""
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
                timeout=self.timeout
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
                timeout=self.timeout
            )
            response_text = message.content[0].text
        else:
            error_msg = f"Model '{self.model_name}' is not supported or API client not initialized."
            logging.error(error_msg)
            return f"Error: {error_msg} Please check your API keys."
        return response_text

    def generate_table_summary(self, content: str) -> str:
        """
        Identifies tables in the provided content and generates a concise summary using the LLM.
        """
        if not content:
            return ""

        table_summaries = []
        # Regex to find HTML tables. This can be extended for other table formats if needed.
        # This regex looks for <table>...</table> tags, including content within.
        table_regex = r"<table.*?>(.*?)</table>"
        tables = re.findall(table_regex, content, re.DOTALL | re.IGNORECASE)

        if not tables:
            logging.info("No tables found in the content for summarization.")
            return ""

        for i, table_content in enumerate(tables):
            summary_prompt = f"""Please summarize the following table data concisely.
            Table Content:
            {table_content}

            Provide a summary that highlights the key information and trends in the table."""
            
            try:
                table_summary = self._get_llm_response(summary_prompt)
                if table_summary:
                    table_summaries.append(f"Table {i+1} Summary: {table_summary}")
            except Exception as e:
                logging.error(f"Error summarizing table {i+1}: {e}")
                table_summaries.append(f"Table {i+1} Summary: Could not generate summary due to an error.")

        if table_summaries:
            final_summary = "Table Summaries:\n" + "\n".join(table_summaries)
            logging.info("Table summaries generated successfully.")
            return final_summary
        else:
            return ""

    def generate_executive_summary(self) -> str:
        """
        Generates an executive summary based on the loaded research content,
        incorporating table summaries if available.
        """
        if not self.research_content:
            return "No research content loaded to generate an executive summary."

        table_summary_text = self.generate_table_summary(self.research_content)

        executive_summary_prompt = f"""
        Generate a comprehensive executive summary based on the following research content.
        The summary should provide a high-level overview of the key findings, methodologies,
        and conclusions. If available, also incorporate insights from the provided table summaries.

        --- Research Content ---
        {self.research_content}
        --- End Research Content ---

        {table_summary_text if table_summary_text else "No specific table insights to include."}

        Please ensure the executive summary is concise, informative, and highlights the most critical aspects.
        """

        try:
            summary = self._get_llm_response(executive_summary_prompt)
            logging.info("Executive summary generated successfully.")
            return summary
        except Exception as e:
            logging.error(f"Error generating executive summary: {e}", exc_info=True)
            return f"I apologize, but I encountered an error while generating the executive summary: {str(e)}"