#!/usr/bin/env python3
"""
Final System Validation for Boom-Bust Sentinel
This script performs comprehensive end-to-end system validation.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging_config import setup_logging

class FinalSystemValidator:
    """Comprehensive final system validation."""
    
    def __init__(self):
        self.logger = setup_logging("final_system_validation")
        self.validation_results = {}
        self.overall_score = 0
        
    def run_command(self, command: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Run a command and return the result."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
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
    
    def validate_code_quality(self) -> Dict[str, Any]:
        """Validate code quality and standards."""
        self.logger.info("Validating code quality and standards...")
        
        quality_results = {}
        
        # Test 1: Run unit tests with coverage
        self.logger.info("Running unit tests with coverage...")
        test_result = self.run_command([
            'python', '-m', 'pytest', 
            'tests/', 
            '--cov=.',
            '--cov-report=json',
            '--cov-report=term-missing',
            '-v'
        ])
        
        quality_results['unit_tests'] = {
            'status': 'pass' if test_result['success'] else 'fail',
            'details': test_result
        }
        
        # Test 2: Code linting with flake8
        self.logger.info("Running code linting...")
        lint_result = self.run_command([
            'python', '-m', 'flake8',
            '--max-line-length=100',
            '--ignore=E501,W503',
            'scrapers/', 'services/', 'utils/', 'handlers/'
        ])
        
        quality_results['linting'] = {
            'status': 'pass' if lint_result['success'] else 'fail',
            'details': lint_result
        }
        
        # Test 3: Type checking with mypy (if available)
        try:
            mypy_result = self.run_command([
                'python', '-m', 'mypy',
                '--ignore-missing-imports',
                'scrapers/', 'services/', 'utils/'
            ])
            
            quality_results['type_checking'] = {
                'status': 'pass' if mypy_result['success'] else 'fail',
                'details': mypy_result
            }
        except:
            quality_results['type_checking'] = {
                'status': 'skipped',
                'reason': 'mypy not available'
            }
        
        # Test 4: Security scanning with bandit (if available)
        try:
            security_result = self.run_command([
                'python', '-m', 'bandit',
                '-r', 'scrapers/', 'services/', 'utils/', 'handlers/',
                '-f', 'json'
            ])
            
            quality_results['security_scan'] = {
                'status': 'pass' if security_result['success'] else 'fail',
                'details': security_result
            }
        except:
            quality_results['security_scan'] = {
                'status': 'skipped',
                'reason': 'bandit not available'
            }
        
        return quality_results
    
    def validate_system_integration(self) -> Dict[str, Any]:
        """Validate complete system integration."""
        self.logger.info("Validating system integration...")
        
        # Run the system integration script
        integration_result = self.run_command([
            'python', 'scripts/system_integration.py',
            '--environment', 'validation',
            '--output', 'integration_validation_results.json'
        ])
        
        integration_status = {
            'status': 'pass' if integration_result['success'] else 'fail',
            'details': integration_result
        }
        
        # Try to load detailed results if available
        try:
            if os.path.exists('integration_validation_results.json'):
                with open('integration_validation_results.json', 'r') as f:
                    detailed_results = json.load(f)
                    integration_status['detailed_results'] = detailed_results
        except Exception as e:
            self.logger.warning(f"Could not load detailed integration results: {e}")
        
        return integration_status
    
    def validate_performance(self) -> Dict[str, Any]:
        """Validate system performance."""
        self.logger.info("Validating system performance...")
        
        # Run the load testing script
        performance_result = self.run_command([
            'python', 'scripts/load_testing.py',
            '--output', 'performance_validation_results.json'
        ])
        
        performance_status = {
            'status': 'pass' if performance_result['success'] else 'fail',
            'details': performance_result
        }
        
        # Try to load detailed results if available
        try:
            if os.path.exists('performance_validation_results.json'):
                with open('performance_validation_results.json', 'r') as f:
                    detailed_results = json.load(f)
                    performance_status['detailed_results'] = detailed_results
        except Exception as e:
            self.logger.warning(f"Could not load detailed performance results: {e}")
        
        return performance_status
    
    def validate_deployment_readiness(self) -> Dict[str, Any]:
        """Validate deployment readiness."""
        self.logger.info("Validating deployment readiness...")
        
        deployment_results = {}
        
        # Test 1: Validate configuration files
        config_files = [
            'serverless.yml',
            'terraform/main.tf',
            'dashboard/package.json',
            'dashboard/vercel.json',
            'requirements.txt'
        ]
        
        config_validation = {}
        for config_file in config_files:
            if os.path.exists(config_file):
                config_validation[config_file] = 'present'
            else:
                config_validation[config_file] = 'missing'
        
        deployment_results['configuration_files'] = config_validation
        
        # Test 2: Validate environment variables and secrets
        required_env_vars = [
            'AWS_REGION',
            'DYNAMODB_TABLE',
            'SNS_TOPIC_ARN'
        ]
        
        env_validation = {}
        for env_var in required_env_vars:
            env_validation[env_var] = 'set' if os.getenv(env_var) else 'missing'
        
        deployment_results['environment_variables'] = env_validation
        
        # Test 3: Validate dependencies
        self.logger.info("Validating Python dependencies...")
        deps_result = self.run_command(['pip', 'check'])
        
        deployment_results['dependencies'] = {
            'status': 'valid' if deps_result['success'] else 'invalid',
            'details': deps_result
        }
        
        # Test 4: Validate frontend dependencies
        if os.path.exists('dashboard/package.json'):
            self.logger.info("Validating frontend dependencies...")
            frontend_deps_result = self.run_command([
                'npm', 'audit', '--audit-level=moderate'
            ], timeout=60)
            
            deployment_results['frontend_dependencies'] = {
                'status': 'valid' if frontend_deps_result['success'] else 'issues_found',
                'details': frontend_deps_result
            }
        
        return deployment_results
    
    def validate_documentation(self) -> Dict[str, Any]:
        """Validate documentation completeness."""
        self.logger.info("Validating documentation...")
        
        doc_results = {}
        
        # Required documentation files
        required_docs = [
            'README.md',
            'DEPLOYMENT.md',
            'LICENSE',
            'requirements.txt',
            '.kiro/specs/boom-bust-sentinel/requirements.md',
            '.kiro/specs/boom-bust-sentinel/design.md',
            '.kiro/specs/boom-bust-sentinel/tasks.md'
        ]
        
        doc_validation = {}
        for doc_file in required_docs:
            if os.path.exists(doc_file):
                # Check if file has content
                try:
                    with open(doc_file, 'r') as f:
                        content = f.read().strip()
                        if len(content) > 100:  # Minimum content threshold
                            doc_validation[doc_file] = 'complete'
                        else:
                            doc_validation[doc_file] = 'incomplete'
                except:
                    doc_validation[doc_file] = 'unreadable'
            else:
                doc_validation[doc_file] = 'missing'
        
        doc_results['required_documentation'] = doc_validation
        
        # Check for inline documentation
        code_files = []
        for root, dirs, files in os.walk('.'):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    code_files.append(os.path.join(root, file))
        
        documented_files = 0
        total_files = len(code_files)
        
        for code_file in code_files[:20]:  # Check first 20 files to avoid timeout
            try:
                with open(code_file, 'r') as f:
                    content = f.read()
                    # Check for docstrings
                    if '"""' in content or "'''" in content:
                        documented_files += 1
            except:
                continue
        
        documentation_coverage = (documented_files / total_files * 100) if total_files > 0 else 0
        
        doc_results['code_documentation'] = {
            'coverage_percentage': documentation_coverage,
            'documented_files': documented_files,
            'total_files': total_files
        }
        
        return doc_results
    
    def validate_security_compliance(self) -> Dict[str, Any]:
        """Validate security compliance."""
        self.logger.info("Validating security compliance...")
        
        security_results = {}
        
        # Test 1: Check for hardcoded secrets
        self.logger.info("Scanning for hardcoded secrets...")
        
        # Simple pattern matching for common secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        potential_secrets = []
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.json', '.yml', '.yaml')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            for pattern in secret_patterns:
                                import re
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                if matches:
                                    potential_secrets.append({
                                        'file': file_path,
                                        'pattern': pattern,
                                        'matches': len(matches)
                                    })
                    except:
                        continue
        
        security_results['hardcoded_secrets'] = {
            'status': 'pass' if len(potential_secrets) == 0 else 'warning',
            'potential_issues': len(potential_secrets),
            'details': potential_secrets[:5]  # Show first 5 issues
        }
        
        # Test 2: Check file permissions
        sensitive_files = [
            'config/secrets.py',
            '.env',
            '.env.local',
            'serverless.yml'
        ]
        
        permission_issues = []
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                try:
                    file_stat = os.stat(file_path)
                    file_mode = oct(file_stat.st_mode)[-3:]
                    
                    # Check if file is world-readable (last digit > 0)
                    if int(file_mode[-1]) > 0:
                        permission_issues.append({
                            'file': file_path,
                            'permissions': file_mode,
                            'issue': 'world_readable'
                        })
                except:
                    continue
        
        security_results['file_permissions'] = {
            'status': 'pass' if len(permission_issues) == 0 else 'warning',
            'issues': permission_issues
        }
        
        return security_results
    
    def calculate_overall_score(self) -> float:
        """Calculate overall system validation score."""
        scores = []
        weights = {
            'code_quality': 0.25,
            'system_integration': 0.30,
            'performance': 0.20,
            'deployment_readiness': 0.15,
            'documentation': 0.05,
            'security_compliance': 0.05
        }
        
        for category, weight in weights.items():
            if category in self.validation_results:
                category_score = self._calculate_category_score(category)
                scores.append(category_score * weight)
        
        return sum(scores)
    
    def _calculate_category_score(self, category: str) -> float:
        """Calculate score for a specific category."""
        results = self.validation_results[category]
        
        if category == 'code_quality':
            # Score based on test results
            scores = []
            if 'unit_tests' in results:
                scores.append(100 if results['unit_tests']['status'] == 'pass' else 0)
            if 'linting' in results:
                scores.append(100 if results['linting']['status'] == 'pass' else 50)
            if 'type_checking' in results:
                if results['type_checking']['status'] == 'pass':
                    scores.append(100)
                elif results['type_checking']['status'] == 'skipped':
                    scores.append(75)  # Neutral score for skipped
                else:
                    scores.append(0)
            
            return sum(scores) / len(scores) if scores else 0
        
        elif category == 'system_integration':
            if 'detailed_results' in results:
                detailed = results['detailed_results']
                if 'summary' in detailed:
                    return detailed['summary'].get('success_rate', 0)
            return 100 if results['status'] == 'pass' else 0
        
        elif category == 'performance':
            if 'detailed_results' in results:
                detailed = results['detailed_results']
                if 'summary' in detailed:
                    return detailed['summary'].get('performance_score', 0)
            return 100 if results['status'] == 'pass' else 0
        
        elif category == 'deployment_readiness':
            scores = []
            
            # Configuration files score
            if 'configuration_files' in results:
                config_files = results['configuration_files']
                present_files = sum(1 for status in config_files.values() if status == 'present')
                total_files = len(config_files)
                scores.append((present_files / total_files * 100) if total_files > 0 else 0)
            
            # Dependencies score
            if 'dependencies' in results:
                scores.append(100 if results['dependencies']['status'] == 'valid' else 0)
            
            return sum(scores) / len(scores) if scores else 0
        
        elif category == 'documentation':
            scores = []
            
            # Required documentation score
            if 'required_documentation' in results:
                docs = results['required_documentation']
                complete_docs = sum(1 for status in docs.values() if status == 'complete')
                total_docs = len(docs)
                scores.append((complete_docs / total_docs * 100) if total_docs > 0 else 0)
            
            # Code documentation score
            if 'code_documentation' in results:
                coverage = results['code_documentation']['coverage_percentage']
                scores.append(coverage)
            
            return sum(scores) / len(scores) if scores else 0
        
        elif category == 'security_compliance':
            scores = []
            
            if 'hardcoded_secrets' in results:
                scores.append(100 if results['hardcoded_secrets']['status'] == 'pass' else 50)
            
            if 'file_permissions' in results:
                scores.append(100 if results['file_permissions']['status'] == 'pass' else 75)
            
            return sum(scores) / len(scores) if scores else 0
        
        return 0
    
    def run_final_validation(self) -> Dict[str, Any]:
        """Run complete final system validation."""
        self.logger.info("Starting final system validation...")
        
        validation_start_time = time.time()
        
        try:
            # Phase 1: Code Quality Validation
            self.logger.info("Phase 1: Code Quality Validation")
            self.validation_results['code_quality'] = self.validate_code_quality()
            
            # Phase 2: System Integration Validation
            self.logger.info("Phase 2: System Integration Validation")
            self.validation_results['system_integration'] = self.validate_system_integration()
            
            # Phase 3: Performance Validation
            self.logger.info("Phase 3: Performance Validation")
            self.validation_results['performance'] = self.validate_performance()
            
            # Phase 4: Deployment Readiness Validation
            self.logger.info("Phase 4: Deployment Readiness Validation")
            self.validation_results['deployment_readiness'] = self.validate_deployment_readiness()
            
            # Phase 5: Documentation Validation
            self.logger.info("Phase 5: Documentation Validation")
            self.validation_results['documentation'] = self.validate_documentation()
            
            # Phase 6: Security Compliance Validation
            self.logger.info("Phase 6: Security Compliance Validation")
            self.validation_results['security_compliance'] = self.validate_security_compliance()
            
            # Calculate overall score
            self.overall_score = self.calculate_overall_score()
            
            total_validation_time = time.time() - validation_start_time
            
            # Generate final summary
            summary = self._generate_final_summary()
            
            self.logger.info(f"Final system validation completed in {total_validation_time:.2f}s")
            
            return {
                'status': 'completed',
                'overall_score': self.overall_score,
                'summary': summary,
                'validation_results': self.validation_results,
                'validation_time': total_validation_time,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Final validation failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'partial_results': self.validation_results
            }
    
    def _generate_final_summary(self) -> Dict[str, Any]:
        """Generate final validation summary."""
        # Determine overall grade
        if self.overall_score >= 90:
            grade = 'A'
            status = 'excellent'
        elif self.overall_score >= 80:
            grade = 'B'
            status = 'good'
        elif self.overall_score >= 70:
            grade = 'C'
            status = 'acceptable'
        elif self.overall_score >= 60:
            grade = 'D'
            status = 'needs_improvement'
        else:
            grade = 'F'
            status = 'unacceptable'
        
        # Generate recommendations
        recommendations = []
        
        if self.overall_score < 90:
            recommendations.append("Review and address failing validation checks")
        
        if self.overall_score < 80:
            recommendations.append("Improve test coverage and code quality")
        
        if self.overall_score < 70:
            recommendations.append("Address performance and integration issues")
        
        if self.overall_score < 60:
            recommendations.append("System requires significant improvements before deployment")
        
        # Category breakdown
        category_scores = {}
        for category in self.validation_results.keys():
            category_scores[category] = self._calculate_category_score(category)
        
        return {
            'overall_score': self.overall_score,
            'grade': grade,
            'status': status,
            'category_scores': category_scores,
            'recommendations': recommendations,
            'ready_for_production': self.overall_score >= 80
        }

