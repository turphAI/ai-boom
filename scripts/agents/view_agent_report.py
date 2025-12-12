#!/usr/bin/env python3
"""
View Agent Reports - Display agent analysis and recommendations.

Usage:
    python scripts/view_agent_report.py              # Show latest report
    python scripts/view_agent_report.py --all        # Show all reports
    python scripts/view_agent_report.py --health     # Show health summary
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scraper_monitor import ScraperMonitor
from agents.pattern_analyzer import PatternAnalyzer


def load_latest_report() -> Dict[str, Any]:
    """Load the latest agent report."""
    reports_dir = Path('logs/agent_reports')
    
    if not reports_dir.exists():
        return None
    
    reports = sorted(reports_dir.glob('scraper_report_*.json'), reverse=True)
    
    if not reports:
        return None
    
    with open(reports[0], 'r') as f:
        return json.load(f)


def load_all_reports() -> List[Dict[str, Any]]:
    """Load all agent reports."""
    reports_dir = Path('logs/agent_reports')
    
    if not reports_dir.exists():
        return []
    
    reports = sorted(reports_dir.glob('scraper_report_*.json'), reverse=True)
    
    all_reports = []
    for report_file in reports:
        with open(report_file, 'r') as f:
            all_reports.append(json.load(f))
    
    return all_reports


def display_report(report: Dict[str, Any]):
    """Display a formatted report."""
    print("\n" + "="*60)
    print("📊 AGENT REPORT")
    print("="*60)
    print(f"   Generated: {report.get('timestamp', 'Unknown')}")
    print()
    
    # Execution Summary
    summary = report.get('execution_summary', {})
    print("📋 Execution Summary:")
    print(f"   Total Time: {summary.get('total_time', 0):.2f}s")
    print(f"   Successful: {summary.get('successful', 0)}/{summary.get('total', 0)}")
    print(f"   Failed: {summary.get('failed', 0)}/{summary.get('total', 0)}")
    print()
    
    # Scraper Results
    print("🔍 Scraper Results:")
    for name, result in report.get('scraper_results', {}).items():
        status = "✅" if result.get('success') else "❌"
        print(f"   {status} {name}: {result.get('execution_time', 0):.2f}s")
        if not result.get('success'):
            print(f"      Error: {result.get('error_message', 'Unknown')}")
    print()
    
    # Detected Patterns
    patterns = report.get('detected_patterns', [])
    if patterns:
        print("🔍 Detected Patterns:")
        for i, pattern in enumerate(patterns, 1):
            print(f"\n   Pattern {i}:")
            print(f"   - Type: {pattern.get('pattern_type')}")
            print(f"   - Scraper: {pattern.get('scraper_name')}")
            print(f"   - Error: {pattern.get('error_type')}")
            print(f"   - Frequency: {pattern.get('frequency')} occurrence(s)")
            print(f"   - Confidence: {pattern.get('confidence', 0):.2f}")
            print(f"   - Suggested Fix: {pattern.get('suggested_fix', 'N/A')}")
        print()
    
    # Pattern Summary
    pattern_summary = report.get('pattern_summary', {})
    if pattern_summary.get('total_patterns', 0) > 0:
        print("📊 Pattern Summary:")
        print(f"   Total Patterns: {pattern_summary.get('total_patterns', 0)}")
        print(f"   By Type: {pattern_summary.get('by_type', {})}")
        print(f"   By Scraper: {pattern_summary.get('by_scraper', {})}")
        print()
    
    # LLM Status
    if report.get('llm_enabled'):
        print(f"🤖 LLM Agent: ENABLED ({report.get('llm_model')})")
    else:
        print("📋 LLM Agent: DISABLED (using rule-based analysis)")
    print()


def display_health_summary():
    """Display current health summary."""
    print("\n" + "="*60)
    print("🏥 AGENT HEALTH SUMMARY")
    print("="*60)
    
    monitor = ScraperMonitor()
    analyzer = PatternAnalyzer(monitor)
    
    stats = monitor.get_statistics()
    patterns = analyzer.analyze_patterns()
    summary = analyzer.get_pattern_summary(patterns)
    
    print("\n📊 Overall Statistics:")
    print(f"   Total Executions: {stats.get('total_executions', 0)}")
    print(f"   Successful: {stats.get('successful', 0)}")
    print(f"   Failed: {stats.get('failed', 0)}")
    print(f"   Success Rate: {stats.get('success_rate', 0):.1%}")
    print()
    
    if patterns:
        print("🔍 Active Patterns:")
        for pattern in patterns[:5]:  # Show top 5
            print(f"   - {pattern.scraper_name}: {pattern.pattern_type} "
                  f"({pattern.frequency} occurrences, confidence: {pattern.confidence:.2f})")
        print()
    
    print("📈 Error Types:")
    for error_type, count in stats.get('error_types', {}).items():
        print(f"   - {error_type}: {count}")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='View agent reports')
    parser.add_argument('--all', action='store_true', help='Show all reports')
    parser.add_argument('--health', action='store_true', help='Show health summary')
    args = parser.parse_args()
    
    if args.health:
        display_health_summary()
        return 0
    
    if args.all:
        reports = load_all_reports()
        if not reports:
            print("❌ No reports found. Run scrapers with agents first.")
            return 1
        
        print(f"\n📚 Found {len(reports)} report(s):\n")
        for i, report in enumerate(reports, 1):
            print(f"\n{'='*60}")
            print(f"REPORT {i} of {len(reports)}")
            print('='*60)
            display_report(report)
        
        return 0
    
    # Show latest report
    report = load_latest_report()
    if not report:
        print("❌ No reports found. Run scrapers with agents first:")
        print("   python scripts/run_scrapers_with_agents.py")
        return 1
    
    display_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

