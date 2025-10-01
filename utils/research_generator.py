import google.generativeai as genai
import logging
import time
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ResearchGenerator:
    def __init__(self, topic, keywords, research_questions, api_key, system_prompt, 
                 max_retries=3, timeout=60):
        """
        Initialize ResearchGenerator with validation and error handling.
        
        Args:
            topic: Research topic
            keywords: Keywords for research
            research_questions: Research questions
            api_key: Gemini API key
            system_prompt: System prompt for generation
            max_retries: Maximum number of retry attempts for API calls
            timeout: Timeout for API calls in seconds
        """
        # Validate inputs
        if not topic or not isinstance(topic, str) or not topic.strip():
            raise ValueError("Topic must be a non-empty string")
        
        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("API key must be a non-empty string")
        
        if not system_prompt or not isinstance(system_prompt, str):
            raise ValueError("System prompt must be a non-empty string")
        
        self.topic = topic.strip()
        self.keywords = self._validate_input(keywords, "Keywords")
        self.research_questions = self._validate_input(research_questions, "Research questions")
        self.api_key = api_key.strip()
        self.system_prompt = system_prompt.strip()
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Configure API
        try:
            genai.configure(api_key=self.api_key)
            logging.info("Successfully configured Gemini API")
        except Exception as e:
            logging.error(f"Failed to configure Gemini API: {e}")
            raise ValueError(f"Invalid API key or configuration error: {str(e)}")

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
        Make API call with retry logic and exponential backoff.
        
        Args:
            prompt: The prompt to send to the API
            section_name: Name of the section being generated
            
        Returns:
            Generated text or error message
        """
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        for attempt in range(self.max_retries):
            try:
                logging.info(f"Attempting to generate {section_name} (attempt {attempt + 1}/{self.max_retries})")
                
                # Generate content with timeout consideration
                response = model.generate_content(prompt)
                
                # Validate response
                if not response or not hasattr(response, 'text'):
                    raise ValueError(f"Invalid response structure for {section_name}")
                
                if not response.text or not response.text.strip():
                    raise ValueError(f"Empty response received for {section_name}")
                
                logging.info(f"Successfully generated {section_name}")
                return response.text
                
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Log different types of errors
                if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                    logging.error(f"API rate limit/quota error for {section_name}: {error_msg}")
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8 seconds
                        logging.info(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        return f"Error: API rate limit exceeded for {section_name}. Please try again later."
                
                elif "timeout" in error_msg.lower():
                    logging.error(f"Timeout error for {section_name}: {error_msg}")
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt)
                        logging.info(f"Timeout occurred. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        return f"Error: Request timeout for {section_name}. Please check your connection and try again."
                
                elif "api" in error_msg.lower() and "key" in error_msg.lower():
                    logging.error(f"API key error for {section_name}: {error_msg}")
                    return f"Error: Invalid API key. Please check your Gemini API key configuration."
                
                elif "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
                    logging.error(f"Permission error for {section_name}: {error_msg}")
                    return f"Error: Permission denied. Please check your API key permissions."
                
                else:
                    logging.error(f"Unexpected error generating {section_name} (attempt {attempt + 1}): {error_type} - {error_msg}")
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logging.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return f"Error generating {section_name}: {error_type} - {error_msg}"
        
        # If all retries failed
        return f"Error: Failed to generate {section_name} after {self.max_retries} attempts. Please try again later."

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
