import os
import json
import logging
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TemplateManager:
    """
    Manages loading and providing custom research templates.
    """

    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_templates()

    def _load_templates(self):
        """Loads all JSON template files from the template directory."""
        if not os.path.exists(self.template_dir):
            logging.warning(f"Template directory '{self.template_dir}' not found.")
            return

        for filename in os.listdir(self.template_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.template_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        template_name = template_data.get("name")
                        if template_name:
                            self.templates[template_name] = template_data
                            logging.info(f"Loaded template: {template_name}")
                        else:
                            logging.warning(f"Template file '{filename}' is missing a 'name' field.")
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from template file '{filename}': {e}")
                except Exception as e:
                    logging.error(f"Error loading template file '{filename}': {e}")
        
        if not self.templates:
            logging.info("No custom templates found or loaded.")

    def get_template_names(self) -> List[str]:
        """Returns a list of available template names."""
        return sorted(list(self.templates.keys()))

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns the data for a specific template by name."""
        return self.templates.get(name)
