# tinyvc: Technical Implementation Plan

**Project Codename:** tinyvc  
**Stack:** Python 3.11+ | GitHub Actions | Gemini API | SMTP  
**Estimated Build Time:** 8-12 hours  

---

## Executive Summary

Build an autonomous, weekly investment research pipeline that:
1. Fetches macro and equity data from free public APIs
2. Applies quantitative filters to surface opportunities
3. Uses Gemini to generate advisory analysis (not prescriptive recommendations)
4. Delivers ranked opportunities and scenarios — the human makes the final call

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        GITHUB ACTIONS (Cron: Sunday 8AM UTC)            │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         1. INGESTION LAYER                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   FRED Client   │  │ yFinance Client │  │Sentiment Scraper│         │
│  │  (Macro Data)   │  │  (Equities)     │  │ (Fear & Greed)  │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
└───────────┼────────────────────┼────────────────────┼───────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      2. QUANTITATIVE ENGINE                             │
│                                                                         │
│   • Validate & clean incoming data                                      │
│   • Apply threshold filters (P/E, 52-week range, etc.)                  │
│   • Calculate correlation matrix for diversification                    │
│   • Generate structured JSON payload for LLM                            │
│                                                                         │
│   OUTPUT: validated_data.json                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       3. RESEARCH ENGINE (Gemini)                       │
│                                                                         │
│   • Receive structured JSON                                             │
│   • Chain-of-Thought prompt forces grounded reasoning                   │
│   • Generate: Ranked Opportunities, Scenarios, Risk Context             │
│   • ADVISORY ONLY — no prescriptive "buy X" recommendations             │
│                                                                         │
│   OUTPUT: analysis.json                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        4. DELIVERY LAYER                                │
│                                                                         │
│   • Compile Markdown report from Jinja2 template                        │
│   • Generate correlation heatmap (matplotlib/seaborn)                   │
│   • Save as GitHub Actions artifact                                     │
│   • Send via SMTP (Gmail)                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
tinyvc/
├── .github/
│   └── workflows/
│       └── weekly_report.yml        # Main pipeline + dashboard deploy
├── src/
│   ├── __init__.py
│   ├── main.py                      # Entrypoint orchestrator
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── fred_client.py
│   │   ├── yfinance_client.py
│   │   └── sentiment_client.py
│   ├── quant_engine/
│   │   ├── __init__.py
│   │   ├── data_validator.py
│   │   ├── filters.py
│   │   ├── correlation.py
│   │   └── payload_builder.py
│   ├── research_engine/
│   │   ├── __init__.py
│   │   ├── gemini_client.py
│   │   └── prompts.py
│   ├── evaluation/                  # NEW: LLM quality checks
│   │   ├── __init__.py
│   │   ├── groundedness.py
│   │   └── schema_compliance.py
│   ├── dashboard/                   # NEW: Static site generator
│   │   ├── __init__.py
│   │   └── site_builder.py
│   └── delivery/
│       ├── __init__.py
│       ├── report_builder.py
│       ├── visualizations.py
│       └── email_sender.py
├── schemas/                         # NEW: Pydantic models
│   ├── __init__.py
│   ├── macro.py
│   ├── equities.py
│   ├── payload.py
│   └── llm_output.py
├── prompts/                         # NEW: Versioned prompts
│   ├── v1.yaml
│   └── current.yaml -> v1.yaml
├── data/                            # NEW: Data lake (git-ignored, persisted)
│   ├── raw/                         # Immutable API snapshots
│   ├── processed/                   # Post-quant-engine outputs
│   └── reports/                     # Historical reports (JSON + MD)
├── docs/                            # NEW: GitHub Pages source
│   ├── index.html
│   ├── reports/                     # Rendered historical reports
│   ├── assets/
│   │   ├── charts/                  # Generated visualizations
│   │   └── css/
│   └── adr/                         # Architecture Decision Records
│       ├── 001-gemini-over-openai.md
│       ├── 002-advisory-not-prescriptive.md
│       └── 003-data-lake-structure.md
├── config/
│   ├── watchlist.yaml
│   └── thresholds.yaml
├── templates/
│   ├── report.md.j2
│   └── dashboard/                   # NEW: Site templates
│       ├── index.html.j2
│       ├── report.html.j2
│       └── base.html.j2
├── tests/
│   ├── unit/
│   │   ├── test_filters.py
│   │   ├── test_correlation.py
│   │   ├── test_schemas.py
│   │   └── test_payload_builder.py
│   ├── integration/
│   │   ├── test_ingestion.py
│   │   ├── test_llm_integration.py
│   │   └── test_email_delivery.py
│   ├── fixtures/
│   │   ├── fred_response.json
│   │   ├── yfinance_response.json
│   │   └── gemini_response.json
│   └── conftest.py
├── Dockerfile                       # NEW: Containerization
├── docker-compose.yml               # NEW: Local dev environment
├── requirements.txt
├── requirements-dev.txt             # NEW: Test/dev dependencies
├── .env.example
└── README.md
```

---

## Module Specifications

### 1. Ingestion Layer

#### 1.1 `fred_client.py`

**Purpose:** Fetch macroeconomic indicators from Federal Reserve Economic Data.

**API:** `https://api.stlouisfed.org/fred/series/observations`

