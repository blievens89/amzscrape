"""Data models for Amazon product information."""
from typing import Optional
from pydantic import BaseModel, Field, validator


class Product(BaseModel):
    """Amazon product data model with validation."""

    type: str = Field(..., description="Product type (Sponsored or Organic)")
    position: Optional[int] = Field(None, description="Position in search results")
    asin: Optional[str] = Field(None, description="Amazon Standard Identification Number")
    brand: str = Field(default="Unknown", description="Product brand")
    title: Optional[str] = Field(None, description="Product title")
    price: Optional[float] = Field(None, ge=0, description="Current price")
    old_price: Optional[float] = Field(None, ge=0, description="Previous price (if on sale)")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Product rating (0-5)")
    reviews: Optional[int] = Field(None, ge=0, description="Number of reviews")
    bought_last_month: Optional[int] = Field(None, ge=0, description="Units bought last month")
    prime: bool = Field(default=False, description="Prime eligible")
    thumbnail: Optional[str] = Field(None, description="Product thumbnail URL")
    link: Optional[str] = Field(None, description="Product page URL")
    discount_pct: float = Field(default=0.0, ge=0, le=100, description="Discount percentage")

    @validator("discount_pct", always=True)
    def calculate_discount(cls, v, values):
        """Calculate discount percentage if not provided."""
        if v == 0.0 and values.get("price") and values.get("old_price"):
            price = values["price"]
            old_price = values["old_price"]
            if old_price > 0:
                return round(((old_price - price) / old_price * 100), 1)
        return v

    @validator("title")
    def validate_title(cls, v):
        """Validate and clean title."""
        if v:
            return v.strip()
        return v

    @validator("brand")
    def validate_brand(cls, v):
        """Validate brand name."""
        if v:
            v = v.strip()
            if len(v) > 50:
                return v[:50]
        return v or "Unknown"

    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class SearchRequest(BaseModel):
    """Search request parameters with validation."""

    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    domain: str = Field(default="amazon.com", description="Amazon domain")
    num_pages: int = Field(default=1, ge=1, le=5, description="Number of pages to scrape")
    include_ads: bool = Field(default=True, description="Include sponsored products")
    include_organic: bool = Field(default=True, description="Include organic products")
    min_rating: float = Field(default=0.0, ge=0, le=5, description="Minimum rating filter")
    min_reviews: int = Field(default=0, ge=0, description="Minimum reviews filter")

    @validator("query")
    def validate_query(cls, v):
        """Validate and sanitize search query."""
        # Remove potentially harmful characters
        v = v.strip()
        # Basic sanitization - remove special characters that could cause issues
        dangerous_chars = ["<", ">", "script", "javascript:", "onerror="]
        v_lower = v.lower()
        for char in dangerous_chars:
            if char in v_lower:
                raise ValueError(f"Query contains invalid characters: {char}")
        return v

    @validator("domain")
    def validate_domain(cls, v):
        """Validate Amazon domain."""
        from config import config
        if v not in config.SUPPORTED_DOMAINS:
            raise ValueError(f"Unsupported domain: {v}")
        return v

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
