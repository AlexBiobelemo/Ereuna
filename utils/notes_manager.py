import os
import logging
from pathlib import Path
from docx import Document
from fpdf import FPDF
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NotesManager:
    def __init__(self, filepath="research_notes.txt"):
        self.filepath = filepath
        self.notes = self.load_notes()

    def load_notes(self):
        """Load notes from file with error handling."""
        try:
            if not os.path.exists(self.filepath):
                logging.info(f"Notes file not found at {self.filepath}. Starting with empty notes.")
                return ""
            
            with open(self.filepath, "r", encoding='utf-8') as f:
                content = f.read()
                logging.info(f"Successfully loaded notes from {self.filepath}")
                return content
        except PermissionError:
            logging.error(f"Permission denied when reading {self.filepath}")
            return ""
        except UnicodeDecodeError as e:
            logging.error(f"Encoding error when reading {self.filepath}: {e}")
            try:
                # Try with different encoding
                with open(self.filepath, "r", encoding='latin-1') as f:
                    return f.read()
            except Exception as fallback_error:
                logging.error(f"Fallback encoding failed: {fallback_error}")
                return ""
        except Exception as e:
            logging.error(f"Unexpected error loading notes: {e}")
            return ""

    def update_notes(self, new_notes):
        """Update notes content and save."""
        if new_notes is None:
            logging.warning("Attempted to update notes with None value")
            return False
        
        self.notes = new_notes
        return self.save_notes()

    def save_notes(self):
        """Save notes to file with error handling."""
        try:
            # Ensure directory exists
            directory = os.path.dirname(self.filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logging.info(f"Created directory: {directory}")
            
            with open(self.filepath, "w", encoding='utf-8') as f:
                f.write(self.notes)
            logging.info(f"Successfully saved notes to {self.filepath}")
            return True
        except PermissionError:
            logging.error(f"Permission denied when writing to {self.filepath}")
            return False
        except OSError as e:
            logging.error(f"OS error when saving notes: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error saving notes: {e}")
            return False

    def format_notes(self):
        """Format notes with error handling."""
        try:
            if not self.notes or not self.notes.strip():
                logging.warning("No notes to format")
                return ""
            
            formatted_text = []
            lines = self.notes.split('\n')
            
            for line in lines:
                stripped_line = line.strip()
                if not stripped_line:
                    formatted_text.append("")
                    continue
                
                # Simple heuristic for section titles
                if stripped_line.endswith(':'):
                    formatted_text.append(f"## {stripped_line}")
                # Already a bullet
                elif stripped_line.startswith('- '):
                    formatted_text.append(line)
                # Any other non-empty line
                else:
                    formatted_text.append(f"- {stripped_line}")
            
            result = "\n".join(formatted_text)
            logging.info("Successfully formatted notes")
            return result
        except Exception as e:
            logging.error(f"Error formatting notes: {e}")
            return self.notes  # Return original notes on error

    def _ensure_output_directory(self, output_path):
        """Ensure the output directory exists."""
        try:
            directory = os.path.dirname(output_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logging.info(f"Created output directory: {directory}")
            return True
        except Exception as e:
            logging.error(f"Failed to create output directory: {e}")
            return False

    def save_as_pdf(self, output_path="research_notes.pdf"):
        """Save notes as PDF with comprehensive error handling."""
        try:
            if not self.notes or not self.notes.strip():
                logging.error("Cannot save PDF: No notes content available")
                raise ValueError("No notes content to save")
            
            # Ensure output directory exists
            if not self._ensure_output_directory(output_path):
                raise OSError(f"Cannot create directory for {output_path}")
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Handle encoding issues by replacing problematic characters
            try:
                clean_notes = self.notes.encode('latin-1', 'replace').decode('latin-1')
            except Exception as e:
                logging.warning(f"Encoding issue in PDF generation: {e}")
                clean_notes = self.notes.encode('ascii', 'ignore').decode('ascii')
            
            pdf.multi_cell(0, 10, clean_notes)
            pdf.output(output_path)
            
            logging.info(f"Successfully saved PDF to {output_path}")
            return output_path
        except ValueError as e:
            logging.error(f"Validation error: {e}")
            raise
        except PermissionError:
            logging.error(f"Permission denied when writing PDF to {output_path}")
            raise
        except Exception as e:
            logging.error(f"Error saving PDF: {e}")
            raise Exception(f"Failed to save PDF: {str(e)}")

    def save_as_docx(self, output_path="research_notes.docx"):
        """Save notes as DOCX with comprehensive error handling."""
        try:
            if not self.notes or not self.notes.strip():
                logging.error("Cannot save DOCX: No notes content available")
                raise ValueError("No notes content to save")
            
            # Ensure output directory exists
            if not self._ensure_output_directory(output_path):
                raise OSError(f"Cannot create directory for {output_path}")
            
            document = Document()
            document.add_paragraph(self.notes)
            document.save(output_path)
            
            logging.info(f"Successfully saved DOCX to {output_path}")
            return output_path
        except ValueError as e:
            logging.error(f"Validation error: {e}")
            raise
        except PermissionError:
            logging.error(f"Permission denied when writing DOCX to {output_path}")
            raise
        except Exception as e:
            logging.error(f"Error saving DOCX: {e}")
            raise Exception(f"Failed to save DOCX: {str(e)}")
