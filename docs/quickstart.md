# Quick Start Guide

## Prerequisites

1. **Python 3.11+** installed
2. **API Keys** ready:
   - FRED API key (get from https://fred.stlouisfed.org/docs/api/api_key.html)
   - Gemini API key (get from https://ai.google.dev/)

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your API keys and email settings:

```env
# Required
FRED_API_KEY=your_fred_key_here
GEMINI_API_KEY=your_gemini_key_here

# Email (Gmail recommended)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
RECIPIENT_EMAIL=your.email@gmail.com

# Optional
WEEKLY_BUDGET=50
INVESTMENT_HORIZON=20
```

**Note**: For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

### 3. Run Tests

```bash
# Run all tests with coverage
python -m pytest -v --cov=src

# Run specific test file
python -m pytest tests/unit/test_schemas.py -v

# Run with detailed output
python -m pytest tests/ -v --tb=short
```

### 4. Run First Pipeline

```bash
python src/main.py
```

**Expected output:**
- Logs showing 7 stages completing
- Files created in `outputs/`:
  - `report.md` - Weekly investment brief
  - `correlation_heatmap.png` - Diversification matrix
  - `opportunities_chart.png` - Top picks chart
- Email delivered to your inbox

## Troubleshooting

### Missing Dependencies

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### API Key Errors

- Check `.env` file exists and has correct keys
- Verify FRED API key at https://fred.stlouisfed.org/docs/api/
- Test Gemini API key at https://ai.google.dev/

### Email Not Sending

- Gmail users: Use App Password, not regular password
- Check SMTP settings in `.env`
- Verify no firewall blocking port 587

### Import Errors

Make sure you're running from the project root:
```bash
cd c:\Users\Dylan\Projects\ai-portfolio\tinyvc
python src/main.py
```

## Next Steps

Once the pipeline runs successfully:

1. Review the generated `outputs/report.md`
2. Check email for delivered report
3. Customize `config/watchlist.yaml` with your preferred tickers
4. Adjust `config/thresholds.yaml` for your risk tolerance
5. Set up GitHub Actions for automated weekly runs (see `docs/deployment.md`)

## Project Structure

```
tinyvc/
├── src/
│   ├── ingestion/       # Data fetching (FRED, yFinance, sentiment)
│   ├── quant_engine/    # Filtering and scoring
│   ├── research_engine/ # Gemini LLM integration
│   ├── delivery/        # Reports and emails
│   └── main.py          # Pipeline orchestrator
├── schemas/             # Pydantic validation models
├── config/              # Watchlist and thresholds
├── prompts/             # LLM prompt templates
├── templates/           # Report templates
├── tests/               # Unit and integration tests
├── outputs/             # Generated reports and charts
└── data/                # Data lake (future Phase 2)
```

## Testing Philosophy

- Unit tests validate individual components
- Integration tests check API interactions (mocked)
- Pytest runs all tests with coverage reporting
- Pre-commit hooks ensure code quality (future)

## Resources

- [Full walkthrough](../brain/bb2224a0-fac1-4e27-8704-3fb8226d5d98/walkthrough.md)
- [Implementation plan](../brain/bb2224a0-fac1-4e27-8704-3fb8226d5d98/plan_review.md)
- [Task tracking](../brain/bb2224a0-fac1-4e27-8704-3fb8226d5d98/task.md)