**Required Secret:** `FRED_API_KEY` (free at https://fred.stlouisfed.org/docs/api/api_key.html)

**Data Points to Fetch:**

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| `DFF` | Federal Funds Effective Rate | Daily |
| `DGS10` | 10-Year Treasury Yield | Daily |
| `CPIAUCSL` | Consumer Price Index | Monthly |
| `UNRATE` | Unemployment Rate | Monthly |
| `GDP` | Gross Domestic Product | Quarterly |
| `T10Y2Y` | 10Y-2Y Treasury Spread (Inversion Signal) | Daily |

**Function Signature:**
```python
def fetch_macro_data(api_key: str, lookback_days: int = 365) -> dict:
    """
    Returns:
    {
        "fed_funds_rate": float,
        "treasury_10y": float,
        "cpi_yoy_change": float,
        "unemployment": float,
        "yield_curve_spread": float,
        "recession_signal": bool,  # True if T10Y2Y < 0
        "fetched_at": str  # ISO timestamp
    }
    """
```

**Error Handling:** Implement exponential backoff (3 retries). Log failures but don't crash pipeline—use cached/stale data if available.

---

#### 1.2 `yfinance_client.py`

**Purpose:** Fetch equity prices, fundamentals, and technicals.

**Library:** `yfinance` (no API key required)

**Watchlist Source:** Load from `config/watchlist.yaml`

**Data Points Per Ticker:**

| Field | Source | Notes |
|-------|--------|-------|
| `current_price` | `info['currentPrice']` | |
| `52_week_high` | `info['fiftyTwoWeekHigh']` | |
| `52_week_low` | `info['fiftyTwoWeekLow']` | |
| `pe_ratio` | `info['trailingPE']` | Handle None |
| `forward_pe` | `info['forwardPE']` | Handle None |
| `peg_ratio` | `info['pegRatio']` | Handle None |
| `market_cap` | `info['marketCap']` | |
| `sector` | `info['sector']` | For diversification |
| `1yr_return` | Calculate from history | |
| `50d_ma` | `info['fiftyDayAverage']` | |
| `200d_ma` | `info['twoHundredDayAverage']` | |

**Function Signature:**
```python
def fetch_equity_data(tickers: list[str]) -> pd.DataFrame:
    """
    Returns DataFrame with columns:
    [ticker, current_price, 52w_high, 52w_low, pe_ratio, forward_pe, 
     peg_ratio, market_cap, sector, 1yr_return, 50d_ma, 200d_ma,
     pct_from_52w_high, above_200d_ma]
    """
```

**Rate Limiting:** Add 0.5s delay between ticker fetches to avoid throttling.

---

#### 1.3 `sentiment_client.py`

**Purpose:** Scrape CNN Fear & Greed Index.

**Source:** `https://production.dataviz.cnn.io/index/fearandgreed/graphdata`

**Function Signature:**
```python
def fetch_fear_greed() -> dict:
    """
    Returns:
    {
        "score": int,  # 0-100
        "label": str,  # "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"
        "previous_close": int,
        "one_week_ago": int,
        "one_month_ago": int,
        "one_year_ago": int
    }
    """
```

---

### 2. Quantitative Engine

#### 2.1 `data_validator.py`

**Purpose:** Ensure data quality before analysis.

**Validations:**
- No null values in critical fields (price, PE)
- Prices > 0
- Timestamps within expected range
- Remove tickers with >20% missing data

**Function Signature:**
```python
def validate_equity_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Returns:
    - Cleaned DataFrame
    - List of dropped tickers with reasons
    """
```

---

#### 2.2 `filters.py`

**Purpose:** Apply quantitative thresholds to surface opportunities.

**Filter Logic (load thresholds from `config/thresholds.yaml`):**

```yaml
# config/thresholds.yaml
value_filters:
  max_pe_ratio: 35
  max_peg_ratio: 2.5
  min_market_cap: 1_000_000_000  # $1B floor

momentum_filters:
  max_pct_from_52w_high: 0.30  # Within 30% of high
  require_above_200d_ma: true

opportunity_signals:
  extreme_fear_threshold: 25  # Buy more aggressively
  greed_threshold: 75         # Hold cash
```

**Function Signature:**
```python
def apply_filters(
    df: pd.DataFrame, 
    thresholds: dict,
    fear_greed_score: int
) -> pd.DataFrame:
    """
    Returns filtered DataFrame with added columns:
    - passes_value_filter: bool
    - passes_momentum_filter: bool
    - opportunity_score: float (0-100, composite ranking)
    """
```

---

#### 2.3 `correlation.py`

**Purpose:** Enforce portfolio diversification using correlation matrix.

**Implementation:**
1. Fetch 1-year daily returns for filtered tickers
2. Calculate Pearson correlation matrix
3. Flag pairs with correlation > 0.85
4. If two tickers highly correlated, keep one with better opportunity_score

**Function Signature:**
```python
def calculate_correlation_matrix(tickers: list[str]) -> pd.DataFrame:
    """Returns NxN correlation DataFrame"""

def enforce_diversification(
    df: pd.DataFrame, 
    corr_matrix: pd.DataFrame,
    max_correlation: float = 0.85
) -> pd.DataFrame:
    """Returns deduplicated DataFrame with redundant tickers removed"""
```

**Visualization Output:** Save heatmap as `correlation_heatmap.png`

---

#### 2.4 `payload_builder.py`

**Purpose:** Structure data for Gemini consumption.

**Output Schema:**
```json
{
  "report_date": "2025-02-09",
  "weekly_budget_usd": 50,
  "investment_horizon_years": 20,
  "macro_environment": {
    "fed_funds_rate": 4.33,
    "treasury_10y": 4.49,
    "cpi_yoy": 2.9,
    "yield_curve_inverted": false,
    "fear_greed_score": 42,
    "fear_greed_label": "Fear",
    "sentiment_context": "Fearful markets often present buying opportunities for quality names at discounts."
  },
  "opportunities": [
    {
      "ticker": "GOOG",
      "sector": "Technology",
      "theme": "ai_compute",
      "current_price": 185.43,
      "pe_ratio": 22.5,
      "peg_ratio": 1.2,
      "pct_from_52w_high": -12.3,
      "above_200d_ma": true,
      "opportunity_score": 78
    }
  ],
  "themes": {
    "ai_compute": ["NVDA", "AMD", "GOOG"],
    "energy_transition": ["ENPH", "FSLR"],
    "biotech": ["LLY", "VRTX"]
  }
}
```

---

### 3. Research Engine

#### 3.1 `gemini_client.py`

**Purpose:** Interface with Google Gemini API.

**API:** Google AI Studio (https://aistudio.google.com/)

**Required Secret:** `GEMINI_API_KEY`

**Model:** `gemini-1.5-flash` (cost-effective for weekly runs)

**Function Signature:**
```python
def generate_analysis(payload: dict, prompt_template: str) -> dict:
    """
    Returns:
    {
        "executive_summary": str,  # 2-3 sentences
        "macro_interpretation": str,  # What the data means
        "opportunities": [
            {
                "ticker": str,
                "conviction_score": int,  # 1-10, higher = stronger case
                "bull_case": str,  # Why it's attractive
                "bear_case": str,  # Risks/concerns
                "key_metrics": str  # "PE: 22, PEG: 1.2, -12% from high"
            }
        ],
        "scenarios": [
            {
                "name": str,  # e.g., "Growth-focused", "Defensive", "Balanced"
                "description": str,  # When this makes sense
                "suggested_tickers": list[str]
            }
        ],
        "themes_in_focus": str,
        "risks_to_watch": str
    }
    """
```

**Configuration:**
```python
generation_config = {
    "temperature": 0.3,  # Lower for more deterministic output
    "top_p": 0.8,
    "max_output_tokens": 2000
}
```

---

#### 3.2 `prompts.py`

**Purpose:** Store and manage prompt templates.

**System Prompt:**
```
You are a research analyst preparing a weekly investment brief for a long-term retail investor.

YOUR ROLE IS ADVISORY — you inform, you do not decide.

STRICT RULES:
1. ONLY reference data provided in the JSON payload — never invent statistics
2. Every opportunity must cite specific metrics (PE, PEG, % from high)
3. Present BOTH bull and bear cases for each opportunity
4. Acknowledge uncertainty — you are reasoning from limited data
5. Think in 20-year timeframes, not weeks
6. Never say "buy X" — instead say "X stands out because..." or "consider X if..."
7. Offer 2-3 scenarios for different investor priorities
8. The human makes the final allocation decision

OUTPUT FORMAT: Respond in valid JSON matching the schema provided.
```

**User Prompt Template:**
```
Here is this week's market data:

<DATA>
{json_payload}
</DATA>

Based on this data, generate a weekly investment brief for a long-term investor. Remember:
- The investor has $50 to allocate this week — they will make the final decision
- They can only trade on Fidelity (stocks) and Coinbase (crypto, not enabled yet)
- Time horizon is 20 years — favor quality compounders
- Current sentiment is {fear_greed_label} ({fear_greed_score}/100)

Your role is ADVISORY, not prescriptive:
- Rank the top opportunities and explain WHY each stands out
- Highlight tradeoffs (e.g., "higher growth but pricier valuation")
- Offer 2-3 scenarios based on different investor priorities
- Let the human make the final call

Respond in JSON format with these keys:
- executive_summary
- macro_interpretation  
- opportunities (array ranked by conviction, with: ticker, conviction_score 1-10, bull_case, bear_case, key_metrics)
- scenarios (2-3 allocation approaches based on different priorities)
- themes_in_focus
- risks_to_watch
```

---

### 4. Delivery Layer

#### 4.1 `report_builder.py`

**Purpose:** Compile final Markdown report.

**Template:** Use Jinja2 (`templates/report.md.j2`)

**Template Structure:**
```markdown
# tinyvc Report: {{ report_date }}

## Executive Summary
{{ executive_summary }}

---

## Macro Dashboard

| Indicator | Value | Signal |
|-----------|-------|--------|
| Fed Funds Rate | {{ fed_funds_rate }}% | {{ rate_signal }} |
| 10Y Treasury | {{ treasury_10y }}% | |
| Fear & Greed | {{ fear_greed_score }} | {{ fear_greed_label }} |
| Yield Curve | {{ yield_curve_status }} | |

{{ macro_interpretation }}

---

## This Week's Opportunities

*Ranked by conviction. You decide how to allocate your $50.*

{% for opp in opportunities %}
### {{ loop.index }}. {{ opp.ticker }} — Conviction: {{ opp.conviction_score }}/10

**Key Metrics:** {{ opp.key_metrics }}

**Bull Case:** {{ opp.bull_case }}

**Bear Case:** {{ opp.bear_case }}

{% endfor %}

---

## Scenarios to Consider

{% for scenario in scenarios %}
### {{ scenario.name }}
{{ scenario.description }}

**Consider:** {{ scenario.suggested_tickers | join(', ') }}

{% endfor %}

---

## Correlation Matrix
![Correlation Heatmap](correlation_heatmap.png)

---

## Theme Tracker
{{ themes_in_focus }}

---

## Risks to Watch
{{ risks_to_watch }}

---

*Report generated automatically on {{ generated_at }}. Final allocation decisions are yours.*
```

**Function Signature:**
```python
def build_report(
    quant_payload: dict,
    llm_analysis: dict,
    heatmap_path: str
) -> str:
    """Returns compiled Markdown string"""
```

---

#### 4.2 `visualizations.py`

**Purpose:** Generate charts for the report.

**Required Charts:**

1. **Correlation Heatmap**
   - Library: `seaborn.heatmap()`
   - Colormap: `RdYlGn_r` (red = high correlation = bad)
   - Save as: `outputs/correlation_heatmap.png`

2. **Fear & Greed Gauge** (optional enhancement)
   - Simple matplotlib gauge showing current score

**Function Signature:**
```python
def generate_heatmap(corr_matrix: pd.DataFrame, output_path: str) -> None:
```

---

#### 4.3 `email_sender.py`

**Purpose:** Send report via SMTP.

**Required Secrets:**
- `SMTP_SERVER`: e.g., `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SMTP_USER`: your Gmail address
- `SMTP_PASSWORD`: Gmail App Password (not regular password)
- `RECIPIENT_EMAIL`: where to send

**Gmail App Password Setup:**
1. Enable 2FA on Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate password for "Mail"

**Function Signature:**
```python
def send_report(
    subject: str,
    markdown_body: str,
    attachments: list[str],  # [heatmap.png, report.md]
    recipient: str
) -> bool:
```

**Implementation Notes:**
- Convert Markdown to HTML using `markdown` library
- Attach both .md (raw) and .png files
- Use `email.mime` for multipart messages

---

### 5. Orchestration

#### 5.1 `main.py`

**Purpose:** Coordinate the full pipeline.

**Flow:**
```python
from datetime import date
from src.storage.data_lake import DataLake
from src.ingestion import fetch_macro_data, fetch_equity_data, fetch_fear_greed
from src.quant_engine import validate_equity_data, apply_filters, calculate_correlation_matrix, enforce_diversification, build_payload
from src.research_engine import PromptManager, generate_analysis
from src.evaluation import GroundednessEvaluator, QualityEvaluator
from src.delivery import build_report, generate_heatmap, send_report
from src.dashboard import DashboardBuilder
from schemas.llm_output import AnalysisOutput
import structlog

logger = structlog.get_logger()

def run_pipeline():
    logger.info("pipeline_started")
    
    # Initialize
    data_lake = DataLake()
    config = load_config()
    prompt_manager = PromptManager()
    
    # 1. Ingest data
    logger.info("ingestion_started")
    macro_data = fetch_macro_data(os.environ["FRED_API_KEY"])
    equity_data = fetch_equity_data(config["watchlist"])
    sentiment = fetch_fear_greed()
    
    # Save raw data (immutable)
    data_lake.save_raw("fred", macro_data.model_dump())
    data_lake.save_raw("equities", equity_data.to_dataframe())
    data_lake.save_raw("sentiment", sentiment.model_dump())
    
    # 2. Quantitative processing
    logger.info("quant_engine_started")
    validated = validate_equity_data(equity_data)
    filtered = apply_filters(validated, config["thresholds"], sentiment.score)
    corr_matrix = calculate_correlation_matrix(filtered["ticker"].tolist())
    final_picks = enforce_diversification(filtered, corr_matrix)
    
    # Save processed data
    data_lake.save_processed("opportunities", final_picks)
    data_lake.save_processed("correlation_matrix", corr_matrix)
    
    # 3. Build LLM payload
    payload = build_payload(macro_data, final_picks, sentiment, config)
    data_lake.save_processed("payload", payload)
    
    # 4. Generate analysis
    logger.info("research_engine_started", prompt_version=prompt_manager.version)
    raw_analysis = generate_analysis(payload, prompt_manager)
    analysis = AnalysisOutput.model_validate(raw_analysis)
    
    # 5. Evaluate LLM output
    logger.info("evaluation_started")
    groundedness = GroundednessEvaluator(payload, analysis)
    quality = QualityEvaluator(analysis)
    
    eval_results = {
        "prompt_version": prompt_manager.version,
        "groundedness": groundedness.overall_score(),
        "quality": quality.summary(),
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info("evaluation_complete", 
                groundedness=eval_results["groundedness"]["overall"],
                quality_passed=eval_results["quality"]["passed"])
    
    # 6. Create outputs
    logger.info("delivery_started")
    generate_heatmap(corr_matrix, "outputs/correlation_heatmap.png")
    report = build_report(payload, analysis, "outputs/correlation_heatmap.png")
    
    # Save report with evaluation
    data_lake.save_report(
        markdown=report,
        json_data=analysis.model_dump(),
        eval_data=eval_results,
        assets=["outputs/correlation_heatmap.png"]
    )
    
    # 7. Send email
    send_report(
        subject=f"tinyvc Report: {date.today()}",
        markdown_body=report,
        attachments=["outputs/report.md", "outputs/correlation_heatmap.png"],
        recipient=os.environ["RECIPIENT_EMAIL"]
    )
    
    # 8. Rebuild dashboard
    logger.info("dashboard_rebuild_started")
    dashboard = DashboardBuilder(data_lake)
    dashboard.build_all()
    
    logger.info("pipeline_complete")

if __name__ == "__main__":
    run_pipeline()
```
```

---

### 6. Data Lake Layer

**Purpose:** Persist all data for reproducibility, debugging, and historical analysis.

#### Storage Structure

```
data/
├── raw/                          # Immutable API responses
│   └── 2025-02-09/
│       ├── fred.json             # Exact API response
│       ├── equities.parquet      # Compressed, columnar
│       ├── sentiment.json
│       └── _metadata.json        # Fetch timestamps, API versions
├── processed/                    # Post-quant-engine
│   └── 2025-02-09/
│       ├── opportunities.parquet
│       ├── correlation_matrix.parquet
│       └── payload.json          # Exact LLM input
└── reports/                      # Final outputs
    └── 2025-02-09/
        ├── report.md
        ├── report.json           # Structured LLM output
        ├── correlation_heatmap.png
        └── _eval.json            # Evaluation scores
```

#### Implementation

```python
# src/storage/data_lake.py

from pathlib import Path
from datetime import date
import json
import pandas as pd

class DataLake:
    def __init__(self, base_path: str = "data"):
        self.base = Path(base_path)
        self.today = date.today().isoformat()
    
    def save_raw(self, name: str, data: dict | pd.DataFrame) -> Path:
        """Save immutable API response."""
        path = self.base / "raw" / self.today
        path.mkdir(parents=True, exist_ok=True)
        
        if isinstance(data, pd.DataFrame):
            filepath = path / f"{name}.parquet"
            data.to_parquet(filepath, compression="snappy")
        else:
            filepath = path / f"{name}.json"
            filepath.write_text(json.dumps(data, indent=2, default=str))
        
        return filepath
    
    def save_processed(self, name: str, data: dict | pd.DataFrame) -> Path:
        """Save quant engine output."""
        path = self.base / "processed" / self.today
        path.mkdir(parents=True, exist_ok=True)
        # ... same pattern
    
    def save_report(self, markdown: str, json_data: dict, assets: list[Path]) -> Path:
        """Save final report with all artifacts."""
        path = self.base / "reports" / self.today
        path.mkdir(parents=True, exist_ok=True)
        
        (path / "report.md").write_text(markdown)
        (path / "report.json").write_text(json.dumps(json_data, indent=2))
        
        for asset in assets:
            shutil.copy(asset, path / asset.name)
        
        return path
    
    def list_historical_reports(self) -> list[str]:
        """Return all report dates, newest first."""
        reports_path = self.base / "reports"
        if not reports_path.exists():
            return []
        return sorted([d.name for d in reports_path.iterdir()], reverse=True)
```

#### Git Configuration

```gitignore
# .gitignore
data/raw/
data/processed/

# Keep reports for dashboard
!data/reports/
```

**Why Parquet:**
- 10x smaller than CSV for numeric data
- Column-oriented (fast for analytical queries)
- Schema-aware (catches type drift)
- Industry standard for data engineering

---

### 7. Schema Validation (Pydantic)

**Purpose:** Enforce data contracts at every boundary. Catch issues early, fail loudly.

#### Schema Definitions

```python
# schemas/macro.py

from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class MacroData(BaseModel):
    """Validated macroeconomic data from FRED."""
    
    fed_funds_rate: float = Field(ge=0, le=25, description="Federal funds rate %")
    treasury_10y: float = Field(ge=0, le=20, description="10-year Treasury yield %")
    treasury_2y: float = Field(ge=0, le=20, description="2-year Treasury yield %")
    cpi_yoy: float = Field(ge=-5, le=20, description="CPI year-over-year %")
    unemployment: float = Field(ge=0, le=30, description="Unemployment rate %")
    yield_curve_spread: float = Field(description="10Y - 2Y spread")
    fetched_at: datetime
    
    @field_validator('yield_curve_spread')
    @classmethod
    def calculate_inversion(cls, v):
        return v  # Could add warning logic here
    
    @property
    def yield_curve_inverted(self) -> bool:
        return self.yield_curve_spread < 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "fed_funds_rate": 4.33,
                "treasury_10y": 4.49,
                "treasury_2y": 4.82,
                "cpi_yoy": 2.9,
                "unemployment": 4.1,
                "yield_curve_spread": -0.33,
                "fetched_at": "2025-02-09T10:30:00Z"
            }
        }
