# Architecture Documentation

This document describes the high-level architecture, design patterns, and system components of the Ereuna Research Report Generator.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Component Diagram](#component-diagram)
- [Data Flow](#data-flow)
- [Design Patterns](#design-patterns)
- [Module Responsibilities](#module-responsibilities)
- [State Management](#state-management)
- [Error Handling](#error-handling)
- [Security Considerations](#security-considerations)
- [Performance Considerations](#performance-considerations)

---

## Overview

Ereuna is a Streamlit-based web application that leverages multiple Large Language Models (LLMs) to generate comprehensive research reports. The system follows a modular architecture with clear separation of concerns, enabling:

- Multi-model support (Gemini, GPT, Claude)
- Scalable document generation (standard and hierarchical)
- Rich export capabilities (DOCX, PPTX, TXT)
- Interactive research Q&A
- Persistent session state

---

## System Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│                    (Streamlit UI)                            │
├─────────────────────────────────────────────────────────────┤
│                      Application Layer                       │
│                   (research.py)                              │
├─────────────────────────────────────────────────────────────┤
│                      Service Layer                           │
│              (ResearchGenerator, ChatManager, etc.)          │
├─────────────────────────────────────────────────────────────┤
│                     Utility Layer                            │
│     (ConfigManager, PromptManager, TemplateManager, etc.)    │
├─────────────────────────────────────────────────────────────┤
│                      External Layer                          │
│          (LLM APIs, Web Search, File I/O)                    │
└─────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
                    ┌──────────────────┐
                    │   Streamlit UI   │
                    │   (research.py)  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   Research      │ │     Chat        │ │   Hierarchical  │
    │   Generator     │ │     Manager     │ │   Generator     │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │
             └───────────────────┼───────────────────┘
                                 │
                                 ▼
                    ┌────────────────────┐
                    │   LLM Client       │
                    │   Manager          │
                    │                    │
                    │  ┌──────────────┐  │
                    │  │   Gemini     │  │
                    │  │   Client     │  │
                    │  └──────────────┘  │
                    │  ┌──────────────┐  │
                    │  │   OpenAI     │  │
                    │  │   Client     │  │
                    │  └──────────────┘  │
                    │  ┌──────────────┐  │
                    │  │  Anthropic   │  │
                    │  │   Client     │  │
                    │  └──────────────┘  │
                    └─────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   Web Scraper   │ │   Content       │ │   Citation      │
    │   (Search/      │ │   Analyzer      │ │   Manager       │
    │    Scrape)      │ │                 │ │                 │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │
             └───────────────────┼───────────────────┘
                                 │
                                 ▼
                    ┌────────────────────┐
                    │   Export Managers  │
                    │                    │
                    │  ┌──────────────┐  │
                    │  │  DocxGen     │  │
                    │  └──────────────┘  │
                    │  ┌──────────────┐  │
                    │  │  PPTX Gen    │  │
                    │  └──────────────┘  │
                    │  ┌──────────────┐  │
                    │  │  Modular     │  │
                    │  │  Exporter    │  │
                    │  └──────────────┘  │
                    └────────────────────┘
```

---

## Data Flow

### Standard Report Generation Flow

```
1. User Input
   ┌─────────────────┐
   │ Topic, Keywords │
   │ Questions, Temp │
   └────────┬────────┘
            │
            ▼
2. Template Loading
   ┌─────────────────┐     ┌─────────────────┐
   │ TemplateManager │────▶│ Sections Config │
   └─────────────────┘     └─────────────────┘
            │
            ▼
3. Section Iteration
   ┌─────────────────┐     ┌─────────────────┐
   │ For each section│────▶│ Generate Content│
   └─────────────────┘     └────────┬────────┘
                                    │
            ┌───────────────────────┼───────────────┐
            │                       │               │
            ▼                       ▼               ▼
   ┌─────────────────┐   ┌─────────────────┐ ┌─────────────────┐
   │ Previous Content│   │ LLM API Call    │ │    Context      │
   │ Accumulation    │   │ (Retry Logic)   │ │    Building     │
   └─────────────────┘   └────────┬────────┘ └─────────────────┘
            │                     │
            └─────────────────────┤
                                  ▼
4. Results Storage
   ┌─────────────────┐     ┌─────────────────┐
   │ Session State   │────▶│ Display Results │
   └─────────────────┘     └─────────────────┘
            │
            ▼
5. Quality Analysis
   ┌─────────────────┐     ┌─────────────────┐
   │ Executive Summary◀────│ LLM API Call    │
   └─────────────────┘     └─────────────────┘
            │
            ▼
6. Export
   ┌─────────────────┐     ┌─────────────────┐
   │ DOCX/PPTX/TXT  │────▶│ Download        │
   └─────────────────┘     └─────────────────┘
```

### Hierarchical Generation Flow

```
1. Outline Phase
   ┌─────────────────┐     ┌─────────────────┐
   │ Generate Master │────▶│ Outline: 20+    │
   │ Outline         │     │ Sections        │
   └─────────────────┘     └─────────────────┘
            │
            ▼
2. Volume Planning
   ┌─────────────────┐     ┌─────────────────┐
   │ Group into      │────▶│ Volume 1: 10    │
   │ Volumes         │     │ Volume 2: 10    │
   └─────────────────┘     └─────────────────┘
            │
            ▼
3. Volume Generation Loop
   ┌─────────────────┐     ┌─────────────────┐
   │ For each volume │────▶│ Generate Sections│
   └─────────────────┘     └────────┬────────┘
            │                       │
            ▼                       ▼
   ┌─────────────────┐     ┌─────────────────┐
   │ Save Checkpoint │     │ Progress Update │
   └─────────────────┘     └─────────────────┘
            │
            ▼
4. Export Phase
   ┌─────────────────┐     ┌─────────────────┐
   │ Individual DOCX │     │ Master Document │
   │ Per Volume      │     │ Combined        │
   └─────────────────┘     └─────────────────┘
            │
            ▼
5. Archive
   ┌─────────────────┐
   │ ZIP with all    │
   │ volumes + master│
   └─────────────────┘
```

---

## Design Patterns

### 1. Singleton Pattern

Used for managers that should have single instances:

```python
class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
```

**Used in:** [`ConfigManager`](utils/config_manager.py:8)

### 2. Factory Pattern

Used for creating LLM clients:

```python
class LLMClientManager:
    def get_client(self, model_name: str):
        model_prefix = model_name.split('-')[0]
        if model_prefix not in self.clients:
            self._initialize_api_client(model_prefix)
        return self.clients.get(model_prefix)
```

**Used in:** [`LLMClientManager`](utils/llm_client_manager.py:34)

### 3. Template Method Pattern

Used in document generators:

```python
class DocxGenerator:
    def generate_docx_report(self, sections_content, output_path):
        document = Document()
        document.add_heading(self.topic, level=1)
        for title, content in sections_content.items():
            document.add_heading(title, level=2)
            self._add_markdown_content(document, content)  # Template method
        document.save(output_path)
```

**Used in:** [`DocxGenerator`](utils/docx_generator.py:215), [`PowerpointGenerator`](utils/powerpoint_generator.py:412)

### 4. Strategy Pattern

Used for different citation styles:

```python
class CitationManager:
    def generate_citation(self, citation: Citation, style: str = "apa") -> str:
        if style == "apa":
            return self._format_apa(citation)
        elif style == "mla":
            return self._format_mla(citation)
        # ... etc
```

**Used in:** [`CitationManager`](utils/citation_manager.py:133)

### 5. Builder Pattern

Used in hierarchical generation:

```python
class HierarchicalGenerator:
    def generate_master_outline(self, num_sections: int) -> List[OutlineSection]:
        # Builds outline incrementally
        ...

    def create_volume_plans(self, outline: List[OutlineSection]) -> List[VolumePlan]:
        # Groups sections into volumes
        ...
```

**Used in:** [`HierarchicalGenerator`](utils/hierarchical_generator.py:313)

### 6. Repository Pattern

Used for data access abstraction:

```python
class SessionStateManager:
    @staticmethod
    def store_research_data(sections: dict, topic: str, ...):
        st.session_state['research_sections'] = sections
        st.session_state['research_generated'] = True
        ...
```

**Used in:** [`SessionStateManager`](utils/session_state_manager.py:113)

---

## Module Responsibilities

### Presentation Layer

| Module                         | Responsibility                                           |
| ------------------------------ | -------------------------------------------------------- |
| [`research.py`](research.py:1) | Main Streamlit application, UI rendering, event handling |

### Application Layer

| Module                                                         | Responsibility                        |
| -------------------------------------------------------------- | ------------------------------------- |
| [`ResearchGenerator`](utils/research_generator.py:29)          | Generate report sections using LLM    |
| [`HierarchicalGenerator`](utils/hierarchical_generator.py:222) | Generate large multi-volume documents |
| [`ChatManager`](utils/chat_manager.py:28)                      | Interactive research Q&A              |
| [`ModularExporter`](utils/modular_exporter.py:65)              | Export to multiple volumes/formats    |

### Service Layer

| Module                                                    | Responsibility                           |
| --------------------------------------------------------- | ---------------------------------------- |
| [`ConfigManager`](utils/config_manager.py:8)              | Manage API keys and model configurations |
| [`PromptManager`](utils/prompt_manager.py:8)              | Manage LLM prompt templates              |
| [`TemplateManager`](utils/template_manager.py:8)          | Manage research templates                |
| [`ContentAnalyzer`](utils/content_analyzer.py:12)         | Analyze content quality metrics          |
| [`CitationManager`](utils/citation_manager.py:40)         | Manage citations in multiple formats     |
| [`WebScraper`](utils/web_scraper.py:13)                   | Search and scrape web content            |
| [`DocxGenerator`](utils/docx_generator.py:27)             | Generate Word documents                  |
| [`PowerpointGenerator`](utils/powerpoint_generator.py:18) | Generate PowerPoint presentations        |
| [`NotesManager`](utils/notes_manager.py:8)                | Manage research notes                    |

### Utility Layer

| Module                                                    | Responsibility                        |
| --------------------------------------------------------- | ------------------------------------- |
| [`LLMClientManager`](utils/llm_client_manager.py:12)      | Initialize and manage LLM API clients |
| [`LLMCallUtils`](utils/llm_call_utils.py:26)              | Retry logic and API call handling     |
| [`SessionStateManager`](utils/session_state_manager.py:7) | Persist Streamlit session state       |
| [`Exceptions`](utils/exceptions.py:7)                     | Custom exception definitions          |

---

## State Management

### Session State Structure

```
st.session_state
├── research_generated: bool
├── research_sections: Dict[str, str]
├── current_topic: str
├── current_keywords: str
├── current_questions: str
├── selected_model_name: str
├── executive_summary: str
├── readability_scores: Dict[str, float]
├── notes_content: str
├── chat_manager: ChatManager
├── error_message: str
├── generation_in_progress: bool
│
├── # File Generation State
├── docx_generated: bool
├── docx_bytes: bytes
├── docx_path: str
│
├── # Hierarchical Generation State
├── hierarchical_generation_enabled: bool
├── hierarchical_generated: bool
├── master_outline: List[Dict]
├── volume_plans: List[Dict]
├── volume_contents: Dict[int, Dict[str, str]]
├── completed_volumes: List[int]
├── total_volumes: int
├── current_volume: int
├── hierarchical_progress: Dict
│
├── # Checkpoint State
├── checkpoint_available: bool
├── checkpoint_path: str
├── checkpoint_timestamp: str
│
├── # Large Document Settings
├── sections_per_volume: int
├── total_target_sections: int
├── enable_checkpoint_resume: bool
│
└── # Export State
├── modular_exports: Dict
├── export_manifest: Dict
├── master_doc_path: str
```

### State Persistence

- **File Data:** Stored as bytes in session state to survive refresh
- **Research Content:** Persisted between UI interactions
- **Checkpoints:** Saved to disk for resume capability

---

## Error Handling

### Exception Hierarchy

```
EreunaError (base class)
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

### Error Handling Strategies

1. **Retry with Exponential Backoff**
   
   - Automatic retries for transient failures
   - Jitter to prevent thundering herd

2. **Graceful Degradation**
   
   - Fallback to development mode if secrets missing
   - Error messages displayed in UI

3. **Validation**
   
   - Input validation at module boundaries
   - Custom ValidationError for user feedback

---

## Security Considerations

### API Key Management

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "..."  # Never commit to version control
OPENAI_API_KEY = "..."
ANTHROPIC_API_KEY = "..."
```

**Best Practices:**

- Keys stored in `secrets.toml` (gitignored)
- Keys not exposed in UI or logs
- Session-scoped key usage
- Memory cleanup with `clear_api_keys()`

### Content Security

- LLM prompt injection prevention
- Safe HTML parsing with BeautifulSoup
- PDF content validation

### File Security

- Path sanitization for exports
- Safe filename generation
- Directory boundary checks

---

## Performance Considerations

### Async Operations

- Web scraping uses async HTTP client
- Google search runs in thread pool

```python
async def scrape_text_from_url(self, url: str) -> Optional[str]:
    content = await self._fetch_content(url)
    # ...
```

### Caching

- Session state prevents redundant computations
- Checkpoint resume avoids reprocessing

### Memory Management

- Streaming markdown parsing for large documents
- Batch processing for table exports
- Bytes storage optimization

### Scalability

- Hierarchical generation for large documents
- Volume-based processing
- Checkpoint-based recovery

---

## Dependencies

### External APIs

| Provider      | Purpose        | Rate Limits      |
| ------------- | -------------- | ---------------- |
| Google Gemini | LLM generation | Per-model limits |
| OpenAI        | LLM generation | Per-model limits |
| Anthropic     | LLM generation | Per-model limits |
| Google Search | Web research   | 100 queries/day  |
| pypdf         | PDF extraction | N/A              |

### Key Libraries

| Library             | Version | Purpose             |
| ------------------- | ------- | ------------------- |
| streamlit           | ≥1.28.0 | UI framework        |
| google-generativeai | ≥0.3.0  | Gemini API          |
| openai              | ≥1.0.0  | OpenAI API          |
| anthropic           | ≥0.3.0  | Anthropic API       |
| python-docx         | ≥0.8.11 | DOCX generation     |
| python-pptx         | ≥0.6.21 | PPTX generation     |
| beautifulsoup4      | ≥4.12.2 | HTML parsing        |
| pypdf               | ≥3.0.0  | PDF extraction      |
| textstat            | ≥0.7.0  | Readability metrics |
| googlesearch-python | ≥1.2.0  | Web search          |

---

## Extension Points

### Adding New LLM Providers

1. Update [`LLMClientManager._initialize_api_client()`](utils/llm_client_manager.py:44)
2. Update [`make_llm_call_with_retry()`](utils/llm_call_utils.py:26)
3. Add provider to [`ConfigManager`](utils/config_manager.py:37)
4. Update prompt templates if needed

### Adding New Export Formats

1. Create new generator class (similar to [`DocxGenerator`](utils/docx_generator.py:27))
2. Update [`ModularExporter`](utils/modular_exporter.py:65) if modular export needed
3. Add to UI in [`research.py`](research.py:1)

### Adding New Analysis Features

1. Create analyzer class (similar to [`ContentAnalyzer`](utils/content_analyzer.py:12))
2. Add to quality analysis section in [`research.py`](research.py:1)
3. Update UI as needed

### Custom Templates

1. Create JSON file in [`templates/`](templates/)
2. Add prompt templates in [`Ereuna/prompts/`](Ereuna/prompts/)
3. Update [`TemplateManager`](utils/template_manager.py:18) if needed
