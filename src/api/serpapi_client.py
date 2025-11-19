"""SerpAPI client with retry logic and error handling."""
import logging
from typing import Dict, Optional, Any
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SerpAPIError(Exception):
    """Base exception for SerpAPI errors."""
    pass


class SerpAPIQuotaError(SerpAPIError):
    """Exception raised when API quota is exceeded."""
    pass


class SerpAPINetworkError(SerpAPIError):
    """Exception raised for network-related errors."""
    pass


class SerpAPIClient:
    """Client for interacting with SerpAPI with robust error handling."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpAPI client.

        Args:
            api_key: SerpAPI key. If not provided, uses config.SERPAPI_KEY
        """
        self.api_key = api_key or config.SERPAPI_KEY
        if not self.api_key:
            raise ValueError("SERPAPI_KEY must be provided or set in environment")

        self.base_url = config.SERPAPI_BASE_URL
        self.timeout = config.REQUEST_TIMEOUT

    @retry(
        retry=retry_if_exception_type((requests.exceptions.RequestException, SerpAPINetworkError)),
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=config.RETRY_BACKOFF_FACTOR, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to SerpAPI with retry logic.

        Args:
            params: Request parameters

        Returns:
            API response as dictionary

        Raises:
            SerpAPINetworkError: For network-related errors
            SerpAPIQuotaError: When API quota is exceeded
            SerpAPIError: For other API errors
        """
        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            # Check for API errors in response
            if "error" in data:
                error_msg = data["error"]

                # Check for quota/credit errors
                if any(keyword in error_msg.lower() for keyword in ["credit", "quota", "limit"]):
                    raise SerpAPIQuotaError(f"API quota exceeded: {error_msg}")

                raise SerpAPIError(f"API error: {error_msg}")

            return data

        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
            raise SerpAPINetworkError(f"Request timed out after {self.timeout}s") from e

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise SerpAPINetworkError("Failed to connect to SerpAPI") from e

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if e.response.status_code == 429:
                raise SerpAPIQuotaError("Rate limit exceeded") from e
            raise SerpAPIError(f"HTTP error: {e}") from e

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise SerpAPINetworkError(f"Request failed: {e}") from e

    def search_amazon(
        self,
        query: str,
        domain: str = "amazon.com",
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Search Amazon products via SerpAPI.

        Args:
            query: Search query
            domain: Amazon domain (e.g., amazon.com, amazon.co.uk)
            page: Page number (1-indexed)

        Returns:
            API response containing product data

        Raises:
            ValueError: For invalid parameters
            SerpAPIError: For API-related errors
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        if page < 1:
            raise ValueError("Page number must be >= 1")

        if domain not in config.SUPPORTED_DOMAINS:
            raise ValueError(f"Unsupported domain: {domain}")

        params = {
            "engine": "amazon",
            "amazon_domain": domain,
            "k": query.strip(),
            "page": page,
            "api_key": self.api_key
        }

        logger.info(f"Searching Amazon: query='{query}', domain={domain}, page={page}")

        try:
            data = self._make_request(params)
            logger.info(f"Successfully retrieved data for page {page}")
            return data

        except SerpAPIQuotaError:
            logger.error("API quota exceeded")
            raise

        except SerpAPINetworkError:
            logger.error("Network error occurred")
            raise

        except SerpAPIError as e:
            logger.error(f"API error: {e}")
            raise

    def get_account_info(self) -> Dict[str, Any]:
        """
        Get SerpAPI account information (credits, usage, etc.).

        Returns:
            Account information dictionary

        Raises:
            SerpAPIError: For API-related errors
        """
        try:
            response = requests.get(
                "https://serpapi.com/account",
                params={"api_key": self.api_key},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get account info: {e}")
            raise SerpAPIError(f"Failed to retrieve account info: {e}") from e
