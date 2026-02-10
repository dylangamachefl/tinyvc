# 🚀 Deployment Checklist

This guide walks you through getting tinyvc live on GitHub Actions.

## Prerequisites

- [ ] GitHub account
- [ ] Gmail account (for email delivery)
- [ ] 30 minutes

---

## Step 1: Get API Keys (15 min)

### FRED API Key (Free)
1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
2. Click "Request API Key"
3. Fill out form (takes 2 minutes)
4. Copy your API key
5. **Save it**: You'll add this to GitHub Secrets later

### Gemini API Key (Free)
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Select a project (or create new one)
4. Copy your API key
5. **Save it**: You'll add this to GitHub Secrets later

### Gmail App Password (Free)
1. **Enable 2FA** on your Google account first
   - Go to https://myaccount.google.com/security
   - Enable "2-Step Verification"
2. Generate App Password
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" → "Other (custom name)"
   - Enter "tinyvc"
   - Click "Generate"
   - Copy the 16-character password (no spaces)
3. **Save it**: This is your `SMTP_PASSWORD`

---

## Step 2: Push Code to GitHub (5 min)

### Create Repository
```bash
# In the tinyvc directory
git init
git add .
git commit -m "Initial commit: tinyvc automated investment pipeline"

# Create repo on GitHub (https://github.com/new)
# Name it: tinyvc
# Keep it public (for free GitHub Actions)
# Don't initialize with README (we already have one)

# Link and push
git remote add origin https://github.com/YOUR_USERNAME/tinyvc.git
git branch -M main
git push -u origin main
```

---

## Step 3: Add GitHub Secrets (5 min)

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** for each:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `FRED_API_KEY` | Your FRED API key | `a1b2c3d4e5f6...` |
| `GEMINI_API_KEY` | Your Gemini API key | `AIza...` |
| `SMTP_SERVER` | `smtp.gmail.com` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` | `587` |
| `SMTP_USER` | Your Gmail address | `yourname@gmail.com` |
| `SMTP_PASSWORD` | Gmail App Password (16 chars) | `abcd efgh ijkl mnop` |
| `RECIPIENT_EMAIL` | Where to send reports | `yourname@gmail.com` |

Optional secrets (have defaults):
| Secret Name | Default | Purpose |
|-------------|---------|---------|
| `WEEKLY_BUDGET` | `50` | Weekly investment budget (USD) |
| `INVESTMENT_HORIZON` | `20` | Investment timeframe (years) |

---

## Step 4: Enable GitHub Pages (2 min)

1. Go to repo → **Settings** → **Pages**
2. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **gh-pages** (will be created automatically)
   - Folder: **/ (root)**
3. Click **Save**

Your dashboard will be live at:
```
https://YOUR_USERNAME.github.io/tinyvc/
```

---

## Step 5: Test the Pipeline (5 min)

### Manual Trigger
1. Go to **Actions** tab
2. Click **"tinyvc Weekly Report"**
3. Click **"Run workflow"** dropdown
4. Select branch: **main**
5. Click **"Run workflow"** button

### Watch Progress
- Test job: Runs test suite (~1 min)
- Generate Report job: Runs pipeline (~2-3 min)
- Deploy Dashboard job: Updates GitHub Pages (~30 sec)

### Check Results
- ✅ Email arrives in your inbox
- ✅ Dashboard updates at `https://YOUR_USERNAME.github.io/tinyvc/`
- ✅ Workflow shows green checkmark

---

## Step 6: Verify Everything Works

### Email Check
- [ ] Report email arrived
- [ ] Has markdown content
- [ ] Has correlation heatmap attachment

### Dashboard Check
- [ ] Dashboard loads at GitHub Pages URL
- [ ] Shows stats (1 run, evaluation score, etc.)
- [ ] Performance section shows recommendations

### Data Lake Check
- [ ] Go to Actions → Latest workflow run → Artifacts
- [ ] Download artifact (contains reports + data)
- [ ] Verify JSON files are populated

---

## Automatic Schedule

The workflow will now run automatically:
- **Every Sunday at 8:00 AM UTC**
- Equivalent to:
  - 3:00 AM EST
  - 12:00 AM PST

To change the schedule, edit `.github/workflows/weekly_report.yml`:
```yaml
schedule:
  - cron: '0 8 * * 0'  # Sunday 8 AM UTC
```

---

## Troubleshooting

### Pipeline Failed
1. Check Actions logs for specific error
2. Common issues:
   - Invalid API keys → double-check secrets
   - Gmail password wrong → use App Password, not regular password
   - 2FA not enabled → enable on Google account first

### Email Not Received
1. Check spam folder
2. Verify `SMTP_PASSWORD` is App Password (16 chars with spaces)
3. Verify 2FA is enabled on Google account
4. Check Actions logs for SMTP errors

### Dashboard Not Updating
1. Wait 2-3 minutes after workflow completes
2. Hard refresh (Ctrl+Shift+R)
3. Check GitHub Pages settings are correct
4. Verify workflow completed successfully

### Tests Failing
Run locally first:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## Local Testing (Optional)

Test the pipeline locally before GitHub Actions:

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API keys

# Run pipeline
python src/main.py

# Check outputs
ls data/
ls outputs/
```

---

## Next Steps

After successful deployment:

1. **Wait for Sunday** - First automatic run
2. **Monitor weekly runs** - Check Actions tab each Monday
3. **Review dashboard** - Track performance over time
4. **Adjust configuration** - Edit `config/watchlist.yaml` or `config/thresholds.yaml`

---

## Support

If you encounter issues:

1. Check `docs/GITHUB_ACTIONS_SETUP.md` for detailed troubleshooting
2. Review workflow logs in Actions tab
3. Verify all secrets are configured correctly
4. Test API keys locally first

---

## Success Criteria ✅

You're fully deployed when:

- [x] First workflow run completes successfully
- [x] Email arrives with report + heatmap
- [x] Dashboard shows data at GitHub Pages URL
- [x] Next Sunday's run executes automatically

**Estimated total time: 30 minutes**

🎉 **Congratulations! Your automated investment pipeline is live!**
