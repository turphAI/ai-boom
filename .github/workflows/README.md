# GitHub Actions Workflows

This directory contains automated workflows for the Boom-Bust Sentinel application.

## Workflows

### 1. Run Data Scrapers (`run-scrapers.yml`)

Automatically runs data scrapers daily to collect financial metrics and sync them to PlanetScale.

**Schedule:** Daily at 2 AM UTC (9 PM EST / 6 PM PST)

**What it does:**
1. Runs all scrapers (`bond_issuance`, `bdc_discount`, `credit_fund`, `bank_provision`)
2. Collects data from:
   - SEC EDGAR filings (bond issuance)
   - BDC RSS feeds and market data (BDC discounts)
   - FRED API (credit fund assets, bank provisions)
3. Syncs scraped data to PlanetScale database
4. Uploads logs as artifacts for debugging

**Manual Trigger:**
You can manually trigger this workflow from the GitHub Actions tab using the "Run workflow" button.

## Required GitHub Secrets

To enable the scrapers workflow, add these secrets to your GitHub repository:

### Settings > Secrets and variables > Actions > New repository secret

1. **DATABASE_URL** (Required)
   - Your PlanetScale database connection string
   - Format: `mysql://username:password@host/database?sslaccept=strict`
   - Get from: PlanetScale dashboard > Database > Connect > Node.js connection string

2. **FRED_API_KEY** (Optional but recommended)
   - API key for Federal Reserve Economic Data (FRED)
   - Used by credit_fund and bank_provision scrapers
   - Get from: https://fred.stlouisfed.org/docs/api/api_key.html
   - Free to register

3. **SEC_EDGAR_EMAIL** (Required for SEC scrapers)
   - Your email address for SEC EDGAR API compliance
   - Required by SEC for all API requests
   - Used by bank_provision and credit_fund scrapers
   - Example: `turphs.ai@gmail.com`

## How to Add Secrets

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** > **Actions**
4. Click **New repository secret**
5. Add each secret with the exact name shown above
6. Click **Add secret**

## Verifying the Workflow

After the workflow runs:

1. Check the **Actions** tab in GitHub to see workflow status
2. View logs to see scraper execution details
3. Download artifacts to review detailed logs
4. Verify data in production:
   - Visit: https://ai-boom-iota.vercel.app/api/metrics/current
   - Should show updated metrics with recent timestamps

## Troubleshooting

### Workflow fails with "DATABASE_URL not set"
- Add the `DATABASE_URL` secret in GitHub repo settings
- Ensure the connection string is valid and has proper permissions

### Workflow fails with FRED API errors
- Add the `FRED_API_KEY` secret
- Verify the API key is valid at https://fred.stlouisfed.org

### Data not appearing in dashboard
- Check workflow logs for errors
- Verify PlanetScale database tables exist
- Run the seed endpoint manually: `POST /api/metrics/seed`

### Manual Testing

To test the scraper locally before pushing:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="your-planetscale-url"
export FRED_API_KEY="your-fred-api-key"
export ENVIRONMENT="production"

# Run scrapers
python scripts/run_all_scrapers_safe.py

# Sync to PlanetScale
python scripts/sync_scraped_data_to_planetscale.py
```

## Monitoring

- Workflow artifacts are retained for 7 days
- Check logs in the **Actions** tab
- Failed runs will show with a red X
- Successful runs will show with a green checkmark

## Next Steps

Consider adding:
- Slack/Discord notifications on failure
- Metrics on scraper success rates
- Automated alerts if data becomes stale
- Backup of scraped data to cloud storage