def main():
    """Main function to run final system validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Boom-Bust Sentinel Final System Validation')
    parser.add_argument('--output', '-o', help='Output file for results (JSON)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Run final validation
    validator = FinalSystemValidator()
    results = validator.run_final_validation()
    
    # Print summary
    print("\n" + "=" * 70)
    print("🎯 BOOM-BUST SENTINEL FINAL SYSTEM VALIDATION")
    print("=" * 70)
    
    if results['status'] == 'completed':
        summary = results['summary']
        print(f"Overall Score: {results['overall_score']:.1f}/100 (Grade: {summary['grade']})")
        print(f"System Status: {summary['status'].upper()}")
        print(f"Production Ready: {'✅ YES' if summary['ready_for_production'] else '❌ NO'}")
        print(f"Validation Time: {results['validation_time']:.2f}s")
        
        print(f"\n📊 Category Scores:")
        for category, score in summary['category_scores'].items():
            print(f"  {category.replace('_', ' ').title()}: {score:.1f}/100")
        
        if summary['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in summary['recommendations']:
                print(f"  - {rec}")
        
        # Show critical issues
        critical_issues = []
        for category, result in results['validation_results'].items():
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, dict) and value.get('status') == 'fail':
                        critical_issues.append(f"{category}.{key}")
        
        if critical_issues:
            print(f"\n🚨 Critical Issues:")
            for issue in critical_issues:
                print(f"  - {issue}")
    else:
        print(f"Validation Status: FAILED")
        print(f"Error: {results.get('error', 'Unknown error')}")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to: {args.output}")
    
    # Exit with appropriate code
    if results['status'] == 'completed' and results['overall_score'] >= 70:
        print("\n🎉 Final system validation completed successfully!")
        print("System is ready for deployment!")
        sys.exit(0)
    else:
        print("\n❌ Final system validation failed!")
        print("System requires improvements before deployment.")
        sys.exit(1)

if __name__ == '__main__':
    main()