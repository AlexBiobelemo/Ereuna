"""
Hierarchical Research Generator Module

This module implements hierarchical generation for large research documents (up to 2000+ pages).
It uses a phased approach:
1. Generate master outline
2. Group into volumes (10 subsections per volume)
3. Generate each volume independently
4. Combine into modular documents

Author: Ereuna Development Team
"""

import streamlit as st
import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import os

from utils.research_generator import ResearchGenerator
from utils.config_manager import ConfigManager
from utils.prompt_manager import PromptManager
from utils.llm_call_utils import make_llm_call_with_retry
from utils.llm_client_manager import LLMClientManager
from utils.exceptions import (
    EreunaError,
    APITimeoutError,
    APIRateLimitError,
    LLMGenerationError
)

logger = logging.getLogger(__name__)


@dataclass
class OutlineSection:
    """Represents a section in the master outline."""
    title: str
    description: str
    subsections: List[str] = field(default_factory=list)
    word_count_estimate: int = 1000
    priority: int = 1
    keywords: List[str] = field(default_factory=list)


@dataclass
class VolumePlan:
    """Represents a volume plan containing multiple sections."""
    volume_number: int
    volume_title: str
    sections: List[OutlineSection]
    total_estimated_words: int = 0
    total_estimated_pages: int = 0
    
    def __post_init__(self):
        self.total_estimated_words = sum(s.word_count_estimate for s in self.sections)
        self.total_estimated_pages = self.total_estimated_words // 250  # ~250 words per page


@dataclass
class CheckpointData:
    """Checkpoint data for resume capability."""
    timestamp: str
    phase: str  # 'outline', 'volumes', 'export'
    topic: str
    master_outline: List[Dict] = field(default_factory=list)
    volume_plans: List[Dict] = field(default_factory=list)
    completed_volumes: List[int] = field(default_factory=list)
    volume_contents: Dict[int, Dict[str, str]] = field(default_factory=dict)
    last_updated: str = field(default_factory=str)


