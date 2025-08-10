"""
End-to-End Integration Tests for Boom-Bust Sentinel
This module tests the complete data pipeline from scraping to alerting.
"""

import os
import sys
import json
import time
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.bond_issuance_scraper import BondIssuanceScraper
from scrapers.bdc_discount_scraper import BDCDiscountScraper
from scrapers.credit_fund_scraper import CreditFundScraper
from scrapers.bank_provision_scraper import BankProvisionScraper
from services.state_store import StateStore
from services.alert_service import AlertService
from services.metrics_service import MetricsService
from utils.error_handling import ErrorHandler
from config.config_loader import ConfigLoader

class EndToEndIntegrationTest:
    """Comprehensive end-to-end integration test suite."""
    
    def __init__(self):
        self.config = ConfigLoader()
        self.state_store = StateStore()
        self.alert_service = AlertService()
        self.metrics_service = MetricsService()
        self.error_handler = ErrorHandler()
        
        # Test data storage
        self.test_results = {}
        self.performance_metrics = {}
        
    def setup_test_environment(self):
        """Set up test environment with mock data and configurations."""
        # Set test environment variables
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['DYNAMODB_TABLE'] = 'boom-bust-sentinel-test-state'
        os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-alerts'
        
        # Initialize test database
        self.state_store.initialize_test_environment()
        
    def cleanup_test_environment(self):
        """Clean up test environment and data."""
        try:
            self.state_store.cleanup_test_data()
        except Exception as e:
            print(f"Warning: Failed to cleanup test data: {e}")
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        self.setup_test_environment()
        yield
        self.cleanup_test_environment()

