"""
Citation Manager - Handles citation generation and management for research content.
Supports APA, MLA, Chicago, and Harvard citation formats.
"""
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Represents a single citation with all its components."""
    title: str
    authors: List[str]
    publication_date: str
    publisher: str
    url: str
    accessed_date: str = ""
    doi: str = ""
    citation_type: str = "webpage"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert citation to dictionary."""
        return {
            "title": self.title,
            "authors": ", ".join(self.authors) if self.authors else "",
            "publication_date": self.publication_date,
            "publisher": self.publisher,
            "url": self.url,
            "accessed_date": self.accessed_date,
            "doi": self.doi,
            "type": self.citation_type
        }


class CitationManager:
    """
    Manages citation generation and formatting for research content.
    Supports APA, MLA, Chicago, and Harvard citation styles.
    """
    
    def __init__(self):
        self.citations: List[Citation] = []
        self.citation_styles = ["apa", "mla", "chicago", "harvard"]
    
    def add_citation(self, citation: Citation):
        """Add a citation to the manager."""
        self.citations.append(citation)
        logger.info(f"Added citation: {citation.title[:50]}...")
    
    def add_citation_from_dict(self, data: Dict[str, str]) -> Citation:
        """Create and add a citation from a dictionary."""
        citation = Citation(
            title=data.get("title", "Untitled"),
            authors=data.get("authors", "").split(";") if data.get("authors") else [],
            publication_date=data.get("publication_date", ""),
            publisher=data.get("publisher", ""),
            url=data.get("url", ""),
            accessed_date=data.get("accessed_date", datetime.now().strftime("%Y-%m-%d")),
            doi=data.get("doi", ""),
            citation_type=data.get("type", "webpage")
        )
        self.add_citation(citation)
        return citation
    
    def format_author(self, authors: List[str], style: str = "apa") -> str:
        """Format authors according to citation style."""
        if not authors:
            return ""
        
        if len(authors) == 1:
            return self._format_single_author(authors[0], style)
        elif len(authors) == 2:
            return f"{self._format_single_author(authors[0], style)} & {self._format_single_author(authors[1], style)}"
        elif len(authors) == 3:
            return f"{self._format_single_author(authors[0], style)}, {self._format_single_author(authors[1], style)}, & {self._format_single_author(authors[2], style)}"
        else:
            first_author = self._format_single_author(authors[0], style)
            return f"{first_author} et al."
    
    def _format_single_author(self, author: str, style: str) -> str:
        """Format a single author's name."""
        parts = author.strip().split()
        if not parts:
            return ""
        
        if style == "apa":
            # Last name, F. M.
            if len(parts) > 1:
                return f"{parts[-1]}, {''.join(p[0] + '.' for p in parts[:-1] if p)}".strip()
            return parts[0]
        elif style == "mla":
            # Last name, First name
            if len(parts) > 1:
                return f"{parts[-1]}, {' '.join(parts[:-1])}"
            return parts[0]
        elif style == "chicago":
            # Last name, First name
            if len(parts) > 1:
                return f"{parts[-1], {' '.join(parts[:-1])}}"
            return parts[0]
        else:  # harvard
            # Last name, F. M.
            if len(parts) > 1:
                return f"{parts[-1]}, {''.join(p[0] + '.' for p in parts[:-1] if p)}".strip()
            return parts[0]
    
    def format_date(self, date_str: str, style: str = "apa") -> str:
        """Format date according to citation style."""
        try:
            # Try to parse various date formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%B %d, %Y", "%d %B %Y", "%Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    if style == "apa":
                        return dt.strftime("%Y, %B %d")
                    elif style == "mla":
                        return dt.strftime("%B %d, %Y")
                    elif style == "chicago":
                        return dt.strftime("%B %d, %Y")
                    else:  # harvard
                        return dt.strftime("%d %B %Y")
                except ValueError:
                    continue
            return date_str
        except Exception:
            return date_str
    
    def generate_citation(self, citation: Citation, style: str = "apa") -> str:
        """Generate a formatted citation string."""
        style = style.lower()
        if style not in self.citation_styles:
            logger.warning(f"Unknown citation style: {style}, defaulting to APA")
            style = "apa"
        
        authors = self.format_author(citation.authors, style)
        date = self.format_date(citation.publication_date, style)
        title = citation.title
        publisher = citation.publisher
        url = citation.url
        accessed = citation.accessed_date
        
        if style == "apa":
            # APA 7th edition format
            parts = []
            if authors:
                parts.append(f"{authors} ({citation.publication_date[:4] if citation.publication_date else 'n.d.'})")
            else:
                parts.append(f"(n.d.)")
            parts.append(f"{title}")
            if publisher:
                parts.append(f"{publisher}")
            if url:
                parts.append(f"Retrieved {accessed}, from {url}")
            return ". ".join(parts)
        
        elif style == "mla":
            # MLA 9th edition format
            parts = []
            if authors:
                parts.append(f"{authors}.")
            parts.append(f'"{title}."')
            if publisher:
                parts.append(f"{publisher},")
            parts.append(f"{date}")
            if url:
                parts.append(f"{url}")
            return ", ".join(parts)
        
        elif style == "chicago":
            # Chicago format
            parts = []
            if authors:
                parts.append(f"{authors}.")
            parts.append(f'"{title}."')
            if publisher:
                parts.append(f"{publisher}")
            parts.append(f"{date}")
            if url:
                parts.append(f"{url}")
            return ". ".join(parts)
        
        else:  # harvard
            # Harvard format
            parts = []
            if authors:
                parts.append(f"{authors} ({citation.publication_date[:4] if citation.publication_date else 'n.d.'})")
            else:
                parts.append(f"(n.d.)")
            parts.append(f"'{title}'")
            if publisher:
                parts.append(f"{publisher}")
            if url:
                parts.append(f"available at: {url} (Accessed: {accessed})")
            return ". ".join(parts)
    
    def generate_reference_list(self, style: str = "apa") -> str:
        """Generate a complete reference list in the specified style."""
        if not self.citations:
            return ""
        
        # Sort citations alphabetically by first author's last name
        sorted_citations = sorted(self.citations, key=lambda c: c.authors[0].split()[-1] if c.authors else c.title)
        
        reference_list = []
        for citation in sorted_citations:
            ref = self.generate_citation(citation, style)
            reference_list.append(ref)
        
        if style == "apa":
            return "\n\n".join(reference_list)
        else:
            return "\n\n".join(reference_list)
    
    def generate_in_text_citation(self, citation: Citation, style: str = "apa", parentheses: bool = True) -> str:
        """Generate an in-text citation."""
        authors = citation.authors
        if not authors:
            return ""
        
        if style == "apa":
            first_author = authors[0].split()[-1]
            year = citation.publication_date[:4] if citation.publication_date else "n.d."
            if len(authors) == 1:
                result = f"{first_author} ({year})"
            elif len(authors) == 2:
                second_author = authors[1].split()[-1]
                result = f"{first_author} & {second_author} ({year})"
            else:
                result = f"{first_author} et al. ({year})"
        elif style == "mla":
            first_author = authors[0].split()[-1]
            if len(authors) == 1:
                result = f'{first_author}'
            elif len(authors) == 2:
                second_author = authors[1].split()[-1]
                result = f'{first_author} and {second_author}'
            else:
                result = f'{first_author} et al.'
        else:
            # Use APA as fallback for other styles
            first_author = authors[0].split()[-1]
            year = citation.publication_date[:4] if citation.publication_date else "n.d."
            result = f"{first_author} ({year})"
        
        return f"({result})" if parentheses else result
    
    def clear(self):
        """Clear all citations."""
        self.citations.clear()
        logger.info("Cleared all citations")
    
    def get_citation_count(self) -> int:
        """Return the number of citations."""
        return len(self.citations)
    
    def export_citations(self, format: str = "bibtex") -> str:
        """Export citations in specified format (bibtex, json)."""
        if format == "bibtex":
            return self._export_bibtex()
        elif format == "json":
            import json
            return json.dumps([c.to_dict() for c in self.citations], indent=2)
        else:
            logger.warning(f"Unknown export format: {format}")
            return ""
    
    def _export_bibtex(self) -> str:
        """Export citations in BibTeX format."""
        bibtex_entries = []
        for i, citation in enumerate(self.citations):
            key = f"ref{i + 1}"
            entry = f"@misc{{{key},\n"
            if citation.authors:
                authors_str = " and ".join(citation.authors)
                entry += f"  author = {{{authors_str}}},\n"
            if citation.title:
                entry += f"  title = {{{citation.title}}},\n"
            if citation.publication_date:
                entry += f"  year = {{{citation.publication_date[:4]}}},\n"
            if citation.publisher:
                entry += f"  publisher = {{{citation.publisher}}},\n"
            if citation.url:
                entry += f"  url = {{{citation.url}}},\n"
            if citation.doi:
                entry += f"  doi = {{{citation.doi}}},\n"
            entry += "}"
            bibtex_entries.append(entry)
        return "\n\n".join(bibtex_entries)
