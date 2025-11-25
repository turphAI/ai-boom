# Scraper Monitoring Agents

AI-powered agents that monitor your scrapers, detect failures, analyze patterns, and automatically fix common issues.

## Quick Start

### 1. Basic Usage (No LLM Required)

```python
from agents.scraper_monitor import ScraperMonitor
from scrapers.bdc_discount_scraper import BDCDiscountScraper

# Create monitor
monitor = ScraperMonitor()

# Run scraper with monitoring
scraper = BDCDiscountScraper()
execution = monitor.monitor_execution(
    scraper_name='bdc_discount',
    scraper_instance=scraper,
    execute_func=lambda: scraper.execute()
)

# Check results
if not execution.success:
    print(f"Failed: {execution.error_message}")
    print(f"Error type: {execution.error_type}")
```

### 2. Pattern Detection

```python
from agents.pattern_analyzer import PatternAnalyzer

# Analyze patterns
analyzer = PatternAnalyzer(monitor)
patterns = analyzer.analyze_patterns()

for pattern in patterns:
    print(f"Pattern: {pattern.pattern_type}")
    print(f"Frequency: {pattern.frequency}")
    print(f"Suggested fix: {pattern.suggested_fix}")
```

### 3. LLM Analysis (Optional)

**Using Anthropic (Claude) - Recommended:**

```python
from agents.llm_agent import LLMAgent

# Set Anthropic API key
import os
os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-your-key-here'
os.environ['ENABLE_LLM_AGENT'] = 'true'

# Agent auto-detects Anthropic
llm_agent = LLMAgent()

if llm_agent.is_enabled():
    analysis = llm_agent.analyze_error(pattern)
    print(f"Root cause: {analysis.root_cause}")
    print(f"Suggested fix: {analysis.suggested_fix}")
```

**Or using OpenAI:**

```python
os.environ['OPENAI_API_KEY'] = 'sk-your-key-here'
llm_agent = LLMAgent(model="gpt-4")
```

## Components

### 1. ScraperMonitor
- **What it does**: Watches scraper executions and collects error data
- **No dependencies**: Works out of the box
- **Output**: Execution history, statistics, error patterns

### 2. PatternAnalyzer
- **What it does**: Identifies recurring failure patterns
- **No dependencies**: Pure Python analysis
- **Output**: Failure patterns with confidence scores

### 3. LLMAgent (Optional)
- **What it does**: Uses AI to analyze errors intelligently
- **Dependencies**: OpenAI or Anthropic API key
- **Output**: Root cause analysis, intelligent fix suggestions

### 4. AutoFixEngine (Future)
- **What it does**: Applies fixes automatically (with approval)
- **Status**: Placeholder for Phase 2 implementation
- **Output**: Fix proposals ready for review

## Integration

### Option 1: Wrap Existing Scraper Execution

```python
from agents.scraper_monitor import ScraperMonitor

monitor = ScraperMonitor()

# Wrap your existing scraper execution
result = monitor.monitor_execution(
    scraper_name='bdc_discount',
    scraper_instance=scraper,
    execute_func=lambda: scraper.execute()
)
```

### Option 2: Use Integrated Runner

```python
from agents.integration_example import AgentIntegratedScraperRunner

runner = AgentIntegratedScraperRunner()
execution = runner.run_scraper_with_monitoring('bdc_discount', scraper)
```

## Configuration

### Environment Variables

```bash
# Enable LLM agent (optional)
ENABLE_LLM_AGENT=true

# Anthropic API key (for Claude) - Recommended, cheaper than OpenAI
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI API key (for GPT-4/GPT-3.5) - Alternative
OPENAI_API_KEY=sk-...

# Log directory (default: logs/agent)
AGENT_LOG_DIR=logs/agent
```

**Quick Setup with Anthropic:**
1. Install: `pip install anthropic`
2. Set key: `export ANTHROPIC_API_KEY=sk-ant-...`
3. Done! Agent auto-detects Anthropic

See `docs/ANTHROPIC_SETUP.md` for detailed instructions.

## Demo

Run the demo to see it in action:

```bash
python agents/demo.py
```

This will:
1. Simulate scraper executions
2. Detect failure patterns
3. Show LLM analysis (if enabled)
4. Generate fix proposals

## How It Works

```
┌─────────────────┐
│  Scraper Runs   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Monitor        │ → Collects execution data
│  (Phase 1)      │ → Logs errors
└────────┬────────┘ → Tracks statistics
         │
         ▼
┌─────────────────┐
│  Pattern        │ → Identifies recurring errors
│  Analyzer       │ → Detects patterns
└────────┬────────┘ → Calculates confidence
         │
         ▼
┌─────────────────┐
│  LLM Agent      │ → Analyzes with AI (optional)
│  (Optional)     │ → Suggests intelligent fixes
└────────┬────────┘ → Explains root causes
         │
         ▼
┌─────────────────┐
│  Auto-Fix       │ → Generates fix proposals
│  Engine         │ → Tests fixes (future)
│  (Future)       │ → Applies with approval
└─────────────────┘
```

## Pros and Cons

### ✅ Pros
- **Saves Time**: Automatically detects and analyzes failures
- **Pattern Recognition**: Identifies recurring issues
- **Intelligent Analysis**: LLM provides context-aware suggestions
- **No Breaking Changes**: Works alongside existing code
- **Optional LLM**: Works without API keys (rule-based fallback)

### ❌ Cons
- **LLM Costs**: ~$5-20/month if using GPT-4/Claude
- **Complexity**: Adds another system to maintain
- **False Positives**: May detect patterns that aren't real issues
- **Manual Fixes**: Still need to implement fixes manually (for now)

## Next Steps

1. **Try the demo**: `python agents/demo.py`
2. **Integrate monitoring**: Add to your scraper execution flow
3. **Enable LLM** (optional): Set API key for intelligent analysis
4. **Review patterns**: Check detected patterns regularly
5. **Future**: Auto-fix engine will apply fixes automatically

## Questions?

See `docs/SCRAPER_AGENT_EXPLANATION.md` for detailed explanation of how agents work.