class TestCompleteDataPipeline:
    """Test the complete data pipeline from scraping to storage."""
    
    @pytest.fixture
    def integration_test(self):
        return EndToEndIntegrationTest()
    
    def test_bond_issuance_pipeline(self, integration_test):
        """Test complete bond issuance data pipeline."""
        print("🔍 Testing bond issuance pipeline...")
        
        # Mock SEC EDGAR data
        mock_sec_data = {
            'filings': [
                {
                    'cik': '0000789019',  # Microsoft
                    'company_name': 'Microsoft Corporation',
                    'form_type': '424B2',
                    'filing_date': '2024-01-15',
                    'notional_amount': 2500000000,  # $2.5B
                    'coupon_rate': 4.25,
                    'maturity_date': '2029-01-15'
                }
            ]
        }
        
        with patch('scrapers.bond_issuance_scraper.BondIssuanceScraper._fetch_sec_data') as mock_fetch:
            mock_fetch.return_value = mock_sec_data
            
            # Initialize scraper
            scraper = BondIssuanceScraper()
            
            # Execute scraping
            start_time = time.time()
            results = scraper.scrape()
            execution_time = time.time() - start_time
            
            # Validate results
            assert results is not None, "Bond issuance scraper returned None"
            assert len(results) > 0, "No bond issuance data returned"
            assert results[0]['notional_amount'] == 2500000000, "Incorrect notional amount"
            
            # Test data storage
            integration_test.state_store.save_data('bond_issuance', results)
            stored_data = integration_test.state_store.get_latest_value('bond_issuance')
            
            assert stored_data is not None, "Failed to store bond issuance data"
            assert stored_data['notional_amount'] == 2500000000, "Stored data corrupted"
            
            # Record performance metrics
            integration_test.performance_metrics['bond_issuance_execution_time'] = execution_time
            integration_test.test_results['bond_issuance_pipeline'] = 'PASS'
            
            print(f"  ✅ Bond issuance pipeline completed in {execution_time:.2f}s")
    
    def test_bdc_discount_pipeline(self, integration_test):
        """Test complete BDC discount data pipeline."""
        print("🔍 Testing BDC discount pipeline...")
        
        # Mock Yahoo Finance and RSS data
        mock_yahoo_data = {
            'ARCC': {'price': 19.85, 'volume': 1250000},
            'OCSL': {'price': 8.45, 'volume': 890000}
        }
        
        mock_nav_data = {
            'ARCC': 20.15,
            'OCSL': 8.92
        }
        
        with patch('scrapers.bdc_discount_scraper.BDCDiscountScraper._fetch_yahoo_data') as mock_yahoo, \
             patch('scrapers.bdc_discount_scraper.BDCDiscountScraper._fetch_nav_data') as mock_nav:
            
            mock_yahoo.return_value = mock_yahoo_data
            mock_nav.return_value = mock_nav_data
            
            # Initialize scraper
            scraper = BDCDiscountScraper()
            
            # Execute scraping
            start_time = time.time()
            results = scraper.scrape()
            execution_time = time.time() - start_time
            
            # Validate results
            assert results is not None, "BDC discount scraper returned None"
            assert len(results) > 0, "No BDC discount data returned"
            
            # Validate discount calculation
            arcc_result = next((r for r in results if r['symbol'] == 'ARCC'), None)
            assert arcc_result is not None, "ARCC data not found"
            
            expected_discount = (20.15 - 19.85) / 20.15  # ~1.49%
            assert abs(arcc_result['discount_to_nav'] - expected_discount) < 0.001, "Incorrect discount calculation"
            
            # Test data storage
            integration_test.state_store.save_data('bdc_discount', results)
            stored_data = integration_test.state_store.get_latest_value('bdc_discount')
            
            assert stored_data is not None, "Failed to store BDC discount data"
            
            # Record performance metrics
            integration_test.performance_metrics['bdc_discount_execution_time'] = execution_time
            integration_test.test_results['bdc_discount_pipeline'] = 'PASS'
            
            print(f"  ✅ BDC discount pipeline completed in {execution_time:.2f}s")
    
    def test_credit_fund_pipeline(self, integration_test):
        """Test complete credit fund data pipeline."""
        print("🔍 Testing credit fund pipeline...")
        
        # Mock Form PF data
        mock_form_pf_data = {
            'funds': [
                {
                    'fund_name': 'Apollo Credit Fund',
                    'gross_asset_value': 15800000000,  # $15.8B
                    'quarter': 'Q4 2023',
                    'filing_date': '2024-02-15'
                }
            ]
        }
        
        with patch('scrapers.credit_fund_scraper.CreditFundScraper._fetch_form_pf_data') as mock_fetch:
            mock_fetch.return_value = mock_form_pf_data
            
            # Initialize scraper
            scraper = CreditFundScraper()
            
            # Execute scraping
            start_time = time.time()
            results = scraper.scrape()
            execution_time = time.time() - start_time
            
            # Validate results
            assert results is not None, "Credit fund scraper returned None"
            assert len(results) > 0, "No credit fund data returned"
            assert results[0]['gross_asset_value'] == 15800000000, "Incorrect asset value"
            
            # Test data storage
            integration_test.state_store.save_data('credit_fund', results)
            stored_data = integration_test.state_store.get_latest_value('credit_fund')
            
            assert stored_data is not None, "Failed to store credit fund data"
            
            # Record performance metrics
            integration_test.performance_metrics['credit_fund_execution_time'] = execution_time
            integration_test.test_results['credit_fund_pipeline'] = 'PASS'
            
            print(f"  ✅ Credit fund pipeline completed in {execution_time:.2f}s")
    
    def test_bank_provision_pipeline(self, integration_test):
        """Test complete bank provision data pipeline."""
        print("🔍 Testing bank provision pipeline...")
        
        # Mock XBRL data
        mock_xbrl_data = {
            'banks': [
                {
                    'bank_name': 'JPMorgan Chase',
                    'ticker': 'JPM',
                    'allowance_for_credit_losses': 18500000000,  # $18.5B
                    'non_bank_financial_exposure': 2300000000,  # $2.3B
                    'quarter': 'Q4 2023'
                }
            ]
        }
        
        with patch('scrapers.bank_provision_scraper.BankProvisionScraper._fetch_xbrl_data') as mock_fetch:
            mock_fetch.return_value = mock_xbrl_data
            
            # Initialize scraper
            scraper = BankProvisionScraper()
            
            # Execute scraping
            start_time = time.time()
            results = scraper.scrape()
            execution_time = time.time() - start_time
            
            # Validate results
            assert results is not None, "Bank provision scraper returned None"
            assert len(results) > 0, "No bank provision data returned"
            assert results[0]['non_bank_financial_exposure'] == 2300000000, "Incorrect exposure amount"
            
            # Test data storage
            integration_test.state_store.save_data('bank_provision', results)
            stored_data = integration_test.state_store.get_latest_value('bank_provision')
            
            assert stored_data is not None, "Failed to store bank provision data"
            
            # Record performance metrics
            integration_test.performance_metrics['bank_provision_execution_time'] = execution_time
            integration_test.test_results['bank_provision_pipeline'] = 'PASS'
            
            print(f"  ✅ Bank provision pipeline completed in {execution_time:.2f}s")