```

```python
# schemas/equities.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional

class EquityData(BaseModel):
    """Validated equity data for a single ticker."""
    
    ticker: str = Field(min_length=1, max_length=10)
    current_price: float = Field(gt=0)
    high_52w: float = Field(gt=0)
    low_52w: float = Field(gt=0)
    pe_ratio: Optional[float] = Field(default=None, ge=0)
    forward_pe: Optional[float] = Field(default=None, ge=0)
    peg_ratio: Optional[float] = Field(default=None)
    market_cap: int = Field(gt=0)
    sector: str
    ma_50d: Optional[float] = Field(default=None, gt=0)
    ma_200d: Optional[float] = Field(default=None, gt=0)
    
    @property
    def pct_from_52w_high(self) -> float:
        return (self.current_price - self.high_52w) / self.high_52w
    
    @property
    def above_200d_ma(self) -> bool:
        if self.ma_200d is None:
            return True  # Assume true if no data
        return self.current_price > self.ma_200d
    
    @field_validator('ticker')
    @classmethod
    def uppercase_ticker(cls, v):
        return v.upper()


class EquityDataset(BaseModel):
    """Collection of validated equity data."""
    
    equities: list[EquityData]
    fetched_at: datetime
    
    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([e.model_dump() for e in self.equities])
