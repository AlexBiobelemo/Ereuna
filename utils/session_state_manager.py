import streamlit as st
import logging
from typing import Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SessionStateManager:
    """
    Manages Streamlit session state to prevent data loss during UI refreshes.
    This is crucial for fixing the download button refresh bug.
    """
    
    @staticmethod
    def initialize_state():
        """Initialize all required session state variables."""
        defaults = {
            'research_generated': False,
            'research_sections': None,
            'pdf_generated': False,
            'pdf_path': None,
            'pdf_bytes': None,
            'pptx_generated': False,
            'pptx_path': None,
            'pptx_bytes': None,
            'docx_generated': False,
            'docx_path': None,
            'docx_bytes': None,
            'current_topic': '',
            'current_keywords': '',
            'current_questions': '',
            'notes_content': '',
            'error_message': None,
            'generation_in_progress': False
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                logging.debug(f"Initialized session state: {key} = {default_value}")

    @staticmethod
    def set_value(key: str, value: Any) -> None:
        """
        Safely set a session state value.
        
        Args:
            key: Session state key
            value: Value to set
        """
        try:
            st.session_state[key] = value
            logging.debug(f"Set session state: {key}")
        except Exception as e:
            logging.error(f"Error setting session state '{key}': {e}")

    @staticmethod
    def get_value(key: str, default: Any = None) -> Any:
        """
        Safely get a session state value.
        
        Args:
            key: Session state key
            default: Default value if key doesn't exist
            
        Returns:
            Value from session state or default
        """
        try:
            return st.session_state.get(key, default)
        except Exception as e:
            logging.error(f"Error getting session state '{key}': {e}")
            return default

    @staticmethod
    def store_research_data(sections: dict, topic: str, keywords: str, questions: str) -> None:
        """
        Store research generation data in session state.
        
        Args:
            sections: Generated research sections
            topic: Research topic
            keywords: Research keywords
            questions: Research questions
        """
        try:
            st.session_state['research_sections'] = sections
            st.session_state['research_generated'] = True
            st.session_state['current_topic'] = topic
            st.session_state['current_keywords'] = keywords
            st.session_state['current_questions'] = questions
            logging.info("Research data stored in session state")
        except Exception as e:
            logging.error(f"Error storing research data: {e}")
            st.session_state['error_message'] = f"Failed to store research data: {str(e)}"

    @staticmethod
    def store_file_data(file_type: str, file_path: str, file_bytes: bytes) -> None:
        """
        Store generated file data in session state to prevent loss on refresh.
        
        Args:
            file_type: Type of file ('pdf', 'pptx', 'docx')
            file_path: Path to the generated file
            file_bytes: Binary content of the file
        """
        try:
            if file_type == 'pdf':
                st.session_state['pdf_path'] = file_path
                st.session_state['pdf_bytes'] = file_bytes
                st.session_state['pdf_generated'] = True
                logging.info("PDF data stored in session state")
            elif file_type == 'pptx':
                st.session_state['pptx_path'] = file_path
                st.session_state['pptx_bytes'] = file_bytes
                st.session_state['pptx_generated'] = True
                logging.info("PPTX data stored in session state")
            elif file_type == 'docx':
                st.session_state['docx_path'] = file_path
                st.session_state['docx_bytes'] = file_bytes
                st.session_state['docx_generated'] = True
                logging.info("DOCX data stored in session state")
            else:
                logging.warning(f"Unknown file type: {file_type}")
        except Exception as e:
            logging.error(f"Error storing {file_type} file data: {e}")
            st.session_state['error_message'] = f"Failed to store {file_type} data: {str(e)}"

    @staticmethod
    def get_file_bytes(file_type: str) -> Optional[bytes]:
        """
        Retrieve file bytes from session state.
        
        Args:
            file_type: Type of file ('pdf', 'pptx', 'docx')
            
        Returns:
            File bytes or None
        """
        try:
            if file_type == 'pdf':
                return st.session_state.get('pdf_bytes')
            elif file_type == 'pptx':
                return st.session_state.get('pptx_bytes')
            elif file_type == 'docx':
                return st.session_state.get('docx_bytes')
            else:
                logging.warning(f"Unknown file type: {file_type}")
                return None
        except Exception as e:
            logging.error(f"Error retrieving {file_type} bytes: {e}")
            return None

    @staticmethod
    def is_file_generated(file_type: str) -> bool:
        """
        Check if a file has been generated.
        
        Args:
            file_type: Type of file ('pdf', 'pptx', 'docx')
            
        Returns:
            True if file is generated, False otherwise
        """
        try:
            if file_type == 'pdf':
                return st.session_state.get('pdf_generated', False)
            elif file_type == 'pptx':
                return st.session_state.get('pptx_generated', False)
            elif file_type == 'docx':
                return st.session_state.get('docx_generated', False)
            else:
                return False
        except Exception as e:
            logging.error(f"Error checking {file_type} generation status: {e}")
            return False

    @staticmethod
    def clear_research_data() -> None:
        """Clear all research-related data from session state."""
        try:
            st.session_state['research_generated'] = False
            st.session_state['research_sections'] = None
            st.session_state['pdf_generated'] = False
            st.session_state['pdf_path'] = None
            st.session_state['pdf_bytes'] = None
            st.session_state['pptx_generated'] = False
            st.session_state['pptx_path'] = None
            st.session_state['pptx_bytes'] = None
            st.session_state['docx_generated'] = False
            st.session_state['docx_path'] = None
            st.session_state['docx_bytes'] = None
            st.session_state['error_message'] = None
            logging.info("Cleared all research data from session state")
        except Exception as e:
            logging.error(f"Error clearing research data: {e}")

    @staticmethod
    def clear_error() -> None:
        """Clear error message from session state."""
        try:
            st.session_state['error_message'] = None
        except Exception as e:
            logging.error(f"Error clearing error message: {e}")

    @staticmethod
    def set_generation_in_progress(in_progress: bool) -> None:
        """
        Set generation in progress flag.
        
        Args:
            in_progress: True if generation is in progress
        """
        try:
            st.session_state['generation_in_progress'] = in_progress
            logging.debug(f"Generation in progress: {in_progress}")
        except Exception as e:
            logging.error(f"Error setting generation progress flag: {e}")

    @staticmethod
    def is_generation_in_progress() -> bool:
        """
        Check if generation is currently in progress.
        
        Returns:
            True if generation is in progress
        """
        return st.session_state.get('generation_in_progress', False)

    @staticmethod
    def store_notes(notes_content: str) -> None:
        """
        Store notes content in session state.
        
        Args:
            notes_content: Notes content to store
        """
        try:
            st.session_state['notes_content'] = notes_content
            logging.debug("Notes content stored in session state")
        except Exception as e:
            logging.error(f"Error storing notes: {e}")

    @staticmethod
    def get_notes() -> str:
        """
        Get notes content from session state.
        
        Returns:
            Notes content or empty string
        """
        return st.session_state.get('notes_content', '')

    @staticmethod
    def debug_session_state() -> dict:
        """
        Get current session state for debugging.
        
        Returns:
            Dictionary of current session state (sanitized)
        """
        try:
            state_info = {}
            for key in st.session_state:
                value = st.session_state[key]
                # Don't include large binary data in debug output
                if key.endswith('_bytes'):
                    state_info[key] = f"<bytes: {len(value)} bytes>" if value else None
                else:
                    state_info[key] = value
            return state_info
        except Exception as e:
            logging.error(f"Error getting debug session state: {e}")
            return {'error': str(e)}
