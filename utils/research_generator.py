import google.generativeai as genai
import logging
import time
from typing import Dict, Optional, List

import openai
import anthropic
from anthropic import Anthropic
from openai import OpenAI

from utils.web_scraper import WebScraper # Import the WebScraper

class ResearchGenerator:
    def __init__(self, topic, keywords, research_questions, api_keys: Dict[str, str],
                 system_prompt, model_name: str = 'gemini-1.5-flash', max_retries=3, timeout=60):
        """
        Initialize ResearchGenerator with validation and error handling.
        
        Args:
            topic: Research topic
            keywords: Keywords for research
            research_questions: Research questions
            api_keys: A dictionary of API keys for different models (e.g., {"gemini": "YOUR_GEMINI_KEY"}).
            system_prompt: System prompt for generation
            model_name: The name of the AI model to use (e.g., 'gemini-1.5-flash', 'gpt-4o', 'claude-3-opus-20240229')
            max_retries: Maximum number of retry attempts for API calls
            timeout: Timeout for API calls in seconds
        """
        # Validate inputs
        if not topic or not isinstance(topic, str) or not topic.strip():
            raise ValueError("Topic must be a non-empty string")
        
        if not system_prompt or not isinstance(system_prompt, str):
            raise ValueError("System prompt must be a non-empty string")
        
        if not isinstance(api_keys, dict):
            raise ValueError("api_keys must be a dictionary")

        self.topic = topic.strip()
        self.keywords = self._validate_input(keywords, "Keywords")
        self.research_questions = self._validate_input(research_questions, "Research questions")
        self.api_keys = api_keys
        self.system_prompt = system_prompt.strip()
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout = timeout
        
        self._initialize_api_clients()
        self.web_scraper = WebScraper(timeout=self.timeout) # Initialize WebScraper

    def _initialize_api_clients(self):
        """Initialize API clients based on the selected model and provided API keys."""
        self.gemini_client = None
        self.openai_client = None
        self.anthropic_client = None

        model_prefix = self.model_name.split('-')[0]
        api_key = self.api_keys.get(model_prefix)

        if not api_key:
            logging.warning(f"API key not provided for model prefix: {model_prefix}. {self.model_name} will not be available.")
            return

        if model_prefix == 'gemini':
            try:
                genai.configure(api_key=api_key)
                self.gemini_client = genai
                logging.info("Successfully configured Gemini API")
            except Exception as e:
                logging.error(f"Failed to configure Gemini API: {e}")
        elif model_prefix == 'gpt':
            try:
                self.openai_client = OpenAI(api_key=api_key)
                logging.info("Successfully configured OpenAI API")
            except Exception as e:
                logging.error(f"Failed to configure OpenAI API: {e}")
        elif model_prefix == 'claude':
            try:
                self.anthropic_client = Anthropic(api_key=api_key)
                logging.info("Successfully configured Anthropic API")
            except Exception as e:
                logging.error(f"Failed to configure Anthropic API: {e}")
        else:
            logging.warning(f"No API client configured for model: {self.model_name}")

    def _validate_input(self, value, name):
        """Validate and clean input values."""
        if value is None:
            logging.warning(f"{name} is None, using empty string")
            return ""
        
        if isinstance(value, (list, tuple)):
            # Convert list to comma-separated string
            return ", ".join(str(item).strip() for item in value if item)
        
        return str(value).strip()

    def _make_api_call_with_retry(self, prompt, section_name):
        """
        Make API call with retry logic and exponential backoff, supporting multiple models.
        
        Args:
            prompt: The prompt to send to the API
            section_name: Name of the section being generated
            
        Returns:
            Generated text or error message
        """
        for attempt in range(self.max_retries):
            try:
                logging.info(f"Attempting to generate {section_name} with {self.model_name} (attempt {attempt + 1}/{self.max_retries})")
                
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
                        timeout=self.timeout
                    )
                    response_text = chat_completion.choices[0].message.content
                elif self.model_name.startswith('claude') and self.anthropic_client:
                    message = self.anthropic_client.messages.create(
                        model=self.model_name,
                        max_tokens=4000, # Increased max_tokens for potentially longer responses
                        system=self.system_prompt,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        timeout=self.timeout
                    )
                    response_text = message.content[0].text
                else:
                    return f"Error: Unsupported model '{self.model_name}' or API client not initialized."

                # Validate response
                if not response_text or not response_text.strip():
                    raise ValueError(f"Empty response received for {section_name}")
                
                logging.info(f"Successfully generated {section_name} with {self.model_name}")
                return response_text
                
            except (genai.types.BlockedPromptException, openai.APITimeoutError, anthropic.APITimeoutError) as e:
                logging.error(f"Timeout error for {section_name} with {self.model_name}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt)
                    logging.info(f"Timeout occurred. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    return f"Error: Request timeout for {section_name} with {self.model_name}. Please check your connection and try again."
            except (genai.RpcError, openai.APIError, anthropic.APIError) as e:
                error_msg = str(e).lower()
                if "quota" in error_msg or "rate" in error_msg:
                    logging.error(f"API rate limit/quota error for {section_name} with {self.model_name}: {e}")
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8 seconds
                        logging.info(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        return f"Error: API rate limit exceeded for {section_name} with {self.model_name}. Please try again later."
                elif "api key" in error_msg or "authentication" in error_msg:
                    logging.error(f"API key error for {section_name} with {self.model_name}: {e}")
                    return f"Error: Invalid API key for {self.model_name}. Please check your configuration."
                elif "permission" in error_msg or "forbidden" in error_msg:
                    logging.error(f"Permission error for {section_name} with {self.model_name}: {e}")
                    return f"Error: Permission denied for {self.model_name}. Please check your API key permissions."
                else:
                    logging.error(f"Unexpected API error generating {section_name} with {self.model_name} (attempt {attempt + 1}): {e}")
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logging.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return f"Error generating {section_name} with {self.model_name}: {e}"
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                logging.error(f"Unexpected error generating {section_name} with {self.model_name} (attempt {attempt + 1}): {error_type} - {error_msg}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return f"Error generating {section_name} with {self.model_name}: {error_type} - {error_msg}"
        
        # If all retries failed
        return f"Error: Failed to generate {section_name} with {self.model_name} after {self.max_retries} attempts. Please try again later."

    def perform_web_research(self, query: str, num_sources: int = 3) -> List[Dict[str, str]]:
        """
        Performs web research using the WebScraper to find academic sources.
        
        Args:
            query: The search query for academic sources.
            num_sources: The number of top sources to retrieve.
            
        Returns:
            A list of dictionaries, each containing 'title' and 'url' of the sources.
        """
        logging.info(f"Performing web research for query: {query}")
        search_results = self.web_scraper.search_academic_sources(query, num_results=num_sources)
        
        if not search_results:
            logging.warning(f"No academic sources found for query: {query}")
            return []
        
        logging.info(f"Found {len(search_results)} academic sources for query: {query}")
        return search_results

    def scrape_source_content(self, url: str) -> Optional[str]:
        """
        Scrapes the content from a given URL using the WebScraper.
        
        Args:
            url: The URL of the source to scrape.
            
        Returns:
            The extracted text content from the URL, or None if scraping fails.
        """
        logging.info(f"Scraping content from URL: {url}")
        content = self.web_scraper.scrape_text_from_url(url)
        if not content:
            logging.error(f"Failed to scrape content from {url}")
        return content

    def generate_section(self, section_name):
        """
        Generate a single section of the research report.
        
        Args:
            section_name: Name of the section to generate
            
        Returns:
            Generated section content or error message
        """
        try:
            if not section_name or not isinstance(section_name, str):
                raise ValueError("Section name must be a non-empty string")
            
            section_name = section_name.strip()
            
            # Construct prompt
            prompt = (
                f"{self.system_prompt}\n\n"
                f"Create a {section_name} for a research report on the topic: {self.topic}. "
                f"Keywords: {self.keywords}. "
                f"Research questions: {self.research_questions}"
            )
            
            logging.info(f"Generating section: {section_name}")
            return self._make_api_call_with_retry(prompt, section_name)
            
        except ValueError as e:
            logging.error(f"Validation error in generate_section: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error in generate_section: {e}")
            return f"Error generating {section_name}: {str(e)}"

    def generate_report(self) -> Dict[str, str]:
        """
        Generate complete research report with all sections.
        
        Returns:
            Dictionary containing all report sections
        """
        try:
            logging.info(f"Starting report generation for topic: {self.topic}")
            
            sections = {
                "Introduction": self.generate_section("introduction"),
                "Literature Review": self.generate_section("literature review"),
                "Methodology": self.generate_section("methodology"),
                "Results": self.generate_section("results"),
                "Discussion": self.generate_section("discussion"),
                "Conclusion": self.generate_section("conclusion")
            }
            
            # Check if any sections failed
            failed_sections = [name for name, content in sections.items() 
                             if content.startswith("Error")]
            
            if failed_sections:
                logging.warning(f"Failed to generate sections: {', '.join(failed_sections)}")
            else:
                logging.info("Successfully generated all report sections")
            
            return sections
            
        except Exception as e:
            logging.error(f"Critical error generating report: {e}")
            # Return error sections
            return {
                "Introduction": f"Error: Failed to generate report - {str(e)}",
                "Literature Review": "Error: Report generation failed",
                "Methodology": "Error: Report generation failed",
                "Results": "Error: Report generation failed",
                "Discussion": "Error: Report generation failed",
                "Conclusion": "Error: Report generation failed"
            }

    def generate_custom_section(self, section_name: str, additional_instructions: Optional[str] = None) -> str:
        """
        Generate a custom section with optional additional instructions.
        
        Args:
            section_name: Name of the custom section
            additional_instructions: Optional additional instructions for generation
            
        Returns:
            Generated section content or error message
        """
        try:
            if not section_name or not isinstance(section_name, str):
                raise ValueError("Section name must be a non-empty string")
            
            section_name = section_name.strip()
            
            # Construct prompt with additional instructions
            prompt = (
                f"{self.system_prompt}\n\n"
                f"Create a {section_name} for a research report on the topic: {self.topic}. "
                f"Keywords: {self.keywords}. "
                f"Research questions: {self.research_questions}"
            )
            
            if additional_instructions:
                prompt += f"\n\nAdditional instructions: {additional_instructions}"
            
            logging.info(f"Generating custom section: {section_name}")
            return self._make_api_call_with_retry(prompt, section_name)
            
        except ValueError as e:
            logging.error(f"Validation error in generate_custom_section: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error in generate_custom_section: {e}")
            return f"Error generating custom section '{section_name}': {str(e)}"

    def generate_summary(self, full_report_content: str) -> str:
        """
        Generates an executive summary of the full research report.
        
        Args:
            full_report_content: The complete text content of the research report.
            
        Returns:
            The generated executive summary or an error message.
        """
        try:
            if not full_report_content or not isinstance(full_report_content, str):
                raise ValueError("Full report content must be a non-empty string for summarization.")
            
            prompt = (
                f"{self.system_prompt}\n\n"
                f"Please provide a concise executive summary (around 200-300 words) of the following research report. "
                f"Focus on the main findings, key arguments, and conclusions. "
                f"Ensure the summary is clear, objective, and highlights the most important aspects.\n\n"
                f"Research Report:\n{full_report_content}"
            )
            
            logging.info("Generating executive summary.")
            return self._make_api_call_with_retry(prompt, "Executive Summary")
            
        except ValueError as e:
            logging.error(f"Validation error in generate_summary: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error in generate_summary: {e}")
            return f"Error generating executive summary: {str(e)}"