```

```python
# schemas/llm_output.py

from pydantic import BaseModel, Field, field_validator
from typing import Literal

class Opportunity(BaseModel):
    """Single investment opportunity from LLM."""
    
    ticker: str
    conviction_score: int = Field(ge=1, le=10)
    bull_case: str = Field(min_length=20, max_length=500)
    bear_case: str = Field(min_length=20, max_length=500)
    key_metrics: str = Field(min_length=10, max_length=200)


class Scenario(BaseModel):
    """Allocation scenario from LLM."""
    
    name: str = Field(min_length=3, max_length=50)
    description: str = Field(min_length=20, max_length=300)
    suggested_tickers: list[str] = Field(min_items=1, max_items=5)


class AnalysisOutput(BaseModel):
    """Complete validated LLM output."""
    
    executive_summary: str = Field(min_length=50, max_length=500)
    macro_interpretation: str = Field(min_length=50, max_length=1000)
    opportunities: list[Opportunity] = Field(min_items=1, max_items=10)
    scenarios: list[Scenario] = Field(min_items=2, max_items=4)
    themes_in_focus: str
    risks_to_watch: str
    
    @field_validator('opportunities')
    @classmethod
    def sort_by_conviction(cls, v):
        return sorted(v, key=lambda x: x.conviction_score, reverse=True)
```

#### Usage in Pipeline

```python
# In ingestion layer
raw_data = fred_api.fetch()
validated = MacroData.model_validate(raw_data)  # Raises ValidationError if bad
data_lake.save_raw("fred", validated.model_dump())

# In LLM layer
response = gemini.generate(payload)
try:
    analysis = AnalysisOutput.model_validate_json(response)
except ValidationError as e:
    logger.error(f"LLM output failed validation: {e}")
    # Retry with stricter prompt, or use fallback
```

---

### 8. LLM Evaluation Framework

**Purpose:** Don't trust the LLM blindly. Score every output.

#### Evaluation Metrics

```python
# src/evaluation/groundedness.py

import re
from schemas.llm_output import AnalysisOutput

class GroundednessEvaluator:
    """Check that LLM output is grounded in provided data."""
    
    def __init__(self, payload: dict, analysis: AnalysisOutput):
        self.payload = payload
        self.analysis = analysis
        self.valid_tickers = {opp['ticker'] for opp in payload['opportunities']}
    
    def ticker_validity_score(self) -> float:
        """All mentioned tickers must be in the payload."""
        mentioned = set()
        for opp in self.analysis.opportunities:
            mentioned.add(opp.ticker)
        for scenario in self.analysis.scenarios:
            mentioned.update(scenario.suggested_tickers)
        
        if not mentioned:
            return 0.0
        
        valid = mentioned & self.valid_tickers
        return len(valid) / len(mentioned)
    
    def metrics_citation_score(self) -> float:
        """Check that key_metrics contain actual numbers from payload."""
        scores = []
        for opp in self.analysis.opportunities:
            payload_opp = next(
                (p for p in self.payload['opportunities'] if p['ticker'] == opp.ticker), 
                None
            )
            if not payload_opp:
                scores.append(0.0)
                continue
            
            # Check if PE, PEG, or % from high appear correctly
            mentioned_pe = re.search(r'PE[:\s]+(\d+\.?\d*)', opp.key_metrics)
            if mentioned_pe and payload_opp.get('pe_ratio'):
                if abs(float(mentioned_pe.group(1)) - payload_opp['pe_ratio']) < 1:
                    scores.append(1.0)
                else:
                    scores.append(0.0)  # Hallucinated number
            else:
                scores.append(0.5)  # Can't verify
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def overall_score(self) -> dict:
        return {
            "ticker_validity": self.ticker_validity_score(),
            "metrics_citation": self.metrics_citation_score(),
            "overall": (self.ticker_validity_score() + self.metrics_citation_score()) / 2
        }
