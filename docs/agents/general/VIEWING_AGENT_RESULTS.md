# How to View Agent Results - Complete Guide

## Quick Overview

There are **3 ways** to view agent results:
1. **Command Line** - View reports locally
2. **GitHub Actions** - Download artifacts from workflow runs
3. **Log Files** - Read raw logs directly

---

## Method 1: Command Line (Recommended)

### View All Results

```bash
source venv/bin/activate
python scripts/view_all_agent_results.py
```

**Shows**:
- ✅ Scraper execution statistics
- ✅ Failure patterns detected
- ✅ Website structure monitoring status
- ✅ Latest agent report summary
- ✅ LLM analysis results

### Quick Summary

```bash
python scripts/view_all_agent_results.py --summary
```

**Shows**: Quick overview of all agent activity

### Structure Monitoring Only

```bash
python scripts/view_all_agent_results.py --structure
```

**Shows**: Website structure monitoring details

### View Latest Agent Report

```bash
python scripts/view_agent_report.py
```

**Shows**: Detailed latest agent report

### View Health Summary

```bash
python scripts/view_agent_report.py --health
```

**Shows**: Current health status of all scrapers

### View All Historical Reports

```bash
python scripts/view_agent_report.py --all
```

**Shows**: All historical agent reports

---

## Method 2: GitHub Actions Artifacts

### Step 1: Go to GitHub Actions

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click on latest workflow run: **"Run Data Scrapers"**

### Step 2: Download Artifacts

At the bottom of the workflow run page, you'll see **Artifacts**:

- **`agent-reports`** - Agent analysis reports (JSON)
- **`scraper-logs`** - Scraper execution logs
- **`structure-reports`** - Website structure monitoring reports (if added)

**To download**:
1. Click on artifact name
2. Click **Download** button
3. Extract ZIP file
4. Open JSON files to view results

### Step 3: View Report Contents

```bash
# After downloading and extracting
cat agent-reports/scraper_report_*.json | jq '.'
```

Or open in your editor - they're JSON files with all the details.

---

## Method 3: Log Files (Direct Access)

### Agent Execution Logs

```bash
# View scraper execution history
cat logs/agent/*_executions.jsonl | tail -20

# View structure monitoring log
cat logs/website_structure_monitor.log | tail -50

# View agent reports
ls -lh logs/agent_reports/
```

### Structure Snapshots

```bash
# View baseline snapshots
ls -lh logs/website_structure/baseline_*.json

# View a specific baseline
cat logs/website_structure/baseline_*.json | jq '.'
```

---

## What You'll See

### 1. Scraper Execution Results

```
📊 Scraper Execution Statistics:
   Total Executions: 45
   Successful: 42
   Failed: 3
   Success Rate: 93.3%

❌ Recent Failures:
   - bdc_discount: HTTP_404_NOT_FOUND
     Time: 2025-11-25 14:30:00
     Error: 404 Not Found: https://example.com/rss
```

### 2. Failure Patterns

```
🔍 Detected Patterns:
   Pattern 1:
   - Type: RECURRING_ERROR
   - Scraper: bdc_discount
   - Error: HTTP_404_NOT_FOUND
   - Frequency: 3 occurrence(s)
   - Confidence: 0.75
   - Suggested Fix: The requested URL may have been removed...
```

### 3. Website Structure Monitoring

```
🌐 Website Structure Monitoring:
   Monitored URLs: 36
   Baseline Snapshots: 36

📋 Registered URLs:
   ✅ Checked bdc_discount:
      URL: https://www.sec.gov/cgi-bin/browse-edgar
      Selectors: .nav-value, #price, .net-asset-value
```

### 4. Selector Adaptations

```
🔧 Selector Adaptations:
   Old: .nav-value
   New: .net-asset-value-per-share
   Confidence: 0.85
   Explanation: The class name changed from nav-value to net-asset-value-per-share
   ✅ Validation: PASSED
```

### 5. LLM Analysis

```
🤖 LLM Analysis:
   Root Cause: The website's HTML structure has been updated...
   Confidence: 0.82
   Suggested Fix: Update CSS selector from .nav-value to .net-asset-value-per-share
   Explanation: The new selector matches the updated HTML structure...
```

---

## Example Workflow

### Daily Review (5 minutes)

```bash
# 1. Quick summary
python scripts/view_all_agent_results.py --summary

# 2. Check for critical issues
python scripts/view_agent_report.py --health

# 3. Review any detected patterns
python scripts/view_agent_report.py
```

### Weekly Deep Dive (15 minutes)

```bash
# 1. Full results
python scripts/view_all_agent_results.py

# 2. All historical reports
python scripts/view_agent_report.py --all

# 3. Structure monitoring status
python scripts/view_all_agent_results.py --structure
```

### When Issues Detected

```bash
# 1. View latest report
python scripts/view_agent_report.py

# 2. Check structure changes
python scripts/monitor_website_structures.py

# 3. Review specific scraper
python scripts/view_agent_report.py --health
```

---

## Report File Locations

### Local Files

```
logs/
├── agent/
│   ├── bdc_discount_executions.jsonl    # Execution history
│   ├── credit_fund_executions.jsonl
│   └── ...
├── agent_reports/
│   ├── scraper_report_20251125_020000.json  # Latest report
│   └── ...
└── website_structure/
    ├── baseline_*.json                   # Structure snapshots
    └── website_structure_monitor.log     # Monitoring log
```

### GitHub Actions Artifacts

After workflow runs:
- **agent-reports/** - JSON reports (30 day retention)
- **scraper-logs/** - Execution logs (7 day retention)

---

## Understanding the Results

### Success Indicators ✅

- **Success Rate > 90%**: System healthy
- **No Patterns Detected**: No recurring issues
- **All Selectors Valid**: Structure monitoring passing
- **LLM Confidence > 0.7**: High confidence in analysis

### Warning Indicators ⚠️

- **Success Rate 70-90%**: Some issues, monitor closely
- **Patterns Detected**: Recurring failures found
- **Selectors Broken**: Structure changes detected
- **LLM Confidence 0.5-0.7**: Medium confidence

### Critical Indicators ❌

- **Success Rate < 70%**: Major issues
- **Critical Patterns**: High-frequency failures
- **Multiple Selectors Broken**: Major structure change
- **LLM Confidence < 0.5**: Low confidence in fixes

---

## Quick Reference

| Command | What It Shows | When to Use |
|---------|--------------|-------------|
| `view_all_agent_results.py` | Complete dashboard | Daily review |
| `view_all_agent_results.py --summary` | Quick summary | Quick check |
| `view_all_agent_results.py --structure` | Structure monitoring | Check website changes |
| `view_agent_report.py` | Latest report | After scraper run |
| `view_agent_report.py --health` | Health summary | Check system status |
| `view_agent_report.py --all` | All reports | Weekly review |
| `monitor_website_structures.py` | Check structures | Manual check |

---

## Tips

1. **Check daily**: Run `--summary` to catch issues early
2. **Review patterns**: Look for recurring failures
3. **Monitor structures**: Check structure changes weekly
4. **Download artifacts**: Keep GitHub Actions artifacts for history
5. **Use JSON**: Parse JSON files for programmatic analysis

---

## Next Steps

After viewing results:

1. **If patterns detected**: Review suggested fixes
2. **If selectors broken**: Check selector adaptations
3. **If critical issues**: Review LLM analysis for root causes
4. **If all good**: Continue monitoring

Everything is automated - just review the results! 🎉

