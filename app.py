"""Amazon Competitor Analysis - Streamlit Application."""
import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from typing import List

from config import config
from src.api.serpapi_client import SerpAPIClient, SerpAPIError, SerpAPIQuotaError
from src.data.models import SearchRequest, Product
from src.data.processor import ProductProcessor
from src.utils.formatters import CurrencyFormatter, DataFrameFormatter, format_percentage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT
)

st.title(f"{config.PAGE_ICON} {config.PAGE_TITLE}")
st.markdown("Analyse competitor products, pricing, ratings, and ad presence on Amazon")


def get_api_key() -> str:
    """Get API key from Streamlit secrets or config."""
    api_key = st.secrets.get("SERPAPI_KEY") or config.SERPAPI_KEY
    if not api_key:
        st.error("SERPAPI_KEY not found. Add it to Streamlit Cloud settings or .env file.")
        st.stop()
    return api_key


def create_sidebar() -> SearchRequest:
    """Create sidebar with search settings and return validated search request."""
    with st.sidebar:
        st.header("⚙️ Search Settings")

        search_query = st.text_input(
            "Search Term",
            value="wireless earbuds",
            help="What product are you researching?"
        )

        amazon_domain = st.selectbox(
            "Amazon Domain",
            config.SUPPORTED_DOMAINS,
            index=1 if len(config.SUPPORTED_DOMAINS) > 1 else 0
        )

        num_pages = st.slider(
            "Number of pages to scrape",
            1,
            config.MAX_PAGES,
            1,
            help=f"Each page = ~{config.PRODUCTS_PER_PAGE} products"
        )

        st.divider()

        st.subheader("Filters")
        include_ads = st.checkbox("Include Sponsored Products", value=True)
        include_organic = st.checkbox("Include Organic Products", value=True)

        min_rating = st.slider("Minimum Rating", 0.0, 5.0, 0.0, 0.5)
        min_reviews = st.number_input("Minimum Reviews", 0, 10000, 0, 100)

    # Create and validate search request
    try:
        search_request = SearchRequest(
            query=search_query,
            domain=amazon_domain,
            num_pages=num_pages,
            include_ads=include_ads,
            include_organic=include_organic,
            min_rating=min_rating,
            min_reviews=min_reviews
        )
        return search_request
    except ValueError as e:
        st.error(f"Invalid search parameters: {e}")
        st.stop()


def fetch_products(
    client: SerpAPIClient,
    processor: ProductProcessor,
    search_request: SearchRequest
) -> List[Product]:
    """Fetch and process products from SerpAPI."""
    all_products = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for page in range(1, search_request.num_pages + 1):
        status_text.text(f"Fetching page {page} of {search_request.num_pages}...")

        try:
            # Fetch data from API
            api_response = client.search_amazon(
                query=search_request.query,
                domain=search_request.domain,
                page=page
            )

            # Process response
            products = processor.process_api_response(
                api_response,
                include_organic=search_request.include_organic,
                include_ads=search_request.include_ads
            )

            all_products.extend(products)

        except SerpAPIQuotaError as e:
            st.error(f"⚠️ API Quota Exceeded: {e}")
            st.info("Please check your SerpAPI account credits.")
            break

        except SerpAPIError as e:
            st.error(f"❌ API Error on page {page}: {e}")
            if page > 1:
                st.warning("Continuing with partial results...")
                break
            else:
                st.stop()

        except Exception as e:
            logger.exception(f"Unexpected error on page {page}")
            st.error(f"❌ Unexpected error on page {page}: {e}")
            break

        progress_bar.progress(page / search_request.num_pages)

    progress_bar.empty()
    status_text.empty()

    return all_products