```

```python
# src/evaluation/quality_checks.py

class QualityEvaluator:
    """Heuristic checks for reasoning quality."""
    
    def __init__(self, analysis: AnalysisOutput):
        self.analysis = analysis
    
    def has_balanced_cases(self) -> bool:
        """Every opportunity has both bull and bear case."""
        return all(
            len(opp.bull_case) > 20 and len(opp.bear_case) > 20
            for opp in self.analysis.opportunities
        )
    
    def has_diverse_scenarios(self) -> bool:
        """Scenarios offer meaningfully different approaches."""
        names = [s.name.lower() for s in self.analysis.scenarios]
        # Check for variety (not all "growth" or all "value")
        return len(set(names)) == len(names)
    
    def conviction_spread(self) -> float:
        """Good analysis has varied conviction, not all 8s."""
        scores = [o.conviction_score for o in self.analysis.opportunities]
        if len(scores) < 2:
            return 1.0
        return (max(scores) - min(scores)) / 9  # Normalized 0-1
    
    def summary(self) -> dict:
        return {
            "balanced_cases": self.has_balanced_cases(),
            "diverse_scenarios": self.has_diverse_scenarios(),
            "conviction_spread": self.conviction_spread(),
            "passed": all([
                self.has_balanced_cases(),
                self.has_diverse_scenarios(),
                self.conviction_spread() > 0.2
            ])
        }
```

#### Prompt Versioning

```yaml
# prompts/v1.yaml
version: 1
created_at: "2025-02-09"
description: "Initial advisory prompt"

system_prompt: |
  You are a research analyst preparing a weekly investment brief...
  [full prompt here]

user_prompt_template: |
  Here is this week's market data:
  <DATA>
  {json_payload}
  </DATA>
  ...

config:
  model: "gemini-1.5-flash"
  temperature: 0.3
  max_tokens: 2000
```

```python
# src/research_engine/prompts.py

import yaml
from pathlib import Path

class PromptManager:
    def __init__(self, prompts_dir: str = "prompts"):
        self.dir = Path(prompts_dir)
        self.current = self._load_current()
    
    def _load_current(self) -> dict:
        current_path = self.dir / "current.yaml"
        return yaml.safe_load(current_path.read_text())
    
    @property
    def version(self) -> int:
        return self.current['version']
    
    @property
    def system_prompt(self) -> str:
        return self.current['system_prompt']
    
    @property
    def user_template(self) -> str:
        return self.current['user_prompt_template']
    
    @property
    def config(self) -> dict:
        return self.current['config']
```

#### Evaluation Integration

```python
# In main.py, after LLM call:

analysis = generate_analysis(payload, prompt_manager)

# Evaluate
groundedness = GroundednessEvaluator(payload, analysis)
quality = QualityEvaluator(analysis)

eval_results = {
    "prompt_version": prompt_manager.version,
    "groundedness": groundedness.overall_score(),
    "quality": quality.summary(),
    "timestamp": datetime.now().isoformat()
}

data_lake.save_report(report_md, analysis.model_dump(), eval_results)

# Log for observability
if eval_results['groundedness']['overall'] < 0.8:
    logger.warning(f"Low groundedness score: {eval_results['groundedness']}")
```

---

### 9. GitHub Pages Dashboard

**Purpose:** Make the project visible and demoable without running code.

#### Static Site Structure

```
docs/
├── index.html                    # Dashboard landing page
├── reports/
│   ├── 2025-02-09.html          # Individual report pages
│   ├── 2025-02-02.html
│   └── index.html               # Report archive list
├── assets/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── charts.js            # Lightweight charting (Chart.js)
│   └── charts/
│       ├── fear_greed_history.png
│       └── sector_exposure.png
└── adr/
    └── index.html               # Architecture decisions
```

#### Site Builder

```python
# src/dashboard/site_builder.py

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import json

class DashboardBuilder:
    def __init__(self, data_lake: DataLake, output_dir: str = "docs"):
        self.data_lake = data_lake
        self.output = Path(output_dir)
        self.env = Environment(loader=FileSystemLoader("templates/dashboard"))
    
    def build_all(self):
        """Regenerate entire static site."""
        self.output.mkdir(exist_ok=True)
        
        reports = self._load_all_reports()
        
        self._build_index(reports)
        self._build_report_pages(reports)
        self._build_report_archive(reports)
        self._generate_charts(reports)
        self._copy_static_assets()
    
    def _load_all_reports(self) -> list[dict]:
        """Load all historical reports with metadata."""
        reports = []
        for date_str in self.data_lake.list_historical_reports():
            report_path = self.data_lake.base / "reports" / date_str
            
            report_json = json.loads((report_path / "report.json").read_text())
            eval_json = json.loads((report_path / "_eval.json").read_text())
            
            reports.append({
                "date": date_str,
                "analysis": report_json,
                "evaluation": eval_json,
                "markdown": (report_path / "report.md").read_text()
            })
        
        return sorted(reports, key=lambda r: r['date'], reverse=True)
    
    def _build_index(self, reports: list[dict]):
        """Build main dashboard page."""
        template = self.env.get_template("index.html.j2")
        
        latest = reports[0] if reports else None
        
        # Aggregate stats
        stats = {
            "total_reports": len(reports),
            "avg_groundedness": sum(
                r['evaluation']['groundedness']['overall'] for r in reports
            ) / len(reports) if reports else 0,
            "latest_fear_greed": latest['analysis']['macro_environment']['fear_greed_score'] if latest else None
        }
        
        html = template.render(
            latest_report=latest,
            stats=stats,
            recent_reports=reports[:5]
        )
        
        (self.output / "index.html").write_text(html)
    
    def _build_report_pages(self, reports: list[dict]):
        """Build individual report pages."""
        template = self.env.get_template("report.html.j2")
        reports_dir = self.output / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        for report in reports:
            html = template.render(report=report)
            (reports_dir / f"{report['date']}.html").write_text(html)
    
    def _generate_charts(self, reports: list[dict]):
        """Generate static chart images."""
        charts_dir = self.output / "assets" / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)
        
        # Fear & Greed history
        dates = [r['date'] for r in reports]
        scores = [r['analysis']['macro_environment']['fear_greed_score'] for r in reports]
        
        plt.figure(figsize=(10, 4))
        plt.plot(dates, scores, marker='o')
        plt.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
        plt.axhline(y=25, color='green', linestyle='--', alpha=0.3)
        plt.axhline(y=75, color='red', linestyle='--', alpha=0.3)
        plt.title("Fear & Greed Over Time")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(charts_dir / "fear_greed_history.png", dpi=100)
        plt.close()
