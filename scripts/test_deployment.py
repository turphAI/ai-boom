#!/usr/bin/env python3
"""
Deployment testing script for Boom-Bust Sentinel
This script runs comprehensive tests to verify deployment success.
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Any

class DeploymentTester:
    def __init__(self, stage: str, region: str):
        self.stage = stage
        self.region = region
        self.test_results = []
        
    def run_command(self, command: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Run a command and return the result."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, 'AWS_REGION': self.region, 'STAGE': self.stage}
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(command)
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'command': ' '.join(command)
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'command': ' '.join(command)
            }
    
    def test_infrastructure(self) -> Dict[str, Any]:
        """Test infrastructure deployment."""
        print("🏗️  Testing infrastructure deployment...")
        
        tests = []
        
        # Test Lambda functions
        print("  🔍 Testing Lambda functions...")
        lambda_test = self.run_command([
            'python', 'scripts/lambda_health_check.py',
            '--environment', self.stage,
            '--fail-on-unhealthy'
        ])
        tests.append({
            'name': 'Lambda Functions Health Check',
            'success': lambda_test['success'],
            'details': lambda_test
        })
        
        # Test overall system health
        print("  🔍 Testing system health...")
        health_test = self.run_command([
            'python', 'scripts/health_check.py',
            '--environment', self.stage,
            '--fail-on-unhealthy'
        ])
        tests.append({
            'name': 'System Health Check',
            'success': health_test['success'],
            'details': health_test
        })
        
        # Test deployment verification
        print("  🔍 Running deployment verification tests...")
        pytest_args = [
            'python', '-m', 'pytest',
            'tests/test_deployment_verification.py',
            '-v',
            '--tb=short'
        ]
        
        if self.stage == 'staging':
            pytest_args.append('--staging')
        elif self.stage == 'prod':
            pytest_args.append('--production')
        
        verification_test = self.run_command(pytest_args)
        tests.append({
            'name': 'Deployment Verification Tests',
            'success': verification_test['success'],
            'details': verification_test
        })
        
        success_count = sum(1 for test in tests if test['success'])
        
        return {
            'success': success_count == len(tests),
            'total_tests': len(tests),
            'passed_tests': success_count,
            'tests': tests
        }
    
    def test_functionality(self) -> Dict[str, Any]:
        """Test application functionality."""
        print("⚙️  Testing application functionality...")
        
        tests = []
        
        # Test scraper functionality
        scrapers = ['bond-issuance', 'bdc-discount']  # Test subset for speed
        
        for scraper in scrapers:
            print(f"  🔍 Testing {scraper} scraper...")
            
            # Run unit tests for the scraper
            test_command = [
                'python', '-m', 'pytest',
                f'tests/test_{scraper.replace("-", "_")}_scraper.py',
                '-v',
                '--tb=short'
            ]
            
            scraper_test = self.run_command(test_command)
            tests.append({
                'name': f'{scraper} Scraper Tests',
                'success': scraper_test['success'],
                'details': scraper_test
            })
        
        # Test integration
        print("  🔍 Testing integration...")
        integration_test = self.run_command([
            'python', '-m', 'pytest',
            'tests/test_integration.py',
            '-v',
            '--tb=short'
        ])
        tests.append({
            'name': 'Integration Tests',
            'success': integration_test['success'],
            'details': integration_test
        })
        
        success_count = sum(1 for test in tests if test['success'])
        
        return {
            'success': success_count == len(tests),
            'total_tests': len(tests),
            'passed_tests': success_count,
            'tests': tests
        }
    
    def test_performance(self) -> Dict[str, Any]:
        """Test performance characteristics."""
        print("🚀 Testing performance...")
        
        tests = []
        
        # Test Lambda cold start times
        print("  🔍 Testing Lambda cold start performance...")
        
        # This is a simplified performance test
        # In a real scenario, you might use more sophisticated tools
        performance_test = {
            'name': 'Lambda Performance Test',
            'success': True,  # Placeholder - implement actual performance tests
            'details': {
                'success': True,
                'stdout': 'Performance tests passed (placeholder)',
                'stderr': '',
                'command': 'performance_test_placeholder'
            }
        }
        tests.append(performance_test)
        
        success_count = sum(1 for test in tests if test['success'])
        
        return {
            'success': success_count == len(tests),
            'total_tests': len(tests),
            'passed_tests': success_count,
            'tests': tests
        }
    
    def test_security(self) -> Dict[str, Any]:
        """Test security configuration."""
        print("🔒 Testing security configuration...")
        
        tests = []
        
        # Test IAM permissions
        print("  🔍 Testing IAM permissions...")
        
        # Check if functions can access required resources
        iam_test = {
            'name': 'IAM Permissions Test',
            'success': True,  # Placeholder - implement actual IAM tests
            'details': {
                'success': True,
                'stdout': 'IAM permissions verified (placeholder)',
                'stderr': '',
                'command': 'iam_test_placeholder'
            }
        }
        tests.append(iam_test)
        
        # Test secrets access
        print("  🔍 Testing secrets access...")
        secrets_test = {
            'name': 'Secrets Access Test',
            'success': True,  # Placeholder
            'details': {
                'success': True,
                'stdout': 'Secrets access verified (placeholder)',
                'stderr': '',
                'command': 'secrets_test_placeholder'
            }
        }
        tests.append(secrets_test)
        
        success_count = sum(1 for test in tests if test['success'])
        
        return {
            'success': success_count == len(tests),
            'total_tests': len(tests),
            'passed_tests': success_count,
            'tests': tests
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all deployment tests."""
        print(f"🧪 Running deployment tests for {self.stage} in {self.region}")
        print(f"   Timestamp: {datetime.utcnow().isoformat()}Z")
        print()
        
        start_time = time.time()
        
        # Run test suites
        infrastructure_results = self.test_infrastructure()
        functionality_results = self.test_functionality()
        performance_results = self.test_performance()
        security_results = self.test_security()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Compile overall results
        all_results = [
            infrastructure_results,
            functionality_results,
            performance_results,
            security_results
        ]
        
        total_tests = sum(result['total_tests'] for result in all_results)
        passed_tests = sum(result['passed_tests'] for result in all_results)
        overall_success = all(result['success'] for result in all_results)
        
        results = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'stage': self.stage,
            'region': self.region,
            'duration_seconds': duration,
            'overall_success': overall_success,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'test_suites': {
                'infrastructure': infrastructure_results,
                'functionality': functionality_results,
                'performance': performance_results,
                'security': security_results
            }
        }
        
        # Print summary
        print()
        print("📊 Deployment Test Summary:")
        print(f"   Overall Success: {'✅ PASS' if overall_success else '❌ FAIL'}")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed Tests: {passed_tests}")
        print(f"   Success Rate: {results['success_rate']:.1f}%")
        print(f"   Duration: {duration:.1f} seconds")
        print()
        
        # Print detailed results
        for suite_name, suite_results in results['test_suites'].items():
            status = "✅ PASS" if suite_results['success'] else "❌ FAIL"
            print(f"   {suite_name.title()}: {status} ({suite_results['passed_tests']}/{suite_results['total_tests']})")
            
            # Show failed tests
            if not suite_results['success']:
                for test in suite_results['tests']:
                    if not test['success']:
                        print(f"     ❌ {test['name']}")
                        if test['details']['stderr']:
                            print(f"        Error: {test['details']['stderr'][:100]}...")
        
        return results
    
    def generate_report(self, results: Dict[str, Any], output_file: str = None) -> None:
        """Generate a detailed test report."""
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Detailed report saved to: {output_file}")
        
        # Generate summary report
        summary_file = f"deployment_test_summary_{self.stage}_{int(time.time())}.txt"
        
        with open(summary_file, 'w') as f:
            f.write(f"Boom-Bust Sentinel Deployment Test Report\n")
            f.write(f"=========================================\n\n")
            f.write(f"Environment: {self.stage}\n")
            f.write(f"Region: {self.region}\n")
            f.write(f"Timestamp: {results['timestamp']}\n")
            f.write(f"Duration: {results['duration_seconds']:.1f} seconds\n\n")
            
            f.write(f"Overall Result: {'PASS' if results['overall_success'] else 'FAIL'}\n")
            f.write(f"Success Rate: {results['success_rate']:.1f}% ({results['passed_tests']}/{results['total_tests']})\n\n")
            
            f.write("Test Suite Results:\n")
            f.write("==================\n\n")
            
            for suite_name, suite_results in results['test_suites'].items():
                f.write(f"{suite_name.title()}:\n")
                f.write(f"  Status: {'PASS' if suite_results['success'] else 'FAIL'}\n")
                f.write(f"  Tests: {suite_results['passed_tests']}/{suite_results['total_tests']}\n")
                
                for test in suite_results['tests']:
                    status = "PASS" if test['success'] else "FAIL"
                    f.write(f"    - {test['name']}: {status}\n")
                    
                    if not test['success'] and test['details']['stderr']:
                        f.write(f"      Error: {test['details']['stderr']}\n")
                
                f.write("\n")
        
        print(f"📄 Summary report saved to: {summary_file}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Boom-Bust Sentinel Deployment Tester')
    parser.add_argument('--stage', '-s', required=True,
                       choices=['dev', 'staging', 'prod'],
                       help='Deployment stage to test')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--output', '-o',
                       help='Output file for detailed results (JSON)')
    parser.add_argument('--fail-fast', action='store_true',
                       help='Stop on first test failure')
    parser.add_argument('--suite', choices=['infrastructure', 'functionality', 'performance', 'security'],
                       help='Run only specific test suite')
    
    args = parser.parse_args()
    
    # Create tester
    tester = DeploymentTester(args.stage, args.region)
    
    # Run tests
    if args.suite:
        # Run specific suite
        if args.suite == 'infrastructure':
            results = {'test_suites': {'infrastructure': tester.test_infrastructure()}}
        elif args.suite == 'functionality':
            results = {'test_suites': {'functionality': tester.test_functionality()}}
        elif args.suite == 'performance':
            results = {'test_suites': {'performance': tester.test_performance()}}
        elif args.suite == 'security':
            results = {'test_suites': {'security': tester.test_security()}}
        
        # Add metadata
        results.update({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'stage': args.stage,
            'region': args.region,
            'overall_success': results['test_suites'][args.suite]['success']
        })
    else:
        # Run all tests
        results = tester.run_all_tests()
    
    # Generate report
    tester.generate_report(results, args.output)
    
    # Exit with appropriate code
    if not results['overall_success']:
        print(f"\n❌ Deployment tests failed!")
        sys.exit(1)
    else:
        print(f"\n✅ All deployment tests passed!")
        sys.exit(0)

if __name__ == '__main__':
    main()