import os
import json
import logging
import re
import time # Import time for exponential backoff
import random # Import random for jitter
from typing import Dict, List, Optional, Any

import google.genai as genai # Added for genai.types.BlockedPromptException
import openai
import anthropic
from utils.web_scraper import WebScraper # Import the WebScraper
from utils.llm_client_manager import LLMClientManager # Import the new LLMClientManager
from utils.config_manager import ConfigManager # Import ConfigManager
from utils.prompt_manager import PromptManager # Import PromptManager
from utils.llm_call_utils import make_llm_call_with_retry # Import shared LLM call utilities
from utils.exceptions import (
    EreunaError,
    APITimeoutError,
    APIRateLimitError,
    APIAuthenticationError,
    APIPermissionError,
    LLMGenerationError
)

logger = logging.getLogger(__name__)

class ChatManager:
    """
    Manages the chat interface, generating responses based on provided research content.
    """

    def __init__(self, config_manager: ConfigManager, prompt_manager: PromptManager, model_name: str = "gemini-2.5-flash", timeout: int = 60, research_topic: str = "", max_retries: int = 3):
        self.config_manager = config_manager
        self.prompt_manager = prompt_manager
        self.model_name = model_name
        self.research_content: str = ""
        self.timeout = timeout
        self.research_topic = research_topic
        self.max_retries = max_retries # Add max_retries to ChatManager
        self.chat_history: List[Dict[str, str]] = [] # Initialize chat history
        
        # System prompt is now managed by PromptManager
        self.system_prompt = "You are a helpful research assistant. Your primary goal is to answer questions ONLY based on the provided research content. If a question cannot be answered using the given content, or if the question is not related to the research topic, you MUST state that you cannot answer questions outside the scope of the research topic. DO NOT use your broader knowledge to answer questions that are outside the research topic. If you use external knowledge, clearly state that the information is not from the provided research."
        
        # Initialize LLM Client Manager
        self.llm_client_manager = LLMClientManager(self.config_manager.get_api_keys())
        self.web_scraper = WebScraper(timeout=self.timeout) # Initialize WebScraper

    def clear_chat_history(self):
        """Clears the chat history."""
        self.chat_history = []
        logger.info("Chat history cleared.")

    def load_research_content(self, content: Dict[str, str]):
        """
        Loads the generated research content for the chatbot to use.
        This content is then used as context for generating chat responses.
        """
        if not content:
            logger.warning("No content provided to load")
            return
        
        # Join all section titles and their content into a single string
        self.research_content = "\n\n".join([f"## {title}\n{text}" for title, text in content.items()])
        logger.info(f"Research content loaded for chatbot. Length: {len(self.research_content)} characters")

    def _make_llm_call_with_retry(self, prompt: str, call_type: str) -> str:
        """
        Helper method to make LLM calls with retry logic and exponential backoff.
        Delegates to shared utility for common LLM call logic.
        
        Args:
            prompt (str): The prompt to send to the LLM.
            call_type (str): A descriptive string for the type of LLM call.
            
        Returns:
            str: The response text from the LLM, or an error message if all retries fail.
        """
        try:
            return make_llm_call_with_retry(
                llm_client_manager=self.llm_client_manager,
                model_name=self.model_name,
                prompt=prompt,
                system_prompt=self.system_prompt,
                max_retries=self.max_retries,
                timeout=self.timeout,
                call_type=call_type
            )
        except APITimeoutError as e:
            return f"Error: Request timeout for {call_type} with {self.model_name}. Please check your connection and try again."
        except APIRateLimitError as e:
            return f"Error: API rate limit exceeded for {call_type} with {self.model_name}. Please try again later."
        except APIAuthenticationError as e:
            return f"Error: Invalid API key for {self.model_name}. Please check your configuration."
        except APIPermissionError as e:
            return f"Error: Permission denied for {self.model_name}. Please check your API key permissions."
        except LLMGenerationError as e:
            return f"Error generating {call_type} with {self.model_name}: {e.message}"
        except EreunaError as e:
            return f"Error: {e.message}"
        except Exception as e:
            logging.error(f"Unexpected error in _make_llm_call_with_retry: {e}")
            return f"Error: An unexpected error occurred while generating {call_type}."

    def generate_chat_response(self, user_query: str) -> str:
        """
        Generates a response to the user's query.
        It first checks if the query is relevant to the loaded research content.
        If the initial response indicates a lack of information, it attempts a web search
        to gather more context before generating a final response.
        
        Args:
            user_query (str): The question or query from the user.
            
        Returns:
            str: The generated chat response, potentially including information from web searches.
        """
        if not user_query or not user_query.strip():
            return "Please ask a question."
            
        try:
            # First, check if the user's query is relevant to the research topic
            relevance_check_prompt = self.prompt_manager.format_prompt(
                "relevance_check",
                research_topic=self.research_topic,
                user_query=user_query
            )
            
            relevance_response = self._make_llm_call_with_retry(relevance_check_prompt, "relevance check")
            if "no" in relevance_response.lower():
                return f"I can only answer questions related to the research topic: '{self.research_topic}'. Your question seems to be outside this scope."

            # Generate an initial response based on the loaded research content
            initial_prompt = self.prompt_manager.format_prompt(
                "chat_response",
                research_content=self.research_content if self.research_content else "No specific research content loaded.",
                user_query=user_query
            )
 
            response_text = self._make_llm_call_with_retry(initial_prompt, "initial chat response")
 
            # Check if the response indicates lack of information from the report
            # and if a web search might be beneficial.
            if "not available in the research" in response_text.lower() or "don't have enough information" in response_text.lower():
                logger.info("Initial response indicates lack of specific research content. Attempting web search.")
                search_query = f"{user_query} research" # Refine search query for better web search results
                web_results = self.web_scraper.search_academic_sources(search_query, num_results=3)
                
                if web_results:
                    scraped_content = []
                    for result in web_results:
                        # Scrape text from the URL and truncate for prompt efficiency
                        content = self.web_scraper.scrape_text_from_url(result['url'])
                        if content:
                            scraped_content.append(f"Source: {result['title']} ({result['url']})\nContent: {content[:1000]}...") # Truncate content
                    
                    if scraped_content:
                        # If web content is found, generate a new response incorporating it
                        web_search_prompt = self.prompt_manager.format_prompt(
                            "web_search_response",
                            scraped_content="\n\n".join(scraped_content),
                            user_query=user_query
                        )
                        response_text = self._make_llm_call_with_retry(web_search_prompt, "web search chat response")
                        # Add a disclaimer if the information is from external sources
                        if "not from the provided research" not in response_text.lower():
                            response_text = "The following information is from external sources and not from the provided research: " + response_text
            
            if not response_text or not response_text.strip():
                return "I received an empty response. Please try rephrasing your question."
            
            # Add user query and model response to chat history
            self.chat_history.append({"role": "user", "content": user_query})
            self.chat_history.append({"role": "assistant", "content": response_text})
                
            logger.info("Chat response generated successfully")
            return response_text
            
        except ValueError as e:
            logger.error(f"Prompt formatting error in generate_chat_response: {e}", exc_info=True)
            return f"I apologize, but there was an issue with the prompt: {str(e)}"
        except Exception as e:
            logger.error(f"Error generating chat response: {e}", exc_info=True)
            return f"I apologize, but I encountered an error: {str(e)}"

    def _get_llm_response(self, prompt: str) -> str:
        """
        Helper method to get response from the appropriate LLM.
        This method is now a wrapper around _make_llm_call_with_retry,
        ensuring all LLM calls benefit from the retry mechanism.
        
        Args:
            prompt (str): The prompt to send to the LLM.
            
        Returns:
            str: The response text from the LLM.
        """
        return self._make_llm_call_with_retry(prompt, "LLM response")

    def generate_table_summary(self, content: str) -> str:
        """
        Identifies tables in the provided content (assumed to be HTML)
        and generates a concise summary for each using the LLM.
        
        Args:
            content (str): The full research content, potentially containing HTML tables.
            
        Returns:
            str: A concatenated string of summaries for all identified tables, or an empty string if no tables are found.
        """
        if not content:
            return ""

        table_summaries = []
        # Regex to find HTML tables. This can be extended for other table formats if needed.
        # This regex looks for <table>...</table> tags, including content within.
        table_regex = r"<table.*?>(.*?)</table>"
        tables = re.findall(table_regex, content, re.DOTALL | re.IGNORECASE)

        if not tables:
            logger.info("No tables found in the content for summarization.")
            return ""

        for i, table_content in enumerate(tables):
            # Format the prompt for table summarization using PromptManager
            summary_prompt = self.prompt_manager.format_prompt(
                "table_summary",
                table_content=table_content
            )
            
            try:
                # Make LLM call with retry for table summary
                table_summary = self._make_llm_call_with_retry(summary_prompt, f"table {i+1} summary")
                if table_summary and not table_summary.startswith("Error:"):
                    table_summaries.append(f"Table {i+1} Summary: {table_summary}")
                else:
                    logger.error(f"Error summarizing table {i+1}: {table_summary}")
                    table_summaries.append(f"Table {i+1} Summary: Could not generate summary due to an error.")
            except ValueError as e:
                logger.error(f"Prompt formatting error for table {i+1} summary: {e}")
                table_summaries.append(f"Table {i+1} Summary: Could not generate summary due to a prompt error.")
            except Exception as e:
                logger.error(f"Error summarizing table {i+1}: {e}")
                table_summaries.append(f"Table {i+1} Summary: Could not generate summary due to an error.")

        if table_summaries:
            final_summary = "Table Summaries:\n" + "\n".join(table_summaries)
            logger.info("Table summaries generated successfully.")
            return final_summary
        else:
            return ""

    def generate_executive_summary(self) -> str:
        """
        Generates an executive summary based on the loaded research content,
        incorporating table summaries if available.
        
        Returns:
            str: The generated executive summary, or an error message if generation fails.
        """
        if not self.research_content:
            return "No research content loaded to generate an executive summary."

        # Generate summaries for any tables present in the research content
        table_summary_text = self.generate_table_summary(self.research_content)

        # Format the prompt for executive summary generation using PromptManager
        executive_summary_prompt = self.prompt_manager.format_prompt(
            "executive_summary",
            full_report_content=self.research_content,
            table_summary_text=table_summary_text if table_summary_text else "No specific table insights to include.",
            summary_detail_instruction="comprehensive", # Placeholder, actual logic for this is in ResearchGenerator
            summary_word_count="N/A", # Placeholder, actual logic for this is in ResearchGenerator
            deep_research_instruction="" # Placeholder, actual logic for this is in ResearchGenerator
        )

        try:
            # Make LLM call with retry for executive summary
            summary = self._make_llm_call_with_retry(executive_summary_prompt, "executive summary")
            if summary.startswith("Error:"):
                logger.error(f"Error generating executive summary: {summary}")
                return f"I apologize, but I encountered an error while generating the executive summary: {summary}"
            logger.info("Executive summary generated successfully.")
            return summary
        except ValueError as e:
            logger.error(f"Prompt formatting error for executive summary: {e}", exc_info=True)
            return f"I apologize, but there was an issue with the prompt for the executive summary: {str(e)}"
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}", exc_info=True)
            return f"I apologize, but I encountered an error while generating the executive summary: {str(e)}"