def display_summary_metrics(df: pd.DataFrame, currency: str):
    """Display summary metrics."""
    st.subheader("📊 Summary")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Total Products", len(df))

    with col2:
        sponsored_count = len(df[df['type'] == 'Sponsored'])
        st.metric("Sponsored", sponsored_count)

    with col3:
        unique_brands = df['brand'].nunique()
        st.metric("Brands", unique_brands)

    with col4:
        avg_price = df['price'].mean()
        st.metric("Avg Price", f"{currency}{avg_price:.2f}" if pd.notna(avg_price) else "N/A")

    with col5:
        avg_rating = df['rating'].mean()
        st.metric("Avg Rating", f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A")

    with col6:
        prime_pct = (df['prime'].sum() / len(df) * 100) if len(df) > 0 else 0
        st.metric("Prime %", f"{prime_pct:.0f}%")


def display_products_tab(df: pd.DataFrame, formatter: DataFrameFormatter, search_query: str):
    """Display products table tab."""
    st.subheader("Product Listings")

    display_cols = ['type', 'position', 'brand', 'title', 'price', 'rating', 'reviews', 'prime', 'discount_pct']
    display_df = formatter.format_for_display(df, display_cols)

    st.dataframe(display_df, use_container_width=True, height=500)

    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Full Data (CSV)",
        data=csv,
        file_name=f"amazon_{search_query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


def display_brands_tab(df: pd.DataFrame, currency: str):
    """Display brand analysis tab."""
    st.subheader("🏷️ Brand Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Products by Brand**")
        brand_counts = df['brand'].value_counts().head(15)
        st.bar_chart(brand_counts)

    with col2:
        st.write("**Average Price by Brand**")
        brand_avg_price = df.groupby('brand')['price'].mean().sort_values(ascending=False).head(15)
        if len(brand_avg_price) > 0:
            st.bar_chart(brand_avg_price)
        else:
            st.info("Insufficient price data")

    # Brand performance summary
    st.write("**Brand Performance Summary**")
    brand_summary = df.groupby('brand').agg({
        'asin': 'count',
        'price': 'mean',
        'rating': 'mean',
        'reviews': 'sum',
        'prime': 'sum'
    }).round(2)
    brand_summary.columns = ['Products', 'Avg Price', 'Avg Rating', 'Total Reviews', 'Prime Count']
    brand_summary = brand_summary.sort_values('Products', ascending=False).head(20)
    brand_summary['Avg Price'] = brand_summary['Avg Price'].apply(
        lambda x: f"{currency}{x:.2f}" if pd.notna(x) else "N/A"
    )

    st.dataframe(brand_summary, use_container_width=True)


def display_analytics_tab(df: pd.DataFrame):
    """Display analytics tab."""
    st.subheader("📈 Product Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Price Distribution**")
        price_data = df[df['price'].notna()]['price']
        if len(price_data) > 0:
            st.bar_chart(price_data.value_counts().sort_index())
        else:
            st.info("No price data available")

    with col2:
        st.write("**Rating Distribution**")
        rating_data = df[df['rating'].notna()]['rating']
        if len(rating_data) > 0:
            rating_counts = rating_data.value_counts().sort_index()
            st.bar_chart(rating_counts)
        else:
            st.info("No rating data available")

    # Reviews vs Rating scatter
    st.write("**Reviews vs Rating**")
    scatter_df = df[df['rating'].notna() & df['reviews'].notna()][['reviews', 'rating', 'type']]
    if len(scatter_df) > 0:
        st.scatter_chart(scatter_df, x='reviews', y='rating', color='type')
    else:
        st.info("Insufficient data for scatter plot")


def display_ad_analysis_tab(df: pd.DataFrame, currency: str):
    """Display advertising analysis tab."""
    st.subheader("🎯 Advertising Analysis")

    sponsored_df = df[df['type'] == 'Sponsored']
    type_counts = df['type'].value_counts()

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Product Type Distribution**")
        st.bar_chart(type_counts)

    with col2:
        st.write("**Sponsored Products Position**")
        if len(sponsored_df) > 0:
            st.write(f"Total sponsored: {len(sponsored_df)}")
            st.write(f"Avg position: {sponsored_df['position'].mean():.1f}")
            st.write(f"Top 3 positions: {len(sponsored_df[sponsored_df['position'] <= 3])}")
        else:
            st.info("No sponsored products found")

    # Brands with most ads
    st.write("**Brands with Most Sponsored Listings**")
    if len(sponsored_df) > 0:
        sponsored_brands = sponsored_df['brand'].value_counts().head(10)
        st.bar_chart(sponsored_brands)
    else:
        st.info("No sponsored products to analyse")

    # Sponsored products table
    st.write("**Top Sponsored Products**")
    if len(sponsored_df) > 0:
        sponsored_table = sponsored_df[['position', 'brand', 'title', 'price', 'rating', 'reviews']].head(10).copy()
        sponsored_table['price'] = sponsored_table['price'].apply(
            lambda x: f"{currency}{x:.2f}" if pd.notna(x) else "N/A"
        )
        st.dataframe(sponsored_table, use_container_width=True)
    else:
        st.info("No sponsored products to display")


def display_pricing_tab(df: pd.DataFrame, currency: str):
    """Display pricing analysis tab."""
    st.subheader("💰 Pricing Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        min_price = df['price'].min()
        st.metric("Lowest Price", f"{currency}{min_price:.2f}" if pd.notna(min_price) else "N/A")

    with col2:
        max_price = df['price'].max()
        st.metric("Highest Price", f"{currency}{max_price:.2f}" if pd.notna(max_price) else "N/A")

    with col3:
        median_price = df['price'].median()
        st.metric("Median Price", f"{currency}{median_price:.2f}" if pd.notna(median_price) else "N/A")

    # Price by type
    st.write("**Average Price by Product Type**")
    price_by_type = df.groupby('type')['price'].mean().round(2)
    st.bar_chart(price_by_type)

    # Products with discounts
    st.write("**Products with Active Discounts**")
    discount_df = df[df['discount_pct'] > 0][['brand', 'title', 'price', 'old_price', 'discount_pct']].sort_values(
        'discount_pct', ascending=False
    )
    if len(discount_df) > 0:
        discount_display = discount_df.head(10).copy()
        discount_display['price'] = discount_display['price'].apply(
            lambda x: f"{currency}{x:.2f}" if pd.notna(x) else "N/A"
        )
        discount_display['old_price'] = discount_display['old_price'].apply(
            lambda x: f"{currency}{x:.2f}" if pd.notna(x) else "N/A"
        )
        discount_display['discount_pct'] = discount_display['discount_pct'].apply(
            lambda x: f"{x:.1f}%"
        )
        st.dataframe(discount_display, use_container_width=True)
    else:
        st.info("No products with active discounts")

    # Price by brand
    st.write("**Price Range by Top Brands**")
    top_brands = df['brand'].value_counts().head(10).index
    brand_price_data = df[df['brand'].isin(top_brands)].groupby('brand')['price'].agg(
        ['min', 'max', 'mean']
    ).round(2)
    brand_price_data.columns = ['Min Price', 'Max Price', 'Avg Price']
    brand_price_data = brand_price_data.sort_values('Avg Price', ascending=False)

    for col in brand_price_data.columns:
        brand_price_data[col] = brand_price_data[col].apply(
            lambda x: f"{currency}{x:.2f}" if pd.notna(x) else "N/A"
        )

    st.dataframe(brand_price_data, use_container_width=True)


def main():
    """Main application logic."""
    # Get API key
    api_key = get_api_key()

    # Create sidebar and get search parameters
    search_request = create_sidebar()

    # Get currency for domain
    currency = config.get_currency(search_request.domain)

    # Main analysis button
    if st.button("🔍 Analyse Products", type="primary"):
        if not search_request.query:
            st.error("Please enter a search term")
            st.stop()

        # Initialize components
        client = SerpAPIClient(api_key=api_key)
        processor = ProductProcessor()

        # Fetch products
        all_products = fetch_products(client, processor, search_request)

        if not all_products:
            st.warning("No products found. Try different search terms.")
            st.stop()

        # Deduplicate products
        all_products = processor.deduplicate_products(all_products)

        # Apply filters
        filtered_products = processor.filter_products(
            all_products,
            min_rating=search_request.min_rating,
            min_reviews=search_request.min_reviews
        )

        if not filtered_products:
            st.warning("No products match your filter criteria. Try adjusting filters.")
            st.stop()

        # Convert to DataFrame
        df = processor.to_dataframe(filtered_products)

        # Store in session state
        st.session_state.df = df
        st.session_state.currency = currency
        st.session_state.search_query = search_request.query

        # Display summary metrics
        display_summary_metrics(df, currency)

        # Create formatter
        formatter = DataFrameFormatter(currency)

        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Products Table",
            "🏷️ Brands",
            "📈 Analytics",
            "🎯 Ad Analysis",
            "💰 Pricing"
        ])

        with tab1:
            display_products_tab(df, formatter, search_request.query)

        with tab2:
            display_brands_tab(df, currency)

        with tab3:
            display_analytics_tab(df)

        with tab4:
            display_ad_analysis_tab(df, currency)

        with tab5:
            display_pricing_tab(df, currency)

    # Footer
    st.divider()
    st.caption(f"Data from Amazon via SerpAPI | Powered by Streamlit")


if __name__ == "__main__":
    main()
