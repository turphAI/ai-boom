#!/usr/bin/env python3
"""
Master Integration Runner for Boom-Bust Sentinel
This script orchestrates all validation phases for complete system testing.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

def run_command(command: List[str], timeout: int = 600) -> Dict[str, Any]:
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

def main():
    """Main function to run complete system validation."""
    print("🚀 BOOM-BUST SENTINEL COMPLETE SYSTEM VALIDATION")
    print("=" * 60)
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}Z")
    print()
    
    validation_start_time = time.time()
    results = {}
    
    # Phase 1: End-to-End Integration Tests
    print("📋 Phase 1: End-to-End Integration Tests")
    print("-" * 40)
    
    e2e_start = time.time()
    e2e_result = run_command([
        'python', 'tests/test_end_to_end_integration.py'
    ])
    e2e_time = time.time() - e2e_start
    
    results['end_to_end_integration'] = {
        'success': e2e_result['success'],
        'execution_time': e2e_time,
        'details': e2e_result
    }
    
    if e2e_result['success']:
        print("✅ End-to-End Integration Tests: PASSED")
    else:
        print("❌ End-to-End Integration Tests: FAILED")
        print(f"   Error: {e2e_result['stderr'][:200]}...")
    
    print(f"   Execution Time: {e2e_time:.2f}s")
    print()
    
    # Phase 2: System Integration
    print("📋 Phase 2: System Integration")
    print("-" * 40)
    
    integration_start = time.time()
    integration_result = run_command([
        'python', 'scripts/system_integration.py',
        '--environment', 'validation',
        '--output', 'system_integration_results.json'
    ])
    integration_time = time.time() - integration_start
    
    results['system_integration'] = {
        'success': integration_result['success'],
        'execution_time': integration_time,
        'details': integration_result
    }
    
    if integration_result['success']:
        print("✅ System Integration: PASSED")
    else:
        print("❌ System Integration: FAILED")
        print(f"   Error: {integration_result['stderr'][:200]}...")
    
    print(f"   Execution Time: {integration_time:.2f}s")
    print()
    
    # Phase 3: Load Testing and Performance
    print("📋 Phase 3: Load Testing and Performance")
    print("-" * 40)
    
    load_start = time.time()
    load_result = run_command([
        'python', 'scripts/load_testing.py',
        '--output', 'load_testing_results.json'
    ])
    load_time = time.time() - load_start
    
    results['load_testing'] = {
        'success': load_result['success'],
        'execution_time': load_time,
        'details': load_result
    }
    
    if load_result['success']:
        print("✅ Load Testing and Performance: PASSED")
    else:
        print("❌ Load Testing and Performance: FAILED")
        print(f"   Error: {load_result['stderr'][:200]}...")
    
    print(f"   Execution Time: {load_time:.2f}s")
    print()
    
    # Phase 4: Final System Validation
    print("📋 Phase 4: Final System Validation")
    print("-" * 40)
    
    final_start = time.time()
    final_result = run_command([
        'python', 'scripts/final_system_validation.py',
        '--output', 'final_validation_results.json'
    ])
    final_time = time.time() - final_start
    
    results['final_validation'] = {
        'success': final_result['success'],
        'execution_time': final_time,
        'details': final_result
    }
    
    if final_result['success']:
        print("✅ Final System Validation: PASSED")
    else:
        print("❌ Final System Validation: FAILED")
        print(f"   Error: {final_result['stderr'][:200]}...")
    
    print(f"   Execution Time: {final_time:.2f}s")
    print()
    
    # Calculate overall results
    total_validation_time = time.time() - validation_start_time
    successful_phases = sum(1 for result in results.values() if result['success'])
    total_phases = len(results)
    success_rate = (successful_phases / total_phases * 100) if total_phases > 0 else 0
    
    # Generate summary
    print("=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total Phases: {total_phases}")
    print(f"Successful Phases: {successful_phases}")
    print(f"Failed Phases: {total_phases - successful_phases}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Validation Time: {total_validation_time:.2f}s")
    print()
    
    # Phase-by-phase results
    print("📋 Phase Results:")
    for phase_name, phase_result in results.items():
        status = "✅ PASS" if phase_result['success'] else "❌ FAIL"
        time_str = f"{phase_result['execution_time']:.2f}s"
        print(f"  {phase_name.replace('_', ' ').title()}: {status} ({time_str})")
    
    print()
    
    # Load detailed results if available
    detailed_results = {}
    
    # Try to load system integration results
    try:
        if os.path.exists('system_integration_results.json'):
            with open('system_integration_results.json', 'r') as f:
                detailed_results['system_integration'] = json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load system integration details: {e}")
    
    # Try to load load testing results
    try:
        if os.path.exists('load_testing_results.json'):
            with open('load_testing_results.json', 'r') as f:
                detailed_results['load_testing'] = json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load load testing details: {e}")
    
    # Try to load final validation results
    try:
        if os.path.exists('final_validation_results.json'):
            with open('final_validation_results.json', 'r') as f:
                detailed_results['final_validation'] = json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load final validation details: {e}")
    
    # Show key metrics if available
    if detailed_results:
        print("📈 Key Metrics:")
        
        # System integration metrics
        if 'system_integration' in detailed_results:
            si_data = detailed_results['system_integration']
            if 'summary' in si_data:
                summary = si_data['summary']
                print(f"  System Integration Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        # Load testing metrics
        if 'load_testing' in detailed_results:
            lt_data = detailed_results['load_testing']
            if 'summary' in lt_data:
                summary = lt_data['summary']
                print(f"  Performance Score: {summary.get('performance_score', 0):.1f}/100")
                print(f"  Performance Grade: {summary.get('performance_grade', 'N/A')}")
        
        # Final validation metrics
        if 'final_validation' in detailed_results:
            fv_data = detailed_results['final_validation']
            print(f"  Overall System Score: {fv_data.get('overall_score', 0):.1f}/100")
            if 'summary' in fv_data:
                summary = fv_data['summary']
                print(f"  Production Ready: {'✅ YES' if summary.get('ready_for_production') else '❌ NO'}")
        
        print()
    
    # Generate recommendations
    recommendations = []
    
    if success_rate < 100:
        recommendations.append("Address failing validation phases before deployment")
    
    if success_rate < 75:
        recommendations.append("System requires significant improvements")
    
    if 'final_validation' in detailed_results:
        fv_data = detailed_results['final_validation']
        if 'summary' in fv_data and 'recommendations' in fv_data['summary']:
            recommendations.extend(fv_data['summary']['recommendations'])
    
    if recommendations:
        print("💡 Recommendations:")
        for rec in recommendations:
            print(f"  - {rec}")
        print()
    
    # Save complete results
    complete_results = {
        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
        'total_validation_time': total_validation_time,
        'success_rate': success_rate,
        'phase_results': results,
        'detailed_results': detailed_results,
        'recommendations': recommendations
    }
    
    with open('complete_validation_results.json', 'w') as f:
        json.dump(complete_results, f, indent=2)
    
    print(f"💾 Complete results saved to: complete_validation_results.json")
    print()
    
    # Final status
    if success_rate >= 80:
        print("🎉 COMPLETE SYSTEM VALIDATION: SUCCESS!")
        print("✅ Boom-Bust Sentinel is ready for deployment!")
        
        # Show deployment next steps
        print()
        print("🚀 Next Steps for Deployment:")
        print("  1. Review any remaining recommendations")
        print("  2. Set up production environment variables")
        print("  3. Configure AWS credentials and secrets")
        print("  4. Run deployment script:")
        print("     ./deploy.sh serverless --stage prod --frontend")
        print("  5. Verify production deployment with health checks")
        
        sys.exit(0)
    else:
        print("❌ COMPLETE SYSTEM VALIDATION: FAILED!")
        print("🔧 System requires improvements before deployment.")
        
        # Show critical issues
        print()
        print("🚨 Critical Issues to Address:")
        failed_phases = [name for name, result in results.items() if not result['success']]
        for phase in failed_phases:
            print(f"  - {phase.replace('_', ' ').title()}")
        
        sys.exit(1)

if __name__ == '__main__':
    main()