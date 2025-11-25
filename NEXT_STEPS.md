# Next Steps - DATABASE_URL Configured ✅

Great! You've added `DATABASE_URL` to GitHub Secrets. Here's what to do next:

## Step 1: Test GitHub Actions Workflow

Now that `DATABASE_URL` is configured, test the automated workflow:

1. **Go to GitHub Actions**
   - Navigate to your repository on GitHub
   - Click the **"Actions"** tab

2. **Manually Trigger the Workflow**
   - Find **"Run Data Scrapers"** workflow in the left sidebar
   - Click on it
   - Click the **"Run workflow"** dropdown button (top right)
   - Click **"Run workflow"** to start it

3. **Monitor Execution**
   - Watch the workflow run in real-time
   - Check each step:
     - ✅ Checkout code
     - ✅ Set up Python
     - ✅ Install dependencies
     - ✅ Run scrapers (this is the main step)
     - ✅ Verify data was stored in PlanetScale

4. **Check Results**
   - If all steps show green checkmarks ✅ → Success!
   - If any step fails ❌ → Click on it to see error logs

## Step 2: Verify Data Was Stored

After the workflow completes successfully:

### Option A: Check GitHub Actions Logs
- Look at the "Verify data was stored in PlanetScale" step
- It should show which scrapers have fresh data

### Option B: Check Your Dashboard
- Visit your dashboard URL
- Check if fresh data appears
- Data should be from the last 24 hours

### Option C: Run Verification Script Locally
```bash
# Activate venv
source venv/bin/activate

# Set DATABASE_URL (same as GitHub secret)
export DATABASE_URL="mysql://user:pass@host.connect.psdb.cloud/database?sslaccept=strict"
export ENVIRONMENT="production"

# Run verification
python scripts/verify_planetscale_data.py
```

## Step 3: Monitor Daily Runs

The workflow is scheduled to run **daily at 2 AM UTC** (9 PM EST / 6 PM PST).

- Check the Actions tab daily for the first few days
- Verify runs are completing successfully
- If runs fail, check the logs to see what went wrong

## Troubleshooting

### Workflow Fails with "DATABASE_URL not set"
- Double-check the secret name is exactly `DATABASE_URL` (case-sensitive)
- Verify it's in **Actions secrets**, not environment secrets
- Try re-adding the secret

### Scrapers Fail Individually
- Check individual scraper logs in the workflow
- Some may fail if external APIs are down (this is normal occasionally)
- Check if `FRED_API_KEY` is needed (optional but recommended)

### Data Not Appearing in Dashboard
- Wait a few minutes after workflow completes
- Check PlanetScale database directly
- Verify dashboard API endpoint: `/api/metrics/current`

## Expected Behavior

✅ **Success looks like:**
- Workflow runs without errors
- All scrapers complete successfully
- Verification step shows fresh data
- Dashboard displays updated metrics within 24 hours

## What Happens Next

1. **Today**: Workflow runs manually (when you trigger it)
2. **Tomorrow**: Workflow runs automatically at 2 AM UTC
3. **Every Day**: Fresh data is collected and stored
4. **Dashboard**: Shows periodic updates automatically

## Additional Configuration (Optional)

### Add FRED_API_KEY (Recommended)
If you want credit_fund and bank_provision scrapers to work better:

1. Get free API key: https://fred.stlouisfed.org/docs/api/api_key.html
2. Add to GitHub Secrets: `FRED_API_KEY`
3. Value: Your FRED API key

### Set Up Notifications (Future)
Consider adding:
- Slack/Discord notifications on workflow failure
- Email alerts if scrapers fail multiple days in a row

## Success Checklist

- [x] DATABASE_URL added to GitHub Secrets
- [ ] GitHub Actions workflow tested manually
- [ ] Workflow completes successfully
- [ ] Data appears in PlanetScale
- [ ] Dashboard shows fresh data
- [ ] Daily automated runs working

## Need Help?

If the workflow fails:
1. Check the error logs in GitHub Actions
2. Run diagnostic script: `python3 scripts/diagnose_scraper_status.py`
3. Verify DATABASE_URL format is correct
4. Check PlanetScale database is accessible

You're all set! 🎉 The system should now run automatically every day.

