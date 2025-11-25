"""
Scraper Monitoring Agents

This module provides AI-powered agents organized by functionality:
- Scraper Monitoring: Monitor executions, detect patterns, analyze failures
- Website Structure: Monitor HTML changes, adapt selectors
- Data Quality: Context-aware anomaly detection, correlation analysis
"""

# Scraper Monitoring Agents
from agents.scraper_monitoring.scraper_monitor import ScraperMonitor
from agents.scraper_monitoring.pattern_analyzer import PatternAnalyzer, FailurePattern
from agents.scraper_monitoring.llm_agent import LLMAgent, LLMAnalysis
from agents.scraper_monitoring.auto_fix_engine import AutoFixEngine

# Website Structure Agents
from agents.website_structure.website_structure_monitor import (
    WebsiteStructureMonitor,
    StructureSnapshot,
    StructureChange
)
from agents.website_structure.scraper_analyzer import ScraperAnalyzer, ScraperUrlInfo
from agents.website_structure.selector_adapter import SelectorAdapter, SelectorAdaptation
from agents.website_structure.change_notifier import ChangeNotifier
from agents.website_structure.change_history import ChangeHistory

# Data Quality Agents
from agents.data_quality.context_analyzer import (
    ContextAnalyzer,
    MarketContext,
    MarketContextType
)
from agents.data_quality.enhanced_anomaly_detector import EnhancedAnomalyDetector, AnomalyResult
from agents.data_quality.correlation_engine import CorrelationEngine, CorrelationResult
from agents.data_quality.learning_system import LearningSystem, FeedbackRecord

# Utilities
from agents.utils.email_summary import EmailSummaryGenerator

# Backward compatibility: Allow old-style imports
# These will work: from agents.scraper_monitor import ScraperMonitor
import sys
import importlib

# Create aliases for backward compatibility
_scraper_monitoring = sys.modules['agents.scraper_monitoring']
_website_structure = sys.modules['agents.website_structure']
_data_quality = sys.modules['agents.data_quality']
_utils = sys.modules['agents.utils']

# Add old-style module aliases
sys.modules['agents.scraper_monitor'] = _scraper_monitoring.scraper_monitor
sys.modules['agents.pattern_analyzer'] = _scraper_monitoring.pattern_analyzer
sys.modules['agents.llm_agent'] = _scraper_monitoring.llm_agent
sys.modules['agents.auto_fix_engine'] = _scraper_monitoring.auto_fix_engine

sys.modules['agents.website_structure_monitor'] = _website_structure.website_structure_monitor
sys.modules['agents.scraper_analyzer'] = _website_structure.scraper_analyzer
sys.modules['agents.selector_adapter'] = _website_structure.selector_adapter
sys.modules['agents.change_notifier'] = _website_structure.change_notifier
sys.modules['agents.change_history'] = _website_structure.change_history

sys.modules['agents.context_analyzer'] = _data_quality.context_analyzer
sys.modules['agents.enhanced_anomaly_detector'] = _data_quality.enhanced_anomaly_detector
sys.modules['agents.correlation_engine'] = _data_quality.correlation_engine
sys.modules['agents.learning_system'] = _data_quality.learning_system

sys.modules['agents.email_summary'] = _utils.email_summary

__all__ = [
    # Scraper Monitoring
    'ScraperMonitor',
    'PatternAnalyzer',
    'FailurePattern',
    'LLMAgent',
    'LLMAnalysis',
    'AutoFixEngine',
    # Website Structure
    'WebsiteStructureMonitor',
    'StructureSnapshot',
    'StructureChange',
    'ScraperAnalyzer',
    'ScraperUrlInfo',
    'SelectorAdapter',
    'SelectorAdaptation',
    'ChangeNotifier',
    'ChangeHistory',
    # Data Quality
    'ContextAnalyzer',
    'MarketContext',
    'MarketContextType',
    'EnhancedAnomalyDetector',
    'AnomalyResult',
    'CorrelationEngine',
    'CorrelationResult',
    'LearningSystem',
    'FeedbackRecord',
    # Utilities
    'EmailSummaryGenerator'
]
