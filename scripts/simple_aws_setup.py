#!/usr/bin/env python3
"""
Simple AWS setup script for boom-bust-sentinel
Creates basic AWS resources without requiring full CloudFormation permissions
"""

import boto3
import json
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError

def get_aws_client(service_name):
    """Get AWS client with credentials from environment"""
    return boto3.client(
        service_name,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )

def create_dynamodb_table():
    """Create DynamoDB table for state storage"""
    dynamodb = get_aws_client('dynamodb')
    table_name = 'boom-bust-sentinel-dev-state'
    
    try:
        # Check if table exists
        dynamodb.describe_table(TableName=table_name)
        print(f"✅ DynamoDB table '{table_name}' already exists")
        return table_name
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Create table
            print(f"📊 Creating DynamoDB table '{table_name}'...")
            
            try:
                response = dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'sk', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'pk', 'AttributeType': 'S'},
                        {'AttributeName': 'sk', 'AttributeType': 'S'},
                        {'AttributeName': 'data_source', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST',
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'DataSourceIndex',
                            'KeySchema': [
                                {'AttributeName': 'data_source', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        }
                    ],
                    Tags=[
                        {'Key': 'Project', 'Value': 'boom-bust-sentinel'},
                        {'Key': 'Environment', 'Value': 'dev'}
                    ]
                )
                
                # Wait for table to be created
                print("⏳ Waiting for table to be created...")
                waiter = dynamodb.get_waiter('table_exists')
                waiter.wait(TableName=table_name)
                
                print(f"✅ DynamoDB table '{table_name}' created successfully")
                return table_name
                
            except ClientError as e:
                print(f"❌ Error creating DynamoDB table: {e}")
                return None
        else:
            print(f"❌ Error checking DynamoDB table: {e}")
            return None

def create_sns_topics():
    """Create SNS topics for alerts"""
    sns = get_aws_client('sns')
    topics = {
        'alerts': 'boom-bust-sentinel-dev-alerts',
        'critical_alerts': 'boom-bust-sentinel-dev-critical-alerts'
    }
    
    topic_arns = {}
    
    for topic_type, topic_name in topics.items():
        try:
            print(f"📢 Creating SNS topic '{topic_name}'...")
            
            response = sns.create_topic(
                Name=topic_name,
                Tags=[
                    {'Key': 'Project', 'Value': 'boom-bust-sentinel'},
                    {'Key': 'Environment', 'Value': 'dev'},
                    {'Key': 'Type', 'Value': topic_type}
                ]
            )
            
            topic_arn = response['TopicArn']
            topic_arns[topic_type] = topic_arn
            
            print(f"✅ SNS topic '{topic_name}' created: {topic_arn}")
            
        except ClientError as e:
            print(f"❌ Error creating SNS topic '{topic_name}': {e}")
            topic_arns[topic_type] = None
    
    return topic_arns

def test_aws_connection():
    """Test AWS connection and permissions"""
    print("🔍 Testing AWS connection...")
    
    try:
        sts = get_aws_client('sts')
        identity = sts.get_caller_identity()
        
        print(f"✅ Connected to AWS as: {identity['Arn']}")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ID: {identity['UserId']}")
        
        return True
        
    except ClientError as e:
        print(f"❌ AWS connection failed: {e}")
        return False

def update_env_file(table_name, topic_arns):
    """Update .env file with created resource information"""
    env_updates = {
        'DATABASE_TABLE_NAME': table_name,
        'DATABASE_PROVIDER': 'dynamodb',
        'SNS_TOPIC_ARN': topic_arns.get('alerts', ''),
        'CRITICAL_ALERTS_SNS_TOPIC': topic_arns.get('critical_alerts', '')
    }
    
    print("📝 Updating .env file with resource information...")
    
    # Read existing .env file
    env_content = []
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.readlines()
    
    # Update or add new variables
    updated_vars = set()
    for i, line in enumerate(env_content):
        if '=' in line:
            var_name = line.split('=')[0].strip()
            if var_name in env_updates:
                env_content[i] = f"{var_name}={env_updates[var_name]}\n"
                updated_vars.add(var_name)
    
    # Add new variables that weren't found
    for var_name, value in env_updates.items():
        if var_name not in updated_vars:
            env_content.append(f"{var_name}={value}\n")
    
    # Write updated .env file
    with open('.env', 'w') as f:
        f.writelines(env_content)
    
    print("✅ .env file updated with AWS resource information")

def main():
    """Main setup function"""
    print("🚀 Starting simple AWS setup for boom-bust-sentinel...")
    print("=" * 60)
    
    # Test AWS connection
    if not test_aws_connection():
        print("❌ Setup failed: Cannot connect to AWS")
        return False
    
    print()
    
    # Create DynamoDB table
    table_name = create_dynamodb_table()
    if not table_name:
        print("❌ Setup failed: Could not create DynamoDB table")
        return False
    
    print()
    
    # Create SNS topics
    topic_arns = create_sns_topics()
    if not any(topic_arns.values()):
        print("❌ Setup failed: Could not create SNS topics")
        return False
    
    print()
    
    # Update .env file
    update_env_file(table_name, topic_arns)
    
    print()
    print("=" * 60)
    print("🎉 AWS setup completed successfully!")
    print()
    print("Created resources:")
    print(f"  📊 DynamoDB Table: {table_name}")
    for topic_type, arn in topic_arns.items():
        if arn:
            print(f"  📢 SNS Topic ({topic_type}): {arn}")
    
    print()
    print("Next steps:")
    print("  1. Test the Python backend: python main.py")
    print("  2. Run a scraper test: python -m pytest tests/test_*_scraper.py -v")
    print("  3. Set up monitoring (Grafana) for observability")
    
    return True

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = main()
    exit(0 if success else 1)