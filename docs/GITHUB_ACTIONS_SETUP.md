# GitHub Actions Setup

This guide explains how to configure GitHub Actions to run the tinyvc pipeline automatically every week.

## Required Secrets

Navigate to your repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `FRED_API_KEY` | Federal Reserve Economic Data API key | https://fred.stlouisfed.org/docs/api/api_key.html |
| `GEMINI_API_KEY` | Google Gemini API key | https://aistudio.google.com/app/apikey |
| `SMTP_SERVER` | SMTP server (e.g., `smtp.gmail.com`) | For Gmail: `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (usually `587`) | For Gmail: `587` |
| `SMTP_USER` | Your email address | Your full Gmail address |
| `SMTP_PASSWORD` | App password (NOT your regular password) | Gmail: https://myaccount.google.com/apppasswords |
| `RECIPIENT_EMAIL` | Where to send reports | Your email |

### Optional Secrets

| Secret Name | Default | Description |
|------------|---------|-------------|
| `WEEKLY_BUDGET` | `50` | Weekly investment budget in USD |
| `INVESTMENT_HORIZON` | `20` | Investment horizon in years |

## Gmail App Password Setup

**Important:** Do NOT use your regular Gmail password. Use an App Password:

1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Select "Mail" and "Other (custom name)"
4. Enter "tinyvc" as the name
5. Click "Generate"
6. Copy the 16-character password (no spaces)
7. Use this as your `SMTP_PASSWORD` secret

## Workflow Schedule

The workflow runs automatically:
- **Every Sunday at 8:00 AM UTC** (cron: `0 8 * * 0`)
- You can also trigger it manually via "Actions" → "tinyvc Weekly Report" → "Run workflow"

## Workflow Jobs

### 1. Test
Runs the test suite to ensure code quality before executing the pipeline.

### 2. Generate Report
- Restores data lake from previous runs (persisted via cache)
- Runs the main pipeline (`python src/main.py`)
- Generates dashboard data
- Saves updated data lake for next run
- Uploads artifacts (reports + dashboard)

### 3. Deploy Dashboard
- Downloads artifacts from previous job
- Deploys `docs/` folder to GitHub Pages
- Dashboard updates automatically

## Enable GitHub Pages

1. Go to repository Settings → Pages
2. Under "Build and deployment" source, select "Deploy from a branch"
3. Select branch: `gh-pages` (created automatically by workflow)
4. Select folder: `/ (root)`
5. Click "Save"

Your dashboard will be live at: `https://[username].github.io/tinyvc/`

## Data Persistence

The workflow uses GitHub Actions cache to persist the `data/` directory between runs:
- Maximum cache size: 10 GB
- Retention: 7 days (automatically refreshed weekly)
- This allows historical analysis and performance tracking

## Manual Trigger

To test the workflow before the scheduled run:

1. Go to Actions tab
2. Click "tinyvc Weekly Report"
3. Click "Run workflow" dropdown
4. Select branch (usually `main`)
5. Click "Run workflow" button

## Troubleshooting

### Pipeline fails on first run
- Check that all secrets are configured correctly
- Verify API keys are valid (test locally first)
- Check Actions logs for specific error messages

### Email not sending
- Verify Gmail App Password (not regular password)
- Check SMTP settings are correct
- Ensure 2FA is enabled on Google account

### Dashboard not updating
- Check that GitHub Pages is enabled
- Verify the workflow completed successfully
- GitHub Pages deployment can take 1-2 minutes

### Data lake not persisting
- Check Actions cache is enabled (should be by default)
- Verify workflow has write permissions to cache
- Large data lakes (>10GB) won't cache fully

## Monitoring

View workflow runs:
1. Go to Actions tab
2. Click on individual run to see logs
3. Each job (`test`, `generate-report`, `deploy-dashboard`) has detailed logs

## Cost Considerations

- **GitHub Actions**: 2,000 free minutes/month for private repos (unlimited for public)
- **FRED API**: Free (5,000 requests/day)
- **Gemini API**: Free tier available (60 requests/minute)
- **SMTP**: Free with Gmail
- **Typical runtime**: ~2-5 minutes per week

Total cost: **$0/month** with free tiers