class CheckpointManager:
    """Manages checkpoints for long-running research generation."""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        self._ensure_checkpoint_dir()
    
    def _ensure_checkpoint_dir(self):
        """Create checkpoint directory if it doesn't exist."""
        import os
        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir, exist_ok=True)
            logger.info(f"Created checkpoint directory: {self.checkpoint_dir}")
    
    def _get_checkpoint_path(self, topic: str) -> str:
        """Generate checkpoint filename from topic."""
        topic_hash = hashlib.md5(topic.lower().encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.checkpoint_dir, f"checkpoint_{topic_hash}_{timestamp}.json")
    
    def save_checkpoint(self, checkpoint: CheckpointData) -> str:
        """Save checkpoint data to file."""
        path = self._get_checkpoint_path(checkpoint.topic)
        checkpoint_data = {
            "timestamp": checkpoint.timestamp,
            "phase": checkpoint.phase,
            "topic": checkpoint.topic,
            "master_outline": [
                {
                    "title": s.title,
                    "description": s.description,
                    "subsections": s.subsections,
                    "word_count_estimate": s.word_count_estimate,
                    "priority": s.priority,
                    "keywords": s.keywords
                }
                for s in checkpoint.master_outline
            ],
            "volume_plans": [
                {
                    "volume_number": v.volume_number,
                    "volume_title": v.volume_title,
                    "sections": [
                        {
                            "title": s.title,
                            "description": s.description,
                            "subsections": s.subsections,
                            "word_count_estimate": s.word_count_estimate,
                            "priority": s.priority,
                            "keywords": s.keywords
                        }
                        for s in v.sections
                    ],
                    "total_estimated_words": v.total_estimated_words,
                    "total_estimated_pages": v.total_estimated_pages
                }
                for v in checkpoint.volume_plans
            ],
            "completed_volumes": checkpoint.completed_volumes,
            "volume_contents": checkpoint.volume_contents,
            "last_updated": checkpoint.last_updated
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved checkpoint to: {path}")
        return path
    
    def load_checkpoint(self, topic: str) -> Optional[CheckpointData]:
        """Load checkpoint data for a topic."""
        import glob
        
        # Find checkpoints for this topic
        topic_hash = hashlib.md5(topic.lower().encode()).hexdigest()[:12]
        pattern = os.path.join(self.checkpoint_dir, f"checkpoint_{topic_hash}_*.json")
        checkpoints = glob.glob(pattern)
        
        if not checkpoints:
            return None
        
        # Load most recent checkpoint
        latest_checkpoint = max(checkpoints, key=os.path.getctime)
        
        with open(latest_checkpoint, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruct objects
        master_outline = [
            OutlineSection(
                title=s["title"],
                description=s["description"],
                subsections=s.get("subsections", []),
                word_count_estimate=s.get("word_count_estimate", 1000),
                priority=s.get("priority", 1),
                keywords=s.get("keywords", [])
            )
            for s in data.get("master_outline", [])
        ]
        
        volume_plans = [
            VolumePlan(
                volume_number=v["volume_number"],
                volume_title=v["volume_title"],
                sections=[
                    OutlineSection(
                        title=s["title"],
                        description=s["description"],
                        subsections=s.get("subsections", []),
                        word_count_estimate=s.get("word_count_estimate", 1000),
                        priority=s.get("priority", 1),
                        keywords=s.get("keywords", [])
                    )
                    for s in v["sections"]
                ],
                total_estimated_words=v.get("total_estimated_words", 0),
                total_estimated_pages=v.get("total_estimated_pages", 0)
            )
            for v in data.get("volume_plans", [])
        ]
        
        return CheckpointData(
            timestamp=data.get("timestamp", ""),
            phase=data.get("phase", "outline"),
            topic=data.get("topic", topic),
            master_outline=master_outline,
            volume_plans=volume_plans,
            completed_volumes=data.get("completed_volumes", []),
            volume_contents=data.get("volume_contents", {}),
            last_updated=data.get("last_updated", "")
        )
    
    def get_latest_checkpoint_path(self, topic: str) -> Optional[str]:
        """Get path to latest checkpoint for a topic."""
        checkpoint = self.load_checkpoint(topic)
        if checkpoint:
            topic_hash = hashlib.md5(topic.lower().encode()).hexdigest()[:12]
            pattern = os.path.join(self.checkpoint_dir, f"checkpoint_{topic_hash}_*.json")
            checkpoints = glob.glob(pattern)
            if checkpoints:
                return max(checkpoints, key=os.path.getctime)
        return None


class HierarchicalGenerator:
    """
    Hierarchical Research Generator for large documents.
    
    This class handles the generation of research documents with 2000+ pages
    using a hierarchical approach:
    1. Generate master outline with all sections
    2. Group sections into volumes (10 sections per volume)
    3. Generate each volume independently
    4. Combine into modular documents
    """
    
    # Constants for configuration
    DEFAULT_SECTIONS_PER_VOLUME = 10
    DEFAULT_PAGES_PER_SECTION = 10
    DEFAULT_WORDS_PER_PAGE = 250
    CHECKPOINT_INTERVAL = 5  # Save checkpoint every N volumes
    
    def __init__(
        self,
        topic: str,
        keywords: List[str],
        research_questions: List[str],
        config_manager: ConfigManager,
        prompt_manager: PromptManager,
        model_name: str = 'gemini-2.5-flash',
        max_retries: int = 7,
        timeout: int = 120,
        spinner_update_callback=None,
        checkpoint_manager: Optional[CheckpointManager] = None,
        sections_per_volume: int = DEFAULT_SECTIONS_PER_VOLUME
    ):
        """
        Initialize HierarchicalGenerator.
        
        Args:
            topic: Research topic
            keywords: Keywords for research
            research_questions: Research questions
            config_manager: ConfigManager instance
            prompt_manager: PromptManager instance
            model_name: LLM model to use
            max_retries: Maximum retry attempts for API calls
            timeout: Timeout for API calls in seconds
            spinner_update_callback: Callback for UI updates
            checkpoint_manager: CheckpointManager instance (creates new if None)
            sections_per_volume: Number of sections per volume (default: 10)
        """
        self.topic = topic
        self.keywords = keywords
        self.research_questions = research_questions
        self.config_manager = config_manager
        self.prompt_manager = prompt_manager
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout = timeout
        self.spinner_update_callback = spinner_update_callback
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.sections_per_volume = sections_per_volume
        
        # Initialize LLM client
        self.llm_client_manager = LLMClientManager(
            self.config_manager.get_api_keys(),
            self.spinner_update_callback
        )
        
        # System prompt
        self.system_prompt = "You are an expert research assistant specializing in comprehensive academic research generation."
        
        # State tracking
        self.checkpoint: Optional[CheckpointData] = None
        self.is_cancelled = False
    
    def _update_spinner(self, message: str):
        """Update spinner with message."""
        if self.spinner_update_callback:
            self.spinner_update_callback(message)
        logger.info(message)
    
    def _make_api_call(self, prompt: str, call_type: str) -> str:
        """Make LLM API call with retry logic."""
        return make_llm_call_with_retry(
            llm_client_manager=self.llm_client_manager,
            model_name=self.model_name,
            prompt=prompt,
            system_prompt=self.system_prompt,
            max_retries=self.max_retries,
            timeout=self.timeout,
            call_type=call_type
        )
    
    def generate_master_outline(self, num_sections: int = 20) -> List[OutlineSection]:
        """
        Generate master outline with all sections for the research topic.
        
        Args:
            num_sections: Number of main sections to generate (default: 20)
            
        Returns:
            List of OutlineSection objects
        """
        self._update_spinner("Generating master research outline...")
        
        # Create prompt for outline generation
        prompt = f"""
Generate a comprehensive research outline for the topic: "{self.topic}"

Requirements:
1. Create exactly {num_sections} main sections
2. Each section should have 5-10 subsections
3. Include detailed descriptions for each section
4. Consider keywords: {', '.join(self.keywords)}
5. Address research questions: {', '.join(self.research_questions)}

Output format (JSON):
{{
    "sections": [
        {{
            "title": "Section Title",
            "description": "Brief description of what this section covers",
            "subsections": ["Subsection 1", "Subsection 2", ...],
            "word_count_estimate": 1000,
            "priority": 1-5,
            "keywords": ["keyword1", "keyword2", ...]
        }}
    ]
}}
"""
        
        try:
            response = self._make_api_call(prompt, "Master Outline Generation")
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            outline_data = json.loads(response)
            sections = []
            
            for s in outline_data.get("sections", []):
                section = OutlineSection(
                    title=s.get("title", "Untitled Section"),
                    description=s.get("description", ""),
                    subsections=s.get("subsections", []),
                    word_count_estimate=s.get("word_count_estimate", 1000),
                    priority=s.get("priority", 1),
                    keywords=s.get("keywords", [])
                )
                sections.append(section)
            
            self._update_spinner(f"✅ Master outline generated with {len(sections)} sections")
            return sections
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse outline JSON: {e}")
            raise LLMGenerationError(f"Failed to parse outline: {e}")
        except Exception as e:
            logger.error(f"Error generating master outline: {e}")
            raise
    
    def create_volume_plans(self, outline: List[OutlineSection]) -> List[VolumePlan]:
        """
        Group outline sections into volumes.
        
        Args:
            outline: List of outline sections
            
        Returns:
            List of VolumePlan objects
        """
        volumes = []
        
        # Group sections into volumes
        for i in range(0, len(outline), self.sections_per_volume):
            volume_sections = outline[i:i + self.sections_per_volume]
            volume_number = (i // self.sections_per_volume) + 1
            volume_title = f"Volume {volume_number}: {volume_sections[0].title} & Related Topics"
            
            volume = VolumePlan(
                volume_number=volume_number,
                volume_title=volume_title,
                sections=volume_sections
            )
            volumes.append(volume)
        
        self._update_spinner(f"📚 Created {len(volumes)} volume plans")
        return volumes
    
    def generate_volume_content(
        self,
        volume: VolumePlan,
        previous_volumes_content: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate content for a single volume.
        
        Args:
            volume: VolumePlan to generate
            previous_volumes_content: Content from previous volumes for context
            
        Returns:
            Dictionary of section titles to content
        """
        self._update_spinner(f"📖 Generating Volume {volume.volume_number}: {volume.volume_title}")
        
        volume_content = {}
        previous_section_content = ""
        
        for idx, section in enumerate(volume.sections):
            section_title = section.title
            
            # Create context-aware prompt
            context = f"""
Previous sections context:
{previous_volumes_content if previous_volumes_content else ''}

Previous section in this volume:
{previous_section_content}

---

Section to generate: {section_title}
Description: {section.description}
Subsections to include:
{chr(10).join(f'- {s}' for s in section.subsections)}

Keywords: {', '.join(section.keywords)}
Research questions: {', '.join(self.research_questions)}

Generate comprehensive content for this section (approx. {section.word_count_estimate} words).
Include all subsections with detailed analysis.
"""
            
            try:
                content = self._make_api_call(
                    f"{context}\n\nWrite the content in markdown format.",
                    f"Volume {volume.volume_number} - {section_title}"
                )
                
                volume_content[section_title] = content
                previous_section_content = f"## {section_title}\n{content}"
                
                self._update_spinner(
                    f"✅ Volume {volume.volume_number}, Section {idx + 1}/{len(volume.sections)}: {section_title}"
                )
                
            except Exception as e:
                logger.error(f"Error generating section {section_title}: {e}")
                volume_content[section_title] = f"Error: Failed to generate content - {str(e)}"
        
        return volume_content
    
    async def generate_async(
        self,
        num_sections: int = 20,
        use_checkpoint: bool = True,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Asynchronously generate complete research with hierarchical approach.
        
        Args:
            num_sections: Number of main sections
            use_checkpoint: Whether to use checkpoint resume
            progress_callback: Callback for progress updates
            
        Returns:
            Dictionary with all generated content and metadata
        """
        self._update_spinner("🚀 Starting hierarchical research generation...")
        
        # Check for existing checkpoint
        if use_checkpoint:
            self.checkpoint = self.checkpoint_manager.load_checkpoint(self.topic)
            if self.checkpoint:
                self._update_spinner(f"📂 Found existing checkpoint from {self.checkpoint.timestamp}")
        
        # Initialize checkpoint if needed
        if not self.checkpoint:
            self.checkpoint = CheckpointData(
                timestamp=datetime.now().isoformat(),
                phase="outline",
                topic=self.topic,
                master_outline=[],
                volume_plans=[],
                completed_volumes=[],
                volume_contents={}
            )
        
        # Phase 1: Generate master outline
        if not self.checkpoint.master_outline:
            self.checkpoint.master_outline = self.generate_master_outline(num_sections)
            self.checkpoint.phase = "volumes"
            self._save_checkpoint()
        
        # Phase 2: Create volume plans
        if not self.checkpoint.volume_plans:
            self.checkpoint.volume_plans = self.create_volume_plans(self.checkpoint.master_outline)
            self._save_checkpoint()
        
        # Phase 3: Generate volumes
        previous_content = ""
        
        for volume in self.checkpoint.volume_plans:
            if volume.volume_number in self.checkpoint.completed_volumes:
                self._update_spinner(f"⏭️ Skipping Volume {volume.volume_number} (already completed)")
                # Accumulate content from completed volumes
                vol_content = self.checkpoint.volume_contents.get(volume.volume_number, {})
                previous_content += "\n\n" + "\n\n".join([
                    f"## {title}\n{content}"
                    for title, content in vol_content.items()
                ])
                continue
            
            # Generate volume content
            volume_content = self.generate_volume_content(volume, previous_content)
            
            # Store in checkpoint
            self.checkpoint.volume_contents[volume.volume_number] = volume_content
            self.checkpoint.completed_volumes.append(volume.volume_number)
            
            # Accumulate for context
            previous_content += "\n\n" + "\n\n".join([
                f"## {title}\n{content}"
                for title, content in volume_content.items()
            ])
            
            # Save checkpoint
            self._save_checkpoint()
            
            # Progress callback
            if progress_callback:
                progress_callback({
                    "current_volume": volume.volume_number,
                    "total_volumes": len(self.checkpoint.volume_plans),
                    "completed_volumes": len(self.checkpoint.completed_volumes),
                    "volume_title": volume.volume_title
                })
        
        self.checkpoint.phase = "completed"
        self.checkpoint.last_updated = datetime.now().isoformat()
        self._save_checkpoint()
        
        self._update_spinner("✅ Hierarchical research generation completed!")
        
        return {
            "topic": self.topic,
            "outline": self._sections_to_dict(self.checkpoint.master_outline),
            "volumes": self._volumes_to_dict(self.checkpoint.volume_plans),
            "volume_contents": self.checkpoint.volume_contents,
            "total_volumes": len(self.checkpoint.volume_plans),
            "total_pages": sum(
                v.total_estimated_pages for v in self.checkpoint.volume_plans
            )
        }
    
    def generate(
        self,
        num_sections: int = 20,
        use_checkpoint: bool = True,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for async generation.
        
        Args:
            num_sections: Number of main sections
            use_checkpoint: Whether to use checkpoint resume
            progress_callback: Callback for progress updates
            
        Returns:
            Dictionary with all generated content and metadata
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_async(
                num_sections=num_sections,
                use_checkpoint=use_checkpoint,
                progress_callback=progress_callback
            )
        )
    
    def _save_checkpoint(self):
        """Save current checkpoint."""
        self.checkpoint.last_updated = datetime.now().isoformat()
        self.checkpoint_manager.save_checkpoint(self.checkpoint)
    
    def _sections_to_dict(self, sections: List[OutlineSection]) -> List[Dict]:
        """Convert sections to dictionary."""
        return [
            {
                "title": s.title,
                "description": s.description,
                "subsections": s.subsections,
                "word_count_estimate": s.word_count_estimate,
                "priority": s.priority,
                "keywords": s.keywords
            }
            for s in sections
        ]
    
    def _volumes_to_dict(self, volumes: List[VolumePlan]) -> List[Dict]:
        """Convert volumes to dictionary."""
        return [
            {
                "volume_number": v.volume_number,
                "volume_title": v.volume_title,
                "sections": self._sections_to_dict(v.sections),
                "total_estimated_words": v.total_estimated_words,
                "total_estimated_pages": v.total_estimated_pages
            }
            for v in volumes
        ]
    
    def cancel_generation(self):
        """Cancel the current generation process."""
        self.is_cancelled = True
        self._update_spinner("🛑 Generation cancelled by user")
    
    def clear_checkpoint(self):
        """Clear checkpoint for current topic."""
        self.checkpoint = None
        self._update_spinner("🗑️ Checkpoint cleared")


# Convenience function for quick initialization
def create_hierarchical_generator(
    topic: str,
    keywords: List[str],
    research_questions: List[str],
    config_manager: ConfigManager,
    prompt_manager: PromptManager,
    model_name: str = 'gemini-2.5-flash',
    sections_per_volume: int = 10,
    spinner_update_callback=None
) -> HierarchicalGenerator:
    """
    Create and return a HierarchicalGenerator instance.
    
    Args:
        topic: Research topic
        keywords: Keywords for research
        research_questions: Research questions
        config_manager: ConfigManager instance
        prompt_manager: PromptManager instance
        model_name: LLM model to use
        sections_per_volume: Number of sections per volume
        spinner_update_callback: UI callback
        
    Returns:
        Configured HierarchicalGenerator instance
    """
    return HierarchicalGenerator(
        topic=topic,
        keywords=keywords,
        research_questions=research_questions,
        config_manager=config_manager,
        prompt_manager=prompt_manager,
        model_name=model_name,
        spinner_update_callback=spinner_update_callback,
        sections_per_volume=sections_per_volume
    )
