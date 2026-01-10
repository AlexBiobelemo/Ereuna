import httpx
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
from pypdf import PdfReader
import io
import urllib.parse
from googlesearch import search as google_search # Using a library for Google search
import asyncio # Import asyncio for asynchronous operations

logger = logging.getLogger(__name__)

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
        self.client = httpx.AsyncClient(headers=self.headers, timeout=self.timeout)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - properly closes the HTTP client."""
        await self.aclose()

    async def aclose(self):
        """Closes the HTTP client asynchronously."""
        if hasattr(self, 'client') and self.client:
            await self.client.aclose()
            logger.info("HTTP client closed successfully.")

    async def _fetch_content(self, url: str) -> Optional[bytes]:
        """Fetches raw content from a given URL asynchronously."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()  # Raise an HTTPStatusError for bad responses (4xx or 5xx)
            logger.info(f"Successfully fetched content from {url}")
            return response.content
        except httpx.RequestError as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching content from {url}: {e}")
            return None

    async def scrape_text_from_url(self, url: str) -> Optional[str]:
        """
        Scrapes and extracts readable text content from a given URL asynchronously.
        Handles both HTML and PDF content.
        """
        content = await self._fetch_content(url)
        if not content:
            return None

        # Try to determine content type
        try:
            head_response = await self.client.head(url)
            content_type = head_response.headers.get('Content-Type', '').lower()
        except httpx.RequestError as e:
            logger.warning(f"Could not get content type for {url}: {e}. Proceeding with HTML parse attempt.")
            content_type = '' # Default to empty to force HTML parse fallback

        if 'application/pdf' in content_type:
            return self._extract_text_from_pdf_bytes(content)
        elif 'text/html' in content_type or 'html' in content_type:
            return self._extract_text_from_html(content)
        else:
            logger.warning(f"Unsupported content type for {url}: {content_type}. Attempting HTML parse.")
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
            logger.info("Successfully extracted text from HTML content.")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return None

    def _extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> Optional[str]:
        """Extracts text from PDF content provided as bytes."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            logger.info("Successfully extracted text from PDF bytes.")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF bytes: {e}")
            return None

    async def search_academic_sources(self, query: str, num_results: int = 5, start_page: int = 0) -> List[Dict[str, str]]:
        """
        Searches academic sources using Google Search and returns a list of titles and URLs.
        This method runs the blocking Google search in a thread pool to avoid blocking the event loop.
        
        Args:
            query: The search query string.
            num_results: Number of results to retrieve.
            start_page: Starting page number for pagination (0-based). Each page typically returns 10 results.
                       Use this for deep research workflows to get additional results beyond the first page.
        """
        logger.info(f"Performing academic search for query: {query} (page {start_page}, {num_results} results)")
        results = []
        try:
            # Use googlesearch to get actual search results
            search_query = f"{query} academic paper OR research OR journal"
            
            # Run blocking google_search in a thread pool to avoid blocking the event loop
            # The 'start' parameter enables pagination for deep research workflows
            urls = await asyncio.to_thread(
                lambda: list(google_search(search_query, num_results=num_results, lang='en', start=start_page))
            )
            
            for url in urls:
                if url and not url.startswith("https://accounts.google.com"):
                    parsed_url = urllib.parse.urlparse(url)
                    title = parsed_url.path.split('/')[-1].replace('_', ' ').replace('-', ' ').split('.')[0]
                    if not title:
                        title = url
                    results.append({"title": title.strip(), "url": url})
        except Exception as e:
            logger.error(f"Error during academic search for query '{query}': {e}")
        return results
