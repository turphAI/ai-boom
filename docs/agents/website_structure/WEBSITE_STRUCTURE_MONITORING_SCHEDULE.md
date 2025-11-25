# Website Structure Monitoring - When It Runs

## Current Status

**❌ NOT automatically triggered yet** - It's a standalone script that needs to be integrated into your automation.

## How to Trigger It

### Option 1: Add to GitHub Actions (Recommended)

Add a new step to your existing workflow:

**File**: `.github/workflows/run-scrapers.yml`

Add this step **before** running scrapers:

```yaml
- name: Monitor website structures
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    ENABLE_LLM_AGENT: true
  run: |
    python scripts/monitor_website_structures.py
```

**When it runs**:
- ✅ Daily at 2 AM UTC (same schedule as scrapers)
- ✅ Before scrapers run (catches issues proactively)
- ✅ Can also be triggered manually via `workflow_dispatch`

### Option 2: Separate GitHub Actions Workflow

Create a new workflow file: `.github/workflows/monitor-structures.yml`

```yaml
name: Monitor Website Structures

on:
  schedule:
    # Run daily at 1 AM UTC (1 hour before scrapers)
    - cron: '0 1 * * *'
  workflow_dispatch: # Allow manual trigger

jobs:
  monitor-structures:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Monitor website structures
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          ENABLE_LLM_AGENT: true
        run: |
          python scripts/monitor_website_structures.py
      
      - name: Upload structure reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: structure-reports
          path: logs/website_structure/
          retention-days: 30
```

**When it runs**:
- ✅ Daily at 1 AM UTC (1 hour before scrapers)
- ✅ Independent schedule
- ✅ Can run more frequently if needed

### Option 3: Add to Existing Scraper Workflow

Integrate it into the scraper execution step:

**File**: `.github/workflows/run-scrapers.yml`

```yaml
- name: Run scrapers with agent monitoring
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
    SEC_EDGAR_EMAIL: ${{ secrets.SEC_EDGAR_EMAIL }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    ENABLE_LLM_AGENT: true
    ENVIRONMENT: production
  run: |
    # Check structures first (proactive)
    python scripts/monitor_website_structures.py || true
    
    # Then run scrapers (with monitoring)
    python scripts/run_scrapers_with_agents.py
```

**When it runs**:
- ✅ Same schedule as scrapers (2 AM UTC daily)
- ✅ Runs before scrapers execute
- ✅ `|| true` means it won't fail the workflow if structure check fails

### Option 4: Local Cron Job

Set up a local cron job:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 1 AM local time)
0 1 * * * cd /Users/turphai/Projects/kiro_aiCrash && source venv/bin/activate && python scripts/monitor_website_structures.py >> logs/structure_monitor.log 2>&1
```

**When it runs**:
- ✅ Daily at 1 AM (local time)
- ✅ Runs on your local machine
- ✅ Good for development/testing

## Recommended Schedule

### Best Practice: Run Before Scrapers

```
1:00 AM UTC - Monitor website structures
2:00 AM UTC - Run scrapers (with agent monitoring)
```

**Why**:
- Structure monitoring is fast (~1-2 minutes)
- Catches issues before scrapers run
- Gives you time to fix if critical changes detected

### Alternative: Run More Frequently

If you want to catch changes faster:

```
Every 6 hours:
- 1:00 AM UTC
- 7:00 AM UTC  
- 1:00 PM UTC
- 7:00 PM UTC
```

**Trade-off**: More API calls, but faster detection

## Current Automation Status

### ✅ Already Automated
- **Scrapers**: Run daily at 2 AM UTC via GitHub Actions
- **Scraper Monitoring**: Integrated into scraper execution

### ❌ NOT Automated Yet
- **Website Structure Monitoring**: Needs to be added

## Quick Setup (Recommended)

Add to your existing GitHub Actions workflow:

```yaml
# Add this step BEFORE running scrapers
- name: Monitor website structures
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    ENABLE_LLM_AGENT: true
  run: |
    python scripts/monitor_website_structures.py || true
```

**That's it!** It will run automatically with your scrapers.

## Manual Trigger

You can also run it manually anytime:

```bash
source venv/bin/activate
python scripts/monitor_website_structures.py
```

## Summary

**Current**: Not automatically triggered (manual only)  
**Recommended**: Add to GitHub Actions workflow  
**Schedule**: Run 1 hour before scrapers (1 AM UTC)  
**Frequency**: Daily (or more often if needed)

Want me to add it to your GitHub Actions workflow now?

