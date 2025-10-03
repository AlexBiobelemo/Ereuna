import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
from pypdf import PdfReader
import io
import urllib.parse
from googlesearch import search as google_search # Using a library for Google search

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebScraper:
    """
    A utility class for web scraping and extracting text from various sources,
    including HTML pages and PDF documents.
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _fetch_content(self, url: str) -> Optional[bytes]:
        """Fetches raw content from a given URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            logging.info(f"Successfully fetched content from {url}")
            return response.content
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching content from {url}: {e}")
            return None

    def scrape_text_from_url(self, url: str) -> Optional[str]:
        """
        Scrapes and extracts readable text content from a given URL.
        Handles both HTML and PDF content.
        """
        content = self._fetch_content(url)
        if not content:
            return None

        # Try to determine content type
        content_type = requests.head(url, headers=self.headers, timeout=self.timeout).headers.get('Content-Type', '').lower()

        if 'application/pdf' in content_type:
            return self._extract_text_from_pdf_bytes(content)
        elif 'text/html' in content_type or 'html' in content_type:
            return self._extract_text_from_html(content)
        else:
            logging.warning(f"Unsupported content type for {url}: {content_type}. Attempting HTML parse.")
            return self._extract_text_from_html(content) # Fallback to HTML parse

    def _extract_text_from_html(self, html_content: bytes) -> Optional[str]:
        """Extracts readable text from HTML content."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script, style, and other non-text elements
            for script in soup(["script", "style", "header", "footer", "nav", "form"]):
                script.extract()
            text = soup.get_text()
            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            logging.info("Successfully extracted text from HTML content.")
            return text
        except Exception as e:
            logging.error(f"Error extracting text from HTML: {e}")
            return None

    def _extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> Optional[str]:
        """Extracts text from PDF content provided as bytes."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            logging.info("Successfully extracted text from PDF bytes.")
            return text
        except Exception as e:
            logging.error(f"Error extracting text from PDF bytes: {e}")
            return None

    def search_academic_sources(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Searches academic sources using Google Search and returns a list of titles and URLs.
        """
        logging.info(f"Performing academic search for query: {query}")
        results = []
        try:
            # Use googlesearch to get actual search results
            # Limiting to academic-focused domains might be beneficial, e.g., site:.edu OR site:.org OR site:.ac.uk
            search_query = f"{query} academic paper OR research OR journal"
            for url in google_search(search_query, num_results=num_results, lang='en'):
                if url and not url.startswith("https://accounts.google.com"): # Filter out Google account links
                    # Attempt to get a title from the URL or a simplified version
                    parsed_url = urllib.parse.urlparse(url)
                    title = parsed_url.path.split('/')[-1].replace('_', ' ').replace('-', ' ').split('.')[0]
                    if not title:
                        title = url # Fallback if no clear title from path
                    results.append({"title": title.strip(), "url": url})
        except Exception as e:
            logging.error(f"Error during academic search for query '{query}': {e}")
        return results
