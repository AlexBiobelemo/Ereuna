# Automated Research Report Generator (Ereuna)

A powerful Streamlit application that leverages multiple AI models (Google Gemini, OpenAI GPT, Anthropic Claude) to generate comprehensive research reports with advanced features including multi-volume document generation, interactive chatbot, and multiple export formats.

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Template System](#template-system)
- [Advanced Features](#advanced-features)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### 🤖 Multi-Model AI Support

- **Google Gemini** - Flash and Pro models
- **OpenAI GPT** - GPT-4o, GPT-3.5 Turbo, and future models
- **Anthropic Claude** - Claude 3 Opus, Sonnet, and variants
- Seamless switching between providers
- Unified API interface via [`LLMClientManager`](utils/llm_client_manager.py:12)

### 📚 Research Generation

- **Standard Reports** - Generate structured research reports with customizable sections
- **Hierarchical Generation** - Create large documents (2000+ pages) organized into volumes
- **Checkpoint Resume** - Save progress and resume interrupted generations
- **Contextual Content** - Each section builds on previous content for coherent flow

### 📝 Quality & Intelligence

- **Executive Summary** - Auto-generated concise summaries
- **Readability Analysis** - Multiple readability metrics (Flesch, Gunning Fog, Coleman-Liau, etc.)
- **Table Summarization** - Extract and summarize tabular data
- **Citation Management** - APA, MLA, Chicago, Harvard formats

### 💬 Interactive Chatbot

- Research-aware Q&A based on generated content
- Web search fallback for additional context
- Conversation memory and history

### 🌐 Web Research

- **Academic Search** - Find scholarly sources via Google
- **Content Scraping** - Extract text from HTML and PDF sources
- **Auto-Citations** - Generate bibliographies from found sources

### 📤 Export Options

- **DOCX** - Microsoft Word format with full formatting
- **PPTX** - PowerPoint presentations
- **TXT** - Plain text notes
- **Modular Export** - Individual volumes or combined master document
- **ZIP Archives** - Bundle all exports

---

## Architecture Overview

```
Ereuna/
├── research.py                 # Main Streamlit application
├── utils/                      # Utility modules
│   ├── research_generator.py   # Core report generation
│   ├── chat_manager.py         # Chatbot functionality
│   ├── hierarchical_generator.py # Large document generation
│   ├── modular_exporter.py     # Multi-volume export
│   ├── config_manager.py       # API configuration
│   ├── prompt_manager.py       # Prompt templates
│   ├── template_manager.py     # Research templates
│   ├── docx_generator.py       # Word export
│   ├── powerpoint_generator.py # PPT export
│   ├── web_scraper.py          # Web research
│   ├── citation_manager.py     # Citation handling
│   ├── content_analyzer.py     # Readability analysis
│   ├── session_state_manager.py # State persistence
│   ├── llm_client_manager.py   # LLM client factory
│   ├── llm_call_utils.py       # API call utilities
│   ├── exceptions.py           # Custom exceptions
│   └── notes_manager.py        # Notes management
├── templates/                  # Research templates
│   ├── scientific_research.json
│   ├── business_report.json
│   ├── literary_analysis.json
│   └── custom.json
├── Ereuna/prompts/            # Prompt templates
│   ├── research_section.json
│   ├── executive_summary.json
│   ├── chat_response.json
│   └── ...
└── .streamlit/                # Streamlit config
    └── secrets.toml           # API keys
```

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/AlexBiobelemo/Ereuna/
cd Ereuna

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your API keys

# Run the application
streamlit run research.py
```

---

## Installation

### Prerequisites

- Python 3.8+
- pip package manager
- API keys for at least one LLM provider

### Dependencies

```txt
streamlit>=1.28.0
google-genai>=0.3.0
python-docx>=0.8.11
fpdf2>=2.7.6
python-pptx>=0.6.21
Pillow>=10.0.0
openai>=1.0.0
anthropic>=0.3.0
pypdf>=3.0.0
requests>=2.31.0
beautifulsoup4>=4.12.2
textstat>=0.7.0
googlesearch-python>=1.2.0
markdown>=3.4.4
```

---

## Configuration

### API Keys Configuration

Create `.streamlit/secrets.toml` in the project root:

```toml
# .streamlit/secrets.toml

# API Keys (at least one required)
GEMINI_API_KEY = "your-gemini-api-key"
OPENAI_API_KEY = "your-openai-api-key"
ANTHROPIC_API_KEY = "your-anthropic-api-key"

# Default model
DEFAULT_LLM_MODEL = "gemini-2.5-flash"

# Model Configuration
[models.gemini]
gemini-2.5-flash = { display_name = "Gemini 2.5 Flash", provider = "gemini" }
gemini-2.5-pro = { display_name = "Gemini 2.5 Pro", provider = "gemini" }

[models.openai]
gpt-4o = { display_name = "GPT-4o", provider = "gpt" }
gpt-3.5-turbo = { display_name = "GPT-3.5 Turbo", provider = "gpt" }

[models.anthropic]
claude-3-5-sonnet-20241022 = { display_name = "Claude 3.5 Sonnet", provider = "claude" }
claude-3-opus-20240229 = { display_name = "Claude 3 Opus", provider = "claude" }
```

### Environment Variables

```bash
# Development mode (uses fallback models if secrets not configured)
export STREAMLIT_ENV=development
```

---

## Usage Guide

### 1. Configuration Panel

Select your preferred AI model and provider from the sidebar.

### 2. Research Setup

Enter your research parameters:

- **Topic**: Main research subject
- **Keywords**: Comma-separated keywords for focus
- **Research Questions**: Specific questions to address
- **Template**: Choose from pre-built templates (Scientific, Business, Literary)

### 3. Large Document Settings

For extensive research (200+ pages):

```
Enable Hierarchical Generation
├── Sections per Volume: 5-20 (default: 10)
├── Total Sections: 10-100 (default: 20)
└── Enable Checkpoint Resume: Save progress for recovery
```

### 4. Generate Report

Click "🚀 Generate Research Report" to begin. The AI will:

1. Generate content for each section
2. Build context from previous sections
3. Store results for download

### 5. Quality Analysis

After generation, access:

- **Executive Summary** - Concise overview
- **Readability Scores** - Multiple metrics
- **Table Summaries** - Data insights

### 6. Export Options

Download your research in multiple formats:

| Format | Features                            |
| ------ | ----------------------------------- |
| DOCX   | Full formatting, tables, hyperlinks |
| PPTX   | Professional presentation slides    |
| TXT    | Plain text for easy editing         |

---

## API Documentation

### Core Classes

#### [`ResearchGenerator`](utils/research_generator.py:29)

Main class for generating research report sections.

```python
from utils.research_generator import ResearchGenerator

generator = ResearchGenerator(
    topic="AI in Education",
    keywords=["AI", "education", "learning"],
    research_questions=["How does AI personalize learning?"],
    config_manager=config_manager,
    prompt_manager=prompt_manager,
    model_name="gemini-2.5-flash"
)

# Generate a section
section = generator.generate_section(
    section_data={"title": "Introduction", "prompt": "Introduce the topic"},
    previous_sections_content=""
)

# Generate executive summary
summary = generator.generate_summary(full_report_content)
```

#### [`HierarchicalGenerator`](utils/hierarchical_generator.py:222)

Generates large multi-volume research documents.

```python
from utils.hierarchical_generator import HierarchicalGenerator

generator = HierarchicalGenerator(
    topic="Comprehensive AI Research",
    keywords=["AI", "ML", "deep learning"],
    research_questions=["What are the latest AI developments?"],
    config_manager=config_manager,
    prompt_manager=prompt_manager,
    model_name="gemini-2.5-flash",
    sections_per_volume=10
)

# Generate complete document
result = generator.generate(
    num_sections=50,  # 50 sections = 5 volumes
    use_checkpoint=True,
    progress_callback=lambda p: print(f"Volume {p['current_volume']}/{p['total_volumes']}")
)

# Access results
print(result['total_volumes'])  # e.g., 5
print(result['volume_contents'])  # Dict of volume -> sections
```

#### [`ChatManager`](utils/chat_manager.py:28)

Interactive chatbot for Q&A about research.

```python
from utils.chat_manager import ChatManager

chatbot = ChatManager(
    config_manager=config_manager,
    prompt_manager=prompt_manager,
    model_name="gemini-2.5-flash",
    research_topic="AI in Education"
)

# Load research content
chatbot.load_research_content({
    "Introduction": "AI is transforming education...",
    "Results": "Studies show improved learning outcomes..."
})

# Generate response
response = chatbot.generate_chat_response(
    "What are the main benefits of AI in education?"
)
```

#### [`ModularExporter`](utils/modular_exporter.py:65)

Export research as individual volumes or master document.

```python
from utils.modular_exporter import ModularExporter, create_modular_exporter

exporter = create_modular_exporter(
    topic="AI Research",
    output_dir="exports",
    include_toc=True,
    include_cover_page=True,
    cross_reference_volumes=True
)

# Export individual volumes
volumes_data = {
    1: {"Introduction": "...", "Background": "..."},
    2: {"Methodology": "...", "Results": "..."}
}
volume_titles = {1: "Foundations", 2: "Analysis"}

exporter.export_all_volumes(volumes_data, volume_titles)

# Create master document
master_path = exporter.create_master_document(
    volumes_data,
    volume_titles,
    master_outline=[...]
)

# Create ZIP archive
zip_path = exporter.create_zip_archive()
```

### Utility Modules

#### [`ConfigManager`](utils/config_manager.py:8)

Singleton for managing API configurations.

```python
config = ConfigManager()
api_keys = config.get_api_keys()
models = config.get_available_models()
default_model = config.get_default_model()
```

#### [`PromptManager`](utils/prompt_manager.py:8)

Manages and formats prompt templates.

```python
prompt_mgr = PromptManager()
template = prompt_mgr.get_template("research_section")
formatted = prompt_mgr.format_prompt(
    "research_section",
    section_name="Introduction",
    topic="AI",
    keywords="AI, ML",
    research_questions="What is AI?"
)
```

#### [`SessionStateManager`](utils/session_state_manager.py:7)

Persists Streamlit session state.

```python
state = SessionStateManager
state.initialize_state()
state.set_value('research_generated', True)
state.store_research_data(sections, topic, keywords, questions, model_name)
```

---

## Template System

### Research Templates

Located in `templates/` directory, JSON files define research structure.

```json
{
    "name": "Scientific Research",
    "description": "Template for scientific research papers",
    "default_topic": "",
    "keywords_suffix": "study, analysis, methodology",
    "questions_prefix": "What methods were used?",
    "sections": [
        {"title": "Abstract", "prompt": "Provide a brief summary", "word_count": 250},
        {"title": "Introduction", "prompt": "Introduce the research topic", "word_count": 500},
        {"title": "Literature Review", "prompt": "Review existing literature", "word_count": 800},
        {"title": "Methodology", "prompt": "Describe research methods", "word_count": 600},
        {"title": "Results", "prompt": "Present findings", "word_count": 700},
        {"title": "Discussion", "prompt": "Analyze results", "word_count": 800},
        {"title": "Conclusion", "prompt": "Summarize conclusions", "word_count": 400}
    ]
}
```

### Prompt Templates

Located in `Ereuna/prompts/` directory.

| Template                   | Purpose                  |
| -------------------------- | ------------------------ |
| `research_section.json`    | Generate report sections |
| `executive_summary.json`   | Create summaries         |
| `chat_response.json`       | Chatbot responses        |
| `relevance_check.json`     | Check query relevance    |
| `web_search_response.json` | Web search answers       |
| `table_summary.json`       | Summarize tables         |

---

## Advanced Features

### Checkpoint Resume

For long-running generations, enable checkpoint saving:

```python
checkpoint_manager = CheckpointManager(checkpoint_dir="checkpoints")
checkpoint = checkpoint_manager.load_checkpoint(topic)

if checkpoint:
    # Resume from checkpoint
    generator.resume_from_checkpoint(checkpoint)
```

### Content Analysis

```python
from utils.content_analyzer import ContentAnalyzer

analyzer = ContentAnalyzer(config_manager=config_manager)

# Readability metrics
scores = analyzer.analyze_readability(text)
# Returns: Flesch Reading Ease, Gunning Fog, Coleman-Liau, etc.

# External checks (requires API keys)
results = analyzer.perform_external_checks(text)
# Plagiarism and fact-checking (placeholder)
```

### Citation Management

```python
from utils.citation_manager import CitationManager, Citation

manager = CitationManager()

# Add citation
citation = Citation(
    title="AI in Education",
    authors=["Smith, John"],
    publication_date="2024-01-15",
    publisher="Academic Press",
    url="https://example.com"
)
manager.add_citation(citation)

# Generate in various formats
apa = manager.generate_citation(citation, style="apa")
mla = manager.generate_citation(citation, style="mla")

# Reference list
refs = manager.generate_reference_list(style="apa")

# Export
bibtex = manager.export_citations(format="bibtex")
```

### PowerPoint Generation

```python
from utils.powerpoint_generator import PowerpointGenerator

ppt = PowerpointGenerator(theme="professional")

# Create slides
ppt.create_title_slide("AI Research", "Comprehensive Analysis", author="Author")

for i, (title, content) in enumerate(sections.items()):
    ppt.create_section_slide(title, section_number=i+1)
    ppt.create_content_slide(title, content[:500])

ppt.create_conclusion_slide("Summary", ["Key Point 1", "Key Point 2"])
ppt.save("research_presentation.pptx")
```

---

## Project Structure

```
Ereuna/
├── .streamlit/
│   └── secrets.toml              # API keys (create from example)
├── Ereuna/
│   └── prompts/                  # LLM prompt templates
│       ├── research_section.json
│       ├── executive_summary.json
│       ├── chat_response.json
│       ├── relevance_check.json
│       ├── web_search_response.json
│       └── table_summary.json
├── templates/                    # Research templates
│   ├── scientific_research.json
│   ├── business_report.json
│   ├── literary_analysis.json
│   └── custom.json
├── utils/                        # Core modules
│   ├── __init__.py
│   ├── research_generator.py    # Main generator
│   ├── hierarchical_generator.py # Large docs
│   ├── chat_manager.py          # Chatbot
│   ├── modular_exporter.py      # Multi-volume export
│   ├── config_manager.py        # API config
│   ├── prompt_manager.py        # Prompts
│   ├── template_manager.py      # Templates
│   ├── docx_generator.py        # DOCX export
│   ├── powerpoint_generator.py  # PPT export
│   ├── web_scraper.py           # Web research
│   ├── citation_manager.py      # Citations
│   ├── content_analyzer.py      # Analysis
│   ├── session_state_manager.py # State
│   ├── llm_client_manager.py    # LLM clients
│   ├── llm_call_utils.py        # API calls
│   ├── exceptions.py            # Custom errors
│   └── notes_manager.py         # Notes
├── exports/                      # Generated files
├── checkpoints/                  # Resume checkpoints
├── research.py                   # Main app
├── requirements.txt              # Dependencies
├── README.md                     # This file
├── Features.md                   # Features documentation
└── DSA_Docs.md                   # Design docs
```

---

## Error Handling

Custom exceptions provide detailed error information:

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
    print(f"Request timed out: {e}")
except APIAuthenticationError as e:
    print(f"Invalid API key: {e}")
except LLMGenerationError as e:
    print(f"Generation failed: {e}")
except ValidationError as e:
    print(f"Invalid input: {e}")
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a Pull Request

### Development Setup

```bash
# Set development environment
export STREAMLIT_ENV=development

# Run with auto-reload
streamlit run research.py --runner.enablerepoqueryrunner=true
```

---

## License

None

---

## Support

For issues and feature requests, please open a GitHub issue.

---

**Author**: AlexAlagoaBiobelemo  
**Version**: 1.0.0  
**Last Updated**: January 2025
