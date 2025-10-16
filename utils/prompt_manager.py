import os
import json
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PromptManager:
    """
    Manages and generates prompts using templates.
    """
    def __init__(self, template_dir: str = "Ereuna/prompts"):
        self.template_dir = template_dir
        self._load_templates()

    def _load_templates(self):
        """Loads prompt templates from the specified directory."""
        self.templates: Dict[str, str] = {}
        if not os.path.exists(self.template_dir):
            logging.warning(f"Prompt template directory not found: {self.template_dir}. Creating default templates.")
            os.makedirs(self.template_dir, exist_ok=True)
            self._create_default_templates()
            return

        for filename in os.listdir(self.template_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.template_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        template_name = os.path.splitext(filename)[0]
                        self.templates[template_name] = template_data.get("prompt", "")
                        logging.info(f"Loaded prompt template: {template_name}")
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from {filepath}: {e}")
                except Exception as e:
                    logging.error(f"Error loading prompt template {filepath}: {e}")
        
        if not self.templates:
            logging.warning(f"No prompt templates found in {self.template_dir}. Creating default templates.")
            self._create_default_templates()

    def _create_default_templates(self):
        """Creates default prompt templates if none are found."""
        default_prompts = {
            "research_section": {
                "prompt": "Create a {section_name} for a research report on the topic: {topic}. Keywords: {keywords}. Research questions: {research_questions}. Ensure the content is approximately {word_count} words. {deep_research_instruction}",
                "description": "Template for generating a standard research report section."
            },
            "executive_summary": {
                "prompt": "Provide a {summary_detail_instruction} executive summary (around {summary_word_count} words) of the following research report. Focus on the main findings, key arguments, and conclusions. Ensure the summary is clear, objective, and highlights the most important aspects. {deep_research_instruction}\n\nResearch Report:\n{full_report_content}",
                "description": "Template for generating an executive summary."
            },
            "chat_response": {
                "prompt": """Based on the following research content, answer the user's question.
If the answer is not directly available in the provided content, state that you don't have enough information in the research to answer, but then attempt to answer using your broader knowledge.
If you use external knowledge, clearly state that the information is not from the provided research.
 
--- Research Content ---
{research_content}
--- End Research Content ---
 
User's Question: {user_query}
 
Please provide a clear, concise answer. Prioritize information from the research content. If you use external knowledge, clearly state that it is not from the provided research.""",
                "description": "Template for generating chat responses based on research content."
            },
            "relevance_check": {
                "prompt": "Given the research topic: '{research_topic}', determine if the following user query is relevant. Respond with 'YES' if relevant, and 'NO' if not relevant. Do not provide any other text.\n\nUser Query: {user_query}",
                "description": "Template for checking query relevance to the research topic."
            },
            "web_search_response": {
                "prompt": """Based on the following web search results and your broader knowledge, answer the user's question.
Clearly state that this information is from external sources and not the original research report.
 
--- Web Search Results ---
{scraped_content}
--- End Web Search Results ---
 
User's Question: {user_query}
 
Please provide a clear, concise answer, explicitly mentioning that this information is from external sources.""",
                "description": "Template for generating chat responses using web search results."
            },
            "table_summary": {
                "prompt": """Please summarize the following table data concisely.
            Table Content:
            {table_content}

            Provide a summary that highlights the key information and trends in the table.""",
                "description": "Template for summarizing table content."
            }
        }

        for name, data in default_prompts.items():
            filepath = os.path.join(self.template_dir, f"{name}.json")
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                self.templates[name] = data["prompt"]
                logging.info(f"Created default prompt template: {name}.json")
            except Exception as e:
                logging.error(f"Error creating default prompt template {filepath}: {e}")

    def get_template(self, template_name: str) -> Optional[str]:
        """Retrieves a prompt template by name."""
        return self.templates.get(template_name)

    def format_prompt(self, template_name: str, **kwargs) -> str:
        """
        Formats a prompt using the specified template and provided keyword arguments.
        
        Args:
            template_name: The name of the template to use.
            **kwargs: Keyword arguments to fill into the template.
            
        Returns:
            The formatted prompt string.
            
        Raises:
            ValueError: If the template name is not found.
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Prompt template '{template_name}' not found.")
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logging.error(f"Missing placeholder in template '{template_name}': {e}")
            raise ValueError(f"Missing data for prompt placeholder: {e}. Check template '{template_name}'.")
        except Exception as e:
            logging.error(f"Error formatting prompt template '{template_name}': {e}")
            raise
