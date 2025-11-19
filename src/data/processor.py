"""Data processing and transformation for Amazon products."""
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from src.data.models import Product
from src.utils.extractors import BrandExtractor

logger = logging.getLogger(__name__)


class ProductProcessor:
    """Process and transform product data from SerpAPI responses."""

    def __init__(self):
        """Initialize product processor."""
        self.brand_extractor = BrandExtractor()

    def process_api_response(
        self,
        api_response: Dict[str, Any],
        include_organic: bool = True,
        include_ads: bool = True
    ) -> List[Product]:
        """
        Process SerpAPI response and extract products.

        Args:
            api_response: Raw API response from SerpAPI
            include_organic: Include organic (non-sponsored) results
            include_ads: Include sponsored results

        Returns:
            List of Product objects
        """
        products = []

        # Process organic results
        if include_organic and "organic_results" in api_response:
            for raw_product in api_response["organic_results"]:
                try:
                    product = self._parse_product(raw_product)
                    if product:
                        # Filter based on sponsored status
                        is_sponsored = product.type == "Sponsored"
                        if (is_sponsored and include_ads) or (not is_sponsored and include_organic):
                            products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to parse product: {e}")
                    continue

        logger.info(f"Processed {len(products)} products from API response")
        return products

    def _parse_product(self, raw_data: Dict[str, Any]) -> Optional[Product]:
        """
        Parse raw product data into Product model.

        Args:
            raw_data: Raw product data from API

        Returns:
            Product object or None if parsing fails
        """
        try:
            # Extract brand
            brand = self.brand_extractor.extract_brand(raw_data)

            # Determine if sponsored
            is_sponsored = raw_data.get("sponsored", False)
            product_type = "Sponsored" if is_sponsored else "Organic"

            # Create product instance
            product = Product(
                type=product_type,
                position=raw_data.get("position"),
                asin=raw_data.get("asin"),
                brand=brand,
                title=raw_data.get("title"),
                price=raw_data.get("extracted_price"),
                old_price=raw_data.get("extracted_old_price"),
                rating=raw_data.get("rating"),
                reviews=raw_data.get("reviews"),
                bought_last_month=raw_data.get("bought_last_month"),
                prime=raw_data.get("prime", False),
                thumbnail=raw_data.get("thumbnail"),
                link=raw_data.get("link_clean") or raw_data.get("link")
            )

            return product

        except Exception as e:
            logger.error(f"Error parsing product: {e}")
            return None

    def filter_products(
        self,
        products: List[Product],
        min_rating: float = 0.0,
        min_reviews: int = 0,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None
    ) -> List[Product]:
        """
        Filter products based on criteria.

        Args:
            products: List of Product objects
            min_rating: Minimum rating (0-5)
            min_reviews: Minimum number of reviews
            max_price: Maximum price (optional)
            min_price: Minimum price (optional)

        Returns:
            Filtered list of Product objects
        """
        filtered = []

        for product in products:
            # Rating filter
            if min_rating > 0:
                if not product.rating or product.rating < min_rating:
                    continue

            # Reviews filter
            if min_reviews > 0:
                if not product.reviews or product.reviews < min_reviews:
                    continue

            # Price filters
            if product.price:
                if max_price and product.price > max_price:
                    continue
                if min_price and product.price < min_price:
                    continue

            filtered.append(product)

        logger.info(f"Filtered {len(products)} products down to {len(filtered)}")
        return filtered

    def to_dataframe(self, products: List[Product]) -> pd.DataFrame:
        """
        Convert list of Product objects to pandas DataFrame.

        Args:
            products: List of Product objects

        Returns:
            DataFrame with product data
        """
        if not products:
            return pd.DataFrame()

        # Convert to dictionaries
        data = [product.model_dump() for product in products]
        df = pd.DataFrame(data)

        # Ensure numeric columns are proper types
        numeric_cols = ["price", "old_price", "rating", "reviews", "discount_pct"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def deduplicate_products(self, products: List[Product]) -> List[Product]:
        """
        Remove duplicate products based on ASIN.

        Args:
            products: List of Product objects

        Returns:
            Deduplicated list of Product objects
        """
        seen_asins = set()
        unique_products = []

        for product in products:
            if product.asin and product.asin in seen_asins:
                logger.debug(f"Skipping duplicate ASIN: {product.asin}")
                continue

            if product.asin:
                seen_asins.add(product.asin)

            unique_products.append(product)

        removed = len(products) - len(unique_products)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate products")

        return unique_products
