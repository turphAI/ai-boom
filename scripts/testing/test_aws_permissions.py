#!/usr/bin/env python3
"""
Test AWS permissions and provide setup guidance
"""

import boto3
import os
from botocore.exceptions import ClientError

def get_aws_client(service_name):
    """Get AWS client with credentials from environment"""
    return boto3.client(
        service_name,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )

def test_service_permissions():
    """Test permissions for each AWS service we need"""
    services_to_test = {
        'sts': ['get_caller_identity'],
        'dynamodb': ['list_tables', 'describe_table'],
        'sns': ['list_topics', 'create_topic'],
        'lambda': ['list_functions'],
        'iam': ['list_roles'],
        'cloudformation': ['describe_stacks']
    }
    
    results = {}
    
    print("🔍 Testing AWS service permissions...")
    print("=" * 50)
    
    for service, operations in services_to_test.items():
        print(f"\n📋 Testing {service.upper()} permissions:")
        results[service] = {}
        
        try:
            client = get_aws_client(service)
            
            for operation in operations:
                try:
                    if service == 'sts' and operation == 'get_caller_identity':
                        response = client.get_caller_identity()
                        print(f"  ✅ {operation}: SUCCESS")
                        results[service][operation] = True
                        
                    elif service == 'dynamodb' and operation == 'list_tables':
                        response = client.list_tables()
                        print(f"  ✅ {operation}: SUCCESS ({len(response.get('TableNames', []))} tables)")
                        results[service][operation] = True
                        
                    elif service == 'dynamodb' and operation == 'describe_table':
                        # Try to describe a non-existent table to test permission
                        try:
                            client.describe_table(TableName='test-permission-check')
                        except ClientError as e:
                            if 'ResourceNotFoundException' in str(e):
                                print(f"  ✅ {operation}: SUCCESS (permission granted)")
                                results[service][operation] = True
                            else:
                                raise e
                                
                    elif service == 'sns' and operation == 'list_topics':
                        response = client.list_topics()
                        print(f"  ✅ {operation}: SUCCESS ({len(response.get('Topics', []))} topics)")
                        results[service][operation] = True
                        
                    elif service == 'sns' and operation == 'create_topic':
                        # We won't actually create, just check if we have permission
                        print(f"  ⚠️  {operation}: SKIPPED (would create resource)")
                        results[service][operation] = 'skipped'
                        
                    elif service == 'lambda' and operation == 'list_functions':
                        response = client.list_functions()
                        print(f"  ✅ {operation}: SUCCESS ({len(response.get('Functions', []))} functions)")
                        results[service][operation] = True
                        
                    elif service == 'iam' and operation == 'list_roles':
                        response = client.list_roles(MaxItems=1)
                        print(f"  ✅ {operation}: SUCCESS")
                        results[service][operation] = True
                        
                    elif service == 'cloudformation' and operation == 'describe_stacks':
                        response = client.describe_stacks()
                        print(f"  ✅ {operation}: SUCCESS ({len(response.get('Stacks', []))} stacks)")
                        results[service][operation] = True
                        
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if 'AccessDenied' in error_code or 'UnauthorizedOperation' in error_code:
                        print(f"  ❌ {operation}: ACCESS DENIED")
                        results[service][operation] = False
                    else:
                        print(f"  ⚠️  {operation}: ERROR - {error_code}")
                        results[service][operation] = 'error'
                        
        except Exception as e:
            print(f"  ❌ Failed to create {service} client: {e}")
            results[service] = {'client_error': str(e)}
    
    return results

def provide_setup_guidance(results):
    """Provide guidance based on permission test results"""
    print("\n" + "=" * 60)
    print("📋 SETUP GUIDANCE")
    print("=" * 60)
    
    # Check what we can do
    can_dynamodb = results.get('dynamodb', {}).get('list_tables', False)
    can_sns = results.get('sns', {}).get('list_topics', False)
    can_lambda = results.get('lambda', {}).get('list_functions', False)
    can_iam = results.get('iam', {}).get('list_roles', False)
    can_cloudformation = results.get('cloudformation', {}).get('describe_stacks', False)
    
    print("\n🎯 RECOMMENDED NEXT STEPS:")
    
    if not any([can_dynamodb, can_sns, can_lambda]):
        print("\n❌ CRITICAL: Your AWS user lacks basic permissions")
        print("   You need to add these AWS managed policies to your user:")
        print("   • AmazonDynamoDBFullAccess")
        print("   • AmazonSNSFullAccess") 
        print("   • AWSLambdaFullAccess")
        print("   • IAMFullAccess")
        print("   • AWSCloudFormationFullAccess")
        print("\n   How to add permissions:")
        print("   1. Go to AWS Console → IAM → Users")
        print("   2. Click on your user 'aiProjects'")
        print("   3. Click 'Add permissions' → 'Attach policies directly'")
        print("   4. Search and select the policies above")
        print("   5. Click 'Add permissions'")
        
    elif can_dynamodb and can_sns:
        print("\n✅ GOOD: You have basic DynamoDB and SNS permissions")
        print("   You can proceed with manual resource creation")
        
        if not can_lambda:
            print("   ⚠️  Add AWSLambdaFullAccess for Lambda deployment")
        if not can_iam:
            print("   ⚠️  Add IAMFullAccess for role creation")
        if not can_cloudformation:
            print("   ⚠️  Add AWSCloudFormationFullAccess for Serverless Framework")
            
    print("\n🔧 ALTERNATIVE APPROACHES:")
    print("   1. MANUAL SETUP: Create resources in AWS Console manually")
    print("   2. TERRAFORM: Use terraform with admin permissions")
    print("   3. LOCAL ONLY: Run scrapers locally without AWS (limited functionality)")
    
    print("\n📊 CURRENT CAPABILITIES:")
    if can_dynamodb:
        print("   ✅ Can create DynamoDB tables for data storage")
    if can_sns:
        print("   ✅ Can create SNS topics for notifications")
    if can_lambda:
        print("   ✅ Can deploy Lambda functions")
    else:
        print("   ❌ Cannot deploy Lambda functions")
        
    print("\n💡 FOR DEVELOPMENT:")
    print("   • You can run scrapers locally: python main.py")
    print("   • Test individual components: python -m pytest tests/ -v")
    print("   • Use file-based storage instead of DynamoDB for now")

def main():
    """Main function"""
    print("🔍 AWS Permissions Test for boom-bust-sentinel")
    print("=" * 60)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test AWS connection first
    try:
        sts = get_aws_client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ Connected to AWS as: {identity['Arn']}")
        print(f"   Account: {identity['Account']}")
        print(f"   Region: {os.getenv('AWS_REGION', 'us-east-1')}")
    except Exception as e:
        print(f"❌ Cannot connect to AWS: {e}")
        return False
    
    # Test service permissions
    results = test_service_permissions()
    
    # Provide guidance
    provide_setup_guidance(results)
    
    return True

if __name__ == "__main__":
    main()