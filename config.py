"""Configuration management for Amazon Scraper application."""
import os
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # API Configuration
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    SERPAPI_BASE_URL: str = "https://serpapi.com/search"

    # Request Configuration
    REQUEST_TIMEOUT: int = 30  # seconds
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0  # exponential backoff multiplier

    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 10

    # Pagination
    PRODUCTS_PER_PAGE: int = 48  # Amazon typically shows 48 products per page
    MAX_PAGES: int = 5

    # Data Quality
    MIN_BRAND_LENGTH: int = 1
    MAX_BRAND_LENGTH: int = 50

    # Currency symbols by domain
    CURRENCY_MAP: Dict[str, str] = {
        "amazon.com": "$",
        "amazon.co.uk": "£",
        "amazon.de": "€",
        "amazon.fr": "€",
        "amazon.ca": "C$",
        "amazon.es": "€",
        "amazon.it": "€",
        "amazon.co.jp": "¥",
        "amazon.com.au": "A$",
        "amazon.in": "₹",
        "amazon.com.br": "R$",
        "amazon.com.mx": "MX$"
    }

    # Supported Amazon domains
    SUPPORTED_DOMAINS: list = [
        "amazon.com",
        "amazon.co.uk",
        "amazon.de",
        "amazon.fr",
        "amazon.ca",
        "amazon.es",
        "amazon.it",
        "amazon.co.jp",
        "amazon.com.au",
        "amazon.in",
        "amazon.com.br",
        "amazon.com.mx"
    ]

    # Streamlit Configuration
    PAGE_TITLE: str = "Amazon Competitor Analysis"
    PAGE_ICON: str = "📦"
    LAYOUT: str = "wide"

    @classmethod
    def get_currency(cls, domain: str) -> str:
        """Get currency symbol for given Amazon domain."""
        return cls.CURRENCY_MAP.get(domain, "$")

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.SERPAPI_KEY:
            return False
        return True


# Export config instance
config = Config()
