import os
from fpdf import FPDF, HTMLMixin
from datetime import datetime
import unicodedata
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PdfGenerator(HTMLMixin, FPDF):
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
        # Use DejaVuSans for broad Unicode support
        # Ensure 'DejaVuSans.ttf' and 'DejaVuSans-Bold.ttf' are in 'utils/fonts/'
        try:
            font_path = "utils/fonts/DejaVuSans.ttf"
            font_bold_path = "utils/fonts/DejaVuSans-Bold.ttf"
            
            if not os.path.exists(font_path):
                logging.warning(f"Font file not found: {font_path}. Falling back to Arial.")
                self.font_name = "Arial"
                return
            
            self.add_font("DejaVuSans", "", font_path, uni=True)
            
            if os.path.exists(font_bold_path):
                self.add_font("DejaVuSans", "B", font_bold_path, uni=True)
            else:
                logging.warning(f"Bold font not found: {font_bold_path}")
            
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

    def generate_table_of_contents(self, sections_with_pages):
        """Generate table of contents with validation."""
        try:
            if not sections_with_pages or not isinstance(sections_with_pages, dict):
                logging.warning("No sections provided for table of contents")
                return
            
            self.add_page()
            self.set_font(self.font_name, "B", 16)
            self.cell(0, 20, self._normalize_text("Table of Contents"), ln=True, align="C")
            self.ln(10)  # Add some space

            self.set_font(self.font_name, "", 12)
            for i, (title, page_num) in enumerate(sections_with_pages.items()):
                try:
                    link = self.add_link()
                    self.set_link(link, page=page_num)
                    self.cell(10, 10, f"{i+1}.", 0, 0, 'L')
                    self.cell(0, 10, self._normalize_text(title), 0, 0, 'L', link=link)
                    self.cell(0, 10, f"... {page_num}", 0, 1, 'R')
                    self.ln(2)
                except Exception as e:
                    logging.warning(f"Error adding TOC entry for '{title}': {e}")
                    continue
            
            logging.info("Table of contents generated successfully")
        except Exception as e:
            logging.error(f"Error generating table of contents: {e}")
            # Don't raise - TOC is not critical

    def _normalize_text(self, text):
        """Normalize text to handle Unicode characters safely."""
        if text is None:
            return ""
        
        try:
            # Convert to string if not already
            text = str(text)
            
            # Normalize to NFC (precomposed characters)
            normalized = unicodedata.normalize('NFC', text)
            
            # Try encoding to Latin-1, replacing unsupported chars
            return normalized.encode('latin-1', 'replace').decode('latin-1')
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            logging.warning(f"Unicode normalization failed: {e}. Using ASCII fallback.")
            try:
                # Fallback to ASCII, replacing non-ASCII chars
                return str(text).encode('ascii', 'replace').decode('ascii')
            except Exception as fallback_error:
                logging.error(f"ASCII fallback failed: {fallback_error}")
                return "[Text encoding error]"

    def generate_section_content(self, title, content):
        """Generate section content with comprehensive error handling."""
        try:
            if not title or not isinstance(title, str):
                logging.warning("Invalid section title provided")
                return
            
            if not content or not isinstance(content, str):
                logging.warning(f"Invalid content for section '{title}'")
                content = "[No content available]"
            
            self.add_page()
            page_num = self.page_no()  # Capture page number for bookmark
            
            self.set_font(self.font_name, "B", 14)
            self.cell(0, 15, self._normalize_text(title), ln=True, align="L")
            self.ln(5)
            
            self.set_font(self.font_name, "", 12)
            try:
                self.multi_cell(0, 10, self._normalize_text(content))
                logging.info(f"Section '{title}' rendered successfully")
            except Exception as e:
                logging.error(f"Error rendering content for '{title}': {e}")
                self.multi_cell(0, 10, "[Content could not be rendered due to encoding issues]")
            
            # Add bookmark
            try:
                self.add_bookmark(title=self._normalize_text(title), level=0, page=page_num)
                logging.info(f"Added bookmark for '{title}' on page {page_num}")
            except AttributeError as e:
                logging.warning(f"Bookmark creation not supported: {e}")
            except Exception as e:
                logging.warning(f"Bookmark creation failed for '{title}': {e}")
        except Exception as e:
            logging.error(f"Error generating section '{title}': {e}")
            # Don't raise - continue with other sections

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
                
                sections_with_pages[title] = self.page_no() + 1
                self.generate_section_content(title, content)
                valid_sections += 1

            # Generate TOC after all content
            if sections_with_pages:
                self.generate_table_of_contents(sections_with_pages)
                logging.info(f"Generated PDF with {valid_sections} sections")
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