```

#### Dashboard Templates

```html
<!-- templates/dashboard/index.html.j2 -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>tinyvc Dashboard</title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
    <header>
        <h1>🌱 tinyvc</h1>
        <p>Automated weekly investment research for the patient investor</p>
    </header>
    
    <main>
        <section class="stats-grid">
            <div class="stat-card">
                <span class="stat-value">{{ stats.total_reports }}</span>
                <span class="stat-label">Reports Generated</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">{{ (stats.avg_groundedness * 100)|round }}%</span>
                <span class="stat-label">Avg Groundedness</span>
            </div>
            <div class="stat-card {% if stats.latest_fear_greed < 25 %}fear{% elif stats.latest_fear_greed > 75 %}greed{% endif %}">
                <span class="stat-value">{{ stats.latest_fear_greed }}</span>
                <span class="stat-label">Latest Fear & Greed</span>
            </div>
        </section>
        
        {% if latest_report %}
        <section class="latest-report">
            <h2>Latest Report: {{ latest_report.date }}</h2>
            <div class="executive-summary">
                {{ latest_report.analysis.executive_summary }}
            </div>
            
            <h3>Top Opportunities</h3>
            <div class="opportunities">
                {% for opp in latest_report.analysis.opportunities[:3] %}
                <div class="opportunity-card">
                    <div class="ticker">{{ opp.ticker }}</div>
                    <div class="conviction">{{ opp.conviction_score }}/10</div>
                    <div class="bull-case">{{ opp.bull_case }}</div>
                </div>
                {% endfor %}
            </div>
            
            <a href="reports/{{ latest_report.date }}.html" class="btn">View Full Report →</a>
        </section>
        {% endif %}
        
        <section class="charts">
            <h2>Trends</h2>
            <img src="assets/charts/fear_greed_history.png" alt="Fear & Greed History">
        </section>
        
        <section class="report-archive">
            <h2>Past Reports</h2>
            <ul>
                {% for report in recent_reports %}
                <li>
                    <a href="reports/{{ report.date }}.html">{{ report.date }}</a>
                    <span class="score">Groundedness: {{ (report.evaluation.groundedness.overall * 100)|round }}%</span>
                </li>
                {% endfor %}
            </ul>
            <a href="reports/index.html">View All →</a>
        </section>
    </main>
    
    <footer>
        <p>Built with Python, Gemini, and GitHub Actions</p>
        <p><a href="https://github.com/yourusername/tinyvc">View Source</a></p>
    </footer>
</body>
</html>
```

**Enable GitHub Pages:**
1. Go to repo Settings → Pages
2. Set source to "GitHub Actions"
3. Dashboard will be at `https://yourusername.github.io/tinyvc`

---

#### 5.2 `.github/workflows/weekly_report.yml`

```yaml
name: tinyvc Weekly Report

on:
  schedule:
    - cron: '0 8 * * 0'  # Every Sunday at 8:00 AM UTC
  workflow_dispatch:  # Manual trigger for testing

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=xml --cov-report=term-missing
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false  # Don't fail build on codecov issues

  generate-report:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Restore data lake
        uses: actions/cache@v4
        with:
          path: data/
          key: data-lake-${{ github.run_number }}
          restore-keys: |
            data-lake-
      
      - name: Run pipeline
        env:
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          SMTP_SERVER: ${{ secrets.SMTP_SERVER }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
        run: python src/main.py
      
      - name: Save data lake
        uses: actions/cache@v4
        with:
          path: data/
          key: data-lake-${{ github.run_number }}
      
      - name: Upload report artifact
        uses: actions/upload-artifact@v4
        with:
          name: tinyvc-report-${{ github.run_number }}
          path: |
            data/reports/
            docs/
          retention-days: 90

  deploy-dashboard:
    needs: generate-report
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Download report artifacts
        uses: actions/download-artifact@v4
        with:
          name: tinyvc-report-${{ github.run_number }}
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
          commit_message: "Update dashboard: ${{ github.run_number }}"
```

---

## Configuration Files

#### `config/watchlist.yaml`

```yaml
# Grouped by investment theme
themes:
  ai_compute:
    - NVDA
    - AMD
    - GOOG
    - MSFT
    - META
  
  energy_transition:
    - ENPH
    - FSLR
    - NEE
    - TSLA
  
  biotech_longevity:
    - LLY
    - VRTX
    - REGN
    - ISRG
  
  fintech:
    - V
    - MA
    - SQ
    - PYPL
  
  quality_compounders:
    - AAPL
    - COST
    - UNH
    - BRK-B

# Flat list for processing
all_tickers:
  - NVDA
  - AMD
  - GOOG
  - MSFT
  - META
  - ENPH
  - FSLR
  - NEE
  - TSLA
  - LLY
  - VRTX
  - REGN
  - ISRG
  - V
  - MA
  - SQ
  - PYPL
  - AAPL
  - COST
  - UNH
  - BRK-B
```

#### `config/thresholds.yaml`

```yaml
value_filters:
  max_pe_ratio: 40
  max_peg_ratio: 2.5
  min_market_cap: 1_000_000_000

momentum_filters:
  max_pct_from_52w_high: 0.35
  require_above_200d_ma: false  # Don't exclude beaten-down quality

correlation:
  max_allowed: 0.85

sentiment_context:
  # Fear & Greed influences how opportunities are framed, not what to buy
  # The human always makes the final allocation decision
  
  extreme_fear:  # score < 25
    narrative: "Markets are fearful — historically a good time to accumulate quality"
    highlight: ["beaten_down_quality", "high_growth"]
    framing: "Discounts available on strong names"
    
  fear:  # score 25-45
    narrative: "Cautious sentiment — look for overlooked opportunities"
    highlight: ["quality_compounders", "ai_compute"]
    framing: "Selective buying conditions"
    
  neutral:  # score 45-55
    narrative: "Balanced sentiment — no strong signals either way"
    highlight: ["diversified"]
    framing: "Spread across themes or add to existing positions"
    
  greed:  # score 55-75
    narrative: "Optimism is high — be selective on valuation"
    highlight: ["quality_compounders", "dividends"]
    framing: "Favor proven winners at reasonable prices"
    
  extreme_greed:  # score > 75
    narrative: "Euphoria zone — historically poor entry points"
    highlight: ["quality_compounders", "low_volatility"]
    framing: "Extra scrutiny on valuation; patience may pay off"
```

---

## Dependencies

#### `requirements.txt`

```
# Data ingestion
yfinance>=0.2.36
fredapi>=0.5.1
requests>=2.31.0
beautifulsoup4>=4.12.0

# Data processing
pandas>=2.1.0
numpy>=1.24.0
pyarrow>=14.0.0           # Parquet support

# Schema validation
pydantic>=2.5.0

# Visualization
matplotlib>=3.8.0
seaborn>=0.13.0

# LLM
google-generativeai>=0.4.0

# Templating & email
Jinja2>=3.1.0
markdown>=3.5.0

# Config
pyyaml>=6.0.0

# Logging & observability
structlog>=23.2.0
```

#### `requirements-dev.txt`

```
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
hypothesis>=6.92.0
responses>=0.24.0
freezegun>=1.2.0

# Code quality
black>=23.12.0
ruff>=0.1.9
mypy>=1.8.0
pre-commit>=3.6.0
```

---

## Containerization

#### `Dockerfile`

```dockerfile
FROM python:3.11-slim

# Metadata
LABEL maintainer="your-email@example.com"
LABEL description="tinyvc - Automated investment research"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY schemas/ ./schemas/
COPY config/ ./config/
COPY templates/ ./templates/
COPY prompts/ ./prompts/

# Create data directories
RUN mkdir -p data/raw data/processed data/reports docs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default command
CMD ["python", "src/main.py"]
```

#### `docker-compose.yml`

```yaml
version: '3.8'

services:
  tinyvc:
    build: .
    environment:
      - FRED_API_KEY=${FRED_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SMTP_SERVER=${SMTP_SERVER}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - RECIPIENT_EMAIL=${RECIPIENT_EMAIL}
    volumes:
      - ./data:/app/data        # Persist data lake
      - ./docs:/app/docs        # Persist dashboard
    command: python src/main.py

  # Local development with hot reload
  dev:
    build: .
    environment:
      - FRED_API_KEY=${FRED_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./src:/app/src
      - ./schemas:/app/schemas
      - ./config:/app/config
      - ./data:/app/data
    command: python -c "print('Dev mode ready. Run commands manually.')" && sleep infinity
```

#### `.dockerignore`

```
.git
.github
__pycache__
*.pyc
.pytest_cache
.coverage
*.egg-info
.env
docs/
data/raw/
data/processed/
tests/
```

#### Local Development

```bash
# Build and run full pipeline
docker-compose run --rm tinyvc

# Run with custom command (e.g., just build dashboard)
docker-compose run --rm tinyvc python -c "from src.dashboard.site_builder import DashboardBuilder; DashboardBuilder().build_all()"

# Interactive development
docker-compose run --rm dev bash
```

