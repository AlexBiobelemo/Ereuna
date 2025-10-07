# Automated Research Report Generator

This Streamlit application leverages various AI models and advanced utilities to generate comprehensive research reports, perform quality analysis, and enhance research capabilities.

## Features

The application includes the following key features:

### 1. Multiple AI Models
- **Provider Selection:** Choose between Google Gemini, OpenAI (GPT), and Anthropic (Claude) as your AI model provider.
- **Model Selection:** Select specific models within each provider (e.g., `gemini-1.5-flash`, `gpt-4o`, `claude-3-opus-20240229`).
- **Flexible API Key Management:** API keys are loaded from `.streamlit/secrets.toml` for security, with a fallback to direct input in the UI if not found.

### 2. Quality & Intelligence
- **Smart Summarization:** Generate a concise executive summary of the entire research report.
- **Table Summary Generation:** Automatically generate summaries for tables found in research content.

### 3. Enhanced Research Capabilities
- **Web Scraping Integration:** Perform web research to find academic sources and scrape their content (HTML and PDF) using `googlesearch-python`.
- **Citation Management:** Auto-generate bibliographies in popular academic styles (APA, MLA, Chicago) based on the found sources.
- **Custom Templates:** Utilize pre-built templates for different research types (Scientific, Business, Literary) to structure your reports, pre-fill system prompts, and suggest keywords/questions.
- **Deep Research Option:** Conduct in-depth research by allowing the AI to ask clarifying questions and refine its understanding of the topic.

## Setup and Installation

To get this application up and running, follow these steps:

### 1. Clone the Repository
```bash
git clone https://github.com/AlexBiobelemo/Ereuna/
cd Project-Geo
```

### 2. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
.\venv\Scripts\activate # On Windows
source venv/bin/activate # On macOS/Linux
```

### 3. Install Dependencies
The application relies on several Python libraries. Install them using `pip`:
```bash
pip install -r requirements.txt
```
The `requirements.txt` file contains:
```
streamlit>=1.28.0
google-generativeai>=0.3.0
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
```

### 4. Configure API Keys
The application requires API keys for the AI models you wish to use. For security, it's recommended to store these in a `.streamlit/secrets.toml` file in the root directory of your project.

Create a file named `.streamlit/secrets.toml` and add your API keys:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"
```
Replace `"YOUR_GEMINI_API_KEY"`, `"YOUR_OPENAI_API_KEY"`, and `"YOUR_ANTHROPIC_API_KEY"` with your actual API keys. If a key is not provided in `secrets.toml`, the application will prompt you to enter it in the Streamlit UI.

## How to Run

Once the dependencies are installed and API keys are configured, you can run the Streamlit application:

```bash
streamlit run research.py
```

This command will open the application in your web browser.

## Usage

1.  **Configuration:**
    *   Select your preferred AI Model Provider (Gemini, GPT, Claude) and a specific model.
    *   Ensure your API keys are correctly configured (either in `secrets.toml` or entered directly).
    *   Optionally, select a **Research Template** to pre-configure the system prompt, suggested sections, keywords, and research questions for different report types (e.g., Scientific, Business, Literary).

2.  **Research Configuration:**
    *   Enter the main **Research Topic**.
    *   Provide **Keywords** (comma-separated) to guide the AI.
    *   List **Research Questions** (comma-separated) that the report should address.

3.  **Generate Report:**
    *   Click the "🚀 Generate Research Report" button. The AI will generate content for each section based on your inputs and the selected template.

4.  **Quality & Intelligence:**
    *   After generation, use the "Generate Executive Summary" button in this section.
    *   The executive summary will be displayed in an expandable section.

5.  **Enhanced Research Capabilities:**
    *   Click "Perform Web Research (Academic Sources)" to search for relevant academic papers using real-time Google searches.
    *   For each found source, you can click "Scrape Content from Source" to extract its text.
    *   If academic sources are found, you can then "Generate Bibliography" in your chosen style (APA, MLA, Chicago).

6.  **Export Options:**
    *   Generate and download the report as a PowerPoint presentation, or a plain text file.

## Project Structure

```
.
├── .streamlit/
│   └── secrets.toml          # API keys and secrets (create this file)
├── templates/
│   ├── business_report.json  # Template for business reports
│   ├── literary_analysis.json# Template for literary analysis
│   └── scientific_research.json # Template for scientific research
├── utils/
│   ├── __init__.py
│   ├── citation_manager.py   # Handles bibliography generation
│   ├── content_analyzer.py   # Handles readability, keywords, plagiarism, fact-checking
│   ├── notes_manager.py      # Manages saving/loading research notes
│   ├── powerpoint_generator.py # Generates PowerPoint presentations
│   ├── research_generator.py # Core AI content generation logic
│   ├── session_state_manager.py # Manages Streamlit session state
│   ├── template_manager.py   # Loads and manages custom templates
│   └── web_scraper.py        # Handles web scraping from URLs
├── research.py               # Main Streamlit application file
└── requirements.txt          # Python dependencies
```

## Contributing

Feel free to fork the repository, open issues, or submit pull requests to improve the application.

## License

This project is open-source and available under the [MIT License](LICENSE).
