#!/usr/bin/env python3
"""
Send Agent Summary Email - Sends formatted email summary of agent results.

Usage:
    python scripts/send_agent_summary_email.py              # Send latest report
    python scripts/send_agent_summary_email.py --all       # Send all reports
    python scripts/send_agent_summary_email.py --test     # Send test email
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.email_summary import EmailSummaryGenerator
from agents.scraper_monitor import ScraperMonitor
from agents.pattern_analyzer import PatternAnalyzer


def load_latest_report() -> Optional[Dict[str, Any]]:
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


def send_test_email(recipient: Optional[str] = None) -> bool:
    """Send a test email."""
    generator = EmailSummaryGenerator()
    
    # Create test report
    test_report = {
        'timestamp': '2025-11-25T02:05:00+00:00',
        'execution_summary': {
            'total': 4,
            'successful': 3,
            'failed': 1,
            'total_time': 45.23
        },
        'scraper_results': {
            'bond_issuance': {
                'success': True,
                'execution_time': 12.45
            },
            'bdc_discount': {
                'success': True,
                'execution_time': 15.32
            },
            'credit_fund': {
                'success': False,
                'execution_time': 8.12,
                'error_message': 'CSS selector not found: .nav-value'
            },
            'bank_provision': {
                'success': True,
                'execution_time': 9.34
            }
        },
        'detected_patterns': [
            {
                'pattern_type': 'RECURRING_ERROR',
                'scraper_name': 'bdc_discount',
                'frequency': 3,
                'confidence': 0.75,
                'suggested_fix': 'The requested URL may have been removed. Consider updating the RSS feed URL.'
            }
        ],
        'llm_enabled': True,
        'llm_model': 'claude-3-sonnet-20240229'
    }
    
    print("📧 Sending test email...")
    success = generator.send_summary_email(test_report, recipient)
    
    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Failed to send test email. Check email configuration.")
    
    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Send agent summary email')
    parser.add_argument('--all', action='store_true', help='Send all reports')
    parser.add_argument('--test', action='store_true', help='Send test email')
    parser.add_argument('--recipient', type=str, help='Email recipient (overrides default)')
    args = parser.parse_args()
    
    generator = EmailSummaryGenerator()
    
    # Check if email is configured
    if not generator.email_channel.is_configured():
        print("❌ Email not configured!")
        print("\nTo configure email, set one of:")
        print("  - SENDGRID_API_KEY (recommended)")
        print("  - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD")
        print("\nAlso set:")
        print("  - EMAIL_RECIPIENT (or use --recipient)")
        print("  - EMAIL_FROM (optional, defaults to noreply@boom-bust-sentinel.com)")
        return 1
    
    # Test email
    if args.test:
        return 0 if send_test_email(args.recipient) else 1
    
    # Send all reports
    if args.all:
        reports = load_all_reports()
        if not reports:
            print("❌ No reports found. Run scrapers with agents first.")
            return 1
        
        print(f"📧 Sending {len(reports)} email summary(ies)...")
        
        success_count = 0
        for i, report in enumerate(reports, 1):
            print(f"\n[{i}/{len(reports)}] Sending summary for {report.get('timestamp', 'Unknown')}...")
            if generator.send_summary_email(report, args.recipient):
                success_count += 1
                print("✅ Sent successfully")
            else:
                print("❌ Failed to send")
        
        print(f"\n📊 Summary: {success_count}/{len(reports)} sent successfully")
        return 0 if success_count == len(reports) else 1
    
    # Send latest report
    report = load_latest_report()
    if not report:
        print("❌ No reports found. Run scrapers with agents first:")
        print("   python scripts/run_scrapers_with_agents.py")
        return 1
    
    print("📧 Sending email summary for latest report...")
    print(f"   Report timestamp: {report.get('timestamp', 'Unknown')}")
    
    success = generator.send_summary_email(report, args.recipient)
    
    if success:
        print("✅ Email summary sent successfully!")
        return 0
    else:
        print("❌ Failed to send email summary")
        return 1


if __name__ == "__main__":
    sys.exit(main())