---

## Documentation

### README.md

```markdown
# tinyvc 🌱

> Automated weekly investment research for the patient investor.

[![Pipeline Status](https://github.com/yourusername/tinyvc/actions/workflows/weekly_report.yml/badge.svg)](https://github.com/yourusername/tinyvc/actions)
[![Coverage](https://codecov.io/gh/yourusername/tinyvc/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/tinyvc)
[![Dashboard](https://img.shields.io/badge/dashboard-live-brightgreen)](https://yourusername.github.io/tinyvc)

## What It Does

Every Sunday, tinyvc automatically:

1. 📊 **Fetches** macro data (FRED) and equity fundamentals (Yahoo Finance)
2. 🔢 **Filters** using quantitative thresholds (PE, PEG, momentum)
3. 🧮 **Analyzes** correlation to ensure diversification
4. 🤖 **Generates** an advisory research brief using Gemini
5. ✅ **Validates** LLM output for groundedness and quality
6. 📬 **Delivers** via email + updates the [live dashboard](https://yourusername.github.io/tinyvc)

The system is **advisory, not prescriptive** — it surfaces opportunities and scenarios, but you make the final call on where to allocate your $50/week.

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   INGESTION LAYER   │────▶│   QUANT ENGINE      │────▶│  RESEARCH ENGINE    │
│  FRED, Yahoo, CNN   │     │  Filters, Corr Mat  │     │  Gemini + Eval      │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
                                                                  │
                            ┌─────────────────────┐               │
                            │   DELIVERY LAYER    │◀──────────────┘
                            │  Email, Dashboard   │
                            └─────────────────────┘
```

## Sample Output

![Dashboard Screenshot](docs/assets/screenshot.png)

## Quick Start

### Run with Docker

```bash
# Clone the repo
git clone https://github.com/yourusername/tinyvc.git
cd tinyvc

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run the pipeline
docker-compose run --rm tinyvc
```

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest --cov=src

# Run pipeline
python src/main.py
```

## Configuration

Edit `config/watchlist.yaml` to customize which stocks to track:

```yaml
themes:
  ai_compute:
    - NVDA
    - AMD
    - GOOG
```

Edit `config/thresholds.yaml` to adjust quantitative filters.

## Project Structure

```
tinyvc/
├── src/                  # Application code
│   ├── ingestion/        # API clients
│   ├── quant_engine/     # Filtering & math
│   ├── research_engine/  # LLM integration
│   ├── evaluation/       # Quality checks
│   └── dashboard/        # Static site builder
├── schemas/              # Pydantic models
├── prompts/              # Versioned LLM prompts
├── data/                 # Data lake (git-ignored)
├── docs/                 # GitHub Pages dashboard
└── tests/                # Test suite
```

## Why I Built This

I wanted a system that would:
- **Think like a VC** — hunting for asymmetric returns across themes
- **Respect my time** — fully automated, zero manual intervention
- **Help me learn** — advisory output that explains the "why"
- **Be honest** — track LLM quality with groundedness scores

Read more in the [Architecture Decision Records](docs/adr/).

## What I Learned

- **Separating deterministic from probabilistic logic** prevents LLM hallucinations from corrupting data
- **Schema validation at every boundary** catches issues early and makes debugging trivial
- **Prompt versioning** is essential for reproducibility — LLMs are sensitive to small changes
- **Static dashboards** are underrated — zero infrastructure, instant demos

## License

MIT
```

### Architecture Decision Records

```markdown
<!-- docs/adr/001-gemini-over-openai.md -->

# ADR 001: Gemini Over OpenAI

## Status
Accepted

## Context
We needed an LLM API for the research engine. Options included OpenAI (GPT-4), Anthropic (Claude), and Google (Gemini).

## Decision
We chose Gemini 1.5 Flash for the following reasons:

1. **Cost**: ~10x cheaper than GPT-4 for comparable output quality
2. **Speed**: Faster response times for our structured output use case
3. **Free tier**: Generous free tier for development and low-volume production
4. **JSON mode**: Native structured output support

## Consequences
- Vendor lock-in to Google AI Studio
- May need to revisit if Gemini quality degrades
- Prompt templates are somewhat model-specific
```

```markdown
<!-- docs/adr/002-advisory-not-prescriptive.md -->

# ADR 002: Advisory, Not Prescriptive

## Status
Accepted

## Context
Early designs had the LLM output specific dollar allocations ("Put $25 in NVDA"). User feedback indicated this felt too rigid.

## Decision
Changed to an advisory model:
- Rank opportunities by conviction (1-10)
- Present bull AND bear cases
- Offer 2-3 scenarios for different investor priorities
- Let the human make the final allocation

## Consequences
- More valuable learning experience for the user
- Avoids regulatory gray areas around investment advice
- Report is useful even if user disagrees with rankings
- Slightly more complex LLM output schema
```

---

## GitHub Secrets to Configure

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `FRED_API_KEY` | FRED API access | https://fred.stlouisfed.org/docs/api/api_key.html |
| `GEMINI_API_KEY` | Google AI Studio | https://aistudio.google.com/apikey |
| `SMTP_SERVER` | Email server | `smtp.gmail.com` for Gmail |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | Sender email | Your Gmail address |
| `SMTP_PASSWORD` | App password | https://myaccount.google.com/apppasswords |
| `RECIPIENT_EMAIL` | Where to send | Your receiving email |

---

## Testing Strategy

### Test Structure

```
tests/
├── unit/
│   ├── test_filters.py           # Quant logic edge cases
│   ├── test_correlation.py       # Matrix math edge cases
│   ├── test_schemas.py           # Pydantic validation
│   └── test_payload_builder.py   # JSON structure
├── integration/
│   ├── test_ingestion.py         # Mock API responses
│   ├── test_llm_integration.py   # Cached LLM responses
│   └── test_email_delivery.py    # SMTP mock
├── fixtures/
│   ├── fred_response.json        # Frozen API responses
│   ├── yfinance_response.json
│   ├── gemini_response.json
│   └── invalid_responses/        # Malformed data for edge cases
│       ├── missing_fields.json
│       └── out_of_range.json
└── conftest.py                   # Shared fixtures
```

### Unit Tests

