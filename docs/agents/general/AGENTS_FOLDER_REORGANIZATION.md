# Agents Folder Reorganization Plan

## Current Structure

All agents are in a flat `agents/` folder:
```
agents/
  ├── scraper_monitor.py
  ├── pattern_analyzer.py
  ├── llm_agent.py
  ├── auto_fix_engine.py
  ├── website_structure_monitor.py
  ├── scraper_analyzer.py
  ├── selector_adapter.py
  ├── change_notifier.py
  ├── change_history.py
  ├── context_analyzer.py
  ├── enhanced_anomaly_detector.py
  ├── correlation_engine.py
  ├── learning_system.py
  ├── email_summary.py
  ├── demo.py
  ├── integration_example.py
  └── README.md
```

## Proposed Structure

Organize by functional groups:

```
agents/
  ├── __init__.py                    # Main exports (backward compatible)
  │
  ├── scraper_monitoring/            # Scraper execution monitoring
  │   ├── __init__.py
  │   ├── scraper_monitor.py        # Monitors scraper executions
  │   ├── pattern_analyzer.py       # Detects failure patterns
  │   ├── llm_agent.py              # LLM-powered analysis
  │   └── auto_fix_engine.py        # Auto-fix proposals
  │
  ├── website_structure/            # Website structure monitoring
  │   ├── __init__.py
  │   ├── website_structure_monitor.py  # Monitors HTML structures
  │   ├── scraper_analyzer.py          # Auto-discovers URLs/selectors
  │   ├── selector_adapter.py         # Adapts selectors with LLM
  │   ├── change_notifier.py          # Alerts on changes
  │   └── change_history.py          # Tracks change history
  │
  ├── data_quality/                 # Data quality & anomaly detection
  │   ├── __init__.py
  │   ├── context_analyzer.py       # Market context detection
  │   ├── enhanced_anomaly_detector.py  # Context-aware detection
  │   ├── correlation_engine.py     # Multi-source correlation
  │   └── learning_system.py        # Feedback & learning
  │
  ├── utils/                        # Shared utilities
  │   ├── __init__.py
  │   └── email_summary.py         # Email summary generation
  │
  ├── examples/                     # Example scripts
  │   ├── demo.py
  │   └── integration_example.py
  │
  └── docs/                        # Documentation
      ├── README.md
      └── QUICK_START_ANTHROPIC.md
```

## Benefits

1. **Clear Organization**: Easy to find related agents
2. **Logical Grouping**: Related functionality together
3. **Scalability**: Easy to add new agents to appropriate groups
4. **Maintainability**: Clear separation of concerns
5. **Backward Compatible**: `__init__.py` maintains existing imports

## Migration Plan

1. Create new folder structure
2. Move files to appropriate folders
3. Update `__init__.py` files to maintain imports
4. Update import statements in codebase
5. Test to ensure everything works

## Import Changes

### Before
```python
from agents.scraper_monitor import ScraperMonitor
from agents.website_structure_monitor import WebsiteStructureMonitor
from agents.enhanced_anomaly_detector import EnhancedAnomalyDetector
```

### After (Still Works!)
```python
# Old imports still work (via __init__.py)
from agents.scraper_monitor import ScraperMonitor
from agents.website_structure_monitor import WebsiteStructureMonitor
from agents.enhanced_anomaly_detector import EnhancedAnomalyDetector

# New organized imports (optional)
from agents.scraper_monitoring import ScraperMonitor
from agents.website_structure import WebsiteStructureMonitor
from agents.data_quality import EnhancedAnomalyDetector
```

## Ready to Reorganize?

This will:
- ✅ Keep all existing imports working
- ✅ Organize agents logically
- ✅ Make it easier to find related code
- ✅ Improve maintainability

Should I proceed with the reorganization?

