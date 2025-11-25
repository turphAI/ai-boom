# Integrating Agents into Your Automation

## Current Situation

Your scrapers are already automated:
- ✅ **GitHub Actions**: Runs daily at 2 AM UTC (`.github/workflows/run-scrapers.yml`)
- ✅ **AWS Lambda**: Scheduled functions (if deployed)
- ✅ **Local Cron**: Daily automation scripts

**But**: Agents are NOT integrated yet - they need to be added to your automation.

## How Agents Work

Agents don't run "in the background" automatically. They:
- ✅ **Monitor** when scrapers run
- ✅ **Analyze** failures after scrapers run
- ✅ **Generate reports** for review

**Key Point**: Agents are called **during** scraper execution, not separately.

## Integration Options

### Option 1: Replace Existing Runner (Recommended)

Update your GitHub Actions workflow to use the agent-integrated runner:

**Current** (`.github/workflows/run-scrapers.yml`):
```yaml
run: |
  python scripts/run_all_scrapers_safe.py
```

**Updated** (with agents):
```yaml
run: |
  python scripts/run_scrapers_with_agents.py
```

This will:
- Run scrapers (same as before)
- Monitor executions automatically
- Detect patterns
- Generate reports
- Upload agent reports as artifacts

### Option 2: Add Agent Monitoring to Existing Runner

Modify `scripts/run_all_scrapers_safe.py` to include agent monitoring without changing the workflow.

### Option 3: Run Agents Separately (Not Recommended)

Run agents as a separate step after scrapers, but this is less efficient.

## Recommended: Update GitHub Actions

Here's what to change in `.github/workflows/run-scrapers.yml`:

```yaml
- name: Run scrapers with agent monitoring
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
    SEC_EDGAR_EMAIL: ${{ secrets.SEC_EDGAR_EMAIL }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}  # Add this
    ENABLE_LLM_AGENT: true  # Add this
    ENVIRONMENT: production
  run: |
    python scripts/run_scrapers_with_agents.py  # Changed from run_all_scrapers_safe.py

- name: Upload agent reports
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: agent-reports
    path: logs/agent_reports/
    retention-days: 30  # Keep reports longer
```

## What Happens Automatically

Once integrated, agents will:

1. **Every time scrapers run** (via GitHub Actions, Lambda, or cron):
   - ✅ Monitor each scraper execution
   - ✅ Collect error data
   - ✅ Detect patterns
   - ✅ Analyze with Claude (if enabled)
   - ✅ Generate reports

2. **You review reports** (when convenient):
   - View latest: `python scripts/view_agent_report.py`
   - Check health: `python scripts/view_agent_report.py --health`

## Setup Steps

### Step 1: Add Anthropic API Key to GitHub Secrets

1. Go to your GitHub repo
2. Settings → Secrets and variables → Actions
3. Add new secret: `ANTHROPIC_API_KEY`
4. Value: Your Anthropic API key (same as in `.env`)

### Step 2: Update GitHub Actions Workflow

Replace `run_all_scrapers_safe.py` with `run_scrapers_with_agents.py`

### Step 3: Test Locally First

```bash
python scripts/run_scrapers_with_agents.py
```

Verify it works before updating GitHub Actions.

### Step 4: Commit and Push

The next GitHub Actions run will automatically use agents!

## Cost Considerations

- **Monitoring**: Free (no API calls)
- **Pattern Detection**: Free (local analysis)
- **LLM Analysis**: ~$0.01-0.02 per analysis (only on failures)
- **Estimated**: $1-5/month for typical usage

**Tip**: You can disable LLM by setting `ENABLE_LLM_AGENT=false` in GitHub Actions if you want free monitoring only.

## Summary

**Answer**: Agents don't run automatically in the background. They need to be integrated into your existing automation.

**Best Approach**: 
1. Replace `run_all_scrapers_safe.py` with `run_scrapers_with_agents.py` in GitHub Actions
2. Add `ANTHROPIC_API_KEY` to GitHub Secrets
3. Agents will automatically monitor every scraper run
4. Review reports when convenient

**Result**: Agents work automatically every time scrapers run, no manual intervention needed!

