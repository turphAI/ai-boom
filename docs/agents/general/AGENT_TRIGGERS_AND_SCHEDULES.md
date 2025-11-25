# Agent Triggers and Schedules - Complete Guide

## Overview

This document explains when each agent runs and what triggers them.

## Agent Execution Flow

```
┌─────────────────────────────────────────┐
│  GitHub Actions Workflow                │
│  Trigger: Daily at 2 AM UTC             │
│  OR: Manual (workflow_dispatch)        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 1: Monitor Website Structures    │
│  (NEW - Proactive)                      │
│  - Checks HTML structures               │
│  - Detects changes before scrapers run  │
│  - Adapts selectors if needed           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 2: Run Scrapers                   │
│  - Executes all 4 scrapers             │
│  - With agent monitoring                │
│  - Collects execution data              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 3: Agent Analysis                 │
│  - Pattern detection                    │
│  - LLM error analysis                   │
│  - Fix proposals                        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 4: Generate Reports               │
│  - Upload as GitHub Actions artifacts   │
│  - Available for review                 │
└─────────────────────────────────────────┘
```

## When Each Agent Runs

### 1. Website Structure Monitor

**Trigger**: 
- ✅ **Automated**: Runs daily at 2 AM UTC (before scrapers)
- ✅ **Manual**: Can run anytime via `python scripts/monitor_website_structures.py`

**What it does**:
- Checks HTML structures of monitored URLs
- Detects changes before scrapers break
- Adapts selectors using LLM if changes found

**Schedule**: 
- Runs **before** scrapers (proactive)
- Takes ~1-2 minutes
- Won't fail workflow if errors (`|| true`)

### 2. Scraper Monitor (Failure Detection)

**Trigger**:
- ✅ **Automated**: Runs during scraper execution (2 AM UTC daily)
- ✅ **Integrated**: Part of `run_scrapers_with_agents.py`

**What it does**:
- Monitors each scraper execution
- Collects error data
- Tracks success/failure rates

**Schedule**:
- Runs **during** scraper execution
- Automatic - no separate trigger needed

### 3. Pattern Analyzer

**Trigger**:
- ✅ **Automated**: Runs after scrapers complete
- ✅ **Integrated**: Part of `run_scrapers_with_agents.py`

**What it does**:
- Analyzes execution history
- Detects recurring failure patterns
- Calculates confidence scores

**Schedule**:
- Runs **after** scrapers complete
- Automatic - analyzes collected data

### 4. LLM Agent (Error Analysis)

**Trigger**:
- ✅ **Automated**: Runs when patterns detected (if enabled)
- ✅ **Conditional**: Only runs if `ENABLE_LLM_AGENT=true`

**What it does**:
- Analyzes errors with Claude
- Generates intelligent fix suggestions
- Explains root causes

**Schedule**:
- Runs **when needed** (on failures)
- Uses Anthropic API (costs apply)

### 5. Selector Adapter

**Trigger**:
- ✅ **Automated**: Runs when structure changes detected
- ✅ **Integrated**: Part of `monitor_website_structures.py`

**What it does**:
- Generates new selectors using LLM
- Validates selectors work
- Provides adaptation suggestions

**Schedule**:
- Runs **when structure changes detected**
- Uses Anthropic API (costs apply)

## Complete Schedule

### Daily Automation (GitHub Actions)

```
2:00 AM UTC - Workflow starts
  ↓
2:00 AM UTC - Monitor website structures (NEW)
  - Check HTML structures
  - Detect changes
  - Adapt selectors if needed
  ↓
2:01 AM UTC - Run scrapers with agent monitoring
  - Execute all 4 scrapers
  - Monitor each execution
  - Collect error data
  ↓
2:05 AM UTC - Analyze patterns
  - Detect recurring failures
  - Analyze with LLM (if enabled)
  - Generate fix proposals
  ↓
2:06 AM UTC - Generate reports
  - Create agent reports
  - Upload as artifacts
  ↓
2:07 AM UTC - Workflow completes
```

### Manual Triggers

You can also trigger manually:

**GitHub Actions**:
- Go to Actions → Run Data Scrapers → Run workflow

**Local**:
```bash
# Structure monitoring
python scripts/monitor_website_structures.py

# Scraper execution with agents
python scripts/run_scrapers_with_agents.py

# View reports
python scripts/view_agent_report.py
```

## Current Status

### ✅ Automated
- **Scrapers**: Daily at 2 AM UTC
- **Scraper Monitoring**: During scraper execution
- **Pattern Analysis**: After scrapers complete
- **Website Structure Monitoring**: Daily at 2 AM UTC (before scrapers)

### ⚙️ Conditional
- **LLM Analysis**: Only if `ENABLE_LLM_AGENT=true` and API key set
- **Selector Adaptation**: Only if structure changes detected

### 📊 Reports
- **Agent Reports**: Generated automatically, uploaded as artifacts
- **Structure Reports**: Generated automatically, stored in `logs/website_structure/`

## Cost Considerations

### Free (No API Calls)
- Structure monitoring (HTML fetching)
- Scraper execution monitoring
- Pattern detection
- Report generation

### Paid (API Calls)
- LLM error analysis: ~$0.01-0.02 per analysis
- Selector adaptation: ~$0.01-0.02 per adaptation
- **Estimated**: $1-5/month total

**Tip**: Set `ENABLE_LLM_AGENT=false` to disable paid features and use free monitoring only.

## Summary

**Website Structure Monitor**:
- ✅ **Runs**: Daily at 2 AM UTC (before scrapers)
- ✅ **Trigger**: GitHub Actions workflow
- ✅ **Manual**: Can run anytime
- ✅ **Status**: Now integrated into workflow!

**All Agents**:
- ✅ Run automatically with GitHub Actions
- ✅ No manual intervention needed
- ✅ Reports available as artifacts

Everything is automated! 🎉

