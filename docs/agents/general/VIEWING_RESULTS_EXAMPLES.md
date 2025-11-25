# Viewing Agent Results - Example Outputs

## Example 1: Quick Summary (`--summary`)

```bash
python scripts/view_all_agent_results.py --summary
```

**Output**:
```
======================================================================
🤖 AGENT SYSTEM - QUICK SUMMARY
======================================================================

📊 Scraper Execution Statistics:
   Total Executions: 45
   Successful: 42
   Failed: 3
   Success Rate: 93.3%

🔍 Failure Patterns:
   Detected Patterns: 2
   - bdc_discount: RECURRING_ERROR (3 occurrences, confidence: 0.75)
   - credit_fund: WEBSITE_STRUCTURE_CHANGE (2 occurrences, confidence: 0.60)

🌐 Website Structure Monitoring:
   Monitored URLs: 36
   - bdc_discount: https://www.sec.gov/cgi-bin/browse-edgar...
   - credit_fund: https://www.sec.gov/Archives/edgar/data...
   - bank_provision: https://www.sec.gov/cgi-bin/browse-edgar...

📄 Latest Report:
   Generated: 2025-11-25T02:05:00+00:00
   Successful: 3/4
   Failed: 1/4

======================================================================
```

**Use this**: Daily quick check (30 seconds)

---

## Example 2: Full Dashboard

```bash
python scripts/view_all_agent_results.py
```

**Output**:
```
======================================================================
🤖 AGENT SYSTEM - COMPREHENSIVE RESULTS
======================================================================

----------------------------------------------------------------------
1️⃣  SCRAPER EXECUTION RESULTS
----------------------------------------------------------------------

📊 Overall Statistics:
   Total Executions: 45
   Successful: 42
   Failed: 3
   Success Rate: 93.3%

❌ Recent Failures (5):
   - bdc_discount: HTTP_404_NOT_FOUND
     Time: 2025-11-25 14:30:00
     Error: 404 Not Found: https://example.com/rss
   - credit_fund: PARSING_SELECTOR_ERROR
     Time: 2025-11-25 14:25:00
     Error: CSS selector not found: .nav-value

----------------------------------------------------------------------
2️⃣  FAILURE PATTERN ANALYSIS
----------------------------------------------------------------------

🔍 Detected 2 Pattern(s):

   Pattern 1:
   - Type: RECURRING_ERROR
   - Scraper: bdc_discount
   - Error: HTTP_404_NOT_FOUND
   - Frequency: 3 occurrence(s)
   - Confidence: 0.75
   - First Seen: 2025-11-20
   - Last Seen: 2025-11-25
   - Suggested Fix: The requested URL may have been removed...

   Pattern 2:
   - Type: WEBSITE_STRUCTURE_CHANGE
   - Scraper: credit_fund
   - Error: PARSING_SELECTOR_ERROR
   - Frequency: 2 occurrence(s)
   - Confidence: 0.60
   - First Seen: 2025-11-23
   - Last Seen: 2025-11-25
   - Suggested Fix: Website HTML structure may have changed...

----------------------------------------------------------------------
3️⃣  WEBSITE STRUCTURE MONITORING
----------------------------------------------------------------------

🌐 Monitored URLs: 36
📸 Baseline Snapshots: 36

📋 Registered URLs:
   ✅ Checked bdc_discount:
      URL: https://www.sec.gov/cgi-bin/browse-edgar
      Selectors: .nav-value, #price, .net-asset-value
   ✅ Checked credit_fund:
      URL: https://www.sec.gov/Archives/edgar/data
      Selectors: .//CreditFunds, .//GrossAssetValue

----------------------------------------------------------------------
4️⃣  LATEST AGENT REPORT
----------------------------------------------------------------------

📄 Report Generated: 2025-11-25T02:05:00+00:00

📊 Execution Summary:
   Total Time: 45.23s
   Successful: 3/4
   Failed: 1/4

🔍 Scraper Results:
   ✅ bond_issuance: 12.45s
   ✅ bdc_discount: 15.32s
   ❌ credit_fund: 8.12s
      Error: CSS selector not found: .nav-value
   ✅ bank_provision: 9.34s

🔍 Detected Patterns: 2
   - bdc_discount: RECURRING_ERROR
     Confidence: 0.75
   - credit_fund: WEBSITE_STRUCTURE_CHANGE
     Confidence: 0.60

🤖 LLM Agent: ENABLED (claude-3-sonnet-20240229)

======================================================================
```

**Use this**: Weekly deep dive (5 minutes)

---

## Example 3: Structure Monitoring

```bash
python scripts/view_all_agent_results.py --structure
```

**Output**:
```
======================================================================
🌐 WEBSITE STRUCTURE MONITORING RESULTS
======================================================================

📊 Monitoring Status:
   Monitored URLs: 36
   Baseline Snapshots: 36

📋 Monitored URLs:

   Scraper: bdc_discount
   URL: https://www.sec.gov/cgi-bin/browse-edgar
   Selectors: .nav-value, #price, .net-asset-value
   Last Checked: 2025-11-25 02:00:00
   Baseline: ✅ Created 2025-11-20

   Scraper: credit_fund
   URL: https://www.sec.gov/Archives/edgar/data
   Selectors: .//CreditFunds, .//GrossAssetValue
   Last Checked: 2025-11-25 02:00:00
   Baseline: ✅ Created 2025-11-20

💡 To check for changes:
   python scripts/monitor_website_structures.py

======================================================================
```

