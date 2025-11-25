#!/usr/bin/env python3
"""
Demo script showing how to use the Scraper Monitoring Agent system.

This demonstrates:
1. Monitoring scraper executions
2. Detecting failure patterns
3. Analyzing errors with LLM (optional)
4. Generating fix proposals

Run this to see the agent system in action!
"""

import sys
import os
import logging
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scraper_monitor import ScraperMonitor
from agents.pattern_analyzer import PatternAnalyzer
from agents.llm_agent import LLMAgent
from agents.auto_fix_engine import AutoFixEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_monitoring():
    """Demonstrate basic monitoring functionality."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Monitoring")
    print("="*60)
    
    # Create monitor
    monitor = ScraperMonitor()
    
    print("\n✅ Monitor created")
    print(f"   Log directory: {monitor.log_dir}")
    
    # Simulate some scraper executions
    print("\n📊 Simulating scraper executions...")
    
    from agents.scraper_monitor import ScraperExecution
    
    # Simulate successful execution
    success_exec = ScraperExecution(
        scraper_name='bdc_discount',
        data_source='bdc_discount',
        metric_name='discount_to_nav',
        success=True,
        execution_time=2.5,
        timestamp=datetime.now(timezone.utc),
        data_quality={'has_value': True, 'confidence': 0.95}
    )
    monitor._store_execution(success_exec)
    print("   ✅ Simulated successful execution")
    
    # Simulate failed execution (404 error)
    fail_exec_1 = ScraperExecution(
        scraper_name='bdc_discount',
        data_source='bdc_discount',
        metric_name='discount_to_nav',
        success=False,
        execution_time=1.2,
        timestamp=datetime.now(timezone.utc),
        error_message='404 Not Found: https://example.com/rss',
        error_type='HTTP_404_NOT_FOUND'
    )
    monitor._store_execution(fail_exec_1)
    print("   ❌ Simulated failed execution (404)")
    
    # Simulate another failed execution (same error)
    fail_exec_2 = ScraperExecution(
        scraper_name='bdc_discount',
        data_source='bdc_discount',
        metric_name='discount_to_nav',
        success=False,
        execution_time=1.1,
        timestamp=datetime.now(timezone.utc),
        error_message='404 Not Found: https://example.com/rss',
        error_type='HTTP_404_NOT_FOUND'
    )
    monitor._store_execution(fail_exec_2)
    print("   ❌ Simulated failed execution (404 again)")
    
    # Show statistics
    stats = monitor.get_statistics()
    print(f"\n📈 Statistics:")
    print(f"   Total executions: {stats['total_executions']}")
    print(f"   Successful: {stats['successful']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    
    # Show recent failures
    failures = monitor.get_recent_failures(limit=5)
    print(f"\n❌ Recent failures: {len(failures)}")
    for failure in failures:
        print(f"   - {failure.scraper_name}: {failure.error_type} ({failure.error_message[:50]}...)")
    
    return monitor


def demo_pattern_analysis(monitor: ScraperMonitor):
    """Demonstrate pattern analysis."""
    print("\n" + "="*60)
    print("DEMO 2: Pattern Analysis")
    print("="*60)
    
    # Create analyzer
    analyzer = PatternAnalyzer(monitor)
    
    print("\n🔍 Analyzing failure patterns...")
    
    # Analyze patterns
    patterns = analyzer.analyze_patterns(min_frequency=1)
    
    print(f"\n✅ Found {len(patterns)} patterns:")
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\n   Pattern {i}:")
        print(f"   - Type: {pattern.pattern_type}")
        print(f"   - Scraper: {pattern.scraper_name}")
        print(f"   - Error: {pattern.error_type}")
        print(f"   - Frequency: {pattern.frequency} occurrences")
        print(f"   - Confidence: {pattern.confidence:.2f}")
        print(f"   - Suggested Fix: {pattern.suggested_fix}")
    
    # Show summary
    summary = analyzer.get_pattern_summary(patterns)
    print(f"\n📊 Pattern Summary:")
    print(f"   Total patterns: {summary['total_patterns']}")
    print(f"   By type: {summary['by_type']}")
    print(f"   By scraper: {summary['by_scraper']}")
    
    return analyzer, patterns


def demo_llm_analysis(patterns):
    """Demonstrate LLM analysis (if enabled)."""
    print("\n" + "="*60)
    print("DEMO 3: LLM Analysis (Optional)")
    print("="*60)
    
    # Create LLM agent
    llm_agent = LLMAgent()
    
    if not llm_agent.is_enabled():
        print("\n⚠️  LLM Agent is disabled")
        print("   To enable:")
        print("   1. Set ENABLE_LLM_AGENT=true")
        print("   2. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        print("   3. Install: pip install openai (or anthropic)")
        print("\n   Using rule-based analysis instead...")
        
        # Show rule-based analysis
        if patterns:
            pattern = patterns[0]
            analysis = llm_agent.analyze_error(pattern)
            print(f"\n📋 Rule-Based Analysis:")
            print(f"   Root Cause: {analysis.root_cause}")
            print(f"   Confidence: {analysis.confidence:.2f}")
            print(f"   Suggested Fix: {analysis.suggested_fix}")
            print(f"   Explanation: {analysis.explanation}")
        
        return None
    
    print("\n🤖 LLM Agent is enabled!")
    
    if patterns:
        pattern = patterns[0]
        print(f"\n🔍 Analyzing pattern: {pattern.pattern_type}")
        
        analysis = llm_agent.analyze_error(pattern)
        
        print(f"\n✅ LLM Analysis:")
        print(f"   Root Cause: {analysis.root_cause}")
        print(f"   Confidence: {analysis.confidence:.2f}")
        print(f"   Suggested Fix: {analysis.suggested_fix}")
        print(f"   Explanation: {analysis.explanation}")
        
        return analysis
    
    return None


def demo_fix_proposal(pattern, analysis):
    """Demonstrate fix proposal generation."""
    print("\n" + "="*60)
    print("DEMO 4: Fix Proposal")
    print("="*60)
    
    # Create auto-fix engine
    fix_engine = AutoFixEngine(auto_apply=False)
    
    if analysis:
        print("\n💡 Generating fix proposal...")
        
        proposal = fix_engine.propose_fix(pattern, analysis)
        
        print(f"\n✅ Fix Proposal Created:")
        print(f"   Scraper: {proposal.pattern.scraper_name}")
        print(f"   Pattern: {proposal.pattern.pattern_type}")
        print(f"   Confidence: {proposal.confidence:.2f}")
        print(f"   Root Cause: {proposal.analysis.root_cause}")
        print(f"   Suggested Fix: {proposal.analysis.suggested_fix}")
        
        print(f"\n⏸️  Auto-apply is disabled")
        print(f"   This fix would require manual review and approval")
        
        return proposal
    
    print("\n⚠️  No analysis available to generate fix proposal")
    return None


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("SCRAPER MONITORING AGENT - DEMO")
    print("="*60)
    print("\nThis demo shows how the agent system works:")
    print("1. Monitors scraper executions")
    print("2. Detects failure patterns")
    print("3. Analyzes errors (with optional LLM)")
    print("4. Generates fix proposals")
    
    try:
        # Demo 1: Monitoring
        monitor = demo_monitoring()
        
        # Demo 2: Pattern Analysis
        analyzer, patterns = demo_pattern_analysis(monitor)
        
        # Demo 3: LLM Analysis
        analysis = demo_llm_analysis(patterns)
        
        # Demo 4: Fix Proposal
        if patterns:
            demo_fix_proposal(patterns[0], analysis)
        
        print("\n" + "="*60)
        print("DEMO COMPLETE!")
        print("="*60)
        print("\nNext steps:")
        print("1. Integrate monitor into your scraper execution flow")
        print("2. Set up LLM agent (optional) for intelligent analysis")
        print("3. Review fix proposals and implement manually")
        print("4. Future: Auto-fix engine will apply fixes automatically")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

