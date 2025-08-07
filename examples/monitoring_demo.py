#!/usr/bin/env python3
"""
Demonstration of the monitoring and observability system.
This script shows how to use the MetricsService and HealthMonitor.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from services.metrics_service import MetricsService
from utils.health_monitor import HealthMonitor
from utils.logging_config import setup_logging, get_contextual_logger
from models.core import MetricValue, ScraperResult


def demo_metrics_service():
    """Demonstrate MetricsService functionality."""
    print("\n=== MetricsService Demo ===")
    
    # Initialize metrics service
    metrics_service = MetricsService()
    
    # Send a single metric
    metric_value = MetricValue(
        value=1500000000,  # $1.5B
        timestamp=datetime.now(timezone.utc),
        confidence=0.95,
        source='demo_scraper',
        metadata={
            'companies': 'MSFT,META',
            'avg_coupon': 4.25
        }
    )
    
    print("Sending single metric...")
    success = metrics_service.send_metric('bond_issuance', 'weekly_total', metric_value)
    print(f"Single metric sent: {success}")
    
    # Send multiple metrics
    metrics = [
        {
            'data_source': 'bdc_discount',
            'metric_name': 'avg_discount',
            'value': -0.15,
            'timestamp': datetime.now(timezone.utc),
            'source': 'demo_scraper',
            'metadata': {'symbols': 'ARCC,OCSL,MAIN'}
        },
        {
            'data_source': 'credit_fund',
            'metric_name': 'asset_value',
            'value': 50000000000,  # $50B
            'timestamp': datetime.now(timezone.utc),
            'source': 'demo_scraper',
            'metadata': {'fund_count': 25}
        }
    ]
    
    print("Sending multiple metrics...")
    success = metrics_service.send_metrics(metrics)
    print(f"Multiple metrics sent: {success}")
    
    # Send scraper result metrics
    scraper_result = ScraperResult(
        data_source='demo_scraper',
        metric_name='test_metric',
        success=True,
        data={
            'total_amount': 2500000000,
            'count': 8,
            'avg_value': 312500000
        },
        error=None,
        execution_time=2.5,
        timestamp=datetime.now(timezone.utc)
    )
    
    print("Sending scraper result metrics...")
    success = metrics_service.send_scraper_metrics(scraper_result)
    print(f"Scraper metrics sent: {success}")
    
    # Update system health
    print("Updating system health...")
    metrics_service.update_system_health(
        component='demo_component',
        status='healthy',
        response_time_ms=45.2,
        error_count=0,
        metadata={'version': '1.0.0'}
    )
    
    # Get system health
    health = metrics_service.get_system_health()
    print(f"System health components: {len(health)}")
    
    # Demonstrate anomaly detection
    print("Testing anomaly detection...")
    
    # Add some historical data
    for i in range(15):
        metrics_service._update_metric_history([{
            'metric_name': 'test_anomaly',
            'value': 10 + (i % 3)  # Values around 10-12
        }])
    
    # Test normal value
    anomaly = metrics_service.detect_anomalies('test_anomaly', 11.0)
    print(f"Normal value anomaly detection: {anomaly.is_anomaly if anomaly else 'No data'}")
    
    # Test anomalous value
    anomaly = metrics_service.detect_anomalies('test_anomaly', 50.0)
    print(f"Anomalous value detection: {anomaly.is_anomaly if anomaly else 'No data'}")
    
    # Get metrics summary
    summary = metrics_service.get_metrics_summary()
    print(f"Metrics summary: {summary}")


def demo_health_monitor():
    """Demonstrate HealthMonitor functionality."""
    print("\n=== HealthMonitor Demo ===")
    
    # Initialize health monitor
    health_monitor = HealthMonitor()
    
    # Register a custom health check
    def custom_health_check():
        """A simple custom health check."""
        return True  # Always healthy for demo
    
    health_monitor.register_health_check(
        name='demo_service',
        check_function=custom_health_check,
        timeout_seconds=5,
        critical=False,
        metadata={'service_type': 'demo'}
    )
    
    print(f"Registered health checks: {health_monitor.get_health_check_names()}")
    
    # Run a specific health check
    print("Running demo_service health check...")
    result = health_monitor.run_health_check('demo_service')
    print(f"Health check result: {result['healthy']} ({result['response_time_ms']:.1f}ms)")
    
    # Run all health checks
    print("Running all health checks...")
    results = health_monitor.run_all_health_checks()
    
    healthy_count = sum(1 for r in results.values() if r['healthy'])
    print(f"Health check results: {healthy_count}/{len(results)} healthy")
    
    # Get system status
    status = health_monitor.get_system_status()
    print(f"Overall system status: {status['status']}")
    print(f"Status message: {status['message']}")
    print(f"Summary: {status['summary']}")


def demo_logging():
    """Demonstrate enhanced logging capabilities."""
    print("\n=== Enhanced Logging Demo ===")
    
    # Get a contextual logger
    logger = get_contextual_logger(__name__, component='demo', version='1.0.0')
    
    # Log different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    
    # Log with extra context
    logger.info(
        "Processing demo data",
        extra={
            'data_source': 'demo',
            'record_count': 100,
            'processing_time': 1.5
        }
    )
    
    # Demonstrate error logging with context
    try:
        raise ValueError("This is a demo error")
    except Exception as e:
        logger.error(
            "Demo error occurred",
            extra={
                'error_type': type(e).__name__,
                'operation': 'demo_processing'
            },
            exc_info=True
        )


def demo_integration():
    """Demonstrate integration between metrics and health monitoring."""
    print("\n=== Integration Demo ===")
    
    # Initialize services
    metrics_service = MetricsService()
    health_monitor = HealthMonitor(metrics_service=metrics_service)
    
    # Simulate a scraper execution with monitoring
    logger = get_contextual_logger(__name__, component='integration_demo')
    
    start_time = time.time()
    
    try:
        # Simulate some work
        logger.info("Starting demo scraper execution")
        time.sleep(0.1)  # Simulate work
        
        # Create scraper result
        execution_time = time.time() - start_time
        scraper_result = ScraperResult(
            data_source='integration_demo',
            metric_name='demo_execution',
            success=True,
            data={'processed_records': 50},
            error=None,
            execution_time=execution_time,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Send metrics
        metrics_service.send_scraper_metrics(scraper_result)
        
        # Update health
        metrics_service.update_system_health(
            component='integration_demo',
            status='healthy',
            response_time_ms=execution_time * 1000,
            error_count=0
        )
        
        logger.info("Demo scraper execution completed successfully")
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        # Create failed scraper result
        scraper_result = ScraperResult(
            data_source='integration_demo',
            metric_name='demo_execution',
            success=False,
            data=None,
            error=str(e),
            execution_time=execution_time,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Send metrics
        metrics_service.send_scraper_metrics(scraper_result)
        
        # Update health
        metrics_service.update_system_health(
            component='integration_demo',
            status='failed',
            response_time_ms=execution_time * 1000,
            error_count=1,
            metadata={'error': str(e)}
        )
        
        logger.error("Demo scraper execution failed", exc_info=True)
    
    # Show final status
    health = metrics_service.get_system_health()
    if 'integration_demo' in health:
        component_health = health['integration_demo']
        print(f"Integration demo component status: {component_health.status}")
        print(f"Success rate: {component_health.success_rate:.2%}")


def main():
    """Main demo function."""
    print("Boom-Bust Sentinel Monitoring & Observability Demo")
    print("=" * 50)
    
    # Setup logging
    setup_logging(log_level='INFO', use_json=False)
    
    # Run demos
    demo_metrics_service()
    demo_health_monitor()
    demo_logging()
    demo_integration()
    
    print("\n=== Demo Complete ===")
    print("Check the logs above to see the monitoring system in action!")
    print("\nIn a real deployment:")
    print("- Metrics would be sent to Grafana Cloud or Datadog")
    print("- Health checks would run continuously")
    print("- Logs would be structured JSON in production")
    print("- Alerts would be sent when thresholds are breached")


if __name__ == '__main__':
    main()