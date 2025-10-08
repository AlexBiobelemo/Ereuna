from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from typing import Dict
import markdown
from bs4 import BeautifulSoup

class DocxGenerator:
    def __init__(self, topic: str):
        self.topic = topic

    def _add_markdown_content(self, document, markdown_text):
        html = markdown.markdown(markdown_text)
        soup = BeautifulSoup(html, 'html.parser')

        for element in soup.children:
            if element.name:
                if element.name.startswith('h') and len(element.name) >= 2:
                    try:
                        level = int(element.name[1])
                        document.add_heading(element.get_text(), level=level)
                    except ValueError:
                        # Fallback to a default heading level if conversion fails
                        document.add_heading(element.get_text(), level=3)
                elif element.name == 'p':
                    p = document.add_paragraph()
                    for content in element.contents:
                        if content.name == 'strong':
                            run = p.add_run(content.get_text())
                            run.bold = True
                        elif content.name == 'em':
                            run = p.add_run(content.get_text())
                            run.italic = True
                        else:
                            p.add_run(content.get_text())
                elif element.name == 'ul':
                    for li in element.find_all('li'):
                        document.add_paragraph(li.get_text(), style='List Bullet')
                else:
                    # Fallback for other tags, just add text content
                    document.add_paragraph(element.get_text())
            elif str(element).strip(): # Handle plain text directly under body
                document.add_paragraph(str(element).strip())


    def generate_docx_report(self, sections_content: Dict[str, str], output_path: str):
        document = Document()

        document.add_heading(self.topic, level=1)

        for title, content in sections_content.items():
            formatted_title = title.format(topic=self.topic)
            document.add_heading(formatted_title, level=2)
            self._add_markdown_content(document, content)

        document.save(output_path)