#!/usr/bin/env python3
"""
View All Agent Results - Comprehensive dashboard for all agent outputs.

This script shows:
- Scraper execution results
- Failure patterns detected
- Website structure changes
- Selector adaptations
- LLM analysis results

Usage:
    python scripts/view_all_agent_results.py              # Show latest results
    python scripts/view_all_agent_results.py --summary    # Quick summary
    python scripts/view_all_agent_results.py --structure  # Structure monitoring only
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scraper_monitor import ScraperMonitor
from agents.pattern_analyzer import PatternAnalyzer
from agents.website_structure_monitor import WebsiteStructureMonitor


def load_latest_agent_report() -> Optional[Dict[str, Any]]:
    """Load latest agent report."""
    reports_dir = Path('logs/agent_reports')
    if not reports_dir.exists():
        return None
    
    reports = sorted(reports_dir.glob('scraper_report_*.json'), reverse=True)
    if not reports:
        return None
    
    with open(reports[0], 'r') as f:
        return json.load(f)


def load_structure_changes() -> List[Dict[str, Any]]:
    """Load structure change reports."""
    structure_dir = Path('logs/website_structure')
    if not structure_dir.exists():
        return []
    
    changes = []
    # Look for change reports (if we save them)
    # For now, check baselines to see what's monitored
    return changes


def display_summary():
    """Display quick summary of all agent activity."""
    print("\n" + "="*70)
    print("🤖 AGENT SYSTEM - QUICK SUMMARY")
    print("="*70)
    
    # Scraper monitoring stats
    monitor = ScraperMonitor()
    stats = monitor.get_statistics()
    
    print("\n📊 Scraper Execution Statistics:")
    print(f"   Total Executions: {stats.get('total_executions', 0)}")
    print(f"   Successful: {stats.get('successful', 0)}")
    print(f"   Failed: {stats.get('failed', 0)}")
    print(f"   Success Rate: {stats.get('success_rate', 0):.1%}")
    
    # Pattern analysis
    analyzer = PatternAnalyzer(monitor)
    patterns = analyzer.analyze_patterns()
    
    print(f"\n🔍 Failure Patterns:")
    print(f"   Detected Patterns: {len(patterns)}")
    if patterns:
        for pattern in patterns[:3]:  # Top 3
            print(f"   - {pattern.scraper_name}: {pattern.pattern_type} "
                  f"({pattern.frequency} occurrences, confidence: {pattern.confidence:.2f})")
    
    # Structure monitoring
    structure_monitor = WebsiteStructureMonitor()
    monitored_urls = structure_monitor.get_monitored_urls()
    
    print(f"\n🌐 Website Structure Monitoring:")
    print(f"   Monitored URLs: {len(monitored_urls)}")
    for url, info in list(monitored_urls.items())[:3]:  # First 3
        scraper = info.get('scraper_name', 'unknown')
        print(f"   - {scraper}: {url[:60]}...")
    
    # Latest report
    report = load_latest_agent_report()
    if report:
        print(f"\n📄 Latest Report:")
        print(f"   Generated: {report.get('timestamp', 'Unknown')}")
        summary = report.get('execution_summary', {})
        print(f"   Successful: {summary.get('successful', 0)}/{summary.get('total', 0)}")
        print(f"   Failed: {summary.get('failed', 0)}/{summary.get('total', 0)}")
    
    print("\n" + "="*70)


def display_full_results():
    """Display comprehensive results."""
    print("\n" + "="*70)
    print("🤖 AGENT SYSTEM - COMPREHENSIVE RESULTS")
    print("="*70)
    
    # 1. Scraper Execution Results
    print("\n" + "-"*70)
    print("1️⃣  SCRAPER EXECUTION RESULTS")
    print("-"*70)
    
    monitor = ScraperMonitor()
    stats = monitor.get_statistics()
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Executions: {stats.get('total_executions', 0)}")
    print(f"   Successful: {stats.get('successful', 0)}")
    print(f"   Failed: {stats.get('failed', 0)}")
    print(f"   Success Rate: {stats.get('success_rate', 0):.1%}")
    
    # Recent failures
    failures = monitor.get_recent_failures(limit=5)
    if failures:
        print(f"\n❌ Recent Failures ({len(failures)}):")
        for failure in failures:
            print(f"   - {failure.scraper_name}: {failure.error_type}")
            print(f"     Time: {failure.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     Error: {failure.error_message[:80]}...")
    
    # 2. Pattern Analysis
    print("\n" + "-"*70)
    print("2️⃣  FAILURE PATTERN ANALYSIS")
    print("-"*70)
    
    analyzer = PatternAnalyzer(monitor)
    patterns = analyzer.analyze_patterns()
    
    if patterns:
        print(f"\n🔍 Detected {len(patterns)} Pattern(s):")
        for i, pattern in enumerate(patterns, 1):
            print(f"\n   Pattern {i}:")
            print(f"   - Type: {pattern.pattern_type}")
            print(f"   - Scraper: {pattern.scraper_name}")
            print(f"   - Error: {pattern.error_type}")
            print(f"   - Frequency: {pattern.frequency} occurrence(s)")
            print(f"   - Confidence: {pattern.confidence:.2f}")
            print(f"   - First Seen: {pattern.first_seen.strftime('%Y-%m-%d')}")
            print(f"   - Last Seen: {pattern.last_seen.strftime('%Y-%m-%d')}")
            print(f"   - Suggested Fix: {pattern.suggested_fix}")
    else:
        print("\n✅ No recurring failure patterns detected")
    
    # 3. Website Structure Monitoring
    print("\n" + "-"*70)
    print("3️⃣  WEBSITE STRUCTURE MONITORING")
    print("-"*70)
    
    structure_monitor = WebsiteStructureMonitor()
    monitored_urls = structure_monitor.get_monitored_urls()
    baselines = structure_monitor.get_baselines()
    
    print(f"\n🌐 Monitored URLs: {len(monitored_urls)}")
    print(f"📸 Baseline Snapshots: {len(baselines)}")
    
    if monitored_urls:
        print(f"\n📋 Registered URLs:")
        for url, info in list(monitored_urls.items())[:10]:  # First 10
            scraper = info.get('scraper_name', 'unknown')
            selectors = info.get('selectors', [])
            last_checked = info.get('last_checked')
            status = "✅ Checked" if last_checked else "⏳ Pending"
            print(f"   {status} {scraper}:")
            print(f"      URL: {url[:70]}...")
            if selectors:
                print(f"      Selectors: {', '.join(selectors[:3])}")
    
    # 4. Latest Agent Report
    print("\n" + "-"*70)
    print("4️⃣  LATEST AGENT REPORT")
    print("-"*70)
    
    report = load_latest_agent_report()
    if report:
        print(f"\n📄 Report Generated: {report.get('timestamp', 'Unknown')}")
        
        summary = report.get('execution_summary', {})
        print(f"\n📊 Execution Summary:")
        print(f"   Total Time: {summary.get('total_time', 0):.2f}s")
        print(f"   Successful: {summary.get('successful', 0)}/{summary.get('total', 0)}")
        print(f"   Failed: {summary.get('failed', 0)}/{summary.get('total', 0)}")
        
        # Scraper results
        scraper_results = report.get('scraper_results', {})
        if scraper_results:
            print(f"\n🔍 Scraper Results:")
            for name, result in scraper_results.items():
                status = "✅" if result.get('success') else "❌"
                print(f"   {status} {name}: {result.get('execution_time', 0):.2f}s")
                if not result.get('success'):
                    print(f"      Error: {result.get('error_message', 'Unknown')[:60]}...")
        
        # Patterns
        detected_patterns = report.get('detected_patterns', [])
        if detected_patterns:
            print(f"\n🔍 Detected Patterns: {len(detected_patterns)}")
            for pattern in detected_patterns[:3]:
                print(f"   - {pattern.get('scraper_name')}: {pattern.get('pattern_type')}")
                print(f"     Confidence: {pattern.get('confidence', 0):.2f}")
        
        # LLM status
        llm_enabled = report.get('llm_enabled', False)
        llm_model = report.get('llm_model', 'N/A')
        print(f"\n🤖 LLM Agent: {'ENABLED' if llm_enabled else 'DISABLED'}")
        if llm_enabled:
            print(f"   Model: {llm_model}")
    else:
        print("\n⚠️  No agent reports found")
        print("   Run scrapers with agents first: python scripts/run_scrapers_with_agents.py")
    
    print("\n" + "="*70)


def display_structure_monitoring():
    """Display structure monitoring results only."""
    print("\n" + "="*70)
    print("🌐 WEBSITE STRUCTURE MONITORING RESULTS")
    print("="*70)
    
    structure_monitor = WebsiteStructureMonitor()
    monitored_urls = structure_monitor.get_monitored_urls()
    baselines = structure_monitor.get_baselines()
    
    print(f"\n📊 Monitoring Status:")
    print(f"   Monitored URLs: {len(monitored_urls)}")
    print(f"   Baseline Snapshots: {len(baselines)}")
    
    if monitored_urls:
        print(f"\n📋 Monitored URLs:")
        for url, info in monitored_urls.items():
            scraper = info.get('scraper_name', 'unknown')
            selectors = info.get('selectors', [])
            last_checked = info.get('last_checked')
            
            print(f"\n   Scraper: {scraper}")
            print(f"   URL: {url}")
            print(f"   Selectors: {', '.join(selectors) if selectors else 'None'}")
            if last_checked:
                print(f"   Last Checked: {last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"   Status: ⏳ Not checked yet")
            
            # Check if baseline exists
            if url in baselines:
                baseline = baselines[url]
                print(f"   Baseline: ✅ Created {baseline.timestamp.strftime('%Y-%m-%d')}")
            else:
                print(f"   Baseline: ❌ Not created")
    
    print("\n💡 To check for changes:")
    print("   python scripts/monitor_website_structures.py")
    
    print("\n" + "="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='View all agent results')
    parser.add_argument('--summary', action='store_true', help='Show quick summary')
    parser.add_argument('--structure', action='store_true', help='Show structure monitoring only')
    args = parser.parse_args()
    
    if args.summary:
        display_summary()
    elif args.structure:
        display_structure_monitoring()
    else:
        display_full_results()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

