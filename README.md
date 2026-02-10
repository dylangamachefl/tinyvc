# tinyvc

> **Automated Market Strategy Pipeline** — Top-down regime analysis + news integration + LLM strategist delivered weekly via email

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://pydantic.dev/)
[![Tests](https://img.shields.io/badge/tests-31%2F31%20passing-success.svg)](tests/)

---

## 🎯 What It Does

**tinyvc** is a fully automated market strategy system that takes a **top-down approach**:

1. **Ingests** macro data (FRED), market news (Tavily), sentiment (Fear & Greed), and market universe prices (yFinance)
2. **Analyzes** market regime (trend, risk appetite, sector rotation) before looking at individual stocks
3. **Synthesizes** via Google's Gemini LLM as a "Chief Market Strategist" with structured prompts
4. **Delivers** strategic reports + sector heatmaps + bonus stock ideas to your inbox weekly

**Key Paradigm Shift:** The report starts with **market regime analysis**, then presents stocks as **bonus opportunities** that align with the current environment — not the other way around.

**Result:** A strategic market outlook that tells you *what the market is doing* first, then *where opportunities might be* second.

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
TAVILY_API_KEY=your_key_here            # Get from https://tavily.com (NEW!)
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_gmail_app_password   # NOT your regular password!
RECIPIENT_EMAIL=your@gmail.com
```

### 3. Run Your First Pipeline

```bash
python src/main.py
```

**Output:**
- `outputs/report.md` — Your weekly market strategy brief
- `outputs/sector_heatmap.png` — Sector rotation visualization ✨ NEW
- `outputs/correlation_heatmap.png` — Portfolio diversification matrix  
- `outputs/opportunities_chart.png` — Bonus stock picks ranked
- **Email** — Report delivered to your inbox

---

## 📊 Architecture

```
┌─────────────────────────────┐
│      Data Sources           │
│ FRED │ yF │ Tavily │ F&G   │
└──────────┬──────────────────┘
           │
    ┌──────▼─────────────────────┐
    │   Ingestion Layer          │
    │  • Macro data (FRED)       │
    │  • Market universe (yF)    │
    │  • Candidate pool (yF)     │
    │  • News narrative (Tavily) │ ✨ NEW
    │  • Sentiment (Fear & Greed)│
    └──────┬─────────────────────┘
           │
    ┌──────▼─────────────────────┐
    │  Quantitative Engine       │
    │  • Market regime calc      │ ✨ NEW
    │  • Sector rotation         │ ✨ NEW
    │  • Quality gate filters    │
    │  • Correlation analysis    │
    └──────┬─────────────────────┘
           │
    ┌──────▼─────────────────────┐
    │  Research Engine           │
    │  • Gemini LLM (v2 prompt)  │ ✨ UPDATED
    │  • Market Strategist role  │ ✨ NEW
    │  • Top-down analysis       │ ✨ NEW
    │  • JSON extraction         │
    └──────┬─────────────────────┘
           │
    ┌──────▼─────────────────────┐
    │    Delivery Layer          │
    │  • Strategic reports       │ ✨ UPDATED
    │  • Sector heatmaps         │ ✨ NEW
    │  • Bonus opportunities     │
    │  • Email (SMTP)            │
    └────────────────────────────┘
```

**Key Design Principles:**
- **Top-down first:** Analyze market regime → sectors → stocks (not the reverse)
- **News-aware:** Integrates real-time market narrative from Tavily
- **Regime-aligned:** Stock picks must match the current market environment
- **Schema-first:** Pydantic validation at every boundary
- **Advisory, not prescriptive:** Human stays in the loop

---

## 🔧 Configuration

### Watchlist (`config/watchlist.yaml`)

**New Two-Tier Structure:**

```yaml
market_universe:
  indices:
    - SPY    # S&P 500
    - QQQ    # Nasdaq
    - IWM    # Russell 2000
  
  sectors:
    - XLK    # Technology
    - XLF    # Financials
    - XLV    # Healthcare
    # ... all 11 SPDR sectors
  
  factors:
    - MTUM   # Momentum
    - VLUE   # Value
    - USMV   # Low Volatility

candidate_pool:
  - NVDA   # Individual stocks to screen
  - GOOGL
  - COST
  # ... your stock picks
```

**Philosophy Change:**
- `market_universe` → Context for regime analysis
- `candidate_pool` → Stocks screened as "bonus opportunities"

### Filters (`config/thresholds.yaml`)

Filters now act as a **quality gate** for the candidate pool:

```yaml
value_filters:
  max_pe_ratio: 30
  max_peg_ratio: 2.5

momentum_filters:
  min_52w_recovery: -0.35  # Max 35% below 52W high
  require_200d_ma: true    # Must be above 200D MA
```

### Prompts (`prompts/current.yaml`)

**V2 "Market Strategist" Prompt:**

```yaml
version: 2
system_prompt: |
  You are a Chief Market Strategist preparing a weekly market outlook.
  
  CRITICAL FRAMEWORK - TOP-DOWN APPROACH:
  1. Start with the BIG PICTURE (regime, trend, risk, news)
  2. Discuss sector rotation
  3. ONLY THEN present stocks as "Bonus Opportunities"
  
  Stock recommendations must ALIGN with identified market regime.
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
- ✅ 31/31 tests passing
- ✅ Schema validation (macro, sentiment, equities, news, market context)
- ✅ Data validator completeness checks
- ✅ Market regime calculations
- ✅ Opportunity filter logic
- ✅ Integration tests (mocked API clients)

---

## 📁 Project Structure

```
tinyvc/
├── src/
│   ├── main.py                 # Pipeline orchestrator
│   ├── ingestion/
│   │   ├── fred_client.py      # Macro data
│   │   ├── yfinance_client.py  # Equities + market universe
│   │   ├── news_client.py      # Tavily integration ✨ NEW
│   │   └── sentiment_client.py # Fear & Greed
│   ├── quant_engine/
│   │   ├── payload_builder.py  # Regime calculations ✨ UPDATED
│   │   ├── filters.py          # Quality gate
│   │   └── correlation.py      # Diversification
│   ├── research_engine/
│   │   ├── gemini_client.py    # LLM integration ✨ UPDATED
│   │   └── prompts.py          # Prompt manager
│   └── delivery/
│       ├── report_builder.py   # Markdown generation ✨ UPDATED
│       ├── visualizations.py   # Charts + sector heatmap ✨ UPDATED
│       └── email_sender.py     # SMTP delivery
├── schemas/
│   ├── payload.py              # LLM input (w/ MarketNews, MarketContext) ✨ UPDATED
│   ├── llm_output.py           # LLM response
│   ├── macro.py
│   ├── sentiment.py
│   └── equities.py
├── config/
│   ├── watchlist.yaml          # Market universe + candidate pool ✨ UPDATED
│   └── thresholds.yaml         # Filter settings
├── prompts/
│   ├── current.yaml            # Active prompt (v2) ✨ UPDATED
│   ├── v2.yaml                 # Market Strategist ✨ NEW
│   └── v1.yaml                 # Legacy stock picker
├── templates/
│   └── report.md.j2            # Three-section strategist template ✨ UPDATED
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── outputs/                    # Generated reports
└── data/                       # Data lake
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Data Ingestion** | fredapi, yfinance, tavily-python ✨ NEW, BeautifulSoup |
| **Validation** | Pydantic v2 |
| **Analysis** | pandas, numpy |
| **LLM** | Google Gemini 3-27B-IT |
| **Visualization** | matplotlib, seaborn |
| **Reporting** | Jinja2, markdown |
| **Email** | SMTP (Gmail) |
| **Testing** | pytest, pytest-cov |
| **Logging** | structlog |

---

## 📈 Example Output

### Report Structure (V2)

```markdown
# Market Strategy Report — Feb 10, 2026

## 1. Executive Strategy

**Current Market Regime:**
- Trend: Bullish (SPY above 200-day MA)
- Risk: Risk-On (Growth outperforming Defensive)
- Sentiment: Fear (42/100)

**News Narrative:**
- Daily Drivers: Tech stocks rally on earnings optimism
- Sector Context: Technology sector leads market gains
- Macro Sentiment: Fed signals potential rate pause

## 2. Market Dashboard

### Sector Rotation
[Sector Heatmap: Technology +5.2%, Financials +3.1%, ...]

### Strategic Interpretation
The market is in a Risk-On environment with bullish technicals...

## 3. Bonus Investment Opportunities

From the candidate pool, here are stocks that align with Risk-On:

### 1. NVDA — Conviction: 9/10
**Bull Case:** Market leader in AI compute...
**Bear Case:** Valuation concerns at 45x P/E...
**Key Metrics:** PE: 45.2, PEG: 1.8, -8% from 52W high
```

### Visualizations

- **Sector Heatmap:** 30-day performance of all 11 sectors ✨ NEW
- **Correlation Matrix:** Portfolio diversification check
- **Opportunity Chart:** Bonus picks ranked by conviction

---

## 🗺️ Roadmap

- [x] **Phase 1:** Core Pipeline (Stock Picker MVP) ✅
- [x] **Phase 1.5:** Engineering Rigor (Testing) ✅
- [x] **Phase 2:** Market Strategist Pivot ✅ **← YOU ARE HERE**
- [ ] **Phase 2.5:** Evaluation Framework (LLM groundedness)
- [ ] **Phase 3:** GitHub Pages Dashboard
- [ ] **Phase 4:** CI/CD with GitHub Actions (Weekly Runs) ✅ Workflow Created

---

## 🔍 What's New in V2 (Market Strategist)

### Conceptual Changes

| Before (V1) | After (V2) |
|-------------|------------|
| Bottom-up stock picker | Top-down market strategist |
| "Here are 10 stocks to buy" | "Here's the market regime, and IF deploying capital, consider these" |
| Themes organized stocks | Market universe provides context |
| Filters were primary screen | Filters are quality gate for bonus picks |

### Technical Additions

✨ **Tavily API Integration** — Real-time market news narrative  
✨ **Market Regime Calculations** — Trend signal, risk regime, sector rotation  
✨ **Sector Heatmap Visualization** — 30-day performance chart  
✨ **V2 Prompt Template** — "Chief Market Strategist" persona  
✨ **Three-Section Report** — Executive Strategy → Dashboard → Bonus Ideas  
✨ **Regime Alignment Logic** — Stocks must fit current environment  

### Migration Guide

If upgrading from V1:

1. **Update `watchlist.yaml`** to new two-tier format
2. **Get Tavily API key** from https://tavily.com
3. **Add `TAVILY_API_KEY`** to `.env` and GitHub Secrets
4. **Run `pip install -r requirements.txt`** to get `tavily-python`

---

## 💡 Philosophy

**Why the Market Strategist pivot?**

V1 was a **stock picker** — it found individual opportunities and presented them.

V2 is a **market strategist** — it analyzes the macro environment first, understands what regime we're in, then presents stocks as *secondary* ideas that align with that regime.

**The difference matters:**

- In **Risk-Off** markets → Recommend defensive quality, not high-beta growth
- In **Bullish trends** → Growth ideas make sense
- In **Bearish trends** → Cash preservation or hedges take priority

**Design ethos:**

- Top-down beats bottom-up for portfolio construction
- Regime awareness prevents fighting the tape
- News narrative provides qualitative context
- Stocks are tools to express a view, not the view itself
- Advisory, not prescriptive — you make the final calls

---

## 🙋 FAQ

**Q: How much does it cost to run?**  
A: API costs are minimal — ~$0.15/week (FRED free, Gemini cheapest tier, Tavily free tier, Gmail free).

**Q: What's the difference between market_universe and candidate_pool?**  
A: `market_universe` tickers (indices, sectors, factors) provide context for regime analysis. `candidate_pool` are individual stocks screened as bonus opportunities.

**Q: Does the LLM make the regime calculations?**  
A: No! Regime signals (trend, risk, rotation) are **quantitative** — calculated deterministically in `payload_builder.py`. The LLM only synthesizes them into narrative.

**Q: Can I switch back to V1 stock picker mode?**  
A: Technically yes (point `current.yaml` at `v1.yaml`), but you'd lose news/regime context.

**Q: Is this financial advice?**  
A: **No.** This is a research tool. Always do your own due diligence.

---

## 🔗 Resources

- **Quickstart Guide:** [`docs/quickstart.md`](docs/quickstart.md)
- **Deployment Guide:** [`DEPLOYMENT.md`](DEPLOYMENT.md)
- **Tavily Setup:** See artifact walkthrough for API key configuration

---

**Built with ❤️ for strategic, data-driven investors**