```python
# tests/unit/test_filters.py

import pytest
import pandas as pd
from src.quant_engine.filters import apply_filters

class TestValueFilters:
    def test_excludes_high_pe(self):
        """Stocks with PE > threshold should fail value filter."""
        df = pd.DataFrame([
            {"ticker": "HIGH", "pe_ratio": 50, "peg_ratio": 1.0, "market_cap": 1e10},
            {"ticker": "LOW", "pe_ratio": 15, "peg_ratio": 1.0, "market_cap": 1e10},
        ])
        thresholds = {"max_pe_ratio": 35, "max_peg_ratio": 2.5, "min_market_cap": 1e9}
        
        result = apply_filters(df, thresholds, fear_greed_score=50)
        
        assert "HIGH" not in result[result['passes_value_filter']]['ticker'].values
        assert "LOW" in result[result['passes_value_filter']]['ticker'].values
    
    def test_handles_null_pe(self):
        """Stocks with null PE should not crash."""
        df = pd.DataFrame([
            {"ticker": "NULLPE", "pe_ratio": None, "peg_ratio": 1.0, "market_cap": 1e10},
        ])
        thresholds = {"max_pe_ratio": 35, "max_peg_ratio": 2.5, "min_market_cap": 1e9}
        
        result = apply_filters(df, thresholds, fear_greed_score=50)
        assert len(result) == 1  # Should not crash


# tests/unit/test_schemas.py

import pytest
from pydantic import ValidationError
from schemas.macro import MacroData
from schemas.llm_output import AnalysisOutput, Opportunity

class TestMacroSchema:
    def test_valid_data_passes(self):
        data = {
            "fed_funds_rate": 4.33,
            "treasury_10y": 4.49,
            "treasury_2y": 4.82,
            "cpi_yoy": 2.9,
            "unemployment": 4.1,
            "yield_curve_spread": -0.33,
            "fetched_at": "2025-02-09T10:30:00Z"
        }
        result = MacroData.model_validate(data)
        assert result.yield_curve_inverted == True
    
    def test_negative_rate_fails(self):
        data = {
            "fed_funds_rate": -1,  # Invalid
            "treasury_10y": 4.49,
            # ...
        }
        with pytest.raises(ValidationError):
            MacroData.model_validate(data)
    
    def test_fear_greed_out_of_range_fails(self):
        """Fear & Greed must be 0-100."""
        # Test in sentiment schema


class TestLLMOutputSchema:
    def test_opportunities_sorted_by_conviction(self):
        """Opportunities should auto-sort by conviction score."""
        data = {
            "executive_summary": "..." * 20,
            "macro_interpretation": "..." * 20,
            "opportunities": [
                {"ticker": "LOW", "conviction_score": 3, "bull_case": "...", "bear_case": "...", "key_metrics": "..."},
                {"ticker": "HIGH", "conviction_score": 9, "bull_case": "...", "bear_case": "...", "key_metrics": "..."},
            ],
            "scenarios": [...],
            # ...
        }
        result = AnalysisOutput.model_validate(data)
        assert result.opportunities[0].ticker == "HIGH"
```

### Integration Tests with Fixtures

```python
# tests/integration/test_ingestion.py

import pytest
import json
from pathlib import Path
from unittest.mock import patch, Mock

from src.ingestion.fred_client import fetch_macro_data

@pytest.fixture
def fred_fixture():
    """Load frozen FRED API response."""
    path = Path(__file__).parent.parent / "fixtures" / "fred_response.json"
    return json.loads(path.read_text())

def test_fred_client_parses_response(fred_fixture):
    """FRED client correctly parses API response."""
    with patch('src.ingestion.fred_client.requests.get') as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: fred_fixture
        )
        
        result = fetch_macro_data(api_key="test_key")
        
        assert "fed_funds_rate" in result
        assert isinstance(result["fed_funds_rate"], float)


# tests/integration/test_llm_integration.py

@pytest.fixture
def gemini_fixture():
    """Load cached Gemini response for deterministic testing."""
    path = Path(__file__).parent.parent / "fixtures" / "gemini_response.json"
    return json.loads(path.read_text())

def test_gemini_response_validates(gemini_fixture):
    """Cached Gemini response passes schema validation."""
    from schemas.llm_output import AnalysisOutput
    
    result = AnalysisOutput.model_validate(gemini_fixture)
    
    assert len(result.opportunities) >= 1
    assert len(result.scenarios) >= 2
```

### CI Workflow with Coverage

```yaml
# Add to .github/workflows/weekly_report.yml

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests with coverage
        run: |
          pytest --cov=src --cov-report=xml --cov-report=term-missing
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: true
  
  generate-report:
    needs: test  # Only run if tests pass
    runs-on: ubuntu-latest
    # ... rest of pipeline
```

### Dev Dependencies

```txt
# requirements-dev.txt

pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
hypothesis>=6.92.0     # Property-based testing
responses>=0.24.0      # HTTP mocking
freezegun>=1.2.0       # Time mocking
```

---

## Development Roadmap

### Phase 1: Core Pipeline (MVP)
**Goal:** Working end-to-end automation

| Task | Demonstrates |
|------|--------------|
| FRED + Yahoo Finance ingestion | API integration |
| Quantitative filters | Business logic |
| Correlation matrix | Linear algebra |
| Gemini integration | LLM API usage |
| Email delivery | SMTP automation |
| GitHub Actions workflow | CI/CD |

**Deliverable:** Weekly email with research brief

---

### Phase 1.5: Engineering Rigor
**Goal:** Production-quality code

| Task | Demonstrates |
|------|--------------|
| Pydantic schemas for all data contracts | Defensive engineering |
| Structured logging with `structlog` | Observability |
| Test suite with 80%+ coverage | Testing discipline |
| Fixtures for deterministic tests | Test isolation |
| Pre-commit hooks (black, ruff, mypy) | Code quality |

**Deliverable:** Codecov badge, clean CI runs

---

### Phase 2: Data Engineering
**Goal:** Historical analysis capability

| Task | Demonstrates |
|------|--------------|
| Data lake with raw/processed/reports structure | Data architecture |
| Parquet storage for efficient analytics | Columnar storage |
| Prompt versioning (YAML + symlinks) | MLOps awareness |
| LLM evaluation framework | AI quality assurance |
| Evaluation scores logged per report | Metrics tracking |

**Deliverable:** 12+ weeks of historical data, evaluation trends

---

### Phase 2.5: Visibility Layer
**Goal:** Demoable, shareable project

| Task | Demonstrates |
|------|--------------|
| Static GitHub Pages dashboard | Full-stack capability |
| Historical report archive | Data presentation |
| Fear & Greed trend charts | Visualization |
| Pipeline health indicators | Monitoring awareness |
| Professional README with badges | Documentation skill |
| Architecture Decision Records | Technical communication |

**Deliverable:** Live dashboard at `yourusername.github.io/tinyvc`

---

### Phase 3: Polish & Extensions (Optional)
**Goal:** Stretch features for differentiation

| Task | Demonstrates |
|------|--------------|
| Add crypto data (CoinGecko) | Multi-source ingestion |
| Insider trading signals (OpenInsider) | Web scraping |
| Dockerfile + docker-compose | Containerization |
| Property-based tests (Hypothesis) | Advanced testing |
| Slack webhook delivery | Multi-channel notification |

---

## Effort Estimates

| Phase | Estimated Hours | Priority |
|-------|-----------------|----------|
| Phase 1 (MVP) | 10-14 hrs | Must have |
| Phase 1.5 (Rigor) | 4-6 hrs | Must have |
| Phase 2 (Data) | 6-8 hrs | Should have |
| Phase 2.5 (Dashboard) | 4-6 hrs | Should have |
| Phase 3 (Polish) | 8-12 hrs | Nice to have |

**Total for interview-ready portfolio piece:** ~30-40 hours

---

## Handoff Checklist

### Setup
- [ ] Developer has access to repo
- [ ] All GitHub Secrets configured (see table below)
- [ ] FRED API key obtained
- [ ] Gemini API key obtained
- [ ] Gmail App Password created
- [ ] GitHub Pages enabled (Settings → Pages → GitHub Actions)

### Configuration
- [ ] Initial watchlist reviewed and approved
- [ ] Threshold values reviewed and approved
- [ ] Prompt v1.yaml reviewed

### Validation
- [ ] First manual `workflow_dispatch` successful
- [ ] Email received with correct formatting
- [ ] Dashboard deploys to GitHub Pages
- [ ] Test suite passes with >80% coverage

### Documentation
- [ ] README updated with actual repo URL
- [ ] Screenshot added to README
- [ ] At least 2 ADRs written

### Cron Schedule
- [ ] Confirm Sunday 8 AM UTC works for your timezone
- [ ] Adjust if needed (see cron syntax below)

```
# Cron examples
0 8 * * 0   # Sunday 8:00 AM UTC
0 14 * * 0  # Sunday 2:00 PM UTC (6 AM PST)
0 13 * * 0  # Sunday 1:00 PM UTC (8 AM EST)
```

---

*Document Version: 2.0*  
*Last Updated: February 2025*  
*Includes: Data Lake, Schema Validation, LLM Evaluation, GitHub Pages Dashboard, Enhanced Testing, Containerization*
