# Agents - Organized by Functionality

This directory contains AI-powered agents organized by their primary function.

## 📁 Directory Structure

```
agents/
├── scraper_monitoring/     # Monitor scraper executions & failures
├── website_structure/      # Monitor website HTML changes
├── data_quality/           # Context-aware anomaly detection
├── utils/                  # Shared utilities
├── examples/               # Example scripts
└── docs/                   # Documentation
```

## 🎯 Agent Groups

### 1. Scraper Monitoring (`scraper_monitoring/`)

Agents that monitor scraper executions and detect failures:

- **`scraper_monitor.py`** - Monitors scraper executions, collects error data
- **`pattern_analyzer.py`** - Analyzes execution history to identify failure patterns
- **`llm_agent.py`** - Uses LLM to analyze errors and suggest fixes
- **`auto_fix_engine.py`** - Generates fix proposals (future: auto-apply)

**Use Case**: Monitor scraper runs, detect recurring failures, get intelligent fix suggestions

### 2. Website Structure (`website_structure/`)

Agents that monitor website HTML structures and adapt selectors:

- **`website_structure_monitor.py`** - Monitors HTML structures for changes
- **`scraper_analyzer.py`** - Auto-discovers URLs and selectors from scraper code
- **`selector_adapter.py`** - Uses LLM to adapt selectors when structure changes
- **`change_notifier.py`** - Alerts when structure changes detected
- **`change_history.py`** - Tracks change history over time

**Use Case**: Detect website changes before scrapers break, adapt selectors automatically

### 3. Data Quality (`data_quality/`)

Agents that provide context-aware anomaly detection:

- **`context_analyzer.py`** - Understands market context (holidays, earnings, FOMC)
- **`enhanced_anomaly_detector.py`** - Context-aware anomaly detection
- **`correlation_engine.py`** - Cross-validates anomalies across metrics
- **`learning_system.py`** - Learns from feedback to improve thresholds

**Use Case**: Reduce false positives, detect real anomalies with context awareness

### 4. Utilities (`utils/`)

Shared utilities:

- **`email_summary.py`** - Generates email summaries from agent results

### 5. Examples (`examples/`)

Example scripts:

- **`demo.py`** - Demo script showing agent usage
- **`integration_example.py`** - Example of integrating agents

## 📦 Importing Agents

### Old Style (Still Works!)

```python
from agents.scraper_monitor import ScraperMonitor
from agents.website_structure_monitor import WebsiteStructureMonitor
from agents.enhanced_anomaly_detector import EnhancedAnomalyDetector
```

### New Style (Organized)

```python
from agents.scraper_monitoring import ScraperMonitor
from agents.website_structure import WebsiteStructureMonitor
from agents.data_quality import EnhancedAnomalyDetector
```

### Main Import (Recommended)

```python
from agents import (
    ScraperMonitor,
    WebsiteStructureMonitor,
    EnhancedAnomalyDetector
)
```

## 🚀 Quick Start

### Scraper Monitoring

```python
from agents.scraper_monitoring import ScraperMonitor, PatternAnalyzer

monitor = ScraperMonitor()
analyzer = PatternAnalyzer(monitor)
patterns = analyzer.analyze_patterns()
```

### Website Structure

```python
from agents.website_structure import WebsiteStructureMonitor

monitor = WebsiteStructureMonitor()
monitor.register_url(url='https://example.com', selectors=['.nav-value'])
changes = monitor.check_for_changes()
```

### Data Quality

```python
from agents.data_quality import EnhancedAnomalyDetector

detector = EnhancedAnomalyDetector()
result = detector.detect_anomaly(
    metric_name='bdc_discount',
    current_value=0.15,
    historical_values=[0.10, 0.11, 0.12, 0.13, 0.14]
)
```

## 📚 Documentation

- **`docs/README.md`** - Detailed agent documentation
- **`docs/QUICK_START_ANTHROPIC.md`** - Quick start guide for Anthropic

## 🔗 Related Scripts

- **`scripts/run_scrapers_with_agents.py`** - Run scrapers with agent monitoring
- **`scripts/monitor_website_structures.py`** - Monitor website structures
- **`scripts/view_agent_report.py`** - View agent analysis reports
- **`scripts/test_enhanced_anomaly_detection.py`** - Test data quality agents

## 🎯 Finding Agents

**Need to monitor scrapers?** → `scraper_monitoring/`
**Need to monitor websites?** → `website_structure/`
**Need anomaly detection?** → `data_quality/`
**Need utilities?** → `utils/`

---

**All imports are backward compatible** - existing code continues to work!
