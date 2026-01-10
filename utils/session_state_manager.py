import streamlit as st
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

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
            'generation_in_progress': False,
            'gemini_api_key': '',
            'openai_api_key': '',
            'anthropic_api_key': '',
            'selected_model_name': 'gemini-1.5-flash', # Default model
            'executive_summary': None,
            'academic_sources': None,
            'scraped_content_0': None, # For scraped content from first source
            'scraped_content_1': None, # For scraped content from second source
            'scraped_content_2': None, # For scraped content from third source
            'scraped_content_3': None, # For scraped content from fourth source
            'scraped_content_4': None, # For scraped content from fifth source
            'bibliography': None,
            'readability_scores': None,
            'keyword_analysis': None,
            'plagiarism_result': None,
            'fact_check_results': None,
            # Hierarchical Generation State
            'hierarchical_generation_enabled': False,
            'hierarchical_generated': False,
            'master_outline': None,
            'volume_plans': None,
            'volume_contents': None,
            'completed_volumes': None,
            'total_volumes': 0,
            'current_volume': 0,
            'hierarchical_progress': None,
            # Modular Export State
            'modular_exports': None,
            'master_doc_path': None,
            'export_manifest': None,
            # Checkpoint State
            'checkpoint_available': False,
            'checkpoint_path': None,
            'checkpoint_timestamp': None,
            # Large Document Settings
            'sections_per_volume': 10,
            'total_target_sections': 20,
            'enable_checkpoint_resume': True
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                logger.debug(f"Initialized session state: {key} = {default_value}")

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
            logger.debug(f"Set session state: {key}")
        except Exception as e:
            logger.error(f"Error setting session state '{key}': {e}")

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
            logger.error(f"Error getting session state '{key}': {e}")
            return default

    @staticmethod
    def store_research_data(sections: dict, topic: str, keywords: str, questions: str, model_name: str) -> None:
        """
        Store research generation data in session state.
        
        Args:
            sections: Generated research sections
            topic: Research topic
            keywords: Research keywords
            questions: Research questions
            model_name: The AI model used for generation
        """
        try:
            st.session_state['research_sections'] = sections
            st.session_state['research_generated'] = True
            st.session_state['current_topic'] = topic
            st.session_state['current_keywords'] = keywords
            st.session_state['current_questions'] = questions
            st.session_state['selected_model_name'] = model_name
            logger.info("Research data stored in session state")
        except Exception as e:
            logger.error(f"Error storing research data: {e}")
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
                logger.info("PDF data stored in session state")
            elif file_type == 'pptx':
                st.session_state['pptx_path'] = file_path
                st.session_state['pptx_bytes'] = file_bytes
                st.session_state['pptx_generated'] = True
                logger.info("PPTX data stored in session state")
            elif file_type == 'docx':
                st.session_state['docx_path'] = file_path
                st.session_state['docx_bytes'] = file_bytes
                st.session_state['docx_generated'] = True
                logger.info("DOCX data stored in session state")
            else:
                logger.warning(f"Unknown file type: {file_type}")
        except Exception as e:
            logger.error(f"Error storing {file_type} file data: {e}")
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
                logger.warning(f"Unknown file type: {file_type}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving {file_type} bytes: {e}")
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
            logger.error(f"Error checking {file_type} generation status: {e}")
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
            logger.info("Cleared all research data from session state")
        except Exception as e:
            logger.error(f"Error clearing research data: {e}")

    @staticmethod
    def clear_error() -> None:
        """Clear error message from session state."""
        try:
            st.session_state['error_message'] = None
        except Exception as e:
            logger.error(f"Error clearing error message: {e}")

    @staticmethod
    def set_generation_in_progress(in_progress: bool) -> None:
        """
        Set generation in progress flag.
        
        Args:
            in_progress: True if generation is in progress
        """
        try:
            st.session_state['generation_in_progress'] = in_progress
            logger.debug(f"Generation in progress: {in_progress}")
        except Exception as e:
            logger.error(f"Error setting generation progress flag: {e}")

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
            logger.debug("Notes content stored in session state")
        except Exception as e:
            logger.error(f"Error storing notes: {e}")

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
            logger.error(f"Error getting debug session state: {e}")
            return {'error': str(e)}
    
    # ==================== Hierarchical Generation State ====================
    
    @staticmethod
    def set_hierarchical_generation_enabled(enabled: bool) -> None:
        """Enable or disable hierarchical generation mode."""
        try:
            st.session_state['hierarchical_generation_enabled'] = enabled
            logger.debug(f"Hierarchical generation enabled: {enabled}")
        except Exception as e:
            logger.error(f"Error setting hierarchical generation flag: {e}")
    
    @staticmethod
    def is_hierarchical_generation_enabled() -> bool:
        """Check if hierarchical generation is enabled."""
        return st.session_state.get('hierarchical_generation_enabled', False)
    
    @staticmethod
    def store_hierarchical_data(
        self,
        master_outline: list,
        volume_plans: list,
        volume_contents: dict,
        completed_volumes: list,
        total_volumes: int
    ) -> None:
        """
        Store hierarchical generation data in session state.
        
        Args:
            master_outline: Generated master outline
            volume_plans: Volume plans
            volume_contents: Dictionary mapping volume numbers to section content
            completed_volumes: List of completed volume numbers
            total_volumes: Total number of volumes
        """
        try:
            st.session_state['master_outline'] = master_outline
            st.session_state['volume_plans'] = volume_plans
            st.session_state['volume_contents'] = volume_contents
            st.session_state['completed_volumes'] = completed_volumes
            st.session_state['total_volumes'] = total_volumes
            st.session_state['hierarchical_generated'] = True
            logger.info("Hierarchical generation data stored in session state")
        except Exception as e:
            logger.error(f"Error storing hierarchical data: {e}")
            st.session_state['error_message'] = f"Failed to store hierarchical data: {str(e)}"
    
    @staticmethod
    def update_hierarchical_progress(current_volume: int, total_volumes: int, volume_title: str) -> None:
        """
        Update hierarchical generation progress.
        
        Args:
            current_volume: Current volume being generated
            total_volumes: Total number of volumes
            volume_title: Title of current volume
        """
        try:
            st.session_state['current_volume'] = current_volume
            st.session_state['hierarchical_progress'] = {
                'current_volume': current_volume,
                'total_volumes': total_volumes,
                'volume_title': volume_title,
                'progress_pct': round((current_volume / total_volumes) * 100, 1)
            }
            logger.debug(f"Updated hierarchical progress: Volume {current_volume}/{total_volumes}")
        except Exception as e:
            logger.error(f"Error updating hierarchical progress: {e}")
    
    @staticmethod
    def get_hierarchical_progress() -> Optional[dict]:
        """
        Get current hierarchical generation progress.
        
        Returns:
            Progress dictionary or None
        """
        return st.session_state.get('hierarchical_progress')
    
    @staticmethod
    def is_hierarchical_generation_complete() -> bool:
        """
        Check if hierarchical generation is complete.
        
        Returns:
            True if all volumes are completed
        """
        completed = st.session_state.get('completed_volumes', []) or []
        total = st.session_state.get('total_volumes', 0)
        return len(completed) >= total and total > 0
    
    @staticmethod
    def get_volume_contents() -> dict:
        """
        Get all generated volume contents.
        
        Returns:
            Dictionary mapping volume numbers to section content
        """
        return st.session_state.get('volume_contents', {})
    
    @staticmethod
    def get_master_outline() -> list:
        """
        Get the master outline.
        
        Returns:
            Master outline list
        """
        return st.session_state.get('master_outline', [])
    
    @staticmethod
    def get_volume_plans() -> list:
        """
        Get the volume plans.
        
        Returns:
            Volume plans list
        """
        return st.session_state.get('volume_plans', [])
    
    @staticmethod
    def clear_hierarchical_data() -> None:
        """
        Clear all hierarchical generation data from session state.
        """
        try:
            st.session_state['hierarchical_generated'] = False
            st.session_state['master_outline'] = None
            st.session_state['volume_plans'] = None
            st.session_state['volume_contents'] = None
            st.session_state['completed_volumes'] = None
            st.session_state['current_volume'] = 0
            st.session_state['hierarchical_progress'] = None
            logger.info("Cleared all hierarchical generation data from session state")
        except Exception as e:
            logger.error(f"Error clearing hierarchical data: {e}")
    
    # ==================== Modular Export State ====================
    
    @staticmethod
    def store_modular_exports(export_manifest: dict, master_doc_path: str = None) -> None:
        """
        Store modular export data in session state.
        
        Args:
            export_manifest: Export manifest dictionary
            master_doc_path: Path to master document
        """
        try:
            st.session_state['export_manifest'] = export_manifest
            st.session_state['master_doc_path'] = master_doc_path
            logger.info("Modular export data stored in session state")
        except Exception as e:
            logger.error(f"Error storing modular export data: {e}")
    
    @staticmethod
    def get_export_manifest() -> Optional[dict]:
        """
        Get the export manifest.
        
        Returns:
            Export manifest dictionary or None
        """
        return st.session_state.get('export_manifest')
    
    @staticmethod
    def get_master_doc_path() -> Optional[str]:
        """
        Get the master document path.
        
        Returns:
            Path to master document or None
        """
        return st.session_state.get('master_doc_path')
    
    # ==================== Checkpoint State ====================
    
    @staticmethod
    def set_checkpoint_available(available: bool, path: str = None, timestamp: str = None) -> None:
        """
        Set checkpoint availability status.
        
        Args:
            available: Whether checkpoint is available
            path: Path to checkpoint file
            timestamp: Checkpoint timestamp
        """
        try:
            st.session_state['checkpoint_available'] = available
            if path:
                st.session_state['checkpoint_path'] = path
            if timestamp:
                st.session_state['checkpoint_timestamp'] = timestamp
            logger.debug(f"Checkpoint available: {available}")
        except Exception as e:
            logger.error(f"Error setting checkpoint status: {e}")
    
    @staticmethod
    def is_checkpoint_available() -> bool:
        """
        Check if a checkpoint is available for the current topic.
        
        Returns:
            True if checkpoint is available
        """
        return st.session_state.get('checkpoint_available', False)
    
    # ==================== Large Document Settings ====================
    
    @staticmethod
    def set_large_document_settings(
        sections_per_volume: int = 10,
        total_target_sections: int = 20,
        enable_checkpoint_resume: bool = True
    ) -> None:
        """
        Configure large document generation settings.
        
        Args:
            sections_per_volume: Number of sections per volume
            total_target_sections: Total sections to generate
            enable_checkpoint_resume: Whether to enable checkpoint resume
        """
        try:
            st.session_state['sections_per_volume'] = sections_per_volume
            st.session_state['total_target_sections'] = total_target_sections
            st.session_state['enable_checkpoint_resume'] = enable_checkpoint_resume
            logger.info(f"Large document settings updated: {sections_per_volume} sections/volume, {total_target_sections} total sections")
        except Exception as e:
            logger.error(f"Error setting large document settings: {e}")
    
    @staticmethod
    def get_sections_per_volume() -> int:
        """
        Get the number of sections per volume.
        
        Returns:
            Sections per volume
        """
        return st.session_state.get('sections_per_volume', 10)
    
    @staticmethod
    def get_total_target_sections() -> int:
        """
        Get the total target sections.
        
        Returns:
            Total target sections
        """
        return st.session_state.get('total_target_sections', 20)
    
    @staticmethod
    def is_checkpoint_resume_enabled() -> bool:
        """
        Check if checkpoint resume is enabled.
        
        Returns:
            True if checkpoint resume is enabled
        """
        return st.session_state.get('enable_checkpoint_resume', True)
