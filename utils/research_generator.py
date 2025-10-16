import streamlit as st
import google.generativeai as genai
import logging
import time
from typing import Dict, Optional, List, Any

import openai
import anthropic
from anthropic import Anthropic
from openai import OpenAI

from utils.web_scraper import WebScraper # Import the WebScraper
from utils.llm_client_manager import LLMClientManager # Import the new LLMClientManager
from utils.config_manager import ConfigManager # Import ConfigManager
from utils.prompt_manager import PromptManager # Import PromptManager

class ResearchGenerator:
    def __init__(self, topic, keywords, research_questions, config_manager: ConfigManager,
                 prompt_manager: PromptManager, deep_research_enabled: bool = False, model_name: str = 'gemini-1.5-flash', max_retries=3, timeout=60, spinner_update_callback=None):
        """
        Initialize ResearchGenerator with validation and error handling.
        
        Args:
            topic: Research topic
            keywords: Keywords for research
            research_questions: Research questions
            config_manager: An instance of ConfigManager for API keys and model management.
            prompt_manager: An instance of PromptManager for handling prompt templates.
            deep_research_enabled: Whether deep research mode is enabled.
            model_name: The name of the AI model to use (e.g., 'gemini-1.5-flash', 'gpt-4o', 'claude-3-opus-20240229')
            max_retries: Maximum number of retry attempts for API calls
            timeout: Timeout for API calls in seconds
        """
        # Validate inputs
        if not topic or not isinstance(topic, str) or not topic.strip():
            raise ValueError("Topic must be a non-empty string")
        
        if not isinstance(config_manager, ConfigManager):
            raise ValueError("config_manager must be an instance of ConfigManager")
        
        if not isinstance(prompt_manager, PromptManager):
            raise ValueError("prompt_manager must be an instance of PromptManager")

        self.topic = topic.strip()
        self.keywords = self._validate_input(keywords, "Keywords")
        self.research_questions = self._validate_input(research_questions, "Research questions")
        self.config_manager = config_manager
        self.prompt_manager = prompt_manager
        self.deep_research_enabled = deep_research_enabled
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout = timeout
        self.spinner_update_callback = spinner_update_callback
        
        # System prompt is now managed by PromptManager
        self.system_prompt = "You are a helpful research assistant. Provide detailed and well-structured information."
        
        self.llm_client_manager = LLMClientManager(self.config_manager.get_api_keys(), self.spinner_update_callback)
        self.web_scraper = WebScraper(timeout=self.timeout) # Initialize WebScraper

    def _validate_input(self, value, name):
        """Validate and clean input values."""
        if value is None:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Warning: {name} is None, using empty string")
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
                if self.spinner_update_callback:
                    # Clean model name for display: remove version numbers and "flash"
                    display_model_name = self.model_name.replace('gemini-1.5-flash', 'Gemini Flash').replace('gemini-2.5-flash', 'Gemini Flash').replace('gemini-pro', 'Gemini Pro')
                    # Remove "(attempt X/Y)" from the spinner message as requested
                    spinner_message = f"Crafting the {section_name} with {display_model_name}"
                    self.spinner_update_callback(spinner_message)
                logging.info(f"Attempting to generate {section_name} with {self.model_name} (attempt {attempt + 1}/{self.max_retries})")
                response_text = ""
                model_prefix = self.model_name.split('-')[0]
                client = self.llm_client_manager.get_client(self.model_name)

                if model_prefix == 'gemini' and client:
                    model = client.GenerativeModel(self.model_name)
                    response = model.generate_content(prompt)
                    response_text = response.text
                elif model_prefix == 'gpt' and client:
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": self.system_prompt}, # Use the system prompt defined in __init__
                            {"role": "user", "content": prompt}
                        ],
                        model=self.model_name,
                        timeout=self.timeout
                    )
                    response_text = chat_completion.choices.message.content
                elif model_prefix == 'claude' and client:
                    message = client.messages.create(
                        model=self.model_name,
                        max_tokens=4000, # Increased max_tokens for potentially longer responses
                        system=self.system_prompt, # Use the system prompt defined in __init__
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        timeout=self.timeout
                    )
                    response_text = message.content.text
                else:
                    return f"Error: Unsupported model '{self.model_name}' or API client not initialized."

                # Validate response
                if not response_text or not response_text.strip():
                    raise ValueError(f"Empty response received for {section_name}")
                
                if self.spinner_update_callback:
                    self.spinner_update_callback(f"The {section_name} is taking shape!")
                logging.info(f"Successfully generated {section_name} with {self.model_name}")
                return response_text
                
            except (genai.types.BlockedPromptException, openai.APITimeoutError, anthropic.APITimeoutError) as e:
                if self.spinner_update_callback:
                    self.spinner_update_callback(f"Error: Timeout error for {section_name} with {self.model_name}: {e}")
                logging.error(f"Timeout error for {section_name} with {self.model_name}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt)
                    if self.spinner_update_callback:
                        self.spinner_update_callback(f"Timeout occurred. Waiting {wait_time} seconds before retry...")
                    logging.info(f"Timeout occurred. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    return f"Error: Request timeout for {section_name} with {self.model_name}. Please check your connection and try again."
            except (genai.APIError, openai.APIError, anthropic.APIError) as e: # Revert to genai.APIError
                error_msg = str(e).lower()
                if "quota" in error_msg or "rate" in error_msg:
                    if self.spinner_update_callback:
                        self.spinner_update_callback(f"Error: API rate limit/quota error for {section_name} with {self.model_name}: {e}")
                    logging.error(f"API rate limit/quota error for {section_name} with {self.model_name}: {e}")
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8 seconds
                        if self.spinner_update_callback:
                            self.spinner_update_callback(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                        logging.info(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        return f"Error: API rate limit exceeded for {section_name} with {self.model_name}. Please try again later."
                elif "api key" in error_msg or "authentication" in error_msg:
                    if self.spinner_update_callback:
                        self.spinner_update_callback(f"Error: API key error for {section_name} with {self.model_name}: {e}")
                    logging.error(f"API key error for {section_name} with {self.model_name}: {e}")
                    return f"Error: Invalid API key for {self.model_name}. Please check your configuration."
                elif "permission" in error_msg or "forbidden" in error_msg:
                    if self.spinner_update_callback:
                        self.spinner_update_callback(f"Error: Permission error for {section_name} with {self.model_name}: {e}")
                    logging.error(f"Permission error for {section_name} with {self.model_name}: {e}")
                    return f"Error: Permission denied for {self.model_name}. Please check your API key permissions."
                else:
                    if self.spinner_update_callback:
                        self.spinner_update_callback(f"Error: Unexpected API error generating {section_name} with {self.model_name} (attempt {attempt + 1}): {e}")
                    logging.error(f"Unexpected API error generating {section_name} with {self.model_name} (attempt {attempt + 1}): {e}")
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        if self.spinner_update_callback:
                            self.spinner_update_callback(f"Retrying in {wait_time} seconds...")
                        logging.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return f"Error generating {section_name} with {self.model_name}: {e}"
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                if self.spinner_update_callback:
                    self.spinner_update_callback(f"Error: Unexpected error generating {section_name} with {self.model_name} (attempt {attempt + 1}): {error_type} - {error_msg}")
                logging.error(f"Unexpected error generating {section_name} with {self.model_name} (attempt {attempt + 1}): {error_type} - {error_msg}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    if self.spinner_update_callback:
                        self.spinner_update_callback(f"Retrying in {wait_time} seconds...")
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return f"Error generating {section_name} with {self.model_name}: {error_type} - {error_msg}"
        
        # If all retries failed
        if self.spinner_update_callback:
            self.spinner_update_callback(f"Oops! The {section_name} couldn't be generated after {self.max_retries} attempts. Let's try again later.")
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
        if self.spinner_update_callback:
            self.spinner_update_callback(f"Performing web research for query: {query}")
        logging.info(f"Performing web research for query: {query}")
        search_results = self.web_scraper.search_academic_sources(query, num_results=num_sources)
        
        if not search_results:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Warning: No academic sources found for query: {query}")
            logging.warning(f"No academic sources found for query: {query}")
            return []
        
        if self.spinner_update_callback:
            self.spinner_update_callback(f"Found {len(search_results)} academic sources for query: {query}")
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
        if self.spinner_update_callback:
            self.spinner_update_callback(f"Scraping content from URL: {url}")
        logging.info(f"Scraping content from URL: {url}")
        content = self.web_scraper.scrape_text_from_url(url)
        if not content:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Error: Failed to scrape content from {url}")
            logging.error(f"Failed to scrape content from {url}")
        return content

    def generate_section(self, section_data: Any, previous_sections_content: Optional[str] = None, spinner_update_callback=None):
        """
        Generate a single section of the research report, using template data if available.
        
        Args:
            section_data: Either a string (section name) or a dictionary
                          containing 'title', 'prompt', and 'word_count'.
            previous_sections_content: Optional string containing content of previously generated sections for context.
            
        Returns:
            Generated section content or error message
        """
        try:
            section_name: str
            section_prompt: str
            word_count: Optional[int] = None

            # Adjust word count and prompt for deep research
            if self.deep_research_enabled:
                # Increase base word count for deep research
                if isinstance(section_data, dict) and "word_count" in section_data:
                    word_count = int(section_data["word_count"] * 1.5) # 50% increase
                elif word_count:
                    word_count = int(word_count * 1.5)
                else:
                    word_count = 500 # Default for deep research if not specified

                # Enhance prompt for more detail and context
                if isinstance(section_data, dict) and "prompt" in section_data:
                    section_data["prompt"] += " Provide extensive details, comprehensive analysis, and a professional, in-depth output."
                elif isinstance(section_data, str):
                    section_prompt = f"Create a detailed and comprehensive {section_name} for a professional research report on the topic: {{topic}}. Provide extensive context, in-depth analysis, and ensure a high level of detail. Keywords: {{keywords}}. Research questions: {{research_questions}}"

            if isinstance(section_data, dict):
                section_name = section_data.get("title", "Untitled Section")
                section_prompt = section_data.get("prompt")
                word_count = section_data.get("word_count")

                if not section_prompt:
                    raise ValueError(f"Section '{section_name}' is missing a 'prompt' field in the template.")
            elif isinstance(section_data, str):
                section_name = section_data
                # Use prompt manager for default section prompt
                section_prompt = self.prompt_manager.get_template("research_section")
                if not section_prompt:
                    raise ValueError(f"Default 'research_section' prompt template not found.")
            else:
                raise ValueError("Invalid section_data type. Must be string or dictionary.")

            # Ensure section_prompt is defined for string-based sections
            if isinstance(section_data, str) and not section_prompt:
                section_prompt = self.prompt_manager.get_template("research_section")
                if not section_prompt:
                    raise ValueError(f"Default 'research_section' prompt template not found for string section '{section_name}'.")
            
            deep_research_instruction = ""
            if self.deep_research_enabled:
                deep_research_instruction = "Provide extensive details, comprehensive analysis, and a professional, in-depth output."

            # Format the prompt using PromptManager
            final_prompt = self.prompt_manager.format_prompt(
                "research_section",
                section_name=section_name,
                topic=self.topic,
                keywords=self.keywords,
                research_questions=self.research_questions,
                word_count=word_count if word_count else "", # Pass word_count if available
                deep_research_instruction=deep_research_instruction,
                previous_sections_content=previous_sections_content if previous_sections_content else "" # Add previous sections content
            )
            
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Generating section: {section_name}")
            if spinner_update_callback: # Use the passed callback if available
                spinner_update_callback(f"Generating section: {section_name}")
            logging.info(f"Generating section: {section_name}")
            return self._make_api_call_with_retry(final_prompt, section_name)
            
        except ValueError as e:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Validation error in generate_section: {e}")
            if spinner_update_callback: # Use the passed callback if available
                spinner_update_callback(f"Validation error in generate_section: {e}")
            logging.error(f"Validation error in generate_section: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Unexpected error in generate_section: {e}")
            if spinner_update_callback: # Use the passed callback if available
                spinner_update_callback(f"Unexpected error in generate_section: {e}")
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
            
            # This method is likely deprecated or used for default generation.
            # The main app() function in research.py now handles section iteration based on templates.
            # For backward compatibility or default behavior, we can keep this,
            # but it should ideally call generate_section with appropriate data.
            
            sections = {}

            if self.spinner_update_callback:
                self.spinner_update_callback("Setting the stage with a compelling Introduction...")
            sections["Introduction"] = self.generate_section({"title": "Introduction", "prompt": "Provide an introduction to the topic.", "word_count": 200})

            if self.spinner_update_callback:
                self.spinner_update_callback("Exploring existing knowledge for the Literature Review...")
            sections["Literature Review"] = self.generate_section({"title": "Literature Review", "prompt": "Review existing literature on the topic.", "word_count": 400})

            if self.spinner_update_callback:
                self.spinner_update_callback("Designing the research approach in Methodology...")
            sections["Methodology"] = self.generate_section({"title": "Methodology", "prompt": "Describe the research methodology.", "word_count": 300})

            if self.spinner_update_callback:
                self.spinner_update_callback("Unveiling the key findings in Research Results...")
            sections["Results"] = self.generate_section({"title": "Results", "prompt": "Present the results of the research.", "word_count": 300})

            if self.spinner_update_callback:
                self.spinner_update_callback("Delving into insights and discussions...")
            sections["Discussion"] = self.generate_section({"title": "Discussion", "prompt": "Discuss the implications of the results.", "word_count": 300})

            if self.spinner_update_callback:
                self.spinner_update_callback("Bringing it all together in the Conclusion...")
            sections["Conclusion"] = self.generate_section({"title": "Conclusion", "prompt": "Conclude the research with key findings.", "word_count": 200})
            
            # Check if any sections failed
            failed_sections = [name for name, content in sections.items()
                             if content.startswith("Error")]
            
            if failed_sections:
                if self.spinner_update_callback:
                    self.spinner_update_callback(f"Warning: Failed to generate sections: {', '.join(failed_sections)}")
                logging.warning(f"Failed to generate sections: {', '.join(failed_sections)}")
            else:
                if self.spinner_update_callback:
                    self.spinner_update_callback("All sections are complete and ready for review!")
                logging.info("Successfully generated all report sections")
            
            return sections
            
        except Exception as e:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Critical error generating report: {e}")
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
            
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Generating custom section: {section_name}")
            logging.info(f"Generating custom section: {section_name}")
            return self._make_api_call_with_retry(prompt, section_name)
            
        except ValueError as e:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Validation error in generate_custom_section: {e}")
            logging.error(f"Validation error in generate_custom_section: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Unexpected error in generate_custom_section: {e}")
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
            
            summary_word_count = "200-300"
            summary_detail_instruction = "concise"
            deep_research_instruction = ""

            if self.deep_research_enabled:
                summary_word_count = "400-600"
                summary_detail_instruction = "detailed and comprehensive"
                deep_research_instruction = "If deep research is enabled, provide a more extensive and in-depth summary."

            prompt = self.prompt_manager.format_prompt(
                "executive_summary",
                summary_detail_instruction=summary_detail_instruction,
                summary_word_count=summary_word_count,
                deep_research_instruction=deep_research_instruction,
                full_report_content=full_report_content
            )
            
            if self.spinner_update_callback:
                self.spinner_update_callback("Generating executive summary.")
            logging.info("Generating executive summary.")
            return self._make_api_call_with_retry(prompt, "Executive Summary")
            
        except ValueError as e:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Validation error in generate_summary: {e}")
            logging.error(f"Validation error in generate_summary: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            if self.spinner_update_callback:
                self.spinner_update_callback(f"Unexpected error in generate_summary: {e}")
            logging.error(f"Unexpected error in generate_summary: {e}")
            return f"Error generating executive summary: {str(e)}"
