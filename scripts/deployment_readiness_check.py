#!/usr/bin/env python3
"""
Comprehensive deployment readiness check for boom-bust-sentinel
"""

import os
import sys
import json
import boto3
import requests
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

class DeploymentChecker:
    def __init__(self):
        load_dotenv()
        self.results = {}
        self.aws_client_cache = {}
    
    def get_aws_client(self, service):
        """Get AWS client with error handling"""
        if service not in self.aws_client_cache:
            try:
                self.aws_client_cache[service] = boto3.client(service)
            except Exception as e:
                print(f"❌ Cannot create {service} client: {e}")
                return None
        return self.aws_client_cache[service]
    
    def check_aws_credentials(self):
        """Check AWS credentials and basic connectivity"""
        print("\n🔐 Checking AWS Credentials...")
        
        try:
            sts = self.get_aws_client('sts')
            if not sts:
                return False
                
            identity = sts.get_caller_identity()
            print(f"✅ AWS Identity: {identity['Arn']}")
            print(f"   Account: {identity['Account']}")
            self.results['aws_identity'] = identity
            return True
            
        except Exception as e:
            print(f"❌ AWS credentials failed: {e}")
            self.results['aws_identity'] = None
            return False
    
    def check_aws_permissions(self):
        """Check specific AWS service permissions needed for deployment"""
        print("\n🔑 Checking AWS Permissions...")
        
        permissions = {
            'dynamodb': ['list_tables', 'create_table', 'describe_table'],
            'lambda': ['list_functions', 'create_function'],
            'iam': ['list_roles', 'create_role'],
            'sns': ['list_topics', 'create_topic'],
            'cloudformation': ['describe_stacks', 'create_stack'],
            'secretsmanager': ['list_secrets', 'create_secret']
        }
        
        permission_results = {}
        
        for service, actions in permissions.items():
            print(f"  📋 Testing {service.upper()}...")
            service_results = {}
            
            client = self.get_aws_client(service)
            if not client:
                permission_results[service] = {'error': 'Cannot create client'}
                continue
            
            for action in actions:
                try:
                    if service == 'dynamodb' and action == 'list_tables':
                        client.list_tables()
                        service_results[action] = True
                        print(f"    ✅ {action}")
                    elif service == 'lambda' and action == 'list_functions':
                        client.list_functions()
                        service_results[action] = True
                        print(f"    ✅ {action}")
                    elif service == 'iam' and action == 'list_roles':
                        client.list_roles(MaxItems=1)
                        service_results[action] = True
                        print(f"    ✅ {action}")
                    elif service == 'sns' and action == 'list_topics':
                        client.list_topics()
                        service_results[action] = True
                        print(f"    ✅ {action}")
                    elif service == 'cloudformation' and action == 'describe_stacks':
                        client.describe_stacks()
                        service_results[action] = True
                        print(f"    ✅ {action}")
                    elif service == 'secretsmanager' and action == 'list_secrets':
                        client.list_secrets(MaxResults=1)
                        service_results[action] = True
                        print(f"    ✅ {action}")
                    else:
                        service_results[action] = 'skipped'
                        print(f"    ⏭️  {action} (skipped)")
                        
                except ClientError as e:
                    if 'AccessDenied' in str(e) or 'UnauthorizedOperation' in str(e):
                        service_results[action] = False
                        print(f"    ❌ {action} - Access Denied")
                    else:
                        service_results[action] = f"Error: {e.response['Error']['Code']}"
                        print(f"    ⚠️  {action} - {e.response['Error']['Code']}")
                except Exception as e:
                    service_results[action] = f"Error: {str(e)}"
                    print(f"    ❌ {action} - {str(e)}")
            
            permission_results[service] = service_results
        
        self.results['aws_permissions'] = permission_results
        return permission_results
    
    def check_deployment_tools(self):
        """Check if deployment tools are available"""
        print("\n🛠️  Checking Deployment Tools...")
        
        tools = {
            'serverless': 'serverless --version',
            'terraform': 'terraform version',
            'aws-cli': 'aws --version',
            'node': 'node --version',
            'npm': 'npm --version'
        }
        
        tool_results = {}
        
        for tool, command in tools.items():
            try:
                import subprocess
                result = subprocess.run(command.split(), capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
                    tool_results[tool] = {'available': True, 'version': version}
                    print(f"✅ {tool}: {version}")
                else:
                    tool_results[tool] = {'available': False, 'error': result.stderr}
                    print(f"❌ {tool}: Not working")
            except Exception as e:
                tool_results[tool] = {'available': False, 'error': str(e)}
                print(f"❌ {tool}: {str(e)}")
        
        self.results['deployment_tools'] = tool_results
        return tool_results
    
    def check_environment_config(self):
        """Check environment configuration"""
        print("\n⚙️  Checking Environment Configuration...")
        
        required_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY', 
            'AWS_REGION',
            'ENVIRONMENT'
        ]
        
        optional_vars = [
            'GRAFANA_URL',
            'GRAFANA_API_KEY',
            'DATABASE_PROVIDER',
            'NOTIFICATION_PROVIDER'
        ]
        
        config_results = {'required': {}, 'optional': {}}
        
        print("  📋 Required variables:")
        for var in required_vars:
            value = os.getenv(var)
            if value:
                config_results['required'][var] = 'set'
                print(f"    ✅ {var}: Set")
            else:
                config_results['required'][var] = 'missing'
                print(f"    ❌ {var}: Missing")
        
        print("  📋 Optional variables:")
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                config_results['optional'][var] = 'set'
                print(f"    ✅ {var}: Set")
            else:
                config_results['optional'][var] = 'missing'
                print(f"    ⚪ {var}: Not set")
        
        self.results['environment_config'] = config_results
        return config_results
    
    def check_local_system(self):
        """Check local system functionality"""
        print("\n🏠 Checking Local System...")
        
        local_results = {}
        
        # Check if scrapers work
        try:
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from scrapers.bond_issuance_scraper import BondIssuanceScraper
            
            scraper = BondIssuanceScraper()
            result = scraper.execute()
            
            local_results['scrapers'] = {
                'working': True,
                'success': result.success,
                'execution_time': result.execution_time
            }
            print(f"✅ Scrapers: Working (success: {result.success})")
            
        except Exception as e:
            local_results['scrapers'] = {'working': False, 'error': str(e)}
            print(f"❌ Scrapers: {str(e)}")
        
        # Check data directory
        data_dir = './data'
        if os.path.exists(data_dir):
            files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
            local_results['data_storage'] = {'working': True, 'files': len(files)}
            print(f"✅ Data Storage: {len(files)} files in {data_dir}")
        else:
            local_results['data_storage'] = {'working': False, 'error': 'Data directory missing'}
            print(f"❌ Data Storage: Directory {data_dir} missing")
        
        # Check dashboard
        dashboard_dir = './dashboard'
        if os.path.exists(dashboard_dir):
            package_json = os.path.join(dashboard_dir, 'package.json')
            if os.path.exists(package_json):
                local_results['dashboard'] = {'working': True}
                print("✅ Dashboard: Ready")
            else:
                local_results['dashboard'] = {'working': False, 'error': 'package.json missing'}
                print("❌ Dashboard: package.json missing")
        else:
            local_results['dashboard'] = {'working': False, 'error': 'Dashboard directory missing'}
            print("❌ Dashboard: Directory missing")
        
        self.results['local_system'] = local_results
        return local_results
    
    def generate_deployment_plan(self):
        """Generate a deployment plan based on current status"""
        print("\n📋 Generating Deployment Plan...")
        
        plan = {
            'readiness_score': 0,
            'blockers': [],
            'recommendations': [],
            'next_steps': []
        }
        
        # Calculate readiness score
        score = 0
        total_checks = 0
        
        # AWS credentials (critical)
        if self.results.get('aws_identity'):
            score += 20
        else:
            plan['blockers'].append("AWS credentials not working")
        total_checks += 20
        
        # AWS permissions (critical)
        permissions = self.results.get('aws_permissions', {})
        permission_score = 0
        for service, actions in permissions.items():
            if isinstance(actions, dict):
                for action, result in actions.items():
                    if result is True:
                        permission_score += 1
        
        if permission_score >= 8:  # Need most permissions
            score += 30
        elif permission_score >= 4:
            score += 15
            plan['blockers'].append("Limited AWS permissions")
        else:
            plan['blockers'].append("Insufficient AWS permissions")
        total_checks += 30
        
        # Deployment tools
        tools = self.results.get('deployment_tools', {})
        tool_score = sum(1 for tool in tools.values() if tool.get('available'))
        score += min(tool_score * 5, 25)
        total_checks += 25
        
        # Environment config
        config = self.results.get('environment_config', {})
        required_set = sum(1 for var in config.get('required', {}).values() if var == 'set')
        score += min(required_set * 6, 25)
        total_checks += 25
        
        plan['readiness_score'] = int((score / total_checks) * 100) if total_checks > 0 else 0
        
        # Generate recommendations
        if plan['readiness_score'] >= 80:
            plan['recommendations'].append("✅ System ready for deployment!")
            plan['next_steps'].extend([
                "Deploy with: serverless deploy --stage dev",
                "Test deployed functions",
                "Set up monitoring"
            ])
        elif plan['readiness_score'] >= 60:
            plan['recommendations'].append("⚠️  System mostly ready, address blockers first")
            plan['next_steps'].extend([
                "Fix AWS permissions",
                "Test deployment in dev environment",
                "Verify all services work"
            ])
        else:
            plan['recommendations'].append("❌ System not ready for deployment")
            plan['next_steps'].extend([
                "Set up AWS credentials properly",
                "Add required AWS permissions",
                "Install missing deployment tools"
            ])
        
        return plan
    
    def run_full_check(self):
        """Run all deployment readiness checks"""
        print("🚀 Boom-Bust Sentinel - Deployment Readiness Check")
        print("=" * 60)
        
        # Run all checks
        self.check_aws_credentials()
        self.check_aws_permissions()
        self.check_deployment_tools()
        self.check_environment_config()
        self.check_local_system()
        
        # Generate plan
        plan = self.generate_deployment_plan()
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT READINESS SUMMARY")
        print("=" * 60)
        
        print(f"\n🎯 Readiness Score: {plan['readiness_score']}/100")
        
        if plan['blockers']:
            print(f"\n🚫 Blockers ({len(plan['blockers'])}):")
            for blocker in plan['blockers']:
                print(f"   • {blocker}")
        
        if plan['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in plan['recommendations']:
                print(f"   • {rec}")
        
        if plan['next_steps']:
            print(f"\n🚀 Next Steps:")
            for i, step in enumerate(plan['next_steps'], 1):
                print(f"   {i}. {step}")
        
        # Save results
        with open('deployment_readiness_report.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'results': self.results,
                'plan': plan
            }, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: deployment_readiness_report.json")
        
        return plan['readiness_score'] >= 60

def main():
    checker = DeploymentChecker()
    success = checker.run_full_check()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())