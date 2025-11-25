"""
Integration Example - How to use agents with your existing scrapers.

This shows how to integrate the agent monitoring system into your
existing scraper execution flow.
"""

import logging
from agents.scraper_monitor import ScraperMonitor
from agents.pattern_analyzer import PatternAnalyzer
from agents.llm_agent import LLMAgent
from agents.auto_fix_engine import AutoFixEngine

logger = logging.getLogger(__name__)


class AgentIntegratedScraperRunner:
    """
    Example: Scraper runner with integrated agent monitoring.
    
    This wraps your existing scraper execution with agent monitoring.
    """
    
    def __init__(self):
        """Initialize with agent components."""
        # Create agent components
        self.monitor = ScraperMonitor()
        self.analyzer = PatternAnalyzer(self.monitor)
        self.llm_agent = LLMAgent()  # Optional - works without API key
        self.fix_engine = AutoFixEngine(auto_apply=False)  # Manual approval
        
        logger.info("✅ Agent-integrated scraper runner initialized")
    
    def run_scraper_with_monitoring(self, scraper_name: str, scraper_instance):
        """
        Run a scraper with agent monitoring.
        
        This is how you'd integrate agents into your existing code:
        
        Example:
            runner = AgentIntegratedScraperRunner()
            scraper = BDCDiscountScraper()
            result = runner.run_scraper_with_monitoring('bdc_discount', scraper)
        """
        logger.info(f"🚀 Running {scraper_name} with agent monitoring...")
        
        # Monitor the execution
        execution = self.monitor.monitor_execution(
            scraper_name=scraper_name,
            scraper_instance=scraper_instance,
            execute_func=lambda: scraper_instance.execute()
        )
        
        # Check if it failed
        if not execution.success:
            logger.warning(f"❌ {scraper_name} failed: {execution.error_message}")
            
            # Analyze patterns
            patterns = self.analyzer.analyze_patterns(
                scraper_name=scraper_name,
                min_frequency=1
            )
            
            if patterns:
                logger.info(f"🔍 Found {len(patterns)} failure patterns")
                
                # Analyze with LLM (if enabled)
                for pattern in patterns:
                    if pattern.confidence > 0.5:  # Only analyze high-confidence patterns
                        analysis = self.llm_agent.analyze_error(pattern)
                        
                        logger.info(f"💡 Analysis for {pattern.pattern_type}:")
                        logger.info(f"   Root Cause: {analysis.root_cause}")
                        logger.info(f"   Suggested Fix: {analysis.suggested_fix}")
                        
                        # Generate fix proposal
                        proposal = self.fix_engine.propose_fix(pattern, analysis)
                        
                        logger.info(f"📋 Fix proposal created (confidence: {proposal.confidence:.2f})")
                        logger.info(f"   ⏸️  Manual review required before applying")
        
        return execution
    
    def get_health_report(self) -> dict:
        """Get a health report of all monitored scrapers."""
        stats = self.monitor.get_statistics()
        patterns = self.analyzer.analyze_patterns()
        
        return {
            'statistics': stats,
            'patterns': [p.to_dict() for p in patterns],
            'summary': self.analyzer.get_pattern_summary(patterns)
        }


# Example usage function
def example_usage():
    """
    Example of how to use the agent system with your scrapers.
    
    This shows the integration pattern - you can adapt this to your
    existing scraper execution code.
    """
    from scrapers.bdc_discount_scraper import BDCDiscountScraper
    
    # Create runner with agents
    runner = AgentIntegratedScraperRunner()
    
    # Run scraper with monitoring
    scraper = BDCDiscountScraper()
    execution = runner.run_scraper_with_monitoring('bdc_discount', scraper)
    
    # Get health report
    health = runner.get_health_report()
    
    print(f"\n📊 Health Report:")
    print(f"   Success Rate: {health['statistics']['success_rate']:.1%}")
    print(f"   Total Patterns: {health['summary']['total_patterns']}")
    
    return execution


if __name__ == "__main__":
    # Run example
    logging.basicConfig(level=logging.INFO)
    example_usage()

