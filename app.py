import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import json

st.set_page_config(
    page_title="Amazon Competitor Analysis",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Amazon Competitor Product Analysis")
st.markdown("Analyse competitor products, pricing, ratings, and ad presence on Amazon")

# Get API key from secrets
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY")

if not SERPAPI_KEY:
    st.error("SERPAPI_KEY not found in secrets. Add it to Streamlit Cloud settings.")
    st.stop()

# Sidebar inputs
with st.sidebar:
    st.header("⚙️ Search Settings")
    
    search_query = st.text_input("Search Term", value="wireless earbuds", help="What product are you researching?")
    
    amazon_domain = st.selectbox(
        "Amazon Domain",
        ["amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr", "amazon.ca"],
        index=1
    )
    
    num_pages = st.slider("Number of pages to scrape", 1, 5, 1, help="Each page = ~50 products")
    
    st.divider()
    
    st.subheader("Filters")
    include_ads = st.checkbox("Include Sponsored Products", value=True)
    include_organic = st.checkbox("Include Organic Products", value=True)
    
    min_rating = st.slider("Minimum Rating", 0.0, 5.0, 0.0, 0.5)
    min_reviews = st.number_input("Minimum Reviews", 0, 10000, 0, 100)

# Main analysis button
if st.button("🔍 Analyse Products", type="primary"):
    if not search_query:
        st.error("Please enter a search term")
        st.stop()
    
    all_products = []
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page in range(1, num_pages + 1):
        status_text.text(f"Fetching page {page} of {num_pages}...")
        
        try:
            # SerpAPI request
            params = {
                "engine": "amazon",
                "k": search_query,
                "amazon_domain": amazon_domain,
                "page": page,
                "api_key": SERPAPI_KEY
            }
            
            response = requests.get("https://serpapi.com/search", params=params)
            data = response.json()
            
            # Check for errors
            if "error" in data:
                st.error(f"API Error: {data['error']}")
                break
            
            # Extract organic results
            if include_organic and "organic_results" in data:
                for product in data["organic_results"]:
                    all_products.append({
                        "type": "Sponsored" if product.get("sponsored") else "Organic",
                        "position": product.get("position"),
                        "asin": product.get("asin"),
                        "title": product.get("title"),
                        "price": product.get("extracted_price"),
                        "old_price": product.get("extracted_old_price"),
                        "rating": product.get("rating"),
                        "reviews": product.get("reviews"),
                        "bought_last_month": product.get("bought_last_month"),
                        "prime": product.get("prime", False),
                        "thumbnail": product.get("thumbnail"),
                        "link": product.get("link_clean")
                    })
            
        except Exception as e:
            st.error(f"Error fetching page {page}: {str(e)}")
            break
        
        progress_bar.progress(page / num_pages)
    
    progress_bar.empty()
    status_text.empty()
    
    if not all_products:
        st.warning("No products found. Try different search terms.")
        st.stop()
    
    # Convert to DataFrame
    df = pd.DataFrame(all_products)
    
    # Apply filters
    if not include_ads:
        df = df[df['type'] != 'Sponsored']
    
    if not include_organic:
        df = df[df['type'] != 'Organic']
    
    if min_rating > 0:
        df = df[df['rating'] >= min_rating]
    
    if min_reviews > 0:
        df = df[df['reviews'] >= min_reviews]
    
    # Calculate discount percentage
    df['discount_pct'] = ((df['old_price'] - df['price']) / df['old_price'] * 100).round(1)
    df['discount_pct'] = df['discount_pct'].fillna(0)
    
    # Store in session state
    st.session_state.df = df
    
    # Summary metrics
    st.subheader("📊 Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Products", len(df))
    
    with col2:
        sponsored_count = len(df[df['type'] == 'Sponsored'])
        st.metric("Sponsored", sponsored_count)
    
    with col3:
        avg_price = df['price'].mean()
        st.metric("Avg Price", f"${avg_price:.2f}" if pd.notna(avg_price) else "N/A")
    
    with col4:
        avg_rating = df['rating'].mean()
        st.metric("Avg Rating", f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A")
    
    with col5:
        prime_pct = (df['prime'].sum() / len(df) * 100)
        st.metric("Prime %", f"{prime_pct:.0f}%")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Products Table", "📈 Analytics", "🎯 Ad Analysis", "💰 Pricing"])
    
    with tab1:
        st.subheader("Product Listings")
        
        # Display columns
        display_cols = ['type', 'position', 'title', 'price', 'rating', 'reviews', 'prime', 'discount_pct']
        display_df = df[display_cols].copy()
        
        # Format for display
        display_df['price'] = display_df['price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
        display_df['discount_pct'] = display_df['discount_pct'].apply(lambda x: f"{x:.1f}%" if x > 0 else "-")
        display_df['prime'] = display_df['prime'].apply(lambda x: "✓" if x else "")
        
        st.dataframe(display_df, use_container_width=True, height=500)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Data (CSV)",
            data=csv,
            file_name=f"amazon_{search_query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with tab2:
        st.subheader("📈 Product Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Price distribution
            st.write("**Price Distribution**")
            price_data = df[df['price'].notna()]['price']
            if len(price_data) > 0:
                st.bar_chart(price_data.value_counts().sort_index())
            else:
                st.info("No price data available")
        
        with col2:
            # Rating distribution
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
    
    with tab3:
        st.subheader("🎯 Advertising Analysis")
        
        # Sponsored vs Organic
        type_counts = df['type'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Product Type Distribution**")
            st.bar_chart(type_counts)
        
        with col2:
            st.write("**Sponsored Products Position**")
            sponsored_df = df[df['type'] == 'Sponsored']
            if len(sponsored_df) > 0:
                st.write(f"Total sponsored: {len(sponsored_df)}")
                st.write(f"Avg position: {sponsored_df['position'].mean():.1f}")
                st.write(f"Top 3 positions: {len(sponsored_df[sponsored_df['position'] <= 3])}")
            else:
                st.info("No sponsored products found")
        
        # Sponsored products table
        st.write("**Top Sponsored Products**")
        sponsored_table = sponsored_df[['position', 'title', 'price', 'rating', 'reviews']].head(10)
        if len(sponsored_table) > 0:
            st.dataframe(sponsored_table, use_container_width=True)
        else:
            st.info("No sponsored products to display")
    
    with tab4:
        st.subheader("💰 Pricing Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Lowest Price", f"${df['price'].min():.2f}" if df['price'].notna().any() else "N/A")
        
        with col2:
            st.metric("Highest Price", f"${df['price'].max():.2f}" if df['price'].notna().any() else "N/A")
        
        with col3:
            median_price = df['price'].median()
            st.metric("Median Price", f"${median_price:.2f}" if pd.notna(median_price) else "N/A")
        
        # Price by type
        st.write("**Average Price by Product Type**")
        price_by_type = df.groupby('type')['price'].mean().round(2)
        st.bar_chart(price_by_type)
        
        # Products with discounts
        st.write("**Products with Active Discounts**")
        discount_df = df[df['discount_pct'] > 0][['title', 'price', 'old_price', 'discount_pct']].sort_values('discount_pct', ascending=False)
        if len(discount_df) > 0:
            st.dataframe(discount_df.head(10), use_container_width=True)
        else:
            st.info("No products with active discounts")

# Footer
st.divider()
st.caption(f"Data from Amazon via SerpAPI | Domain: {amazon_domain}")
```

---

### `requirements.txt`
```
streamlit
pandas
requests
