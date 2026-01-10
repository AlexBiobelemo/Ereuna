# API Reference

This section provides detailed API documentation for all utility modules in Ereuna.

---

## Table of Contents

1. [LLM Client Manager](#llm-client-manager)
2. [LLM Call Utils](#llm-call-utils)
3. [Prompt Manager](#prompt-manager)
4. [Config Manager](#config-manager)
5. [Session State Manager](#session-state-manager)
6. [Exception Classes](#exception-classes)
7. [Content Analyzer](#content-analyzer)
8. [Citation Manager](#citation-manager)
9. [Web Scraper](#web-scraper)
10. [Notes Manager](#notes-manager)
11. [Template Manager](#template-manager)
12. [Research Generator](#research-generator)
13. [Chat Manager](#chat-manager)
14. [Modular Exporter](#modular-exporter)
15. [Hierarchical Generator](#hierarchical-generator)
16. [Document Generators](#document-generators)

---

## LLM Client Manager

**File:** [`utils/llm_client_manager.py`](utils/llm_client_manager.py)

Manages initialization and configuration of various LLM API clients (Google Gemini, OpenAI GPT, Anthropic Claude).

### Class: `LLMClientManager`

```python
from utils.llm_client_manager import LLMClientManager
```

#### Constructor

```python
LLMClientManager(api_keys: Dict[str, str], spinner_update_callback: Optional[Any] = None)
```

| Parameter                 | Type             | Description                                                                                |
| ------------------------- | ---------------- | ------------------------------------------------------------------------------------------ |
| `api_keys`                | `Dict[str, str]` | Dictionary mapping provider prefixes to API keys (e.g., `{"gemini": "key", "gpt": "key"}`) |
| `spinner_update_callback` | `Optional[Any]`  | Optional callback function for status updates                                              |

#### Methods

##### `get_api_keys() -> Dict[str, str]`

Returns a copy of the stored API keys (not the original reference).

```python
api_keys = manager.get_api_keys()
print(api_keys)  # {'gemini': '...', 'gpt': '...', 'claude': '...'}
```

##### `clear_api_keys()`

Securely clears all API keys from memory. Call this when the application shuts down or when keys are no longer needed.

```python
manager.clear_api_keys()
```

##### `get_client(model_name: str) -> Optional[Any]`

Returns an initialized API client for the given model name. Initializes the client if not already done.

| Parameter    | Type  | Description                                              |
| ------------ | ----- | -------------------------------------------------------- |
| `model_name` | `str` | Full model name (e.g., `"gemini-2.5-flash"`, `"gpt-4o"`) |

```python
client = manager.get_client("gemini-2.5-flash")
# Returns configured genai module for Gemini
client = manager.get_client("gpt-4o")
# Returns AsyncOpenAI client for OpenAI
client = manager.get_client("claude-3-opus-20240229")
# Returns AsyncAnthropic client for Anthropic
```

#### Supported Model Prefixes

| Prefix   | Provider      | Client Type                  |
| -------- | ------------- | ---------------------------- |
| `gemini` | Google Gemini | `google.genai` module |
| `gpt`    | OpenAI        | `AsyncOpenAI`                |
| `claude` | Anthropic     | `AsyncAnthropic`             |

---

## LLM Call Utils

**File:** [`utils/llm_call_utils.py`](utils/llm_call_utils.py)

Shared utility module for LLM API calls with retry logic and exponential backoff.

### Functions

#### `make_llm_call_with_retry()`

```python
from utils.llm_call_utils import make_llm_call_with_retry
```

Makes an LLM API call with retry logic and exponential backoff with jitter.

```python
response = make_llm_call_with_retry(
    llm_client_manager=manager,
    model_name="gemini-2.5-flash",
    prompt="Explain quantum computing in simple terms.",
    system_prompt="You are a helpful AI assistant.",
    max_retries=3,
    timeout=60,
    call_type="Explanation generation"
)
```

| Parameter            | Type               | Default      | Description                                       |
| -------------------- | ------------------ | ------------ | ------------------------------------------------- |
| `llm_client_manager` | `LLMClientManager` | Required     | The LLMClientManager instance for API clients     |
| `model_name`         | `str`              | Required     | The name of the model to use                      |
| `prompt`             | `str`              | Required     | The prompt to send to the LLM                     |
| `system_prompt`      | `Optional[str]`    | `None`       | Optional system prompt for models that support it |
| `max_retries`        | `int`              | `3`          | Maximum number of retry attempts                  |
| `timeout`            | `int`              | `60`         | Timeout for API calls in seconds                  |
| `call_type`          | `str`              | `"LLM call"` | Descriptive string for the type of LLM call       |

**Returns:** `str` - The response text from the LLM

**Raises:**

- [`APITimeoutError`](utils/exceptions.py:9) - When API request times out
- [`APIRateLimitError`](utils/exceptions.py:14) - When rate limit is exceeded
- [`APIAuthenticationError`](utils/exceptions.py:19) - When API authentication fails
- [`APIPermissionError`](utils/exceptions.py:24) - When API permission is denied
- [`LLMGenerationError`](utils/exceptions.py:29) - When all retries fail or unrecoverable error occurs

#### `adapt_prompt_for_model()`

```python
from utils.llm_call_utils import adapt_prompt_for_model
```

Adapts the prompt format for the specified model.

```python
messages, kwargs = adapt_prompt_for_model(
    model_name="gemini-2.5-flash",
    prompt="Explain quantum computing.",
    system_prompt="You are a physics expert."
)
# messages = [{"role": "user", "parts": ["Explain quantum computing."]}]
# kwargs = {}
```

| Parameter       | Type            | Description                  |
| --------------- | --------------- | ---------------------------- |
| `model_name`    | `str`           | The name of the model to use |
| `prompt`        | `str`           | The user prompt              |
| `system_prompt` | `Optional[str]` | Optional system prompt       |

**Returns:** `Tuple[list, dict]` - (messages, kwargs) adapted for the model's API

---

## Prompt Manager

**File:** [`utils/prompt_manager.py`](utils/prompt_manager.py)

Manages and generates prompts using JSON templates.

### Class: `PromptManager`

```python
from utils.prompt_manager import PromptManager
```

#### Constructor

```python
PromptManager(template_dir: str = "Ereuna/prompts")
```

| Parameter      | Type  | Default            | Description                                     |
| -------------- | ----- | ------------------ | ----------------------------------------------- |
| `template_dir` | `str` | `"Ereuna/prompts"` | Directory containing prompt template JSON files |

#### Methods

##### `get_template(template_name: str) -> Optional[str]`

Retrieves a prompt template by name.

```python
template = manager.get_template("research_section")
# Returns the prompt string or None if not found
```

##### `format_prompt(template_name: str, **kwargs) -> str`

Formats a prompt using the specified template and provided keyword arguments.

```python
formatted = manager.format_prompt(
    template_name="research_section",
    section_name="Introduction",
    topic="Artificial Intelligence",
    keywords="machine learning, neural networks, deep learning",
    research_questions="What are the main applications of AI?",
    word_count=500,
    deep_research_instruction=""
)
```

| Parameter       | Type  | Description                                              |
| --------------- | ----- | -------------------------------------------------------- |
| `template_name` | `str` | The name of the template to use                          |
| `**kwargs`      | Any   | Keyword arguments to fill into the template placeholders |

**Returns:** `str` - The formatted prompt string

**Raises:** `ValueError` - If template name is not found or missing placeholders

#### Available Templates

| Template Name         | Description                                                      |
| --------------------- | ---------------------------------------------------------------- |
| `research_section`    | Template for generating a standard research report section       |
| `executive_summary`   | Template for generating an executive summary                     |
| `chat_response`       | Template for generating chat responses based on research content |
| `relevance_check`     | Template for checking query relevance to the research topic      |
| `web_search_response` | Template for generating chat responses using web search results  |
| `table_summary`       | Template for summarizing table content                           |

---

## Config Manager

**File:** [`utils/config_manager.py`](utils/config_manager.py)

Singleton configuration manager for loading API keys and model configurations from Streamlit secrets.

### Class: `ConfigManager`

```python
from utils.config_manager import ConfigManager

config = ConfigManager()  # Uses singleton pattern
```

#### Methods

##### `get_api_keys() -> Dict[str, str]`

Returns the configured API keys.

```python
api_keys = config.get_api_keys()
# {'gemini': '...', 'gpt': '...', 'claude': '...'}
```

##### `get_default_model() -> str`

Returns the default model name.

```python
default_model = config.get_default_model()
# "gemini-2.5-flash"
```

##### `get_available_models() -> Dict[str, Any]`

Returns all available models with their configurations.

```python
models = config.get_available_models()
# {
#     "gemini-2.5-flash": {"display_name": "Gemini 2.5 Flash", "provider": "gemini"},
#     "gpt-4o": {"display_name": "GPT-4o", "provider": "gpt"},
#     ...
# }
```

##### `get_model_provider(model_name: str)`

Returns the provider for a given model.

```python
provider = config.get_model_provider("gemini-2.5-flash")
# "gemini"
```

##### `get_model_display_name(model_name: str)`

Returns the display name for a given model.

```python
display_name = config.get_model_display_name("gemini-2.5-flash")
# "Gemini 2.5 Flash"
```

#### Configuration Format (secrets.toml)

```toml
[models.gemini]
gemini-2.5-flash = { display_name = "Gemini 2.5 Flash", provider = "gemini" }
gemini-1.5-pro = { display_name = "Gemini 1.5 Pro", provider = "gemini" }

[models.openai]
gpt-4o = { display_name = "GPT-4o", provider = "gpt" }

[models.anthropic]
claude-3-opus-20240229 = { display_name = "Claude 3 Opus", provider = "claude" }
```

---

## Session State Manager

**File:** [`utils/session_state_manager.py`](utils/session_state_manager.py)

Manages Streamlit session state to prevent data loss during UI refreshes.

### Class: `SessionStateManager`

```python
from utils.session_state_manager import SessionStateManager

SessionStateManager.initialize_state()
```

#### Static Methods

##### `initialize_state()`

Initialize all required session state variables with default values.

```python
SessionStateManager.initialize_state()
```

##### `set_value(key: str, value: Any)`

Safely set a session state value.

```python
SessionStateManager.set_value("custom_key", "custom_value")
```

##### `get_value(key: str, default: Any = None)`

Safely get a session state value.

```python
value = SessionStateManager.get_value("custom_key", "default_value")
```

##### `store_research_data(sections, topic, keywords, questions, model_name)`

Store research generation data in session state.

```python
SessionStateManager.store_research_data(
    sections={"Introduction": "...", "Methods": "..."},
    topic="Machine Learning",
    keywords="AI, neural networks",
    questions="What is deep learning?",
    model_name="gemini-2.5-flash"
)
```

##### `store_file_data(file_type, file_path, file_bytes)`

Store generated file data in session state.

```python
SessionStateManager.store_file_data(
    file_type="pdf",
    file_path="/path/to/report.pdf",
    file_bytes=b"..."
)
```

| File Type | Description             |
| --------- | ----------------------- |
| `pdf`     | PDF document            |
| `pptx`    | PowerPoint presentation |
| `docx`    | Word document           |

##### `get_file_bytes(file_type) -> Optional[bytes]`

Retrieve file bytes from session state.

```python
pdf_bytes = SessionStateManager.get_file_bytes("pdf")
```

##### `is_file_generated(file_type) -> bool`

Check if a file has been generated.

```python
is_generated = SessionStateManager.is_file_generated("pdf")
```

##### `clear_research_data()`

Clear all research-related data from session state.

```python
SessionStateManager.clear_research_data()
```

##### `clear_error()`

Clear error message from session state.

```python
SessionStateManager.clear_error()
```

##### `set_generation_in_progress(in_progress)`

Set generation in progress flag.

```python
SessionStateManager.set_generation_in_progress(True)
```

##### `is_generation_in_progress() -> bool`

Check if generation is currently in progress.

```python
in_progress = SessionStateManager.is_generation_in_progress()
```

#### Hierarchical Generation Methods

```python
# Enable/disable hierarchical generation
SessionStateManager.set_hierarchical_generation_enabled(True)
SessionStateManager.is_hierarchical_generation_enabled()

# Store hierarchical generation data
SessionStateManager.store_hierarchical_data(
    master_outline=[...],
    volume_plans=[...],
    volume_contents={...},
    completed_volumes=[...],
    total_volumes=5
)

# Update progress
SessionStateManager.update_hierarchical_progress(
    current_volume=2,
    total_volumes=5,
    volume_title="Chapter 2: Methods"
)

# Get progress
progress = SessionStateManager.get_hierarchical_progress()

# Check completion
is_complete = SessionStateManager.is_hierarchical_generation_complete()

# Get data
outline = SessionStateManager.get_master_outline()
volumes = SessionStateManager.get_volume_contents()
plans = SessionStateManager.get_volume_plans()

# Clear hierarchical data
SessionStateManager.clear_hierarchical_data()
```

#### Checkpoint Methods

```python
# Set checkpoint availability
SessionStateManager.set_checkpoint_available(
    available=True,
    path="/path/to/checkpoint.json",
    timestamp="2024-01-15T10:30:00Z"
)

# Check availability
is_available = SessionStateManager.is_checkpoint_available()
```

#### Large Document Settings

```python
# Configure settings
SessionStateManager.set_large_document_settings(
    sections_per_volume=10,
    total_target_sections=50,
    enable_checkpoint_resume=True
)

# Get settings
sections_per_volume = SessionStateManager.get_sections_per_volume()
total_sections = SessionStateManager.get_total_target_sections()
checkpoint_enabled = SessionStateManager.is_checkpoint_resume_enabled()
```

---

## Exception Classes

**File:** [`utils/exceptions.py`](utils/exceptions.py)

Custom exception classes for error handling.

### Exception Hierarchy

```
EreunaBaseException (base)
├── APIError
│   ├── APITimeoutError
│   ├── APIRateLimitError
│   ├── APIAuthenticationError
│   └── APIPermissionError
├── LLMGenerationError
├── ContentAnalysisError
├── CitationError
├── FileGenerationError
└── WebScrapingError
```

### Classes

#### `EreunaBaseException`

Base exception class for all Ereuna exceptions.

```python
raise EreunaBaseException("Something went wrong", details={"key": "value"})
```

#### `APITimeoutError`

Raised when an API request times out.

```python
raise APITimeoutError(provider="gemini", model="gemini-2.5-flash", timeout=60)
```

#### `APIRateLimitError`

Raised when API rate limit is exceeded.

```python
raise APIRateLimitError(provider="openai", model="gpt-4o")
```

#### `APIAuthenticationError`

Raised when API authentication fails.

```python
raise APIAuthenticationError(provider="anthropic", model="claude-3-opus")
```

#### `APIPermissionError`

Raised when API permission is denied.

```python
raise APIPermissionError(provider="openai", model="gpt-4o")
```

#### `LLMGenerationError`

Raised when LLM content generation fails.

```python
raise LLMGenerationError(
    message="Failed to generate content",
    model="gemini-2.5-flash",
    section="Introduction",
    attempt=1
)
```

#### `ContentAnalysisError`

Raised when content analysis fails.

```python
raise ContentAnalysisError("Failed to analyze content", content="...")
```

#### `CitationError`

Raised when citation generation fails.

```python
raise CitationError("Invalid citation format", source="...")
```

#### `FileGenerationError`

Raised when file generation fails.

```python
raise FileGenerationError("PDF generation failed", file_type="pdf")
```

#### `WebScrapingError`

Raised when web scraping fails.

```python
raise WebScrapingError("Failed to scrape URL", url="https://...")
```

---

## Content Analyzer

**File:** [`utils/content_analyzer.py`](utils/content_analyzer.py)

Analyzes research content for readability, keywords, and other metrics.

### Class: `ContentAnalyzer`

```python
from utils.content_analyzer import ContentAnalyzer

analyzer = ContentAnalyzer()
```

#### Methods

##### `calculate_readability_scores(text: str) -> Dict[str, float]`

Calculates various readability metrics.

```python
scores = analyzer.calculate_readability_scores("Research content...")
# {
#     "flesch_kincaid_grade": 12.5,
#     "flesch_reading_ease": 45.2,
#     "gunning_fog": 14.3,
#     "smog_index": 11.8,
#     "coleman_liau": 13.2,
#     "automated_readability": 11.5
# }
```

##### `extract_keywords(text: str, num_keywords: int = 10) -> List[str]`

Extracts keywords from text using TF-IDF.

```python
keywords = analyzer.extract_keywords(content, num_keywords=10)
# ["machine learning", "neural networks", "deep learning", ...]
```

##### `analyze_content(text: str) -> Dict[str, Any]`

Performs comprehensive content analysis.

```python
analysis = analyzer.analyze_content(text)
# {
#     "readability": {...},
#     "keywords": [...],
#     "sentences": 150,
#     "words": 3000,
#     "characters": 15000
# }
```

---

## Citation Manager

**File:** [`utils/citation_manager.py`](utils/citation_manager.py)

Generates and manages academic citations.

### Class: `CitationManager`

```python
from utils.citation_manager import CitationManager

manager = CitationManager()
```

#### Methods

##### `format_citation(source: Dict[str, str], style: str = "apa") -> str`

Formats a citation in the specified style.

```python
source = {
    "title": "Deep Learning Advances",
    "authors": "Smith, J., & Doe, A.",
    "year": "2024",
    "url": "https://example.com/paper"
}

citation = manager.format_citation(source, style="apa")
# "Smith, J., & Doe, A. (2024). Deep Learning Advances. https://example.com/paper"
```

| Style     | Description     |
| --------- | --------------- |
| `apa`     | APA 7th edition |
| `mla`     | MLA 9th edition |
| `chicago` | Chicago style   |
| `harvard` | Harvard style   |
| `ieee`    | IEEE style      |

##### `generate_bibliography(sources: List[Dict], style: str = "apa") -> str`

Generates a formatted bibliography.

```python
bibliography = manager.generate_bibliography(sources, style="apa")
```

##### `extract_sources_from_text(text: str) -> List[Dict]`

Extracts potential sources from text.

```python
sources = manager.extract_sources_from_text(text)
```

---

## Web Scraper

**File:** [`utils/web_scraper.py`](utils/web_scraper.py)

Scrapes and extracts content from web pages.

### Class: `WebScraper`

```python
from utils.web_scraper import WebScraper

scraper = WebScraper()
```

#### Methods

##### `scrape(url: str) -> Optional[str]`

Scrapes content from a URL.

```python
content = scraper.scrape("https://example.com/article")
```

##### `scrape_multiple(urls: List[str]) -> List[Dict]`

Scrapes multiple URLs concurrently.

```python
results = scraper.scrape_multiple([
    "https://example.com/article1",
    "https://example.com/article2"
])
# [{"url": "...", "content": "...", "success": True}, ...]
```

##### `extract_main_content(html: str) -> str`

Extracts main content from HTML.

```python
content = scraper.extract_main_content(html)
```

---

## Notes Manager

**File:** [`utils/notes_manager.py`](utils/notes_manager.py)

Manages research notes with markdown support.

### Class: `NotesManager`

```python
from utils.notes_manager import NotesManager

manager = NotesManager()
```

#### Methods

##### `save_notes(notes: str, topic: str) -> str`

Saves notes to a file.

```python
filepath = manager.save_notes("# Notes\nContent...", "machine_learning")
```

##### `load_notes(filepath: str) -> str`

Loads notes from a file.

```python
notes = manager.load_notes(filepath)
```

##### `export_notes_html(notes: str) -> str`

Exports notes as HTML.

```python
html = manager.export_notes_html(notes)
```

---

## Template Manager

**File:** [`utils/template_manager.py`](utils/template_manager.py)

Manages document templates.

### Class: `TemplateManager`

```python
from utils.template_manager import TemplateManager

manager = TemplateManager()
```

#### Methods

##### `get_template(template_name: str) -> Optional[Dict]`

Retrieves a template by name.

```python
template = manager.get_template("scientific_research")
```

##### `list_templates() -> List[str]`

Lists all available templates.

```python
templates = manager.list_templates()
# ["scientific_research", "business_report", "literary_analysis", ...]
```

##### `apply_template(template_name: str, **kwargs) -> Dict`

Applies a template with provided data.

```python
document = manager.apply_template(
    "scientific_research",
    title="AI Research",
    author="John Doe",
    content="..."
)
```

#### Available Templates

| Template              | Description                      |
| --------------------- | -------------------------------- |
| `scientific_research` | Scientific research paper format |
| `business_report`     | Business report format           |
| `literary_analysis`   | Literary analysis format         |
| `learning_approach`   | Educational content format       |
| `custom`              | Custom document format           |

---

## Research Generator

**File:** [`utils/research_generator.py`](utils/research_generator.py)

Core module for generating research reports.

### Class: `ResearchGenerator`

```python
from utils.research_generator import ResearchGenerator

generator = ResearchGenerator(llm_client_manager, prompt_manager)
```

#### Methods

##### `generate_research(topic: str, keywords: str, questions: str, **kwargs) -> Dict`

Generates a complete research report.

```python
research = generator.generate_research(
    topic="Machine Learning",
    keywords="neural networks, deep learning",
    questions="What is deep learning?",
    num_sections=10,
    model_name="gemini-2.5-flash"
)
# {
#     "sections": {...},
#     "executive_summary": "...",
#     "bibliography": [...],
#     ...
# }
```

##### `generate_section(section_name: str, **kwargs) -> str`

Generates a single research section.

```python
section = generator.generate_section(
    "Introduction",
    topic="Machine Learning",
    keywords="...",
    questions="..."
)
```

---

## Chat Manager

**File:** [`utils/chat_manager.py`](utils/chat_manager.py)

Manages interactive chat sessions about research content.

### Class: `ChatManager`

```python
from utils.chat_manager import ChatManager

manager = ChatManager(llm_client_manager, prompt_manager)
```

#### Methods

##### `is_query_relevant(query: str, research_topic: str) -> bool`

Checks if a query is relevant to the research topic.

```python
is_relevant = manager.is_query_relevant(
    query="How does neural network training work?",
    research_topic="Machine Learning"
)
```

##### `generate_response(research_content: str, query: str) -> str`

Generates a response based on research content.

```python
response = manager.generate_response(
    research_content=section_content,
    query="What are the applications?"
)
```

##### `chat_with_web_search(query: str, scraped_content: str) -> str`

Generates a response using web search results.

```python
response = manager.chat_with_web_search(
    query="Latest AI developments",
    scraped_content=scraped_content
)
```

---

## Modular Exporter

**File:** [`utils/modular_exporter.py`](utils/modular_exporter.py)

Exports research content in modular formats.

### Class: `ModularExporter`

```python
from utils.modular_exporter import ModularExporter

exporter = ModularExporter(export_dir="./exports")
```

#### Methods

##### `export_modular(research_sections: Dict, format: str = "markdown") -> Dict`

Exports research content in modular format.

```python
result = exporter.export_modular(
    research_sections=sections,
    format="markdown"
)
# {
#     "manifest": {...},
#     "files": [...],
#     "master_doc_path": "..."
# }
```

##### `create_master_document(sections: List[Dict]) -> str`

Creates a master document from sections.

```python
master_doc = exporter.create_master_document([
    {"title": "Introduction", "content": "..."},
    {"title": "Methods", "content": "..."}
])
```

---

## Hierarchical Generator

**File:** [`utils/hierarchical_generator.py`](utils/hierarchical_generator.py)

Generates large documents using hierarchical volume structure.

### Class: `HierarchicalGenerator`

```python
from utils.hierarchical_generator import HierarchicalGenerator

generator = HierarchicalGenerator(llm_client_manager, prompt_manager)
```

#### Methods

##### `generate_master_outline(topic: str, keywords: str, num_sections: int = 20) -> List[Dict]`

Generates a master outline for large documents.

```python
outline = generator.generate_master_outline(
    topic="World History",
    keywords="civilization, empires, wars",
    num_sections=50
)
# [{"volume": 1, "title": "Ancient Civilizations", "sections": [...]}, ...]
```

##### `generate_volume(outline: Dict, model_name: str) -> Dict`

Generates content for a single volume.

```python
volume = generator.generate_volume(
    outline=volume_outline,
    model_name="gemini-2.5-flash"
)
```

##### `generate_all_volumes(outline: List[Dict], model_name: str, **kwargs) -> Dict`

Generates content for all volumes.

```python
result = generator.generate_all_volumes(
    outline=master_outline,
    model_name="gemini-2.5-flash",
    show_progress=True
)
```

---

## Document Generators

### PDF Generator

**File:** [`utils/pdf_generator.py`](utils/pdf_generator.py)

Generates PDF documents from research content.

```python
from utils.pdf_generator import PDFGenerator

generator = PDFGenerator()
pdf_bytes = generator.generate(research_data, template="default")
```

### DOCX Generator

**File:** [`utils/docx_generator.py`](utils/docx_generator.py)

Generates Word documents from research content.

```python
from utils.docx_generator import DOCXGenerator

generator = DOCXGenerator()
docx_bytes = generator.generate(research_data)
```

### PowerPoint Generator

**File:** [`utils/powerpoint_generator.py`](utils/powerpoint_generator.py)

Generates PowerPoint presentations from research content.

```python
from utils.powerpoint_generator import PowerPointGenerator

generator = PowerPointGenerator()
pptx_bytes = generator.generate(research_data, slides_per_section=3)
```

---

## Usage Examples

### Complete Research Workflow

```python
from utils.llm_client_manager import LLMClientManager
from utils.prompt_manager import PromptManager
from utils.research_generator import ResearchGenerator
from utils.content_analyzer import ContentAnalyzer

# Initialize components
api_keys = {"gemini": "your-api-key"}
client_manager = LLMClientManager(api_keys)
prompt_manager = PromptManager()

# Generate research
generator = ResearchGenerator(client_manager, prompt_manager)
research = generator.generate_research(
    topic="Climate Change Impact on Agriculture",
    keywords="global warming, food security, crop yields",
    questions="What are the main impacts? How can we adapt?",
    num_sections=10,
    model_name="gemini-2.5-flash"
)

# Analyze content
analyzer = ContentAnalyzer()
for title, content in research["sections"].items():
    scores = analyzer.calculate_readability_scores(content)
    print(f"{title}: Flesch-Kincaid Grade = {scores['flesch_kincaid_grade']}")
```

### Chat Interaction

```python
from utils.llm_client_manager import LLMClientManager
from utils.prompt_manager import PromptManager
from utils.chat_manager import ChatManager

# Initialize
client_manager = LLMClientManager(api_keys)
prompt_manager = PromptManager()
chat_manager = ChatManager(client_manager, prompt_manager)

# Check relevance
is_relevant = chat_manager.is_query_relevant(
    query="What are the economic impacts?",
    research_topic="Climate Change and Agriculture"
)

if is_relevant:
    response = chat_manager.generate_response(
        research_content=research["sections"]["Economic Impact"],
        query="What are the economic impacts?"
    )
```

### Export to Multiple Formats

```python
from utils.pdf_generator import PDFGenerator
from utils.docx_generator import DOCXGenerator
from utils.powerpoint_generator import PowerPointGenerator

# Generate documents
pdf_bytes = PDFGenerator().generate(research_data)
docx_bytes = DOCXGenerator().generate(research_data)
pptx_bytes = PowerPointGenerator().generate(research_data)

# Save to files
with open("report.pdf", "wb") as f:
    f.write(pdf_bytes)

with open("report.docx", "wb") as f:
    f.write(docx_bytes)

with open("presentation.pptx", "wb") as f:
    f.write(pptx_bytes)
```

---

## Error Handling

All modules use Ereuna's custom exception classes. Here's a comprehensive error handling pattern:

```python
from utils.exceptions import (
    LLMGenerationError,
    APIRateLimitError,
    ContentAnalysisError,
    FileGenerationError
)

try:
    # Your code here
    research = generator.generate_research(...)
except LLMGenerationError as e:
    print(f"Generation failed: {e.message}")
    print(f"Model: {e.model}, Section: {e.section}")
except APIRateLimitError as e:
    print(f"Rate limited. Provider: {e.provider}")
    # Implement backoff logic
except ContentAnalysisError as e:
    print(f"Analysis failed: {e.message}")
except FileGenerationError as e:
    print(f"File generation failed: {e.message}")
    print(f"File type: {e.file_type}")
```

---

## Configuration

### Environment Variables

| Variable        | Description                                         | Default      |
| --------------- | --------------------------------------------------- | ------------ |
| `STREAMLIT_ENV` | Environment mode (`development` or `production`)    | `production` |
| `LOG_LEVEL`     | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO`       |

### Streamlit Secrets

Create a `.streamlit/secrets.toml` file:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
OPENAI_API_KEY = "your-openai-api-key"
ANTHROPIC_API_KEY = "your-anthropic-api-key"
DEFAULT_LLM_MODEL = "gemini-2.5-flash"

[models.gemini]
gemini-2.5-flash = { display_name = "Gemini 2.5 Flash", provider = "gemini" }
gemini-1.5-pro = { display_name = "Gemini 1.5 Pro", provider = "gemini" }

[models.openai]
gpt-4o = { display_name = "GPT-4o", provider = "gpt" }

[models.anthropic]
claude-3-5-sonnet-20241022 = { display_name = "Claude 3.5 Sonnet", provider = "claude" }
```
