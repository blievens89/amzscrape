"""Utility functions for formatting data for display."""
import pandas as pd
from typing import Any, Optional
from config import config


class CurrencyFormatter:
    """Format currency values for display."""

    def __init__(self, domain: str = "amazon.com"):
        """
        Initialize currency formatter.

        Args:
            domain: Amazon domain to determine currency symbol
        """
        self.currency_symbol = config.get_currency(domain)

    def format_price(self, price: Optional[float]) -> str:
        """
        Format price with currency symbol.

        Args:
            price: Price value

        Returns:
            Formatted price string
        """
        if price is None or pd.isna(price):
            return "N/A"
        return f"{self.currency_symbol}{price:.2f}"

    def format_discount(self, discount_pct: float) -> str:
        """
        Format discount percentage.

        Args:
            discount_pct: Discount percentage

        Returns:
            Formatted discount string
        """
        if discount_pct is None or pd.isna(discount_pct) or discount_pct <= 0:
            return "-"
        return f"{discount_pct:.1f}%"


class DataFrameFormatter:
    """Format DataFrame for display in Streamlit."""

    def __init__(self, currency_symbol: str = "$"):
        """
        Initialize DataFrame formatter.

        Args:
            currency_symbol: Currency symbol to use
        """
        self.currency_formatter = CurrencyFormatter()
        self.currency_formatter.currency_symbol = currency_symbol

    def format_for_display(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """
        Format DataFrame for display.

        Args:
            df: Input DataFrame
            columns: Columns to include

        Returns:
            Formatted DataFrame
        """
        if df.empty:
            return df

        # Create a copy with selected columns
        display_df = df[columns].copy()

        # Format price columns
        if 'price' in display_df.columns:
            display_df['price'] = display_df['price'].apply(
                self.currency_formatter.format_price
            )

        if 'old_price' in display_df.columns:
            display_df['old_price'] = display_df['old_price'].apply(
                self.currency_formatter.format_price
            )

        # Format discount
        if 'discount_pct' in display_df.columns:
            display_df['discount_pct'] = display_df['discount_pct'].apply(
                self.currency_formatter.format_discount
            )

        # Format prime as checkmark
        if 'prime' in display_df.columns:
            display_df['prime'] = display_df['prime'].apply(
                lambda x: "✓" if x else ""
            )

        # Format ratings
        if 'rating' in display_df.columns:
            display_df['rating'] = display_df['rating'].apply(
                lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
            )

        return display_df


def format_number(value: Any, decimals: int = 0) -> str:
    """
    Format number with thousands separator.

    Args:
        value: Numeric value
        decimals: Number of decimal places

    Returns:
        Formatted number string
    """
    if value is None or pd.isna(value):
        return "N/A"

    try:
        if decimals > 0:
            return f"{float(value):,.{decimals}f}"
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "N/A"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format percentage value.

    Args:
        value: Percentage value (0-100)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:.{decimals}f}%"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