**Use this**: Check website monitoring status

---

## Example 4: Latest Agent Report

```bash
python scripts/view_agent_report.py
```

**Output**:
```
============================================================
📊 AGENT REPORT
============================================================
   Generated: 2025-11-25T02:05:00+00:00

📋 Execution Summary:
   Total Time: 45.23s
   Successful: 3/4
   Failed: 1/4

🔍 Scraper Results:
   ✅ bond_issuance: 12.45s
   ✅ bdc_discount: 15.32s
   ❌ credit_fund: 8.12s
      Error: CSS selector not found: .nav-value
   ✅ bank_provision: 9.34s

🔍 Detected Patterns:

   Pattern 1:
   - Type: RECURRING_ERROR
   - Scraper: bdc_discount
   - Error: HTTP_404_NOT_FOUND
   - Frequency: 3 occurrence(s)
   - Confidence: 0.75
   - Suggested Fix: The requested URL may have been removed...

   Pattern 2:
   - Type: WEBSITE_STRUCTURE_CHANGE
   - Scraper: credit_fund
   - Error: PARSING_SELECTOR_ERROR
   - Frequency: 2 occurrence(s)
   - Confidence: 0.60
   - Suggested Fix: Website HTML structure may have changed...

📊 Pattern Summary:
   Total Patterns: 2
   By Type: {'RECURRING_ERROR': 1, 'WEBSITE_STRUCTURE_CHANGE': 1}
   By Scraper: {'bdc_discount': 1, 'credit_fund': 1}

🤖 LLM Agent: ENABLED (claude-3-sonnet-20240229)

============================================================
```

**Use this**: After scraper runs to see detailed analysis

---

## Example 5: Health Summary

```bash
python scripts/view_agent_report.py --health
```

**Output**:
```
============================================================
🏥 AGENT HEALTH SUMMARY
============================================================

📊 Overall Statistics:
   Total Executions: 45
   Successful: 42
   Failed: 3
   Success Rate: 93.3%

🔍 Active Patterns:
   - bdc_discount: RECURRING_ERROR (3 occurrences, confidence: 0.75)
   - credit_fund: WEBSITE_STRUCTURE_CHANGE (2 occurrences, confidence: 0.60)

📈 Error Types:
   - HTTP_404_NOT_FOUND: 3
   - PARSING_SELECTOR_ERROR: 2

============================================================
```

**Use this**: Quick health check

---

## Example 6: GitHub Actions Artifacts

After workflow runs, download artifacts:

**File**: `agent-reports/scraper_report_20251125_020000.json`

```json
{
  "timestamp": "2025-11-25T02:05:00+00:00",
  "execution_summary": {
    "total_time": 45.23,
    "successful": 3,
    "failed": 1,
    "total": 4
  },
  "scraper_results": {
    "bond_issuance": {
      "success": true,
      "execution_time": 12.45,
      "error_message": null,
      "error_type": null
    },
    "credit_fund": {
      "success": false,
      "execution_time": 8.12,
      "error_message": "CSS selector not found: .nav-value",
      "error_type": "PARSING_SELECTOR_ERROR"
    }
  },
  "detected_patterns": [
    {
      "pattern_type": "RECURRING_ERROR",
      "scraper_name": "bdc_discount",
      "error_type": "HTTP_404_NOT_FOUND",
      "frequency": 3,
      "confidence": 0.75,
      "suggested_fix": "The requested URL may have been removed..."
    }
  ],
  "llm_enabled": true,
  "llm_model": "claude-3-sonnet-20240229"
}
```

**Use this**: Programmatic analysis, historical tracking

---

## Quick Reference Card

### Daily (30 seconds)
```bash
python scripts/view_all_agent_results.py --summary
```

### After Scraper Run (2 minutes)
```bash
python scripts/view_agent_report.py
```

### Weekly Review (5 minutes)
```bash
python scripts/view_all_agent_results.py
python scripts/view_agent_report.py --all
```

### Check Structure Changes (1 minute)
```bash
python scripts/view_all_agent_results.py --structure
```

### GitHub Actions
1. Go to Actions → Latest run
2. Download `agent-reports` artifact
3. View JSON files

---

## What to Look For

### ✅ Healthy System
- Success rate > 90%
- No patterns detected
- All selectors valid
- LLM confidence > 0.7

### ⚠️ Needs Attention
- Success rate 70-90%
- Patterns detected
- Some selectors broken
- LLM confidence 0.5-0.7

### ❌ Critical Issues
- Success rate < 70%
- Critical patterns
- Multiple selectors broken
- LLM confidence < 0.5

---

## Pro Tips

1. **Set up daily reminder**: Check `--summary` every morning
2. **Review patterns weekly**: Look for trends
3. **Download artifacts**: Keep GitHub Actions artifacts for history
4. **Use JSON**: Parse JSON files for custom analysis
5. **Check structures**: Monitor website changes proactively

---

That's it! You now know how to view all agent results. 🎉

