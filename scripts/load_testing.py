#!/usr/bin/env python3
"""
Load Testing and Performance Validation for Boom-Bust Sentinel
This script performs comprehensive load testing and performance validation.
"""

import os
import sys
import json
import time
import asyncio
import threading
import statistics
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple
import psutil
import gc

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.bond_issuance_scraper import BondIssuanceScraper
from scrapers.bdc_discount_scraper import BDCDiscountScraper
from services.state_store import StateStore
from services.alert_service import AlertService
from utils.logging_config import setup_logging

class LoadTester:
    """Comprehensive load testing and performance validation."""
    
    def __init__(self):
        self.logger = setup_logging("load_testing")
        self.results = {}
        self.performance_metrics = {}
        
        # System monitoring
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
    def monitor_system_resources(self, duration: int = 60) -> Dict[str, Any]:
        """Monitor system resources during testing."""
        self.logger.info(f"Monitoring system resources for {duration}s...")
        
        cpu_samples = []
        memory_samples = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            cpu_samples.append(cpu_percent)
            memory_samples.append(memory_mb)
            
            time.sleep(1)
        
        return {
            'cpu_usage': {
                'avg': statistics.mean(cpu_samples),
                'max': max(cpu_samples),
                'min': min(cpu_samples),
                'samples': len(cpu_samples)
            },
            'memory_usage': {
                'avg': statistics.mean(memory_samples),
                'max': max(memory_samples),
                'min': min(memory_samples),
                'initial': self.initial_memory,
                'peak_increase': max(memory_samples) - self.initial_memory
            }
        }
    
    def test_scraper_concurrency(self, scraper_class, num_concurrent: int = 10, iterations: int = 5) -> Dict[str, Any]:
        """Test scraper performance under concurrent load."""
        scraper_name = scraper_class.__name__
        self.logger.info(f"Testing {scraper_name} concurrency: {num_concurrent} concurrent, {iterations} iterations each")
        
        def run_scraper_iteration():
            """Run a single scraper iteration."""
            scraper = scraper_class()
            start_time = time.time()
            
            try:
                results = scraper.scrape()
                execution_time = time.time() - start_time
                
                return {
                    'status': 'success',
                    'execution_time': execution_time,
                    'data_points': len(results) if results else 0,
                    'memory_usage': self.process.memory_info().rss / 1024 / 1024
                }
            except Exception as e:
                execution_time = time.time() - start_time
                return {
                    'status': 'error',
                    'execution_time': execution_time,
                    'error': str(e),
                    'memory_usage': self.process.memory_info().rss / 1024 / 1024
                }
        
        # Start resource monitoring
        monitor_thread = threading.Thread(
            target=lambda: self.monitor_system_resources(duration=30),
            daemon=True
        )
        monitor_thread.start()
        
        # Run concurrent tests
        all_results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            # Submit all tasks
            futures = []
            for _ in range(num_concurrent):
                for _ in range(iterations):
                    future = executor.submit(run_scraper_iteration)
                    futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                result = future.result()
                all_results.append(result)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_runs = [r for r in all_results if r['status'] == 'success']
        failed_runs = [r for r in all_results if r['status'] == 'error']
        
        if successful_runs:
            execution_times = [r['execution_time'] for r in successful_runs]
            memory_usage = [r['memory_usage'] for r in successful_runs]
            
            performance_stats = {
                'total_runs': len(all_results),
                'successful_runs': len(successful_runs),
                'failed_runs': len(failed_runs),
                'success_rate': len(successful_runs) / len(all_results) * 100,
                'total_time': total_time,
                'avg_execution_time': statistics.mean(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
                'median_execution_time': statistics.median(execution_times),
                'p95_execution_time': sorted(execution_times)[int(len(execution_times) * 0.95)],
                'throughput_per_second': len(successful_runs) / total_time,
                'avg_memory_usage': statistics.mean(memory_usage),
                'peak_memory_usage': max(memory_usage),
                'memory_increase': max(memory_usage) - self.initial_memory
            }
        else:
            performance_stats = {
                'total_runs': len(all_results),
                'successful_runs': 0,
                'failed_runs': len(failed_runs),
                'success_rate': 0,
                'total_time': total_time,
                'errors': [r['error'] for r in failed_runs]
            }
        
        self.logger.info(f"{scraper_name} concurrency test completed: {performance_stats.get('success_rate', 0):.1f}% success rate")
        
        return performance_stats
    
    def test_data_pipeline_throughput(self, num_records: int = 1000) -> Dict[str, Any]:
        """Test data pipeline throughput with large datasets."""
        self.logger.info(f"Testing data pipeline throughput with {num_records} records...")
        
        state_store = StateStore()
        
        # Generate test data
        test_data = []
        for i in range(num_records):
            test_data.append({
                'id': i,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'value': i * 1.5,
                'metadata': {
                    'source': 'load_test',
                    'batch': i // 100,
                    'data': 'x' * 100  # 100 bytes per record
                }
            })
        
        # Test write throughput
        write_start = time.time()
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        try:
            state_store.save_data('load_test_throughput', test_data)
            write_time = time.time() - write_start
            write_memory = self.process.memory_info().rss / 1024 / 1024
            
            # Test read throughput
            read_start = time.time()
            retrieved_data = state_store.get_historical_data(
                'load_test_throughput',
                start_time=datetime.now(timezone.utc) - timedelta(hours=1)
            )
            read_time = time.time() - read_start
            read_memory = self.process.memory_info().rss / 1024 / 1024
            
            # Calculate throughput metrics
            write_throughput = num_records / write_time  # records per second
            read_throughput = len(retrieved_data) / read_time if retrieved_data else 0
            
            # Data size calculations
            estimated_data_size = len(json.dumps(test_data)) / 1024 / 1024  # MB
            write_bandwidth = estimated_data_size / write_time  # MB/s
            
            throughput_stats = {
                'status': 'success',
                'num_records': num_records,
                'write_time': write_time,
                'read_time': read_time,
                'write_throughput_rps': write_throughput,
                'read_throughput_rps': read_throughput,
                'write_bandwidth_mbps': write_bandwidth,
                'data_size_mb': estimated_data_size,
                'memory_usage': {
                    'initial_mb': initial_memory,
                    'write_peak_mb': write_memory,
                    'read_peak_mb': read_memory,
                    'write_increase_mb': write_memory - initial_memory,
                    'read_increase_mb': read_memory - write_memory
                },
                'data_integrity': len(retrieved_data) == num_records if retrieved_data else False
            }
            
            # Cleanup test data
            try:
                state_store.delete_data('load_test_throughput')
            except:
                pass  # Ignore cleanup errors
            
            self.logger.info(f"Data pipeline throughput test completed: {write_throughput:.1f} writes/s, {read_throughput:.1f} reads/s")
            
        except Exception as e:
            throughput_stats = {
                'status': 'error',
                'error': str(e),
                'num_records': num_records
            }
            self.logger.error(f"Data pipeline throughput test failed: {e}")
        
        return throughput_stats
    
    def test_alert_system_load(self, num_alerts: int = 100, concurrent_channels: int = 3) -> Dict[str, Any]:
        """Test alert system under load."""
        self.logger.info(f"Testing alert system load: {num_alerts} alerts across {concurrent_channels} channels")
        
        alert_service = AlertService()
        
        def send_test_alert(alert_id: int):
            """Send a single test alert."""
            alert_data = {
                'alert_type': 'load_test',
                'message': f'Load test alert #{alert_id}',
                'severity': 'low',
                'data_source': 'load_test',
                'value': alert_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            start_time = time.time()
            
            try:
                # Test multiple channels
                channels = ['sns', 'telegram', 'slack'][:concurrent_channels]
                results = {}
                
                for channel in channels:
                    try:
                        result = alert_service.send_alert(alert_data, channels=[channel])
                        results[channel] = {
                            'status': 'success' if result.get('success') else 'failed',
                            'response': result
                        }
                    except Exception as e:
                        results[channel] = {
                            'status': 'error',
                            'error': str(e)
                        }
                
                execution_time = time.time() - start_time
                successful_channels = sum(1 for r in results.values() if r['status'] == 'success')
                
                return {
                    'alert_id': alert_id,
                    'status': 'success' if successful_channels > 0 else 'failed',
                    'execution_time': execution_time,
                    'successful_channels': successful_channels,
                    'total_channels': len(channels),
                    'channel_results': results
                }
                
            except Exception as e:
                execution_time = time.time() - start_time
                return {
                    'alert_id': alert_id,
                    'status': 'error',
                    'execution_time': execution_time,
                    'error': str(e)
                }
        
        # Run alert load test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=min(num_alerts, 20)) as executor:
            futures = [executor.submit(send_test_alert, i) for i in range(num_alerts)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_alerts = [r for r in results if r['status'] == 'success']
        failed_alerts = [r for r in results if r['status'] in ['failed', 'error']]
        
        if successful_alerts:
            execution_times = [r['execution_time'] for r in successful_alerts]
            channel_success_rates = []
            
            for result in successful_alerts:
                if 'successful_channels' in result and 'total_channels' in result:
                    channel_success_rates.append(
                        result['successful_channels'] / result['total_channels'] * 100
                    )
            
            alert_load_stats = {
                'status': 'success',
                'total_alerts': num_alerts,
                'successful_alerts': len(successful_alerts),
                'failed_alerts': len(failed_alerts),
                'success_rate': len(successful_alerts) / num_alerts * 100,
                'total_time': total_time,
                'avg_execution_time': statistics.mean(execution_times),
                'max_execution_time': max(execution_times),
                'min_execution_time': min(execution_times),
                'alert_throughput': len(successful_alerts) / total_time,
                'avg_channel_success_rate': statistics.mean(channel_success_rates) if channel_success_rates else 0
            }
        else:
            alert_load_stats = {
                'status': 'failed',
                'total_alerts': num_alerts,
                'successful_alerts': 0,
                'failed_alerts': len(failed_alerts),
                'success_rate': 0,
                'total_time': total_time,
                'errors': [r.get('error', 'Unknown error') for r in failed_alerts]
            }
        
        self.logger.info(f"Alert system load test completed: {alert_load_stats.get('success_rate', 0):.1f}% success rate")
        
        return alert_load_stats
    
    def test_memory_leak_detection(self, iterations: int = 50) -> Dict[str, Any]:
        """Test for memory leaks during repeated operations."""
        self.logger.info(f"Testing memory leak detection over {iterations} iterations...")
        
        memory_samples = []
        scraper = BondIssuanceScraper()
        state_store = StateStore()
        
        # Baseline memory
        gc.collect()  # Force garbage collection
        baseline_memory = self.process.memory_info().rss / 1024 / 1024
        memory_samples.append(baseline_memory)
        
        for i in range(iterations):
            try:
                # Perform operations that might leak memory
                results = scraper.scrape()
                
                if results:
                    # Store and retrieve data
                    state_store.save_data(f'memory_test_{i}', results)
                    retrieved = state_store.get_latest_value(f'memory_test_{i}')
                    
                    # Create some temporary objects
                    temp_data = [{'id': j, 'data': 'x' * 1000} for j in range(100)]
                    del temp_data
                
                # Force garbage collection every 10 iterations
                if i % 10 == 0:
                    gc.collect()
                
                # Sample memory usage
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                
                if i % 10 == 0:
                    self.logger.info(f"Memory leak test iteration {i}: {current_memory:.1f}MB")
                
            except Exception as e:
                self.logger.warning(f"Memory leak test iteration {i} failed: {e}")
        
        # Final garbage collection
        gc.collect()
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_samples.append(final_memory)
        
        # Analyze memory usage pattern
        memory_increase = final_memory - baseline_memory
        max_memory = max(memory_samples)
        avg_memory = statistics.mean(memory_samples)
        
        # Calculate memory growth trend
        if len(memory_samples) > 10:
            # Simple linear regression to detect memory growth trend
            x_values = list(range(len(memory_samples)))
            y_values = memory_samples
            
            n = len(memory_samples)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            memory_growth_rate = slope  # MB per iteration
        else:
            memory_growth_rate = 0
        
        # Determine if there's a potential memory leak
        leak_threshold = 0.1  # MB per iteration
        potential_leak = memory_growth_rate > leak_threshold
        
        memory_leak_stats = {
            'status': 'completed',
            'iterations': iterations,
            'baseline_memory_mb': baseline_memory,
            'final_memory_mb': final_memory,
            'max_memory_mb': max_memory,
            'avg_memory_mb': avg_memory,
            'memory_increase_mb': memory_increase,
            'memory_growth_rate_mb_per_iteration': memory_growth_rate,
            'potential_memory_leak': potential_leak,
            'leak_severity': 'high' if memory_growth_rate > 0.5 else 'medium' if memory_growth_rate > 0.1 else 'low',
            'memory_samples': memory_samples[-10:]  # Last 10 samples
        }
        
        self.logger.info(f"Memory leak detection completed: {memory_increase:.1f}MB increase, growth rate: {memory_growth_rate:.3f}MB/iteration")
        
        return memory_leak_stats
    
    def run_comprehensive_load_test(self) -> Dict[str, Any]:
        """Run comprehensive load testing suite."""
        self.logger.info("Starting comprehensive load testing suite...")
        
        load_test_start = time.time()
        
        try:
            # Test 1: Scraper concurrency
            self.logger.info("Phase 1: Testing scraper concurrency...")
            scraper_tests = {}
            
            scrapers_to_test = [
                (BondIssuanceScraper, 5, 3),  # 5 concurrent, 3 iterations each
                (BDCDiscountScraper, 3, 2)    # 3 concurrent, 2 iterations each
            ]
            
            for scraper_class, concurrent, iterations in scrapers_to_test:
                scraper_name = scraper_class.__name__
                scraper_tests[scraper_name] = self.test_scraper_concurrency(
                    scraper_class, concurrent, iterations
                )
            
            self.results['scraper_concurrency'] = scraper_tests
            
            # Test 2: Data pipeline throughput
            self.logger.info("Phase 2: Testing data pipeline throughput...")
            throughput_results = self.test_data_pipeline_throughput(num_records=500)
            self.results['data_pipeline_throughput'] = throughput_results
            
            # Test 3: Alert system load
            self.logger.info("Phase 3: Testing alert system load...")
            alert_load_results = self.test_alert_system_load(num_alerts=50, concurrent_channels=2)
            self.results['alert_system_load'] = alert_load_results
            
            # Test 4: Memory leak detection
            self.logger.info("Phase 4: Testing memory leak detection...")
            memory_leak_results = self.test_memory_leak_detection(iterations=30)
            self.results['memory_leak_detection'] = memory_leak_results
            
            # Test 5: System resource monitoring
            self.logger.info("Phase 5: Final system resource monitoring...")
            final_resources = self.monitor_system_resources(duration=10)
            self.results['final_system_resources'] = final_resources
            
            total_load_test_time = time.time() - load_test_start
            
            # Generate performance summary
            summary = self._generate_load_test_summary()
            
            self.performance_metrics = {
                'total_load_test_time': total_load_test_time,
                'phases_completed': len(self.results),
                'overall_performance_score': summary.get('performance_score', 0)
            }
            
            self.logger.info(f"Comprehensive load testing completed in {total_load_test_time:.2f}s")
            
            return {
                'status': 'completed',
                'summary': summary,
                'results': self.results,
                'performance_metrics': self.performance_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Load testing failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'partial_results': self.results
            }
    
    def _generate_load_test_summary(self) -> Dict[str, Any]:
        """Generate load test summary and performance score."""
        performance_scores = []
        
        # Scraper concurrency score
        if 'scraper_concurrency' in self.results:
            scraper_scores = []
            for scraper_name, scraper_result in self.results['scraper_concurrency'].items():
                success_rate = scraper_result.get('success_rate', 0)
                avg_time = scraper_result.get('avg_execution_time', float('inf'))
                
                # Score based on success rate and performance
                time_score = min(100, 1000 / avg_time) if avg_time > 0 else 0
                scraper_score = (success_rate * 0.7) + (time_score * 0.3)
                scraper_scores.append(scraper_score)
            
            if scraper_scores:
                performance_scores.append(statistics.mean(scraper_scores))
        
        # Data pipeline throughput score
        if 'data_pipeline_throughput' in self.results:
            throughput_result = self.results['data_pipeline_throughput']
            if throughput_result.get('status') == 'success':
                write_throughput = throughput_result.get('write_throughput_rps', 0)
                read_throughput = throughput_result.get('read_throughput_rps', 0)
                
                # Score based on throughput (assuming 100 rps is excellent)
                write_score = min(100, write_throughput / 100 * 100)
                read_score = min(100, read_throughput / 100 * 100)
                throughput_score = (write_score + read_score) / 2
                performance_scores.append(throughput_score)
        
        # Alert system load score
        if 'alert_system_load' in self.results:
            alert_result = self.results['alert_system_load']
            success_rate = alert_result.get('success_rate', 0)
            throughput = alert_result.get('alert_throughput', 0)
            
            # Score based on success rate and throughput
            throughput_score = min(100, throughput / 10 * 100)  # 10 alerts/s is excellent
            alert_score = (success_rate * 0.8) + (throughput_score * 0.2)
            performance_scores.append(alert_score)
        
        # Memory leak score
        if 'memory_leak_detection' in self.results:
            memory_result = self.results['memory_leak_detection']
            has_leak = memory_result.get('potential_memory_leak', False)
            growth_rate = memory_result.get('memory_growth_rate_mb_per_iteration', 0)
            
            # Score based on memory stability
            if not has_leak:
                memory_score = 100
            elif growth_rate < 0.1:
                memory_score = 80
            elif growth_rate < 0.5:
                memory_score = 60
            else:
                memory_score = 30
            
            performance_scores.append(memory_score)
        
        # Calculate overall performance score
        overall_score = statistics.mean(performance_scores) if performance_scores else 0
        
        # Determine performance grade
        if overall_score >= 90:
            grade = 'A'
        elif overall_score >= 80:
            grade = 'B'
        elif overall_score >= 70:
            grade = 'C'
        elif overall_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'performance_score': overall_score,
            'performance_grade': grade,
            'component_scores': {
                'scraper_concurrency': performance_scores[0] if len(performance_scores) > 0 else 0,
                'data_pipeline': performance_scores[1] if len(performance_scores) > 1 else 0,
                'alert_system': performance_scores[2] if len(performance_scores) > 2 else 0,
                'memory_stability': performance_scores[3] if len(performance_scores) > 3 else 0
            },
            'recommendations': self._generate_performance_recommendations(overall_score)
        }
    
    def _generate_performance_recommendations(self, score: float) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        if score < 90:
            recommendations.append("Consider optimizing scraper execution times")
        
        if score < 80:
            recommendations.append("Review data pipeline throughput and consider caching")
        
        if score < 70:
            recommendations.append("Investigate alert system performance bottlenecks")
        
        if score < 60:
            recommendations.append("Address potential memory leaks and resource usage")
        
        if 'memory_leak_detection' in self.results:
            memory_result = self.results['memory_leak_detection']
            if memory_result.get('potential_memory_leak'):
                recommendations.append("Investigate and fix memory leaks")
        
        return recommendations

def main():
    """Main function to run load testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Boom-Bust Sentinel Load Testing')
    parser.add_argument('--output', '-o', help='Output file for results (JSON)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Run load testing
    load_tester = LoadTester()
    results = load_tester.run_comprehensive_load_test()
    
    # Print summary
    print("\n" + "=" * 60)
    print("🚀 BOOM-BUST SENTINEL LOAD TESTING RESULTS")
    print("=" * 60)
    
    if results['status'] == 'completed':
        summary = results['summary']
        print(f"Performance Score: {summary['performance_score']:.1f}/100 (Grade: {summary['performance_grade']})")
        print(f"Load Test Time: {results['performance_metrics']['total_load_test_time']:.2f}s")
        
        print(f"\n📊 Component Scores:")
        for component, score in summary['component_scores'].items():
            print(f"  {component}: {score:.1f}/100")
        
        if summary['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in summary['recommendations']:
                print(f"  - {rec}")
    else:
        print(f"Load Testing Status: FAILED")
        print(f"Error: {results.get('error', 'Unknown error')}")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to: {args.output}")
    
    # Exit with appropriate code
    if results['status'] == 'completed' and results['summary']['performance_score'] >= 70:
        print("\n✅ Load testing completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Load testing failed or performance is below acceptable threshold!")
        sys.exit(1)

if __name__ == '__main__':
    main()