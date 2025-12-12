# GitHub Actions Setup Guide - Remote Scrapers

## ✅ Status Check

- [x] GitHub Actions workflow configured (`.github/workflows/run-scrapers.yml`)
- [x] Scrapers tested locally and working
- [x] DATABASE_URL confirmed working with PlanetScale
- [ ] DATABASE_URL added to GitHub Secrets (YOU ARE HERE)
- [ ] First manual workflow run completed
- [ ] Automated daily runs enabled

---

## 🚀 Step 1: Add DATABASE_URL to GitHub Secrets

### Go to Your Repository Secrets Page

**Direct Link:** https://github.com/turphAI/ai-boom/settings/secrets/actions

Or manually navigate:
1. Go to: https://github.com/turphAI/ai-boom
2. Click **Settings** (top menu bar)
3. Scroll down left sidebar → **Secrets and variables** → **Actions**

### Add the Secret

1. Click the **"New repository secret"** button (green button, top right)

2. Fill in the form:
   ```
   Name: DATABASE_URL
   
   Secret: mysql://username:password@host.connect.psdb.cloud/database?sslaccept=strict
   (Replace with your actual PlanetScale connection string)
   ```
   
3. Click **"Add secret"** button

4. You should see `DATABASE_URL` in your secrets list with a green checkmark

---

## 🎯 Step 2: Run the Workflow Manually (First Time)

### Go to GitHub Actions

**Direct Link:** https://github.com/turphAI/ai-boom/actions

Or manually:
1. Go to your repository
2. Click **Actions** tab (top menu bar)

### Trigger the Workflow

1. In the left sidebar, click **"Run Data Scrapers"**

2. You'll see a blue banner that says "This workflow has a workflow_dispatch event trigger"

3. Click the **"Run workflow"** dropdown button (right side)

4. Keep the branch as `main`

5. Click the green **"Run workflow"** button

6. Wait 10-15 seconds, then refresh the page

7. You should see a new workflow run appear with a yellow dot (running)

### Monitor the Run

1. Click on the workflow run (it will say "Run Data Scrapers")

2. Click on **"run-scrapers"** job to see live logs

3. Wait 2-5 minutes for completion

4. ✅ Success = Green checkmark
   ❌ Failure = Red X (check logs for errors)

---

## 🔍 Step 3: Verify Data in Your Dashboard

After the workflow completes successfully:

### Check via API (Terminal)

```bash
curl https://ai-boom-iota.vercel.app/api/metrics/current
```

Look for timestamps from today (2025-10-20).

### Check via Dashboard

Go to: https://ai-boom-iota.vercel.app

You should see:
- Updated metrics with today's date
- Green "healthy" status indicators
- Recent timestamps (not Oct 6th anymore!)

---

## 🎉 Step 4: Confirm Automation is Active

Once the manual run succeeds:

✅ **Your scrapers will now run automatically:**
- **Daily at 2 AM UTC** (9 PM EST / 6 PM PST)
- Even when your laptop is **off** or **asleep**
- Fresh data will appear every 24 hours
- No more Oct 6th data!

### View Future Scheduled Runs

Go to: https://github.com/turphAI/ai-boom/actions

You'll see scheduled runs appear daily at 2 AM UTC.

---

## 🐛 Troubleshooting

### Workflow Fails with "DATABASE_URL not set"

- Make sure you added the secret with **exact name**: `DATABASE_URL`
- Re-check that you clicked "Add secret" and it appears in the secrets list

### Workflow Fails with Python Errors

- Check the workflow logs in GitHub Actions
- Look for specific error messages
- Common issues:
  - Missing dependencies (should auto-install from requirements.txt)
  - API rate limits (SEC EDGAR, FRED)
  - Network timeouts

### Data Still Shows Oct 6th

- Wait 5-10 minutes after workflow completes (dashboard may cache)
- Refresh your browser with Cmd+Shift+R (hard refresh)
- Check API directly: `curl https://ai-boom-iota.vercel.app/api/metrics/current`

### Need to Re-run Manually

Go to: https://github.com/turphAI/ai-boom/actions/workflows/run-scrapers.yml

Click "Run workflow" anytime to trigger manually.

---

## 📊 What Gets Updated

The automated scraper collects and syncs:

1. **Bond Issuance** - Weekly tech company bond issuance from SEC EDGAR
2. **BDC Discount to NAV** - Business Development Company discount rates
3. **Credit Fund Assets** - Private credit fund gross asset values
4. **Bank Provisions** - Bank provisioning for non-bank financial exposures

All data gets stored in your PlanetScale database and appears on your dashboard.

---

## 🎯 Next Steps After Setup

1. **Monitor First Few Runs** - Check Actions tab daily for first week
2. **Set Up Notifications** (Optional) - Get email alerts if workflow fails
3. **Review Dashboard** - Ensure data quality and freshness
4. **Disable Local Cron** - Since GitHub Actions handles it now

---

## ℹ️ Additional Info

- **Free Tier:** 2000 minutes/month (this uses ~5 min/day = 150 min/month)
- **Logs Retention:** 7 days (artifacts downloadable)
- **Manual Runs:** Unlimited via "Run workflow" button
- **Modify Schedule:** Edit `.github/workflows/run-scrapers.yml` cron expression

---

**Need Help?**

If you get stuck, check:
1. GitHub Actions logs for error details
2. PlanetScale database connectivity
3. API endpoints returning data

**Current Status:** Local testing complete ✅ | Need to add GitHub secret next ⏭️


