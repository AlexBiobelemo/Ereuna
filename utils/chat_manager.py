import os
import json
import logging
import re
import time # Import time for exponential backoff
from typing import Dict, List, Optional, Any

import google.generativeai as genai # Added for genai.types.BlockedPromptException
from utils.web_scraper import WebScraper # Import the WebScraper
from utils.llm_client_manager import LLMClientManager # Import the new LLMClientManager
from utils.config_manager import ConfigManager # Import ConfigManager
from utils.prompt_manager import PromptManager # Import PromptManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.info("Chat history cleared.")

    def load_research_content(self, content: Dict[str, str]):
        """
        Loads the generated research content for the chatbot to use.
        This content is then used as context for generating chat responses.
        """
        if not content:
            logging.warning("No content provided to load")
            return
        
        # Join all section titles and their content into a single string
        self.research_content = "\n\n".join([f"## {title}\n{text}" for title, text in content.items()])
        logging.info(f"Research content loaded for chatbot. Length: {len(self.research_content)} characters")

    def _make_llm_call_with_retry(self, prompt: str, call_type: str) -> str:
        """
        Helper method to make LLM calls with retry logic and exponential backoff.
        It attempts to call the LLM API multiple times, waiting longer between retries
        in case of transient errors like timeouts or rate limits.
        
        Args:
            prompt (str): The prompt to send to the LLM.
            call_type (str): A descriptive string for the type of LLM call (e.g., "relevance check", "chat response").
            
        Returns:
            str: The response text from the LLM, or an error message if all retries fail.
        """
        for attempt in range(self.max_retries):
            try:
                logging.info(f"Attempting to generate {call_type} with {self.model_name} (attempt {attempt + 1}/{self.max_retries})")
                response_text = ""
                model_prefix = self.model_name.split('-')[0]
                client = self.llm_client_manager.get_client(self.model_name)

                if model_prefix == 'gemini' and client:
                    # Call Google Gemini API
                    model = client.GenerativeModel(self.model_name)
                    # Gemini models can handle a list of messages directly
                    messages = [{"role": "user", "parts": [prompt]}]
                    if self.chat_history:
                        # Prepend chat history to the current prompt
                        messages = [{"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]} for msg in self.chat_history] + messages
                    response = model.generate_content(messages)
                    response_text = response.text
                elif model_prefix == 'gpt' and client:
                    # Call OpenAI GPT API
                    messages = [{"role": "system", "content": self.system_prompt}]
                    if self.chat_history:
                        messages.extend([{"role": msg["role"], "content": msg["content"]} for msg in self.chat_history])
                    messages.append({"role": "user", "content": prompt})
                    
                    chat_completion = client.chat.completions.create(
                        messages=messages,
                        model=self.model_name,
                        timeout=self.timeout
                    )
                    response_text = chat_completion.choices[0].message.content
                elif model_prefix == 'claude' and client:
                    # Call Anthropic Claude API
                    messages = []
                    if self.chat_history:
                        messages.extend([{"role": msg["role"], "content": msg["content"]} for msg in self.chat_history])
                    messages.append({"role": "user", "content": prompt})

                    message = client.messages.create(
                        model=self.model_name,
                        max_tokens=2000,
                        system=self.system_prompt,
                        messages=messages,
                        timeout=self.timeout
                    )
                    response_text = message.content[0].text
                else:
                    error_msg = f"Model '{self.model_name}' is not supported or API client not initialized."
                    logging.error(error_msg)
                    return f"Error: {error_msg} Please check your API keys."

                if not response_text or not response_text.strip():
                    raise ValueError(f"Empty response received for {call_type}")
                
                logging.info(f"Successfully generated {call_type} with {self.model_name}")
                return response_text

            except (genai.types.BlockedPromptException, openai.APITimeoutError, anthropic.APITimeoutError) as e:
                # Handle timeout errors with exponential backoff
                logging.error(f"Timeout error for {call_type} with {self.model_name}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) # Exponential backoff: 1, 2, 4 seconds
                    logging.info(f"Timeout occurred. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    return f"Error: Request timeout for {call_type} with {self.model_name}. Please check your connection and try again."
            except (genai.APIError, openai.APIError, anthropic.APIError) as e:
                # Handle various API errors, including rate limits, invalid API keys, and permissions
                error_msg = str(e).lower()
                if "quota" in error_msg or "rate" in error_msg:
                    logging.error(f"API rate limit/quota error for {call_type} with {self.model_name}: {e}")
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8 seconds
                        logging.info(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        return f"Error: API rate limit exceeded for {call_type} with {self.model_name}. Please try again later."
                elif "api key" in error_msg or "authentication" in error_msg:
                    logging.error(f"API key error for {call_type} with {self.model_name}: {e}")
                    return f"Error: Invalid API key for {self.model_name}. Please check your configuration."
                elif "permission" in error_msg or "forbidden" in error_msg:
                    logging.error(f"Permission error for {call_type} with {self.model_name}: {e}")
                    return f"Error: Permission denied for {self.model_name}. Please check your API key permissions."
                else:
                    # Handle other unexpected API errors
                    logging.error(f"Unexpected API error generating {call_type} with {self.model_name} (attempt {attempt + 1}): {e}")
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logging.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return f"Error generating {call_type} with {self.model_name}: {e}"
            except Exception as e:
                # Catch any other unexpected exceptions
                error_type = type(e).__name__
                error_msg = str(e)
                logging.error(f"Unexpected error generating {call_type} with {self.model_name} (attempt {attempt + 1}): {error_type} - {error_msg}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return f"Error generating {call_type} with {self.model_name}: {error_type} - {error_msg}"
        
        return f"Error: Failed to generate {call_type} with {self.model_name} after {self.max_retries} attempts. Please try again later."

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
                logging.info("Initial response indicates lack of specific research content. Attempting web search.")
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
                
            logging.info("Chat response generated successfully")
            return response_text
            
        except ValueError as e:
            logging.error(f"Prompt formatting error in generate_chat_response: {e}", exc_info=True)
            return f"I apologize, but there was an issue with the prompt: {str(e)}"
        except Exception as e:
            logging.error(f"Error generating chat response: {e}", exc_info=True)
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
            logging.info("No tables found in the content for summarization.")
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
                    logging.error(f"Error summarizing table {i+1}: {table_summary}")
                    table_summaries.append(f"Table {i+1} Summary: Could not generate summary due to an error.")
            except ValueError as e:
                logging.error(f"Prompt formatting error for table {i+1} summary: {e}")
                table_summaries.append(f"Table {i+1} Summary: Could not generate summary due to a prompt error.")
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
                logging.error(f"Error generating executive summary: {summary}")
                return f"I apologize, but I encountered an error while generating the executive summary: {summary}"
            logging.info("Executive summary generated successfully.")
            return summary
        except ValueError as e:
            logging.error(f"Prompt formatting error for executive summary: {e}", exc_info=True)
            return f"I apologize, but there was an issue with the prompt for the executive summary: {str(e)}"
        except Exception as e:
            logging.error(f"Error generating executive summary: {e}", exc_info=True)
            return f"I apologize, but I encountered an error while generating the executive summary: {str(e)}"
