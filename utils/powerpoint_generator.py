import os
import logging
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from datetime import datetime
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PowerpointGenerator:
    def __init__(self, topic):
        if not topic or not isinstance(topic, str) or not topic.strip():
            raise ValueError("Topic must be a non-empty string")
        self.topic = topic.strip()

    def create_title_slide(self, prs):
        """Create title slide with error handling."""
        try:
            if not prs or not hasattr(prs, 'slide_layouts'):
                raise ValueError("Invalid presentation object")
            
            # Check if title slide layout exists
            if len(prs.slide_layouts) < 1:
                raise ValueError("No slide layouts available in presentation")
            
            slide_layout = prs.slide_layouts[0]
            slide = prs.slides.add_slide(slide_layout)
            
            # Safely access title
            if hasattr(slide.shapes, 'title') and slide.shapes.title:
                title = slide.shapes.title
                title.text = self.topic
            else:
                logging.warning("Title placeholder not found in slide layout")
            
            # Safely access subtitle
            try:
                if len(slide.placeholders) > 1:
                    subtitle = slide.placeholders[1]
                    subtitle.text = f"Research Presentation\nGenerated: {datetime.now().strftime('%Y-%m-%d')}"
                else:
                    logging.warning("Subtitle placeholder not found in slide layout")
            except (IndexError, KeyError) as e:
                logging.warning(f"Could not access subtitle placeholder: {e}")
            
            logging.info("Title slide created successfully")
            return slide
        except Exception as e:
            logging.error(f"Error creating title slide: {e}")
            raise

    def create_content_slide(self, prs, title_text, bullets):
        """Create content slide with comprehensive error handling."""
        try:
            if not prs or not hasattr(prs, 'slide_layouts'):
                raise ValueError("Invalid presentation object")
            
            if not title_text or not isinstance(title_text, str):
                logging.warning("Invalid title text provided, using default")
                title_text = "Untitled Slide"
            
            if not bullets or not isinstance(bullets, (list, tuple)):
                logging.warning(f"Invalid bullets for slide '{title_text}', using empty list")
                bullets = []
            
            # Check if content slide layout exists
            if len(prs.slide_layouts) < 2:
                raise ValueError("Content slide layout not available in presentation")
            
            slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(slide_layout)
            
            # Safely set title
            try:
                if hasattr(slide.shapes, 'title') and slide.shapes.title:
                    title = slide.shapes.title
                    title.text = title_text[:250]  # Limit title length
                else:
                    logging.warning(f"Title placeholder not found for slide '{title_text}'")
            except Exception as e:
                logging.warning(f"Error setting title for slide '{title_text}': {e}")
            
            # Safely set content
            try:
                if len(slide.placeholders) > 1:
                    content_box = slide.placeholders[1]
                    
                    if hasattr(content_box, 'text_frame'):
                        text_frame = content_box.text_frame
                        text_frame.clear()

                        # Add bullets with validation
                        for i, bullet in enumerate(bullets):
                            try:
                                if not bullet or not isinstance(bullet, str):
                                    logging.warning(f"Skipping invalid bullet at index {i}")
                                    continue
                                
                                # Limit bullet text length to prevent overflow
                                bullet_text = str(bullet).strip()[:500]
                                
                                p = text_frame.add_paragraph()
                                p.text = bullet_text
                                p.level = 0
                                
                                # Safely set font size
                                try:
                                    p.font.size = Pt(18)
                                except Exception as font_error:
                                    logging.warning(f"Could not set font size: {font_error}")
                            except Exception as bullet_error:
                                logging.warning(f"Error adding bullet {i}: {bullet_error}")
                                continue
                    else:
                        logging.warning(f"Content placeholder has no text_frame for slide '{title_text}'")
                else:
                    logging.warning(f"Content placeholder not found for slide '{title_text}'")
            except Exception as e:
                logging.warning(f"Error setting content for slide '{title_text}': {e}")
            
            logging.info(f"Content slide '{title_text}' created successfully with {len(bullets)} bullets")
            return slide
        except Exception as e:
            logging.error(f"Error creating content slide '{title_text}': {e}")
            raise

    def generate_powerpoint(self, slides_data, output_path="research_presentation.pptx"):
        """Generate PowerPoint presentation with comprehensive error handling."""
        try:
            # Validate inputs
            if not slides_data or not isinstance(slides_data, (list, tuple)):
                raise ValueError("slides_data must be a non-empty list")
            
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
            
            # Create presentation
            try:
                prs = Presentation()
                prs.slide_width = Inches(10)
                prs.slide_height = Inches(7.5)
            except Exception as e:
                logging.error(f"Error creating presentation object: {e}")
                raise
            
            # Validate that presentation has required layouts
            if not hasattr(prs, 'slide_layouts') or len(prs.slide_layouts) < 2:
                raise ValueError("Presentation template does not have required slide layouts")
            
            # Process slides
            valid_slides = 0
            for i, slide_data in enumerate(slides_data):
                try:
                    # Validate slide data structure
                    if not isinstance(slide_data, dict):
                        logging.warning(f"Skipping invalid slide data at index {i}: not a dictionary")
                        continue
                    
                    if "title" not in slide_data:
                        logging.warning(f"Skipping slide at index {i}: missing 'title' key")
                        continue
                    
                    title = slide_data.get("title", "")
                    bullets = slide_data.get("bullets", [])
                    
                    # Validate title and bullets
                    if not title or not isinstance(title, str):
                        logging.warning(f"Skipping slide at index {i}: invalid title")
                        continue
                    
                    if not isinstance(bullets, (list, tuple)):
                        logging.warning(f"Converting bullets to list for slide '{title}'")
                        bullets = [str(bullets)] if bullets else []
                    
                    self.create_content_slide(prs, title, bullets)
                    valid_slides += 1
                except Exception as e:
                    logging.error(f"Error processing slide {i}: {e}")
                    continue
            
            if valid_slides == 0:
                raise ValueError("No valid slides were created")
            
            logging.info(f"Created PowerPoint with {valid_slides} valid slides")
            
            # Save PowerPoint
            try:
                # Save to bytes first for validation
                ppt_bytes = io.BytesIO()
                prs.save(ppt_bytes)
                ppt_bytes.seek(0)

                # Write to file
                with open(output_path, 'wb') as f:
                    f.write(ppt_bytes.read())
                
                logging.info(f"PowerPoint saved successfully to {output_path}")
            except PermissionError:
                logging.error(f"Permission denied when writing to {output_path}")
                raise
            except Exception as e:
                logging.error(f"Error saving PowerPoint to {output_path}: {e}")
                raise

            return output_path
        except ValueError as e:
            logging.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error generating PowerPoint: {e}")
            raise