#!/usr/bin/env python3
"""
Run all scrapers with Agent Monitoring integrated.

This script runs all scrapers and uses the agent system to:
- Monitor executions
- Detect failure patterns
- Analyze errors with AI (if LLM enabled)
- Generate fix proposals

Usage:
    python scripts/run_scrapers_with_agents.py
"""

import sys
import os
import time
import logging
import json
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.bond_issuance_scraper import BondIssuanceScraper
from scrapers.bdc_discount_scraper import BDCDiscountScraper
from scrapers.credit_fund_scraper import CreditFundScraper
from scrapers.bank_provision_scraper import BankProvisionScraper

# Import agent components
from agents.scraper_monitor import ScraperMonitor
from agents.pattern_analyzer import PatternAnalyzer
from agents.llm_agent import LLMAgent
from agents.auto_fix_engine import AutoFixEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper_with_agents.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AgentIntegratedScraperRunner:
    """Run scrapers with integrated agent monitoring."""
    
    def __init__(self):
        """Initialize with agent components."""
        logger.info("🤖 Initializing Agent-Integrated Scraper Runner...")
        
        # Initialize agent components
        self.monitor = ScraperMonitor()
        self.analyzer = PatternAnalyzer(self.monitor)
        self.llm_agent = LLMAgent()
        self.fix_engine = AutoFixEngine(auto_apply=False)
        
        # Define scrapers
        self.scrapers = {
            'bond_issuance': BondIssuanceScraper(),
            'bdc_discount': BDCDiscountScraper(),
            'credit_fund': CreditFundScraper(),
            'bank_provision': BankProvisionScraper()
        }
        
        logger.info(f"✅ Initialized with {len(self.scrapers)} scrapers")
        if self.llm_agent.is_enabled():
            logger.info(f"   🤖 LLM Agent: ENABLED ({self.llm_agent.model})")
        else:
            logger.info(f"   📋 LLM Agent: DISABLED (using rule-based analysis)")
    
    def run_all_scrapers(self):
        """Run all scrapers with agent monitoring."""
        logger.info("\n" + "="*60)
        logger.info("🚀 Starting Scraper Execution with Agent Monitoring")
        logger.info("="*60)
        logger.info(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        
        results = {}
        start_time = time.time()
        
        # Run each scraper with monitoring
        for name, scraper in self.scrapers.items():
            logger.info(f"\n📊 Running {name} scraper with agent monitoring...")
            
            # Monitor execution
            execution = self.monitor.monitor_execution(
                scraper_name=name,
                scraper_instance=scraper,
                execute_func=lambda s=scraper: s.execute()
            )
            
            # Store result
            results[name] = {
                'success': execution.success,
                'execution_time': execution.execution_time,
                'error_message': execution.error_message,
                'error_type': execution.error_type,
                'timestamp': execution.timestamp.isoformat()
            }
            
            if execution.success:
                logger.info(f"✅ {name} completed successfully in {execution.execution_time:.2f}s")
            else:
                logger.warning(f"❌ {name} failed: {execution.error_message}")
        
        # Calculate summary
        total_time = time.time() - start_time
        successful = sum(1 for r in results.values() if r['success'])
        total = len(results)
        
        logger.info("\n" + "="*60)
        logger.info("📋 Execution Summary")
        logger.info("="*60)
        logger.info(f"   Total execution time: {total_time:.2f}s")
        logger.info(f"   Successful: {successful}/{total}")
        logger.info(f"   Failed: {total - successful}/{total}")
        logger.info("")
        
        for name, result in results.items():
            status = "✅" if result['success'] else "❌"
            logger.info(f"   {status} {name}: {result['execution_time']:.2f}s")
        
        # Analyze patterns if there were failures
        if successful < total:
            logger.info("\n" + "="*60)
            logger.info("🔍 Agent Analysis")
            logger.info("="*60)
            self._analyze_failures()
        
        # Generate report
        report = self._generate_report(results, total_time)
        self._save_report(report)
        
        return results
    
    def _analyze_failures(self):
        """Analyze failures using agent system."""
        logger.info("\n🔍 Analyzing failure patterns...")
        
        # Get patterns
        patterns = self.analyzer.analyze_patterns(min_frequency=1)
        
        if not patterns:
            logger.info("   ℹ️  No recurring patterns detected")
            return
        
        logger.info(f"\n✅ Found {len(patterns)} failure pattern(s):")
        
        for i, pattern in enumerate(patterns, 1):
            logger.info(f"\n   Pattern {i}: {pattern.pattern_type}")
            logger.info(f"   - Scraper: {pattern.scraper_name}")
            logger.info(f"   - Error: {pattern.error_type}")
            logger.info(f"   - Frequency: {pattern.frequency} occurrence(s)")
            logger.info(f"   - Confidence: {pattern.confidence:.2f}")
            logger.info(f"   - Suggested Fix: {pattern.suggested_fix}")
            
            # Use LLM for intelligent analysis if enabled
            if self.llm_agent.is_enabled() and pattern.confidence > 0.5:
                logger.info(f"\n   🤖 LLM Analysis:")
                try:
                    analysis = self.llm_agent.analyze_error(pattern)
                    logger.info(f"   - Root Cause: {analysis.root_cause}")
                    logger.info(f"   - Confidence: {analysis.confidence:.2f}")
                    logger.info(f"   - Suggested Fix: {analysis.suggested_fix}")
                    logger.info(f"   - Explanation: {analysis.explanation}")
                    
                    # Generate fix proposal
                    proposal = self.fix_engine.propose_fix(pattern, analysis)
                    logger.info(f"\n   💡 Fix Proposal Generated:")
                    logger.info(f"   - Confidence: {proposal.confidence:.2f}")
                    logger.info(f"   - Status: Requires manual review")
                    
                except Exception as e:
                    logger.warning(f"   ⚠️  LLM analysis failed: {e}")
    
    def _generate_report(self, results: dict, total_time: float) -> dict:
        """Generate comprehensive report."""
        stats = self.monitor.get_statistics()
        patterns = self.analyzer.analyze_patterns()
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'execution_summary': {
                'total_time': total_time,
                'successful': sum(1 for r in results.values() if r['success']),
                'failed': sum(1 for r in results.values() if not r['success']),
                'total': len(results)
            },
            'scraper_results': results,
            'agent_statistics': stats,
            'detected_patterns': [p.to_dict() for p in patterns],
            'pattern_summary': self.analyzer.get_pattern_summary(patterns),
            'llm_enabled': self.llm_agent.is_enabled(),
            'llm_model': self.llm_agent.model if self.llm_agent.is_enabled() else None
        }
    
    def _save_report(self, report: dict):
        """Save report to file."""
        reports_dir = Path('logs/agent_reports')
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f'scraper_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"\n📄 Report saved to: {report_file}")
    
    def get_health_summary(self) -> dict:
        """Get health summary of all scrapers."""
        stats = self.monitor.get_statistics()
        patterns = self.analyzer.analyze_patterns()
        
        return {
            'overall_stats': stats,
            'patterns': [p.to_dict() for p in patterns],
            'summary': self.analyzer.get_pattern_summary(patterns)
        }


def main():
    """Main entry point."""
    try:
        runner = AgentIntegratedScraperRunner()
        results = runner.run_all_scrapers()
        
        # Exit with error code if any scrapers failed
        failed = sum(1 for r in results.values() if not r['success'])
        if failed > 0:
            logger.warning(f"\n⚠️  {failed} scraper(s) failed. Check agent analysis above.")
            return 1
        
        logger.info("\n🎉 All scrapers completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

