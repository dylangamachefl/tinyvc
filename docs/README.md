# Dashboard

The tinyvc dashboard provides visibility into your pipeline's historical performance, LLM quality metrics, and recommendation returns.

## Setup

### 1. Enable GitHub Pages

1. Go to your repository settings
2. Navigate to "Pages"
3. Set source to "Deploy from a branch"
4. Select branch: `main` (or your default branch)
5. Select folder: `/docs`
6. Click "Save"

Your dashboard will be available at: `https://[username].github.io/tinyvc/`

### 2. Generate Dashboard Data

After running the pipeline at least once, generate the dashboard data:

```bash
python scripts/generate_dashboard.py
```

This creates JSON files in `docs/data/`:
- `metadata.json` - General information
- `runs.json` - Pipeline execution history
- `evaluations.json` - LLM quality metrics
- `performance.json` - Recommendation returns

### 3. Commit and Push

```bash
git add docs/data/
git commit -m "Update dashboard data"
git push
```

The dashboard will update automatically on GitHub Pages.

## Features

### 📊 Stats Overview
- Total pipeline runs
- Average LLM quality score
- Total recommendations tracked
- Average 1-month return

### 🎯 Evaluation Metrics
- Quality grades (A-F) for each run
- Macro/ticker/metric consistency scores
- Hallucination detection

### 💰 Performance Tracking
- Recommendation returns (1W, 1M, 3M)
- Alpha vs S&P 500 benchmark
- Conviction score analysis

### 📅 Pipeline Runs
- Execution history
- Duration and status
- Number of opportunities per run

## Automation

To keep the dashboard up-to-date, add this to your CI/CD or cron job after each pipeline run:

```bash
python scripts/generate_dashboard.py
git add docs/data/
git commit -m "Update dashboard $(date +%Y-%m-%d)"
git push
```

## Local Development

To view the dashboard locally:

```bash
# Simple HTTP server
python -m http.server 8000 --directory docs

# Then open: http://localhost:8000
```