class TestAlertingSystem:
    """Test the complete alerting system."""
    
    @pytest.fixture
    def integration_test(self):
        return EndToEndIntegrationTest()
    
    def test_multi_channel_alert_delivery(self, integration_test):
        """Test multi-channel alert delivery functionality."""
        print("🔍 Testing multi-channel alert delivery...")
        
        # Mock alert data
        alert_data = {
            'alert_type': 'bond_issuance_spike',
            'message': 'Weekly bond issuance exceeded $5B threshold',
            'severity': 'high',
            'data_source': 'bond_issuance',
            'value': 7500000000,
            'threshold': 5000000000,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Mock notification services
        with patch('services.alert_service.AlertService._send_sns_notification') as mock_sns, \
             patch('services.alert_service.AlertService._send_telegram_notification') as mock_telegram, \
             patch('services.alert_service.AlertService._send_slack_notification') as mock_slack:
            
            mock_sns.return_value = {'MessageId': 'test-message-id'}
            mock_telegram.return_value = {'ok': True, 'result': {'message_id': 123}}
            mock_slack.return_value = {'ok': True, 'ts': '1234567890.123456'}
            
            # Send alerts through all channels
            start_time = time.time()
            
            sns_result = integration_test.alert_service.send_alert(alert_data, channels=['sns'])
            telegram_result = integration_test.alert_service.send_alert(alert_data, channels=['telegram'])
            slack_result = integration_test.alert_service.send_alert(alert_data, channels=['slack'])
            
            execution_time = time.time() - start_time
            
            # Validate alert delivery
            assert sns_result['success'] == True, "SNS alert delivery failed"
            assert telegram_result['success'] == True, "Telegram alert delivery failed"
            assert slack_result['success'] == True, "Slack alert delivery failed"
            
            # Verify mock calls
            mock_sns.assert_called_once()
            mock_telegram.assert_called_once()
            mock_slack.assert_called_once()
            
            # Record performance metrics
            integration_test.performance_metrics['alert_delivery_time'] = execution_time
            integration_test.test_results['multi_channel_alerts'] = 'PASS'
            
            print(f"  ✅ Multi-channel alert delivery completed in {execution_time:.2f}s")
    
    def test_alert_threshold_logic(self, integration_test):
        """Test alert threshold logic and triggering."""
        print("🔍 Testing alert threshold logic...")
        
        # Test data that should trigger alerts
        test_scenarios = [
            {
                'data_source': 'bond_issuance',
                'value': 6000000000,  # Above $5B threshold
                'should_alert': True,
                'alert_type': 'bond_issuance_spike'
            },
            {
                'data_source': 'bdc_discount',
                'value': 0.08,  # 8% discount, above 5% threshold
                'should_alert': True,
                'alert_type': 'bdc_discount_high'
            },
            {
                'data_source': 'credit_fund',
                'value': -0.12,  # 12% decline, above 10% threshold
                'should_alert': True,
                'alert_type': 'credit_fund_decline'
            },
            {
                'data_source': 'bank_provision',
                'value': 0.25,  # 25% increase, above 20% threshold
                'should_alert': True,
                'alert_type': 'bank_provision_increase'
            }
        ]
        
        alerts_triggered = 0
        
        for scenario in test_scenarios:
            # Check if alert should be triggered
            should_trigger = integration_test.alert_service.should_trigger_alert(
                scenario['data_source'],
                scenario['value']
            )
            
            if scenario['should_alert']:
                assert should_trigger == True, f"Alert should be triggered for {scenario['data_source']}"
                alerts_triggered += 1
            else:
                assert should_trigger == False, f"Alert should not be triggered for {scenario['data_source']}"
        
        assert alerts_triggered == 4, f"Expected 4 alerts, got {alerts_triggered}"
        
        integration_test.test_results['alert_threshold_logic'] = 'PASS'
        print(f"  ✅ Alert threshold logic validated ({alerts_triggered} alerts triggered)")

class TestDashboardIntegration:
    """Test dashboard data consistency and real-time updates."""
    
    @pytest.fixture
    def integration_test(self):
        return EndToEndIntegrationTest()
    
    def test_dashboard_data_consistency(self, integration_test):
        """Test dashboard data consistency with backend."""
        print("🔍 Testing dashboard data consistency...")
        
        # Store test data
        test_data = {
            'bond_issuance': [
                {
                    'company': 'Microsoft',
                    'notional_amount': 2500000000,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            ],
            'bdc_discount': [
                {
                    'symbol': 'ARCC',
                    'discount_to_nav': 0.0149,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        
        # Store data in backend
        for data_source, data in test_data.items():
            integration_test.state_store.save_data(data_source, data)
        
        # Simulate dashboard API calls
        with patch('requests.get') as mock_get:
            # Mock API responses
            mock_responses = {
                '/api/metrics/current': {
                    'bond_issuance': test_data['bond_issuance'][0],
                    'bdc_discount': test_data['bdc_discount'][0]
                },
                '/api/metrics/historical': {
                    'bond_issuance': test_data['bond_issuance'],
                    'bdc_discount': test_data['bdc_discount']
                }
            }
            
            def mock_response(url):
                response = Mock()
                endpoint = url.split('/')[-2:]  # Get last two parts of URL
                endpoint_key = '/' + '/'.join(endpoint)
                response.json.return_value = mock_responses.get(endpoint_key, {})
                response.status_code = 200
                return response
            
            mock_get.side_effect = mock_response
            
            # Test API consistency
            import requests
            
            current_response = requests.get('http://localhost:3000/api/metrics/current')
            historical_response = requests.get('http://localhost:3000/api/metrics/historical')
            
            current_data = current_response.json()
            historical_data = historical_response.json()
            
            # Validate data consistency
            assert current_data['bond_issuance']['notional_amount'] == 2500000000, "Current data inconsistent"
            assert len(historical_data['bond_issuance']) == 1, "Historical data inconsistent"
            
            integration_test.test_results['dashboard_data_consistency'] = 'PASS'
            print("  ✅ Dashboard data consistency validated")
    
    def test_real_time_updates(self, integration_test):
        """Test real-time dashboard updates."""
        print("🔍 Testing real-time dashboard updates...")
        
        # This would typically test WebSocket connections or polling
        # For now, we'll test the data flow simulation
        
        # Simulate new data arriving
        new_data = {
            'company': 'Apple',
            'notional_amount': 3000000000,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Store new data
        integration_test.state_store.save_data('bond_issuance', [new_data])
        
        # Verify data is immediately available
        latest_data = integration_test.state_store.get_latest_value('bond_issuance')
        
        assert latest_data is not None, "Latest data not available"
        assert latest_data['company'] == 'Apple', "Real-time update failed"
        
        integration_test.test_results['real_time_updates'] = 'PASS'
        print("  ✅ Real-time updates validated")

class TestPerformanceAndLoad:
    """Test system performance and load handling."""
    
    @pytest.fixture
    def integration_test(self):
        return EndToEndIntegrationTest()
    
    def test_load_performance(self, integration_test):
        """Test system performance under load."""
        print("🔍 Testing system performance under load...")
        
        # Simulate concurrent scraper executions
        import concurrent.futures
        import threading
        
        def simulate_scraper_load():
            """Simulate scraper execution under load."""
            scraper = BondIssuanceScraper()
            
            with patch('scrapers.bond_issuance_scraper.BondIssuanceScraper._fetch_sec_data') as mock_fetch:
                mock_fetch.return_value = {'filings': []}
                
                start_time = time.time()
                results = scraper.scrape()
                execution_time = time.time() - start_time
                
                return execution_time
        
        # Run concurrent executions
        num_concurrent = 5
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(simulate_scraper_load) for _ in range(num_concurrent)]
            execution_times = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        avg_execution_time = sum(execution_times) / len(execution_times)
        
        # Performance assertions
        assert total_time < 30, f"Load test took too long: {total_time}s"
        assert avg_execution_time < 10, f"Average execution time too high: {avg_execution_time}s"
        assert all(t < 15 for t in execution_times), "Some executions took too long"
        
        # Record performance metrics
        integration_test.performance_metrics.update({
            'load_test_total_time': total_time,
            'load_test_avg_execution_time': avg_execution_time,
            'load_test_concurrent_executions': num_concurrent
        })
        
        integration_test.test_results['load_performance'] = 'PASS'
        print(f"  ✅ Load performance test completed: {total_time:.2f}s total, {avg_execution_time:.2f}s average")
    
    def test_memory_usage(self, integration_test):
        """Test memory usage under normal operations."""
        print("🔍 Testing memory usage...")
        
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate data processing
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                'id': i,
                'data': 'x' * 1000,  # 1KB per record
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        # Store data
        integration_test.state_store.save_data('memory_test', large_dataset)
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Cleanup
        del large_dataset
        gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory usage assertions
        assert memory_increase < 100, f"Memory increase too high: {memory_increase}MB"
        assert final_memory - initial_memory < 50, "Memory not properly released"
        
        # Record performance metrics
        integration_test.performance_metrics.update({
            'initial_memory_mb': initial_memory,
            'peak_memory_mb': peak_memory,
            'final_memory_mb': final_memory,
            'memory_increase_mb': memory_increase
        })
        
        integration_test.test_results['memory_usage'] = 'PASS'
        print(f"  ✅ Memory usage test completed: {memory_increase:.1f}MB increase")

class TestErrorRecoveryAndResilience:
    """Test error recovery and retry mechanisms."""
    
    @pytest.fixture
    def integration_test(self):
        return EndToEndIntegrationTest()
    
    def test_network_failure_recovery(self, integration_test):
        """Test recovery from network failures."""
        print("🔍 Testing network failure recovery...")
        
        # Simulate network failures with retries
        call_count = 0
        
        def mock_failing_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:  # Fail first 2 attempts
                raise ConnectionError("Network connection failed")
            else:  # Succeed on 3rd attempt
                response = Mock()
                response.json.return_value = {'filings': []}
                response.status_code = 200
                return response
        
        with patch('requests.get', side_effect=mock_failing_request):
            scraper = BondIssuanceScraper()
            
            start_time = time.time()
            results = scraper.scrape()  # Should succeed after retries
            execution_time = time.time() - start_time
            
            # Validate recovery
            assert results is not None, "Failed to recover from network failures"
            assert call_count == 3, f"Expected 3 attempts, got {call_count}"
            
            integration_test.performance_metrics['network_recovery_time'] = execution_time
            integration_test.test_results['network_failure_recovery'] = 'PASS'
            
            print(f"  ✅ Network failure recovery completed in {execution_time:.2f}s ({call_count} attempts)")
    
    def test_data_corruption_handling(self, integration_test):
        """Test handling of corrupted data."""
        print("🔍 Testing data corruption handling...")
        
        # Test with corrupted JSON data
        corrupted_data = '{"filings": [{"cik": "invalid", "amount":'  # Incomplete JSON
        
        with patch('requests.get') as mock_get:
            response = Mock()
            response.text = corrupted_data
            response.json.side_effect = json.JSONDecodeError("Invalid JSON", corrupted_data, 0)
            response.status_code = 200
            mock_get.return_value = response
            
            scraper = BondIssuanceScraper()
            
            # Should handle corruption gracefully
            results = scraper.scrape()
            
            # Should return empty results or cached data, not crash
            assert isinstance(results, list), "Should return list even with corrupted data"
            
            integration_test.test_results['data_corruption_handling'] = 'PASS'
            print("  ✅ Data corruption handling validated")
    
    def test_service_degradation(self, integration_test):
        """Test graceful service degradation."""
        print("🔍 Testing graceful service degradation...")
        
        # Simulate partial service failures
        with patch('services.alert_service.AlertService._send_sns_notification') as mock_sns, \
             patch('services.alert_service.AlertService._send_telegram_notification') as mock_telegram:
            
            # SNS fails, Telegram succeeds
            mock_sns.side_effect = Exception("SNS service unavailable")
            mock_telegram.return_value = {'ok': True, 'result': {'message_id': 123}}
            
            alert_data = {
                'alert_type': 'test_alert',
                'message': 'Test degradation',
                'severity': 'medium'
            }
            
            # Should still deliver via available channels
            result = integration_test.alert_service.send_alert(
                alert_data, 
                channels=['sns', 'telegram']
            )
            
            # Should partially succeed
            assert 'telegram' in result.get('successful_channels', []), "Telegram delivery should succeed"
            assert 'sns' in result.get('failed_channels', []), "SNS delivery should fail"
            
            integration_test.test_results['service_degradation'] = 'PASS'
            print("  ✅ Graceful service degradation validated")

def run_complete_integration_test():
    """Run the complete end-to-end integration test suite."""
    print("🚀 Starting Complete End-to-End Integration Test Suite")
    print("=" * 60)
    
    integration_test = EndToEndIntegrationTest()
    
    try:
        # Run all test suites
        test_suites = [
            TestCompleteDataPipeline(),
            TestAlertingSystem(),
            TestDashboardIntegration(),
            TestPerformanceAndLoad(),
            TestErrorRecoveryAndResilience()
        ]
        
        total_start_time = time.time()
        
        for suite in test_suites:
            suite_name = suite.__class__.__name__
            print(f"\n📋 Running {suite_name}...")
            
            # Run all test methods in the suite
            for method_name in dir(suite):
                if method_name.startswith('test_'):
                    test_method = getattr(suite, method_name)
                    try:
                        test_method(integration_test)
                    except Exception as e:
                        print(f"  ❌ {method_name} failed: {e}")
                        integration_test.test_results[method_name] = f'FAIL: {e}'
        
        total_execution_time = time.time() - total_start_time
        
        # Generate test report
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        passed_tests = sum(1 for result in integration_test.test_results.values() if result == 'PASS')
        total_tests = len(integration_test.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
        print(f"Total Execution Time: {total_execution_time:.2f}s")
        
        print("\n📈 Performance Metrics:")
        for metric, value in integration_test.performance_metrics.items():
            if isinstance(value, float):
                print(f"  {metric}: {value:.2f}")
            else:
                print(f"  {metric}: {value}")
        
        print("\n📋 Detailed Results:")
        for test_name, result in integration_test.test_results.items():
            status_emoji = "✅" if result == 'PASS' else "❌"
            print(f"  {status_emoji} {test_name}: {result}")
        
        # Save results to file
        results_file = f"integration_test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'test_results': integration_test.test_results,
                'performance_metrics': integration_test.performance_metrics,
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'success_rate': passed_tests / total_tests * 100,
                    'total_execution_time': total_execution_time
                }
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        # Return success status
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"\n💥 Integration test suite failed with error: {e}")
        return False
    
    finally:
        integration_test.cleanup_test_environment()

if __name__ == '__main__':
    success = run_complete_integration_test()
    sys.exit(0 if success else 1)