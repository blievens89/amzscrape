# Amazon Competitor Analysis Tool

A professional-grade Streamlit application for analyzing Amazon product data, competitor pricing, ratings, and advertising presence across multiple Amazon marketplaces.

## Features

- **Multi-Domain Support**: Search across 12+ Amazon marketplaces (US, UK, DE, FR, CA, ES, IT, JP, AU, IN, BR, MX)
- **Comprehensive Analysis**: Product pricing, ratings, reviews, Prime eligibility, and discount tracking
- **Advertising Insights**: Track sponsored vs. organic products and analyze competitor ad presence
- **Brand Analytics**: Identify top brands, pricing strategies, and market share
- **Data Export**: Download results as CSV for further analysis
- **Robust Error Handling**: Automatic retry logic and graceful error recovery
- **Data Validation**: Pydantic models ensure data quality and consistency

## Architecture

The application follows a modular architecture for maintainability and testability:

```
amzscrape/
├── src/
│   ├── api/
│   │   └── serpapi_client.py      # SerpAPI integration with retry logic
│   ├── data/
│   │   ├── models.py               # Pydantic data models
│   │   └── processor.py            # Data transformation & filtering
│   └── utils/
│       ├── extractors.py           # Brand extraction logic
│       └── formatters.py           # Display formatting utilities
├── tests/                          # Unit and integration tests
├── app.py                          # Streamlit application entry point
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- SerpAPI account and API key ([Sign up here](https://serpapi.com/))

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd amzscrape
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your SerpAPI key:
   ```
   SERPAPI_KEY=your_api_key_here
   ```

   **For Streamlit Cloud**: Add `SERPAPI_KEY` to your app secrets in the Streamlit Cloud dashboard.

## Usage

### Running Locally

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.

### Using the Application

1. **Enter Search Parameters**:
   - Search term (e.g., "wireless earbuds")
   - Select Amazon domain
   - Choose number of pages to scrape

2. **Set Filters**:
   - Include/exclude sponsored products
   - Include/exclude organic products
   - Minimum rating filter
   - Minimum reviews filter

3. **Analyze Results**:
   - **Products Table**: Browse all products with key metrics
   - **Brands**: Analyze brand distribution and pricing
   - **Analytics**: View price and rating distributions
   - **Ad Analysis**: Track sponsored product performance
   - **Pricing**: Deep-dive into pricing strategies and discounts

4. **Export Data**: Download results as CSV for further analysis

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SERPAPI_KEY` | Your SerpAPI API key | Yes | - |

### Application Settings

Edit `config.py` to customize:

- `REQUEST_TIMEOUT`: API request timeout (default: 30s)
- `MAX_RETRIES`: Number of retry attempts (default: 3)
- `MAX_PAGES`: Maximum pages to scrape (default: 5)
- `PRODUCTS_PER_PAGE`: Expected products per page (default: 48)

## Error Handling

The application includes comprehensive error handling:

- **Automatic Retries**: Network errors trigger exponential backoff retries
- **Quota Management**: Graceful handling of API quota limits
- **Partial Results**: Continue with available data if some requests fail
- **Input Validation**: Pydantic models validate all inputs and API responses

## Data Quality

- **Brand Extraction**: Advanced regex patterns extract brands from product titles
- **Deduplication**: Automatic removal of duplicate products by ASIN
- **Field Validation**: Type checking and range validation for all fields
- **Missing Data**: Graceful handling of missing or invalid fields

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_extractors.py
```

## Code Quality

The project uses industry-standard code quality tools:

```bash
# Format code
black .

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## API Usage & Costs

This application uses SerpAPI to fetch Amazon data. Be aware of:

- **API Credits**: Each page request consumes 1 API credit
- **Rate Limits**: SerpAPI has rate limits based on your plan
- **Cost Monitoring**: Check your usage at https://serpapi.com/account

## Deployment

### Streamlit Cloud

1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud
3. Add `SERPAPI_KEY` to Streamlit secrets
4. Deploy!

### Docker (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## Troubleshooting

### Common Issues

**"SERPAPI_KEY not found"**
- Ensure `.env` file exists with `SERPAPI_KEY=your_key`
- For Streamlit Cloud, check secrets configuration

**"API Quota Exceeded"**
- Check your SerpAPI account credits
- Reduce number of pages to scrape
- Consider upgrading your SerpAPI plan

**"No products found"**
- Try different search terms
- Check selected Amazon domain
- Verify the product exists on that marketplace

## Enhancements Implemented

This version includes significant improvements over the original:

### Architecture
- ✅ Modular code organization with separation of concerns
- ✅ Pydantic models for data validation
- ✅ Type hints throughout the codebase
- ✅ Comprehensive logging

### Reliability
- ✅ Automatic retry with exponential backoff
- ✅ Specific error handling (network, quota, API errors)
- ✅ Graceful degradation on partial failures
- ✅ Input sanitization and validation

### Performance
- ✅ Efficient data processing with pandas
- ✅ ASIN-based deduplication
- ✅ Configurable timeouts and limits

### Data Quality
- ✅ Improved brand extraction with regex patterns
- ✅ Field normalization and cleaning
- ✅ Comprehensive data validation

### Developer Experience
- ✅ Version-pinned dependencies
- ✅ Comprehensive documentation
- ✅ Testing infrastructure
- ✅ Code quality tools setup

## Future Enhancements

Potential improvements for future versions:

- [ ] Async API calls for better performance
- [ ] Caching layer to reduce API calls
- [ ] Historical data tracking and price alerts
- [ ] Advanced analytics (market share, trends)
- [ ] Export to Excel with multiple sheets
- [ ] Email notifications for price changes
- [ ] Search history and saved configurations

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code passes linting and type checking
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Open an issue on GitHub
- Check SerpAPI documentation: https://serpapi.com/amazon-search-api
- Review Streamlit docs: https://docs.streamlit.io

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [SerpAPI](https://serpapi.com/)
- Data processing with [pandas](https://pandas.pydata.org/)
- Validation with [Pydantic](https://pydantic-docs.helpmanual.io/)
