#!/usr/bin/env python3
"""
Monitor Website Structures - Proactively check for HTML structure changes.

This script monitors registered URLs for structural changes and alerts
when selectors might break.

Usage:
    python scripts/monitor_website_structures.py
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.website_structure_monitor import WebsiteStructureMonitor, StructureChange
from agents.scraper_analyzer import ScraperAnalyzer
from agents.selector_adapter import SelectorAdapter
from agents.llm_agent import LLMAgent
from agents.change_notifier import ChangeNotifier
from agents.change_history import ChangeHistory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/website_structure_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def register_scraper_urls(monitor: WebsiteStructureMonitor):
    """
    Automatically discover and register URLs from scrapers.
    
    Uses ScraperAnalyzer to find URLs and selectors in scraper code.
    """
    logger.info("📋 Auto-discovering URLs from scrapers...")
    
    # Analyze all scrapers
    analyzer = ScraperAnalyzer()
    scraper_urls = analyzer.analyze_all_scrapers()
    
    # Register discovered URLs
    registered_count = 0
    
    for scraper_name, url_infos in scraper_urls.items():
        for url_info in url_infos:
            # Only register static/base URLs (skip dynamic ones)
            if url_info.url_type in ['static', 'base']:
                # Extract selectors (limit to reasonable ones)
                selectors = url_info.selectors[:5] if url_info.selectors else []
                
                # Register URL
                monitor.register_url(
                    url=url_info.url,
                    selectors=selectors,
                    scraper_name=scraper_name,
                    check_interval_hours=24
                )
                registered_count += 1
                logger.info(f"   ✅ Registered: {url_info.url} ({scraper_name})")
    
    logger.info(f"✅ Auto-registered {registered_count} URL(s) from {len(scraper_urls)} scraper(s)")
    
    # If no URLs found, register some common SEC EDGAR URLs manually
    if registered_count == 0:
        logger.info("⚠️  No URLs auto-discovered, registering common SEC EDGAR URLs...")
        monitor.register_url(
            url='https://www.sec.gov/cgi-bin/browse-edgar',
            selectors=['.nav-value', '.net-asset-value'],
            scraper_name='sec_edgar',
            check_interval_hours=24
        )
        registered_count = 1
    
    return registered_count


def main():
    """Main entry point."""
    logger.info("\n" + "="*60)
    logger.info("🌐 Website Structure Monitor")
    logger.info("="*60)
    
    try:
        # Create monitor
        monitor = WebsiteStructureMonitor()
        
        # Register URLs to monitor
        register_scraper_urls(monitor)
        
        # Check for changes
        logger.info("\n🔍 Checking for structure changes...")
        changes = monitor.check_for_changes()
        
        if not changes:
            logger.info("✅ No structure changes detected")
            return 0
        
        # Record changes to history
        history = ChangeHistory()
        for change in changes:
            history.record_change(change)
        logger.info(f"📝 Recorded {len(changes)} change(s) to history")
        
        # Send notifications
        notifier = ChangeNotifier()
        notification_results = notifier.notify_changes(changes)
        if notification_results:
            logger.info(f"📧 Sent notifications via: {', '.join([k for k, v in notification_results.items() if v])}")
        
        # Report changes and adapt selectors
        logger.warning(f"\n⚠️  Detected {len(changes)} structure change(s):")
        
        selector_adapter = SelectorAdapter()
        
        for i, change in enumerate(changes, 1):
            logger.warning(f"\n   Change {i}:")
            logger.warning(f"   - URL: {change.url}")
            logger.warning(f"   - Type: {change.change_type}")
            logger.warning(f"   - Severity: {change.severity}")
            logger.warning(f"   - Description: {change.description}")
            
            if change.broken_selectors:
                logger.warning(f"   - Broken Selectors: {', '.join(change.broken_selectors)}")
                
                # Phase 2: Adapt selectors using LLM
                if change.severity in ['HIGH', 'CRITICAL']:
                    logger.info(f"\n   🔧 Adapting selectors (Phase 2)...")
                    
                    # Fetch current HTML for adaptation
                    try:
                        import requests
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (compatible; BoomBustSentinel/1.0)'
                        }
                        response = requests.get(change.url, headers=headers, timeout=30)
                        html_content = response.text
                        
                        # Adapt selectors
                        adaptations = selector_adapter.adapt_selectors(change, html_content)
                        
                        if adaptations:
                            logger.info(f"   ✅ Generated {len(adaptations)} selector adaptation(s):")
                            for adaptation in adaptations:
                                logger.info(f"      Old: {adaptation.old_selector}")
                                logger.info(f"      New: {adaptation.new_selector}")
                                logger.info(f"      Confidence: {adaptation.confidence:.2f}")
                                logger.info(f"      Explanation: {adaptation.explanation}")
                                
                                # Validate new selector
                                is_valid = selector_adapter.validate_selector(
                                    adaptation.new_selector,
                                    html_content,
                                    adaptation.selector_type
                                )
                                adaptation.validation_status = is_valid
                                
                                if is_valid:
                                    logger.info(f"      ✅ Validation: PASSED")
                                else:
                                    logger.warning(f"      ⚠️  Validation: FAILED")
                        else:
                            logger.warning(f"   ⚠️  Could not adapt selectors automatically")
                            
                    except Exception as e:
                        logger.error(f"   ❌ Error adapting selectors: {e}")
            
            # If LLM is enabled, get intelligent analysis
            llm_agent = LLMAgent()
            if llm_agent.is_enabled() and change.severity in ['HIGH', 'CRITICAL']:
                logger.info(f"\n   🤖 LLM Analysis:")
                logger.info(f"   - Structure change detected, selector adaptations generated above")
        
        logger.warning("\n💡 Action Required:")
        logger.warning("   Review detected changes and update scrapers if needed")
        logger.warning("   Run: python scripts/view_agent_report.py --health")
        
        return 1  # Return error code if changes detected
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

