"""Utility functions for extracting data from product information."""
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BrandExtractor:
    """Extract brand information from product data."""

    # Common patterns for brand extraction
    BRAND_PATTERNS = [
        # "Brand - Product" or "Brand – Product"
        r"^([^-–]+)(?:\s*[-–]\s*)",
        # "Brand, Product" or "Brand,Product"
        r"^([^,]+),\s*",
        # "Brand by ..."
        r"^(.+?)\s+by\s+",
        # "Brand | Product"
        r"^([^|]+)\|",
    ]

    # Common brand keywords to help identify brands
    BRAND_KEYWORDS = [
        "official", "store", "brand", "genuine", "original",
        "authorized", "certified", "licensed"
    ]

    # Words to exclude from brand names
    EXCLUDE_WORDS = [
        "pack", "set", "bundle", "piece", "pieces", "pcs",
        "compatible", "replacement", "for"
    ]

    def __init__(self):
        """Initialize brand extractor."""
        self.compiled_patterns = [re.compile(pattern) for pattern in self.BRAND_PATTERNS]

    def extract_brand(self, product_data: Dict[str, Any]) -> str:
        """
        Extract brand from product data.

        Args:
            product_data: Raw product data dictionary

        Returns:
            Extracted brand name or "Unknown"
        """
        # Try to get explicit brand field if available
        if "brand" in product_data and product_data["brand"]:
            brand = str(product_data["brand"]).strip()
            if brand and brand.lower() not in ["unknown", "n/a", "none"]:
                return self._clean_brand_name(brand)

        # Try to extract from title
        title = product_data.get("title", "")
        if title:
            brand = self._extract_from_title(title)
            if brand:
                return brand

        return "Unknown"

    def _extract_from_title(self, title: str) -> Optional[str]:
        """
        Extract brand from product title.

        Args:
            title: Product title

        Returns:
            Extracted brand or None
        """
        title = title.strip()

        # Try regex patterns first
        for pattern in self.compiled_patterns:
            match = pattern.match(title)
            if match:
                potential_brand = match.group(1).strip()
                if self._is_valid_brand(potential_brand):
                    return self._clean_brand_name(potential_brand)

        # Fallback: take first 1-3 words as brand
        words = title.split()
        if len(words) >= 2:
            # Try 2 words first
            potential_brand = f"{words[0]} {words[1]}"
            if self._is_valid_brand(potential_brand):
                return self._clean_brand_name(potential_brand)

        # Single word brand
        if len(words) >= 1:
            potential_brand = words[0]
            if self._is_valid_brand(potential_brand):
                return self._clean_brand_name(potential_brand)

        return None

    def _is_valid_brand(self, brand: str) -> bool:
        """
        Check if extracted text is likely a valid brand name.

        Args:
            brand: Potential brand name

        Returns:
            True if likely a valid brand
        """
        if not brand or len(brand) < 2:
            return False

        # Too long, probably not just a brand
        if len(brand) > 50:
            return False

        # Check for excluded words
        brand_lower = brand.lower()
        for exclude_word in self.EXCLUDE_WORDS:
            if exclude_word in brand_lower:
                return False

        # Should not be all numbers
        if brand.replace(" ", "").isdigit():
            return False

        return True

    def _clean_brand_name(self, brand: str) -> str:
        """
        Clean and normalize brand name.

        Args:
            brand: Raw brand name

        Returns:
            Cleaned brand name
        """
        # Remove extra whitespace
        brand = " ".join(brand.split())

        # Remove common suffixes
        brand = re.sub(r'\s+(Store|Official|Shop)$', '', brand, flags=re.IGNORECASE)

        # Capitalize properly
        # Keep if already has mixed case (likely correct)
        if not (brand.isupper() or brand.islower()):
            return brand.strip()

        # Title case for all lowercase or all uppercase
        return brand.strip().title()
