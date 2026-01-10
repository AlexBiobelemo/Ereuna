# API Documentation

This document provides detailed API reference for all modules in the Ereuna project.

## Table of Contents

- [Core Classes](#core-classes)
- [Utility Classes](#utility-classes)
- [Data Classes](#data-classes)
- [Exceptions](#exceptions)
- [Module Index](#module-index)

---

## Core Classes

### ResearchGenerator

**File:** [`utils/research_generator.py`](utils/research_generator.py:29)

Main class for generating research report sections.

```python
from utils.research_generator import ResearchGenerator
```

#### Constructor

```python
ResearchGenerator(
    topic: str,
    keywords: List[str],
    research_questions: List[str],
    config_manager: ConfigManager,
    prompt_manager: PromptManager,
    deep_research_enabled: bool = False,
    model_name: str = 'gemini-2.5-flash',
    max_retries: int = 7,
    timeout: int = 60,
    spinner_update_callback=None
)
```

| Parameter               | Type          | Default            | Description                 |
| ----------------------- | ------------- | ------------------ | --------------------------- |
| topic                   | str           | Required           | Research topic              |
| keywords                | List[str]     | Required           | Keywords for research focus |
| research_questions      | List[str]     | Required           | Questions to address        |
| config_manager          | ConfigManager | Required           | API configuration           |
| prompt_manager          | PromptManager | Required           | Prompt templates            |
| deep_research_enabled   | bool          | False              | Enable extended research    |
| model_name              | str           | 'gemini-2.5-flash' | LLM model to use            |
| max_retries             | int           | 7                  | Retry attempts on failure   |
| timeout                 | int           | 60                 | API timeout in seconds      |
| spinner_update_callback | callable      | None               | UI progress callback        |

#### Methods

##### generate_section()

```python
def generate_section(
    self,
    section_data: Union[str, Dict],
    previous_sections_content: Optional[str] = None,
    spinner_update_callback=None
) -> str
```

Generate a single section of the research report.

**Parameters:**

- `section_data` (str | dict): Section title or dict with 'title', 'prompt', 'word_count'
- `previous_sections_content` (str, optional): Content from previous sections for context

**Returns:** Generated section content or error message

**Example:**

```python
section = generator.generate_section(
    section_data={
        "title": "Introduction",
        "prompt": "Introduce the research topic",
        "word_count": 500
    },
    previous_sections_content=""
)
```

##### generate_summary()

```python
def generate_summary(self, full_report_content: str) -> str
```

Generate an executive summary of the full report.

**Parameters:**

- `full_report_content` (str): Complete report text

**Returns:** Executive summary text

##### perform_web_research()

```python
def perform_web_research(self, query: str, num_sources: int = 3) -> List[Dict[str, str]]
```

Search for academic sources on a topic.

**Parameters:**

- `query` (str): Search query
- `num_sources` (int): Number of sources to return

**Returns:** List of dicts with 'title' and 'url' keys

##### generate_report()

```python
def generate_report(self) -> Dict[str, str]
```

Generate complete research report with all sections.

**Returns:** Dict mapping section names to content

---

### HierarchicalGenerator

**File:** [`utils/hierarchical_generator.py`](utils/hierarchical_generator.py:222)

Generates large multi-volume research documents (2000+ pages).

```python
from utils.hierarchical_generator import HierarchicalGenerator
```

#### Constructor

```python
HierarchicalGenerator(
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
    sections_per_volume: int = 10
)
```

#### Methods

##### generate()

```python
def generate(
    self,
    num_sections: int = 20,
    use_checkpoint: bool = True,
    progress_callback=None
) -> Dict[str, Any]
```

Synchronous generation of complete multi-volume document.

**Parameters:**

- `num_sections` (int): Total sections to generate (default: 20)
- `use_checkpoint` (bool): Enable checkpoint resume (default: True)
- `progress_callback` (callable): Progress update function

**Returns:** Dict with:

- `topic`: Research topic
- `outline`: Master outline structure
- `volumes`: Volume plans
- `volume_contents`: Dict of volume number -> sections
- `total_volumes`: Number of volumes
- `total_pages`: Estimated page count

**Example:**

```python
result = generator.generate(
    num_sections=50,  # 5 volumes of 10 sections each
    use_checkpoint=True,
    progress_callback=lambda p: print(f"Volume {p['current_volume']}/{p['total_volumes']}")
)
```

##### generate_master_outline()

```python
def generate_master_outline(self, num_sections: int = 20) -> List[OutlineSection]
```

Generate the master outline for the research topic.

##### create_volume_plans()

```python
def create_volume_plans(self, outline: List[OutlineSection]) -> List[VolumePlan]
```

Group outline sections into volumes.

---

### ChatManager

**File:** [`utils/chat_manager.py`](utils/chat_manager.py:28)

Manages interactive chatbot for research Q&A.

```python
from utils.chat_manager import ChatManager
```

#### Constructor

```python
ChatManager(
    config_manager: ConfigManager,
    prompt_manager: PromptManager,
    model_name: str = "gemini-2.5-flash",
    timeout: int = 60,
    research_topic: str = "",
    max_retries: int = 3
)
```

#### Methods

##### load_research_content()

```python
def load_research_content(self, content: Dict[str, str])
```

Load generated research content for the chatbot.

**Parameters:**

- `content` (dict): Dict mapping section titles to content

##### generate_chat_response()

```python
def generate_chat_response(self, user_query: str) -> str
```

Generate response to user question.

**Parameters:**

- `user_query` (str): Question about research

**Returns:** Response text

##### generate_table_summary()

```python
def generate_table_summary(self, content: str) -> str
```

Generate summaries for tables in content.

##### generate_executive_summary()

```python
def generate_executive_summary(self) -> str
```

Generate executive summary from research.

##### clear_chat_history()

```python
def clear_chat_history(self)
```

Clear conversation history.

---

### ModularExporter

**File:** [`utils/modular_exporter.py`](utils/modular_exporter.py:65)

Handles exporting research as individual volumes or master document.

```python
from utils.modular_exporter import ModularExporter, create_modular_exporter
```

#### Constructor

```python
ModularExporter(
    topic: str,
    output_dir: str = "exports",
    export_options: Optional[ExportOptions] = None
)
```

#### Methods

##### export_single_volume()

```python
def export_single_volume(
    self,
    volume_number: int,
    volume_title: str,
    sections_content: Dict[str, str],
    include_toc: bool = True,
    include_references: bool = True
) -> VolumeExport
```

Export a single volume as DOCX.

**Returns:** VolumeExport object with file details

##### export_all_volumes()

```python
def export_all_volumes(
    self,
    volumes_data: Dict[int, Dict[str, str]],
    volume_titles: Optional[Dict[int, str]] = None
) -> List[VolumeExport]
```

Export all volumes as separate documents.

##### create_master_document()

```python
def create_master_document(
    self,
    volumes_data: Dict[int, Dict[str, str]],
    volume_titles: Optional[Dict[int, str]] = None,
    master_outline: Optional[List[Dict]] = None,
    generate_toc: bool = True
) -> str
```

Create combined master document.

**Returns:** Path to master document

##### create_zip_archive()

```python
def create_zip_archive(self, archive_name: Optional[str] = None) -> str
```

Create ZIP containing all exports.

**Returns:** Path to ZIP file

##### get_export_summary()

```python
def get_export_summary(self) -> Dict[str, Any]
```

Get summary of all exports.

**Returns:** Dict with totals and volume details

---

## Utility Classes

### ConfigManager

**File:** [`utils/config_manager.py`](utils/config_manager.py:8)

Singleton for managing API configurations.

```python
from utils.config_manager import ConfigManager

config = ConfigManager()  # Uses singleton pattern
```

#### Methods

| Method                               | Returns         | Description                |
| ------------------------------------ | --------------- | -------------------------- |
| `get_api_keys()`                     | Dict[str, str]  | Load API keys from secrets |
| `get_default_model()`                | str             | Default model name         |
| `get_available_models()`             | Dict[str, Dict] | Available models config    |
| `get_model_provider(model_name)`     | str             | Provider for a model       |
| `get_model_display_name(model_name)` | str             | Display name for a model   |

---

### PromptManager

**File:** [`utils/prompt_manager.py`](utils/prompt_manager.py:8)

Manages and formats LLM prompt templates.

```python
from utils.prompt_manager import PromptManager

prompt_mgr = PromptManager()
```

#### Methods

| Method                          | Returns       | Description                 |
| ------------------------------- | ------------- | --------------------------- |
| `get_template(name)`            | Optional[str] | Get prompt template         |
| `format_prompt(name, **kwargs)` | str           | Format template with values |

**Available Templates:**

- `research_section`
- `executive_summary`
- `chat_response`
- `relevance_check`
- `web_search_response`
- `table_summary`

---

### TemplateManager

**File:** [`utils/template_manager.py`](utils/template_manager.py:8)

Manages research report templates.

```python
from utils.template_manager import TemplateManager

tmpl_mgr = TemplateManager()
```

#### Methods

| Method                 | Returns        | Description            |
| ---------------------- | -------------- | ---------------------- |
| `get_template_names()` | List[str]      | List of template names |
| `get_template(name)`   | Optional[Dict] | Get template data      |

---

### SessionStateManager

**File:** [`utils/session_state_manager.py`](utils/session_state_manager.py:7)

Persists Streamlit session state.

```python
from utils.session_state_manager import SessionStateManager
```

#### Methods

| Method                         | Returns         | Description                    |
| ------------------------------ | --------------- | ------------------------------ |
| `initialize_state()`           | None            | Initialize all state variables |
| `set_value(key, value)`        | None            | Set a state value              |
| `get_value(key, default)`      | Any             | Get a state value              |
| `store_research_data(...)`     | None            | Store research generation data |
| `store_file_data(...)`         | None            | Store generated file data      |
| `get_file_bytes(type)`         | Optional[bytes] | Get file content               |
| `is_file_generated(type)`      | bool            | Check if file exists           |
| `clear_research_data()`        | None            | Clear research data            |
| `store_hierarchical_data(...)` | None            | Store volume data              |
| `store_modular_exports(...)`   | None            | Store export data              |
| `debug_session_state()`        | Dict            | Get state for debugging        |

---

### ContentAnalyzer

**File:** [`utils/content_analyzer.py`](utils/content_analyzer.py:12)

Analyzes content for quality metrics.

```python
from utils.content_analyzer import ContentAnalyzer

analyzer = ContentAnalyzer(config_manager=config_manager)
```

#### Methods

| Method                          | Returns          | Description           |
| ------------------------------- | ---------------- | --------------------- |
| `analyze_readability(text)`     | Dict[str, float] | Readability scores    |
| `perform_external_checks(text)` | Dict[str, Any]   | Plagiarism/fact check |
| `_check_plagiarism(text)`       | Dict             | Placeholder           |
| `_check_facts(text)`            | Dict             | Placeholder           |

**Readability Metrics:**

- Flesch Reading Ease
- Gunning Fog Index
- Coleman-Liau Index
- Automated Readability Index
- Dale-Chall Readability Score

---

### CitationManager

**File:** [`utils/citation_manager.py`](utils/citation_manager.py:40)

Manages citations in multiple formats.

```python
from utils.citation_manager import CitationManager, Citation
```

#### Methods

| Method                                       | Returns  | Description           |
| -------------------------------------------- | -------- | --------------------- |
| `add_citation(citation)`                     | None     | Add a citation        |
| `add_citation_from_dict(data)`               | Citation | Create from dict      |
| `generate_citation(citation, style)`         | str      | Format citation       |
| `generate_reference_list(style)`             | str      | Full bibliography     |
| `generate_in_text_citation(citation, style)` | str      | In-text citation      |
| `export_citations(format)`                   | str      | Export as BibTeX/JSON |
| `clear()`                                    | None     | Clear all citations   |
| `get_citation_count()`                       | int      | Number of citations   |

**Styles:** `apa`, `mla`, `chicago`, `harvard`

---

### LLMClientManager

**File:** [`utils/llm_client_manager.py`](utils/llm_client_manager.py:12)

Manages LLM API client initialization.

```python
from utils.llm_client_manager import LLMClientManager

client_mgr = LLMClientManager(api_keys)
```

#### Methods

| Method                   | Returns          | Description            |
| ------------------------ | ---------------- | ---------------------- |
| `get_client(model_name)` | Optional[Client] | Get API client         |
| `get_api_keys()`         | Dict[str, str]   | Get API keys copy      |
| `clear_api_keys()`       | None             | Clear keys from memory |

---

### WebScraper

**File:** [`utils/web_scraper.py`](utils/web_scraper.py:13)

Web scraping and search functionality.

```python
from utils.web_scraper import WebScraper

scraper = WebScraper(timeout=30)
```

#### Methods

| Method                                        | Returns       | Description     |
| --------------------------------------------- | ------------- | --------------- |
| `search_academic_sources(query, num_results)` | List[Dict]    | Search Google   |
| `scrape_text_from_url(url)`                   | Optional[str] | Extract content |
| `_extract_text_from_html(bytes)`              | Optional[str] | Parse HTML      |
| `_extract_text_from_pdf_bytes(bytes)`         | Optional[str] | Parse PDF       |

---

### DocxGenerator

**File:** [`utils/docx_generator.py`](utils/docx_generator.py:27)

Generates Word documents from markdown.

```python
from utils.docx_generator import DocxGenerator

docx_gen = DocxGenerator(topic="Research Title")
docx_gen.generate_docx_report(sections, "output.docx")
```

#### Methods

| Method                                        | Returns | Description      |
| --------------------------------------------- | ------- | ---------------- |
| `generate_docx_report(sections, output_path)` | None    | Create DOCX file |

---

### PowerpointGenerator

**File:** [`utils/powerpoint_generator.py`](utils/powerpoint_generator.py:18)

Generates PowerPoint presentations.

```python
from utils.powerpoint_generator import PowerpointGenerator

ppt = PowerpointGenerator(theme="professional")
```

#### Methods

| Method                                                 | Description       |
| ------------------------------------------------------ | ----------------- |
| `create_title_slide(title, subtitle, date, author)`    | Title slide       |
| `create_section_slide(title, section_number)`          | Section divider   |
| `create_content_slide(title, content, bullets)`        | Content slide     |
| `create_image_slide(title, image_path, caption)`       | Image slide       |
| `create_table_slide(title, headers, rows)`             | Table slide       |
| `create_conclusion_slide(title, key_points, thoughts)` | Summary slide     |
| `create_references_slide(title, references)`           | References slide  |
| `generate_presentation(sections, output_path, title)`  | Full presentation |
| `save(output_path)`                                    | Save to file      |
| `save_to_bytes()`                                      | BytesIO object    |

---

### NotesManager

**File:** [`utils/notes_manager.py`](utils/notes_manager.py:8)

Manages research notes.

```python
from utils.notes_manager import NotesManager

notes = NotesManager(filepath="notes.txt")
```

#### Methods

| Method                      | Returns | Description        |
| --------------------------- | ------- | ------------------ |
| `load_notes()`              | str     | Load from file     |
| `update_notes(new_notes)`   | bool    | Update content     |
| `save_notes()`              | bool    | Save to file       |
| `format_notes()`            | str     | Format as markdown |
| `save_as_docx(output_path)` | str     | Export as DOCX     |

---

### CheckpointManager

**File:** [`utils/hierarchical_generator.py`](utils/hierarchical_generator.py:78)

Manages checkpoints for resume capability.

```python
from utils.hierarchical_generator import CheckpointManager

checkpoint_mgr = CheckpointManager()
```

#### Methods

| Method                              | Returns                  | Description         |
| ----------------------------------- | ------------------------ | ------------------- |
| `save_checkpoint(checkpoint)`       | str                      | Save to file        |
| `load_checkpoint(topic)`            | Optional[CheckpointData] | Load checkpoint     |
| `get_latest_checkpoint_path(topic)` | Optional[str]            | Get checkpoint path |

---

## Data Classes

### Citation

**File:** [`utils/citation_manager.py`](utils/citation_manager.py:14)

```python
@dataclass
class Citation:
    title: str
    authors: List[str]
    publication_date: str
    publisher: str
    url: str
    accessed_date: str = ""
    doi: str = ""
    citation_type: str = "webpage"

    def to_dict(self) -> Dict[str, str]
```

---

### OutlineSection

**File:** [`utils/hierarchical_generator.py`](utils/hierarchical_generator.py:40)

```python
@dataclass
class OutlineSection:
    title: str
    description: str
    subsections: List[str] = field(default_factory=list)
    word_count_estimate: int = 1000
    priority: int = 1
    keywords: List[str] = field(default_factory=list)
```

---

### VolumePlan

**File:** [`utils/hierarchical_generator.py`](utils/hierarchical_generator.py:51)

```python
@dataclass
class VolumePlan:
    volume_number: int
    volume_title: str
    sections: List[OutlineSection]
    total_estimated_words: int = 0
    total_estimated_pages: int = 0
```

---

### CheckpointData

**File:** [`utils/hierarchical_generator.py`](utils/hierarchical_generator.py:65)

```python
@dataclass
class CheckpointData:
    timestamp: str
    phase: str
    topic: str
    master_outline: List[Dict] = field(default_factory=list)
    volume_plans: List[Dict] = field(default_factory=list)
    completed_volumes: List[int] = field(default_factory=list)
    volume_contents: Dict[int, Dict[str, str]] = field(default_factory=dict)
    last_updated: str = field(default_factory=str)
```

---

### VolumeExport

**File:** [`utils/modular_exporter.py`](utils/modular_exporter.py:54)

```python
@dataclass
class VolumeExport:
    volume_number: int
    volume_title: str
    file_path: str
    file_size: int
    pages: int
    sections: List[str]
```

---

### ExportOptions

**File:** [`utils/modular_exporter.py`](utils/modular_exporter.py:38)

```python
@dataclass
class ExportOptions:
    output_format: str = "docx"
    include_toc: bool = True
    include_cover_page: bool = True
    include_references: bool = True
    cross_reference_volumes: bool = True
    page_size: str = "A4"
    margins: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    font_family: str = "Times New Roman"
    font_size: int = 12
    line_spacing: float = 1.5
    volume_prefix: str = "Volume"
```

---

## Exceptions

**File:** [`utils/exceptions.py`](utils/exceptions.py:7)

### Exception Hierarchy

```
EreunaError (base)
├── ConfigurationError (C001)
├── APIError (A000)
│   ├── APITimeoutError (A001)
│   ├── APIRateLimitError (A002)
│   ├── APIAuthenticationError (A003)
│   └── APIPermissionError (A004)
├── LLMGenerationError (G000)
├── ContentExtractionError (E001)
├── WebSearchError (S000)
├── DocumentGenerationError (D000)
└── ValidationError (V000)
```

### Usage

```python
from utils.exceptions import (
    EreunaError,
    APITimeoutError,
    APIRateLimitError,
    APIAuthenticationError,
    LLMGenerationError,
    ValidationError
)

try:
    result = generator.generate_section(section_data)
except APITimeoutError as e:
    logger.error(f"Request timed out: {e}")
except APIAuthenticationError as e:
    logger.error(f"Invalid API key: {e}")
except LLMGenerationError as e:
    logger.error(f"Generation failed: {e}")
except ValidationError as e:
    logger.error(f"Invalid input: {e}")
except EreunaError as e:
    logger.error(f"Ereuna error: {e}")
```

---

## Module Index

| Module                                                             | Purpose                   |
| ------------------------------------------------------------------ | ------------------------- |
| [`research_generator.py`](utils/research_generator.py:29)          | Core report generation    |
| [`hierarchical_generator.py`](utils/hierarchical_generator.py:222) | Large document generation |
| [`chat_manager.py`](utils/chat_manager.py:28)                      | Chatbot functionality     |
| [`modular_exporter.py`](utils/modular_exporter.py:65)              | Multi-volume export       |
| [`config_manager.py`](utils/config_manager.py:8)                   | API configuration         |
| [`prompt_manager.py`](utils/prompt_manager.py:8)                   | Prompt templates          |
| [`template_manager.py`](utils/template_manager.py:8)               | Research templates        |
| [`docx_generator.py`](utils/docx_generator.py:27)                  | Word export               |
| [`powerpoint_generator.py`](utils/powerpoint_generator.py:18)      | PPT export                |
| [`web_scraper.py`](utils/web_scraper.py:13)                        | Web research              |
| [`citation_manager.py`](utils/citation_manager.py:40)              | Citation handling         |
| [`content_analyzer.py`](utils/content_analyzer.py:12)              | Quality analysis          |
| [`session_state_manager.py`](utils/session_state_manager.py:7)     | State persistence         |
| [`llm_client_manager.py`](utils/llm_client_manager.py:12)          | LLM clients               |
| [`llm_call_utils.py`](utils/llm_call_utils.py:26)                  | API call utilities        |
| [`exceptions.py`](utils/exceptions.py:7)                           | Custom exceptions         |
| [`notes_manager.py`](utils/notes_manager.py:8)                     | Notes management          |
