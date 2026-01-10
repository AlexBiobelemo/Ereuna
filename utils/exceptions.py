"""
Custom exceptions for the Ereuna research application.
Provides standardized error handling with error codes and consistent patterns.
"""


class EreunaError(Exception):
    """Base exception for all Ereuna application errors."""
    
    def __init__(self, message: str, error_code: str = "E000", details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"


class ConfigurationError(EreunaError):
    """Raised when there's a configuration issue (missing API keys, invalid settings, etc.)."""
    
    def __init__(self, message: str, config_key: str = None, details: dict = None):
        super().__init__(message, error_code="C001", details=details)
        self.config_key = config_key


class APIError(EreunaError):
    """Base exception for API-related errors."""
    
    def __init__(self, message: str, provider: str = None, model: str = None, status_code: int = None, details: dict = None):
        details = details or {}
        if provider:
            details["provider"] = provider
        if model:
            details["model"] = model
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, error_code="A000", details=details)
        self.provider = provider
        self.model = model
        self.status_code = status_code


class APITimeoutError(APIError):
    """Raised when an API request times out."""
    
    def __init__(self, provider: str = None, model: str = None, timeout: int = None):
        details = {}
        if timeout:
            details["timeout_seconds"] = timeout
        super().__init__(
            f"API request timed out",
            provider=provider,
            model=model,
            details=details
        )
        self.error_code = "A001"


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, provider: str = None, model: str = None, retry_after: int = None):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(
            f"API rate limit exceeded",
            provider=provider,
            model=model,
            details=details
        )
        self.error_code = "A002"


class APIAuthenticationError(APIError):
    """Raised when API authentication fails (invalid API key, etc.)."""
    
    def __init__(self, provider: str = None, model: str = None):
        super().__init__(
            f"API authentication failed",
            provider=provider,
            model=model
        )
        self.error_code = "A003"


class APIPermissionError(APIError):
    """Raised when API permission is denied."""
    
    def __init__(self, provider: str = None, model: str = None):
        super().__init__(
            f"API permission denied",
            provider=provider,
            model=model
        )
        self.error_code = "A004"


class LLMGenerationError(EreunaError):
    """Raised when LLM generation fails."""
    
    def __init__(self, message: str, model: str = None, section: str = None, attempt: int = None, details: dict = None):
        details = details or {}
        if model:
            details["model"] = model
        if section:
            details["section"] = section
        if attempt:
            details["attempt"] = attempt
        super().__init__(message, error_code="G000", details=details)
        self.model = model
        self.section = section
        self.attempt = attempt


class ContentExtractionError(EreunaError):
    """Raised when content extraction from a source fails."""
    
    def __init__(self, message: str, source_type: str = None, url: str = None, details: dict = None):
        details = details or {}
        if source_type:
            details["source_type"] = source_type
        if url:
            details["url"] = url
        super().__init__(message, error_code="E001", details=details)
        self.source_type = source_type
        self.url = url


class WebSearchError(EreunaError):
    """Raised when web search fails."""
    
    def __init__(self, message: str, query: str = None, num_results: int = None, details: dict = None):
        details = details or {}
        if query:
            details["query"] = query
        if num_results:
            details["num_results"] = num_results
        super().__init__(message, error_code="S000", details=details)
        self.query = query
        self.num_results = num_results


class DocumentGenerationError(EreunaError):
    """Raised when document generation fails."""
    
    def __init__(self, message: str, document_type: str = None, output_path: str = None, details: dict = None):
        details = details or {}
        if document_type:
            details["document_type"] = document_type
        if output_path:
            details["output_path"] = output_path
        super().__init__(message, error_code="D000", details=details)
        self.document_type = document_type
        self.output_path = output_path


class ValidationError(EreunaError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: str = None, value: any = None, details: dict = None):
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, error_code="V000", details=details)
        self.field = field
        self.value = value
