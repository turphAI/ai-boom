"""
Website Structure Monitoring Agents

Agents that monitor website HTML structures, detect changes, adapt selectors,
and track change history.
"""

from agents.website_structure.website_structure_monitor import (
    WebsiteStructureMonitor,
    StructureSnapshot,
    StructureChange
)
from agents.website_structure.scraper_analyzer import (
    ScraperAnalyzer,
    ScraperUrlInfo
)
from agents.website_structure.selector_adapter import (
    SelectorAdapter,
    SelectorAdaptation
)
from agents.website_structure.change_notifier import ChangeNotifier
from agents.website_structure.change_history import ChangeHistory

__all__ = [
    'WebsiteStructureMonitor',
    'StructureSnapshot',
    'StructureChange',
    'ScraperAnalyzer',
    'ScraperUrlInfo',
    'SelectorAdapter',
    'SelectorAdaptation',
    'ChangeNotifier',
    'ChangeHistory'
]

