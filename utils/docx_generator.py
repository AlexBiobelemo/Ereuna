from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from typing import Dict
import markdown
from bs4 import BeautifulSoup
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.table import _Cell
from docx.text.paragraph import Paragraph
from typing import Dict, Any

class DocxGenerator:
    def __init__(self, topic: str):
        self.topic = topic

    def _add_markdown_content(self, document, markdown_text):
        """
        Parses markdown text and adds it to the document with enhanced styling.
        It supports headings, paragraphs, lists, blockquotes, code blocks,
        horizontal rules, tables, images (as placeholders), and hyperlinks.
        """
        # Use a more advanced markdown extension for better parsing, e.g., 'fenced_code'
        # 'tables' for markdown tables, 'nl2br' for newline to break conversion
        html = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables', 'nl2br'])
        soup = BeautifulSoup(html, 'html.parser')

        # Iterate through each top-level HTML element parsed from the markdown
        for element in soup.children:
            if element.name: # Check if it's a tag (e.g., p, h1, ul)
                if element.name.startswith('h') and len(element.name) >= 2:
                    try:
                        # Extract heading level (h1, h2, etc.)
                        level = int(element.name[1])
                        # Ensure heading levels are within DOCX's supported range (1-9)
                        document.add_heading(element.get_text(), level=min(level, 9))
                    except ValueError:
                        # Fallback to level 3 if heading level is invalid
                        document.add_heading(element.get_text(), level=3)
                elif element.name == 'p':
                    # Add a new paragraph and apply inline styles
                    p = document.add_paragraph()
                    self._apply_inline_styles(p, element)
                elif element.name == 'ul':
                    # Handle unordered lists
                    for li in element.find_all('li'):
                        p = document.add_paragraph(style='List Bullet') # Apply bullet list style
                        self._apply_inline_styles(p, li)
                elif element.name == 'ol':
                    # Handle ordered lists
                    for i, li in enumerate(element.find_all('li')):
                        p = document.add_paragraph(style='List Number') # Apply numbered list style
                        self._apply_inline_styles(p, li)
                elif element.name == 'blockquote':
                    # Handle blockquotes using a built-in DOCX style
                    p = document.add_paragraph(style='Intense Quote')
                    self._apply_inline_styles(p, element)
                elif element.name == 'pre': # For code blocks
                    code_text = element.get_text()
                    p = document.add_paragraph(code_text)
                    try:
                       p.style = 'Code'
                       except KeyError:
                           # Style does not exist; fall back to Normal
                           p.style = 'Normal'
                    # Apply monospace font directly for better code block representation
                    for run in p.runs:
                        run.font.name = 'Courier New'
                        run.font.size = Pt(10)
                elif element.name == 'hr': # Horizontal Rule
                    # Represent horizontal rule with a simple text line
                    document.add_paragraph("---", style='Normal')
                elif element.name == 'table':
                    # Convert HTML table to DOCX table
                    self._add_html_table_to_docx(document, element)
                elif element.name == 'img': # Images (add placeholder or link)
                    img_src = element.get('src', 'No source')
                    img_alt = element.get('alt', 'Image')
                    # Add a placeholder text for images, as direct image embedding is more complex
                    document.add_paragraph(f"[[Image: {img_alt} - {img_src}]]", style='Normal')
                elif element.name == 'a': # Hyperlinks
                    # Links are handled within _apply_inline_styles for paragraph content,
                    # so no direct action needed here for top-level 'a' tags.
                    pass
                else:
                    # Fallback for other unhandled tags, just add their text content
                    if element.get_text(strip=True):
                        document.add_paragraph(element.get_text())
            elif str(element).strip(): # Handle plain text directly under body (not wrapped in tags)
                document.add_paragraph(str(element).strip())

    def _apply_inline_styles(self, paragraph: Paragraph, soup_element: Any):
        """
        Applies inline styles (bold, italic, inline code, hyperlinks) to a paragraph
        based on the parsed BeautifulSoup element's contents.
        """
        for content in soup_element.contents:
            if content.name == 'strong':
                run = paragraph.add_run(content.get_text())
                run.bold = True
            elif content.name == 'em':
                run = paragraph.add_run(content.get_text())
                run.italic = True
            elif content.name == 'code': # Inline code
                run = paragraph.add_run(content.get_text())
                run.font.name = 'Courier New' # Apply monospace font for inline code
                run.font.size = Pt(10)
            elif content.name == 'a': # Hyperlink
                # Add a hyperlink to the paragraph
                self._add_hyperlink(paragraph, content.get_text(), content.get('href', '#'))
            elif content.string:
                # Add plain text content
                paragraph.add_run(content.string)
            elif content.name: # Handle nested tags like <strong><em>text</em></strong>
                # Recursively apply styles for nested elements
                self._apply_inline_styles(paragraph, content)

    def _add_hyperlink(self, paragraph, text, url):
        """
        Adds a hyperlink to a paragraph.
        This involves creating a relationship to the external URL and
        embedding the hyperlink XML element into the paragraph.
        """
        part = paragraph.part
        # Create a relationship to the external URL
        rId = part.relate_to(url, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', is_external=True)
        
        # Create the w:hyperlink XML element
        hyperlink = OxmlElement('w:hyperlink')
        hyperlink.set(qn('r:id'), rId,) # Set the relationship ID
        
        # Create a new run for the hyperlink text
        new_run = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr') # Run properties
        new_run.append(rPr)
        
        # Add color and underline to hyperlink text for visual indication
        c = OxmlElement('w:color')
        c.set(qn('w:val'), "0000FF") # Blue color
        rPr.append(c)
        
        u = OxmlElement('w:u')
        u.set(qn('w:val'), "single") # Single underline
        rPr.append(u)
        
        # Add the text content to the run
        new_run.add_child_element(OxmlElement('w:t', text=text))
        hyperlink.append(new_run)
        paragraph._p.append(hyperlink) # Append the hyperlink to the paragraph's XML
        return hyperlink

    def _add_html_table_to_docx(self, document, html_table):
        """
        Converts an HTML table (BeautifulSoup object) into a DOCX table.
        It extracts headers and rows from the HTML and populates a new DOCX table.
        """
        # Extract table headers
        headers = [th.get_text(strip=True) for th in html_table.find_all('th')]
        rows = []
        # Extract table rows and cells
        for tr in html_table.find_all('tr'):
            cols = [td.get_text(strip=True) for td in tr.find_all('td')]
            if cols: # Only add rows that have actual td elements
                rows.append(cols)

        if not headers and not rows:
            return # No table content to add, so return early

        # Determine the number of columns based on headers or the first row
        num_cols = len(headers) if headers else (len(rows[0]) if rows else 0)
        if num_cols == 0:
            return # Cannot create a table with 0 columns

        # Add a new table to the document with an initial row
        table = document.add_table(rows=1, cols=num_cols)
        table.style = 'Table Grid' # Apply a basic table style for borders

        # Add headers to the first row of the DOCX table
        if headers:
            hdr_cells = table.rows[0].cells
            for i, header_text in enumerate(headers):
                if i < num_cols: # Ensure we don't go out of bounds
                    hdr_cells[i].text = header_text
                    # Make header text bold
                    for paragraph in hdr_cells[i].paragraphs:
                        for run in paragraph.runs:
                            run.bold = True
        # If no explicit headers, the first row will be used for data,
        # so no special handling needed here.
        
        # Add data rows to the DOCX table
        # If headers exist, start adding data from the second row (index 1)
        # Otherwise, start from the first row (index 0)
        start_row_idx = 1 if headers else 0 

        for row_data in rows:
            # Ensure row_data has enough elements for the columns, pad with empty strings if necessary
            row_data_padded = row_data + [''] * (num_cols - len(row_data))
            
            cells = table.add_row().cells # Add a new row to the table
            for i, cell_text in enumerate(row_data_padded):
                if i < num_cols:
                    cells[i].text = cell_text


    def generate_docx_report(self, sections_content: Dict[str, str], output_path: str):
        """
        Generates a DOCX report from a dictionary of section titles and their markdown content.
        """
        document = Document()

        # Add the main topic as a level 1 heading
        document.add_heading(self.topic, level=1)

        # Iterate through each section and add its title and content
        for title, content in sections_content.items():
            # Format the title with the main topic if needed
            formatted_title = title.format(topic=self.topic)
            document.add_heading(formatted_title, level=2) # Add section title as a level 2 heading
            self._add_markdown_content(document, content) # Add markdown content for the section

        document.save(output_path)
