# tinyvc

> **Automated Investment Research Pipeline** — Quantitative screening + LLM analysis delivered weekly via email

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://pydantic.dev/)
[![Tests](https://img.shields.io/badge/tests-9%2F9%20passing-success.svg)](tests/)

---

## 🎯 What It Does

**tinyvc** is a fully automated investment research system that:

1. **Ingests** macro data (FRED), stock fundamentals (yFinance), and market sentiment (Fear & Greed)
2. **Filters** opportunities using value + momentum screens with correlation-based diversification
3. **Analyzes** via Google's Gemini LLM with structured prompts and validated JSON output
4. **Delivers** markdown reports + visualizations to your inbox weekly

**Result:** A personalized, data-driven investment brief in your inbox every week — zero manual work required.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create `.env` file:
```bash
cp .env.example .env
```

Add your keys:
```env
FRED_API_KEY=your_key_here              # Get from https://fred.stlouisfed.org
GEMINI_API_KEY=your_key_here            # Get from https://ai.google.dev
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_gmail_app_password   # NOT your regular password!
RECIPIENT_EMAIL=your@gmail.com
```

### 3. Run Your First Pipeline

```bash
python src/main.py
```

**Output:**
- `outputs/report.md` — Your weekly brief
- `outputs/correlation_heatmap.png` — Diversification matrix  
- `outputs/opportunities_chart.png` — Top picks ranked
- **Email** — Report delivered to your inbox

---

## 📊 Architecture

```
┌─────────────────┐
│   Data Sources  │
│  FRED │ yF │ CNN│
└────────┬────────┘
         │
    ┌────▼────────────────┐
    │  Ingestion Layer    │
    │  • Retry logic      │
    │  • Rate limiting    │
    │  • Validation       │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │ Quantitative Engine │
    │  • Value filters    │
    │  • Momentum checks  │
    │  • Correlation      │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │  Research Engine    │
    │  • Gemini LLM       │
    │  • JSON extraction  │
    │  • Validation       │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │   Delivery Layer    │
    │  • Jinja2 reports   │
    │  • Visualizations   │
    │  • Email (SMTP)     │
    └─────────────────────┘
```

**Key Design Principles:**
- **Schema-first:** Pydantic validation at every boundary
- **Separation of concerns:** Deterministic (quant) vs probabilistic (LLM) clearly split
- **Advisory, not prescriptive:** Human stays in the loop
- **Reproducible:** Versioned prompts, test fixtures, mocked API responses

---

## 🔧 Configuration

### Watchlist (`config/watchlist.yaml`)

Define your investment universe:

```yaml
themes:
  ai_infrastructure:
    - NVDA
    - GOOGL
  cloud_saas:
    - CRM
    - SNOW
```

### Filters (`config/thresholds.yaml`)

Adjust screening criteria:

```yaml
value_filters:
  max_pe_ratio: 30
  max_peg_ratio: 2.5

momentum_filters:
  min_52w_recovery: -0.35  # Max 35% below 52W high
  require_200d_ma: true    # Must be above 200D MA
```

### Prompts (`prompts/v1.yaml`)

Customize LLM behavior:

```yaml
system: |
  You are a senior equity analyst...
user_template: |
  Weekly Budget: {{weekly_budget_usd}}
  Horizon: {{investment_horizon_years}} years
  ...
```

---

## 🧪 Testing

```bash
# Run all tests
pytest -v --cov=src

# Run specific test suite
pytest tests/unit/test_schemas.py -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

**Test Coverage:**
- ✅ 9/9 unit tests passing
- ✅ Schema validation (macro, sentiment, equities, LLM output)
- ✅ Data validator completeness checks
- ✅ Opportunity filter logic
- ✅ Integration tests (mocked API clients)

---

## 📁 Project Structure

```
tinyvc/
├── src/
│   ├── main.py                 # Pipeline orchestrator
│   ├── ingestion/              # Data fetching (FRED, yFinance, CNN)
│   ├── quant_engine/           # Filtering, scoring, correlation
│   ├── research_engine/        # Gemini LLM integration
│   └── delivery/               # Reports, visualizations, email
├── schemas/                    # Pydantic validation models
│   ├── macro.py
│   ├── sentiment.py
│   ├── equities.py
│   ├── payload.py              # LLM input
│   └── llm_output.py           # LLM response
├── config/
│   ├── watchlist.yaml          # Your stock picks
│   └── thresholds.yaml         # Filter settings
├── prompts/
│   └── v1.yaml                 # LLM prompt template
├── templates/
│   └── report.md.j2            # Report template
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data
├── outputs/                    # Generated reports
└── data/                       # Data lake (future)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Data Ingestion** | fredapi, yfinance, BeautifulSoup |
| **Validation** | Pydantic v2 |
| **Analysis** | pandas, numpy |
| **LLM** | Google Gemini 1.5 Flash |
| **Visualization** | matplotlib, seaborn |
| **Reporting** | Jinja2, markdown |
| **Email** | SMTP (Gmail) |
| **Testing** | pytest, pytest-cov |
| **Logging** | structlog |

---

## 📈 Example Output

### Report Snippet

```markdown
# Weekly Investment Brief — Feb 9, 2025

## 📊 Market Dashboard
- **Fed Funds Rate:** 4.33%
- **10Y Treasury:** 4.49%
- **Yield Curve:** -0.33% (⚠️ Inverted)
- **Fear & Greed:** 42 (Fear)

## 💎 Top Opportunities

### 1. GOOGL — Technology (Conviction: 89/100)

**Bull Case:** Market-leading position in AI compute with strong FCF...
**Bear Case:** Regulatory headwinds and advertising slowdown...
**Key Metrics:** PE: 22.5, PEG: 1.2, -12% from 52W high
```

### Visualizations

- **Correlation Heatmap:** Ensures portfolio diversification (max 0.85 correlation)
- **Opportunity Chart:** Top picks ranked by conviction score

---

## 🗺️ Roadmap

- [x] **Phase 1:** Core Pipeline (MVP) ✅
- [x] **Phase 1.5:** Engineering Rigor (Testing) ✅
- [ ] **Phase 2:** Data Lake + Historical Tracking
- [ ] **Phase 2.5:** Evaluation Framework (LLM groundedness)
- [ ] **Phase 3:** GitHub Pages Dashboard
- [ ] **Phase 4:** CI/CD with GitHub Actions

---

## 🤝 Contributing

See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for development workflow, testing guidelines, and PR process.

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🔍 Key Features

### 🎯 Smart Filtering
- **Value screens:** PE, PEG, price-to-book ratios
- **Momentum indicators:** 52W high proximity, MA crossovers
- **Diversification:** Correlation-based position limits (max 0.85)

### 🧠 LLM Integration
- **Structured prompts:** Versioned YAML templates
- **JSON validation:** Pydantic schemas enforce output contracts
- **Retry logic:** Automatic fallback for API failures

### 📧 Automated Delivery
- **Markdown reports:** Template-based generation
- **Visualizations:** Correlation heatmaps, opportunity charts
- **Email delivery:** HTML formatting with file attachments

### ✅ Production-Ready
- **Type safety:** Full Pydantic v2 validation
- **Error handling:** Graceful degradation with logging
- **Testing:** Comprehensive unit + integration tests
- **Reproducibility:** Mocked API responses for tests

---

## 💡 Philosophy

**Why tinyvc exists:**

1. **Democratize research tools:** Institutional-grade analysis should be accessible
2. **Human + AI synergy:** Quant screens + LLM analysis > either alone
3. **Reduce bias:** Structured data flows prevent cherry-picking
4. **Save time:** Automate repetitive tasks, focus on decision-making

**Design ethos:**

- Advisory, not prescriptive — you make the final calls
- Explainable — every recommendation includes bull/bear cases
- Transparent — open-source prompts and filter logic
- Testable — every component is unit-tested

---

## 🙋 FAQ

**Q: How much does it cost to run?**  
A: API costs are minimal — ~$0.10/week (FRED free, Gemini cheapest tier, Gmail free).

**Q: Can I customize the filters?**  
A: Yes! Edit `config/thresholds.yaml` to adjust PE ratios, momentum thresholds, etc.

**Q: How does correlation filtering work?**  
A: The system calculates pairwise correlations between stocks and removes highly correlated holdings (>0.85) to ensure diversification.

**Q: Can I switch LLM providers?**  
A: Currently Gemini-only, but the `research_engine/` is designed to be swappable.

**Q: Is this financial advice?**  
A: **No.** This is a research tool. Always do your own due diligence.

---

## 🔗 Resources

- **Quickstart Guide:** [`docs/quickstart.md`](docs/quickstart.md)
- **Architecture Deep Dive:** [`docs/walkthrough.md`](C:\Users\Dylan\.gemini\antigravity\brain\bb2224a0-fac1-4e27-8704-3fb8226d5d98\walkthrough.md)
- **Implementation Details:** [`docs/plan_review.md`](C:\Users\Dylan\.gemini\antigravity\brain\bb2224a0-fac1-4e27-8704-3fb8226d5d98\plan_review.md)

---

**Built with ❤️ for data-driven investors**
