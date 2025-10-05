import os
from fpdf import FPDF, HTMLMixin
from datetime import datetime
import unicodedata
import logging
import re

# Configure logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PdfGenerator(FPDF, HTMLMixin):
    def __init__(self, topic, author="Research Assistant"):
        super().__init__()  # Initialize FPDF superclass
        
        # Validate inputs
        if not topic or not isinstance(topic, str) or not topic.strip():
            raise ValueError("Topic must be a non-empty string")
        
        self.topic = topic.strip()
        self.author = author.strip() if author else "Research Assistant"
        self.font_name = "DejaVuSans"  # Default to DejaVuSans for Unicode support

    def setup_fonts(self):
        """Setup fonts with fallback handling."""
        try:
            font_path = "utils/fonts/DejaVuSans.ttf"
            font_bold_path = "utils/fonts/DejaVuSans-Bold.ttf"
            font_italic_path = "utils/fonts/DejaVuSans-Oblique.ttf"
            font_bold_italic_path = "utils/fonts/DejaVuSans-BoldOblique.ttf"
            
            if not os.path.exists(font_path):
                logging.warning(f"Font file not found: {font_path}. Falling back to Arial.")
                self.font_name = "Arial"
                return
            
            self.add_font("DejaVuSans", "", font_path, uni=True)
            
            if os.path.exists(font_bold_path):
                self.add_font("DejaVuSans", "B", font_bold_path, uni=True)
            else:
                logging.warning(f"Bold font not found: {font_bold_path}")
            
            if os.path.exists(font_italic_path):
                self.add_font("DejaVuSans", "I", font_italic_path, uni=True)
            else:
                logging.warning(f"Italic font not found: {font_italic_path}")
                
            if os.path.exists(font_bold_italic_path):
                self.add_font("DejaVuSans", "BI", font_bold_italic_path, uni=True)
            else:
                logging.warning(f"Bold-Italic font not found: {font_bold_italic_path}")
            
            logging.info("Successfully loaded DejaVuSans fonts.")
        except (RuntimeError, FileNotFoundError) as e:
            logging.warning(f"Font loading failed: {e}. Falling back to Arial.")
            self.font_name = "Arial"
        except Exception as e:
            logging.error(f"Unexpected error loading fonts: {e}. Using Arial.")
            self.font_name = "Arial"

    def generate_cover_page(self):
        """Generate cover page with error handling."""
        try:
            self.add_page()
            self.set_font(self.font_name, "B", 24)
            self.cell(0, 20, self._normalize_text("Research Report"), ln=True, align="C")
            self.set_font(self.font_name, "B", 16)
            self.cell(0, 10, self._normalize_text(self.topic), ln=True, align="C")
            self.set_font(self.font_name, "", 12)
            self.cell(0, 10, self._normalize_text(f"Author: {self.author}"), ln=True, align="C")
            self.cell(0, 10, self._normalize_text(f"Date: {datetime.now().strftime('%Y-%m-%d')}"), ln=True, align="C")
            logging.info("Cover page generated successfully")
        except Exception as e:
            logging.error(f"Error generating cover page: {e}")
            raise

    def generate_table_of_contents(self, sections_with_pages, toc_page_num):
        """Generate table of contents with validation."""
        try:
            if not sections_with_pages or not isinstance(sections_with_pages, dict):
                logging.warning("No sections provided for table of contents")
                return
            
            # Go to the designated TOC page
            self.set_page(toc_page_num)
            self.set_font(self.font_name, "B", 16)
            self.cell(0, 20, self._normalize_text("Table of Contents"), ln=True, align="C")
            self.ln(10)

            self.set_font(self.font_name, "", 12)
            for i, (title, page_num) in enumerate(sections_with_pages.items()):
                try:
                    # Create a link to the section
                    link = self.add_link()
                    self.set_link(link, page=page_num)
                    
                    # Strip markdown from title
                    clean_title = self._strip_markdown(title)
                    
                    # Output the title and page number
                    self.cell(10, 10, f"{i+1}.", 0, 0, 'L')
                    self.cell(0, 10, self._normalize_text(clean_title), 0, 0, 'L', link=link)
                    self.cell(0, 10, f"... {page_num}", 0, 1, 'R')
                    self.ln(2)
                except Exception as e:
                    logging.warning(f"Error adding TOC entry for '{title}': {e}")
                    continue
            
            logging.info("Table of contents generated successfully")
        except Exception as e:
            logging.error(f"Error generating table of contents: {e}")

    def _normalize_text(self, text):
        """Normalize text to handle Unicode characters safely."""
        if text is None:
            return ""
        
        try:
            text = str(text)
            normalized = unicodedata.normalize('NFC', text)
            return normalized.encode('latin-1', 'replace').decode('latin-1')
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            logging.warning(f"Unicode normalization failed: {e}. Using ASCII fallback.")
            try:
                return str(text).encode('ascii', 'replace').decode('ascii')
            except Exception as fallback_error:
                logging.error(f"ASCII fallback failed: {fallback_error}")
                return "[Text encoding error]"

    def _strip_markdown(self, text):
        """Remove ALL markdown formatting from text."""
        if not text:
            return ""
        
        # Remove headers (#### or ###)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove bold (**text**)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        # Remove italic (*text*)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)', r'\1', text)
        # Remove code (`text`)
        text = re.sub(r'`(.+?)`', r'\1', text)
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _process_inline_markdown(self, text):
        """
        Process inline markdown and return list of segments with styles.
        This handles **bold**, *italic*, and `code`.
        """
        segments = []
        pos = 0
        
        # More aggressive pattern that catches bold/italic/code
        # Check ** before single * to avoid breaking bold into italic
        pattern = r'`([^`]+)`|\*\*([^\*]+?)\*\*|\*([^\*\s]+(?:[^\*]*[^\*\s])?)\*'
        
        for match in re.finditer(pattern, text):
            # Add plain text before the match
            if match.start() > pos:
                plain = text[pos:match.start()]
                if plain:
                    segments.append({'text': plain, 'style': ''})
            
            # Check which group matched
            if match.group(1):  # Code: `text`
                segments.append({'text': match.group(1), 'style': 'code'})
                logging.debug(f"Found code: {match.group(1)[:20]}")
            elif match.group(2):  # Bold: **text**
                segments.append({'text': match.group(2), 'style': 'B'})
                logging.debug(f"Found bold: {match.group(2)[:20]}")
            elif match.group(3):  # Italic: *text*
                segments.append({'text': match.group(3), 'style': 'I'})
                logging.debug(f"Found italic: {match.group(3)[:20]}")
            
            pos = match.end()
        
        # Add remaining text
        if pos < len(text):
            remaining = text[pos:]
            if remaining:
                segments.append({'text': remaining, 'style': ''})
        
        # If no segments found, return the original text as plain
        if not segments:
            segments = [{'text': text, 'style': ''}]
        
        return segments

    def _render_paragraph_with_formatting(self, text, indent=0):
        """Render a paragraph with inline formatting support."""
        segments = self._process_inline_markdown(text)
        
        x_start = self.l_margin + indent
        y_start = self.get_y()
        max_width = self.w - self.r_margin - x_start
        
        self.set_x(x_start)
        
        for segment in segments:
            style = segment['style']
            content = segment['text']
            
            # Set appropriate font
            if style == 'B':
                self.set_font(self.font_name, 'B', 12)
            elif style == 'I':
                self.set_font(self.font_name, 'I', 12)
            elif style == 'code':
                self.set_font('Courier', '', 10)
            else:
                self.set_font(self.font_name, '', 12)
            
            # Handle word wrapping
            words = content.split(' ')
            for i, word in enumerate(words):
                if i > 0:
                    word = ' ' + word
                
                word_width = self.get_string_width(word)
                current_x = self.get_x()
                
                # Check if word fits on current line
                if current_x + word_width > self.w - self.r_margin:
                    self.ln(6)
                    self.set_x(x_start)
                
                self.cell(word_width, 6, self._normalize_text(word), 0, 0)

    def generate_section_content(self, title, content):
        """Generate section content with proper markdown formatting."""
        try:
            if not title or not isinstance(title, str):
                logging.warning("Invalid section title provided")
                return
            
            if not content or not isinstance(content, str):
                logging.warning(f"Invalid content for section '{title}'")
                content = "[No content available]"
            
            self.add_page()
            page_num = self.page_no()
            
            # Render section title (strip any markdown from it)
            clean_title = self._strip_markdown(title)
            self.set_font(self.font_name, "B", 14)
            self.cell(0, 15, self._normalize_text(clean_title), ln=True, align="L")
            self.ln(5)
            
            # Process content line by line
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines):
                line = line.rstrip()
                
                # Skip empty lines
                if not line.strip():
                    self.ln(3)
                    continue
                
                try:
                    # DEBUG: Log the line being processed
                    logging.debug(f"Processing line {line_num}: {line[:50]}...")
                    
                    # Check for headers (#### or ###, etc.)
                    # Look for lines starting with # (with optional leading spaces)
                    header_match = re.match(r'^\s*(#{1,6})\s+(.+)$', line)
                    if header_match:
                        level = len(header_match.group(1))
                        header_text = header_match.group(2)
                        
                        logging.info(f"Found header level {level}: {header_text[:30]}...")
                        
                        # Size based on level: # = 16pt, ## = 14pt, ### = 13pt, #### = 12pt
                        size = max(17 - level, 11)
                        
                        self.ln(4)
                        self.set_font(self.font_name, 'B', size)
                        
                        # Strip markdown from header text
                        clean_header = self._strip_markdown(header_text)
                        self.multi_cell(0, 7, self._normalize_text(clean_header))
                        self.ln(2)
                        continue
                    
                    # Check for bullet points (with optional leading spaces)
                    bullet_match = re.match(r'^\s*[\*\-\+]\s+(.+)$', line)
                    if bullet_match:
                        bullet_text = bullet_match.group(1)
                        
                        logging.debug(f"Found bullet: {bullet_text[:30]}...")
                        
                        # Render bullet
                        self.set_font(self.font_name, '', 12)
                        self.cell(8, 6, self._normalize_text('•'), 0, 0)
                        
                        # Render text with inline formatting
                        self._render_paragraph_with_formatting(bullet_text, indent=8)
                        self.ln(6)
                        continue
                    
                    # Check for numbered lists (with optional leading spaces)
                    numbered_match = re.match(r'^\s*(\d+)\.\s+(.+)$', line)
                    if numbered_match:
                        number = numbered_match.group(1)
                        numbered_text = numbered_match.group(2)
                        
                        logging.debug(f"Found numbered item: {number}. {numbered_text[:30]}...")
                        
                        # Render number
                        self.set_font(self.font_name, '', 12)
                        num_width = self.get_string_width(f'{number}. ')
                        self.cell(num_width, 6, self._normalize_text(f'{number}. '), 0, 0)
                        
                        # Render text with inline formatting
                        self._render_paragraph_with_formatting(numbered_text, indent=num_width)
                        self.ln(6)
                        continue
                    
                    # Regular paragraph with inline formatting
                    logging.debug(f"Regular paragraph: {line[:30]}...")
                    self._render_paragraph_with_formatting(line)
                    self.ln(7)
                    
                except Exception as e:
                    logging.error(f"Error rendering line {line_num} in '{title}': {e}")
                    logging.error(f"Problematic line: {line}")
                    # Fallback to plain text
                    self.set_font(self.font_name, "", 12)
                    self.multi_cell(0, 6, self._normalize_text(line))
                    self.ln(2)
            
            logging.info(f"Section '{title}' rendered successfully")
            
            # Add bookmark with clean title
            self.add_bookmark(self._normalize_text(clean_title), level=0)
            
        except Exception as e:
            logging.error(f"Error generating section '{title}': {e}")

    def generate_pdf_report(self, sections_content, output_path="research_report.pdf"):
        """Generate complete PDF report with validation and error handling."""
        try:
            # Validate inputs
            if not sections_content or not isinstance(sections_content, dict):
                raise ValueError("sections_content must be a non-empty dictionary")
            
            if not output_path or not isinstance(output_path, str):
                raise ValueError("output_path must be a valid string")
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    logging.info(f"Created output directory: {output_dir}")
                except Exception as e:
                    logging.error(f"Failed to create output directory: {e}")
                    raise
            
            # Setup PDF
            self.set_auto_page_break(auto=True, margin=15)
            self.setup_fonts()

            # Generate cover page
            self.generate_cover_page()

            # Add a placeholder page for TOC and get its page number
            self.add_page()
            toc_page_num = self.page_no()
            
            # Generate content and capture page numbers for TOC
            sections_with_pages = {}
            valid_sections = 0
            
            for title, content in sections_content.items():
                if not title or not isinstance(title, str) or not title.strip():
                    logging.warning(f"Skipping section with invalid title")
                    continue
                
                if not content or not isinstance(content, str) or not content.strip():
                    logging.warning(f"Skipping empty section: '{title}'")
                    continue
                
                # Store the page number *before* generating the section content
                sections_with_pages[title] = self.page_no() + 1
                self.generate_section_content(title, content)
                valid_sections += 1

            # Generate TOC after all content
            if sections_with_pages:
                self.generate_table_of_contents(sections_with_pages, toc_page_num)
                logging.info(f"Generated PDF with {valid_sections} sections and Table of Contents")
            else:
                logging.warning("No valid sections found. PDF may be empty.")

            # Save PDF
            try:
                self.output(output_path)
                logging.info(f"PDF saved successfully to {output_path}")
            except PermissionError:
                logging.error(f"Permission denied when writing to {output_path}")
                raise
            except Exception as e:
                logging.error(f"Error saving PDF to {output_path}: {e}")
                raise
            
            return output_path
        except ValueError as e:
            logging.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error generating PDF report: {e}")
            raise
