#!/bin/bash

# Deployment script for Boom-Bust Sentinel serverless functions
# This script provides options for both Serverless Framework and Terraform deployments

set -e

# Configuration
PROJECT_NAME="boom-bust-sentinel"
DEFAULT_REGION="us-east-1"
DEFAULT_STAGE="dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] COMMAND

Commands:
    serverless    Deploy using Serverless Framework
    terraform     Deploy using Terraform
    test          Run local tests
    clean         Clean up deployment artifacts

Options:
    -s, --stage STAGE       Deployment stage (default: dev)
    -r, --region REGION     AWS region (default: us-east-1)
    -h, --help              Show this help message

Examples:
    $0 serverless                    # Deploy to dev stage using Serverless
    $0 -s prod -r us-west-2 terraform   # Deploy to prod in us-west-2 using Terraform
    $0 test                          # Run tests
    $0 clean                         # Clean up artifacts

EOF
}

check_dependencies() {
    local deployment_type=$1
    
    log_info "Checking dependencies for $deployment_type deployment..."
    
    # Common dependencies
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required but not installed"
        exit 1
    fi
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is required but not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    # Deployment-specific dependencies
    case $deployment_type in
        "serverless")
            if ! command -v npm &> /dev/null; then
                log_error "npm is required for Serverless Framework deployment"
                exit 1
            fi
            
            if ! command -v serverless &> /dev/null && ! command -v sls &> /dev/null; then
                log_warning "Serverless Framework not found. Installing..."
                npm install -g serverless
            fi
            ;;
        "terraform")
            if ! command -v terraform &> /dev/null; then
                log_error "Terraform is required but not installed"
                exit 1
            fi
            ;;
    esac
    
    log_success "All dependencies satisfied"
}

install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    
    log_success "Python dependencies installed"
}

run_tests() {
    log_info "Running tests..."
    
    source venv/bin/activate
    
    # Run unit tests
    python -m pytest tests/ -v --tb=short
    
    # Run integration tests if available
    if [ -f "tests/test_integration.py" ]; then
        log_info "Running integration tests..."
        python -m pytest tests/test_integration.py -v
    fi
    
    log_success "Tests completed"
}

deploy_serverless() {
    local stage=$1
    local region=$2
    
    log_info "Deploying with Serverless Framework to stage: $stage, region: $region"
    
    # Install Serverless plugins
    if [ ! -d "node_modules" ]; then
        log_info "Installing Serverless plugins..."
        npm install
    fi
    
    # Deploy
    sls deploy --stage $stage --region $region --verbose
    
    log_success "Serverless deployment completed"
    
    # Show deployment info
    log_info "Deployment information:"
    sls info --stage $stage --region $region
}

deploy_terraform() {
    local stage=$1
    local region=$2
    
    log_info "Deploying with Terraform to environment: $stage, region: $region"
    
    cd terraform
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    log_info "Creating Terraform plan..."
    terraform plan -var="environment=$stage" -var="region=$region" -out=tfplan
    
    # Apply deployment
    log_info "Applying Terraform configuration..."
    terraform apply tfplan
    
    # Show outputs
    log_info "Deployment outputs:"
    terraform output
    
    cd ..
    
    log_success "Terraform deployment completed"
}

setup_secrets() {
    local stage=$1
    local region=$2
    
    log_info "Setting up AWS Secrets Manager secrets..."
    
    # Create secrets for API keys and configuration
    local secret_prefix="${PROJECT_NAME}/${stage}"
    
    # Check if secrets exist, create if they don't
    secrets=(
        "api-keys"
        "webhook-urls"
        "database-config"
    )
    
    for secret in "${secrets[@]}"; do
        local secret_name="${secret_prefix}/${secret}"
        
        if ! aws secretsmanager describe-secret --secret-id "$secret_name" --region "$region" &> /dev/null; then
            log_info "Creating secret: $secret_name"
            
            case $secret in
                "api-keys")
                    aws secretsmanager create-secret \
                        --name "$secret_name" \
                        --description "API keys for external services" \
                        --secret-string '{"symbl_api_key":"REPLACE_WITH_ACTUAL_KEY","sec_api_key":"REPLACE_WITH_ACTUAL_KEY"}' \
                        --region "$region"
                    ;;
                "webhook-urls")
                    aws secretsmanager create-secret \
                        --name "$secret_name" \
                        --description "Webhook URLs for notifications" \
                        --secret-string '{"slack_webhook":"REPLACE_WITH_ACTUAL_URL","telegram_bot_token":"REPLACE_WITH_ACTUAL_TOKEN"}' \
                        --region "$region"
                    ;;
                "database-config")
                    aws secretsmanager create-secret \
                        --name "$secret_name" \
                        --description "Database configuration" \
                        --secret-string '{"connection_string":"REPLACE_WITH_ACTUAL_STRING"}' \
                        --region "$region"
                    ;;
            esac
            
            log_warning "Please update the secret values in AWS Secrets Manager: $secret_name"
        else
            log_info "Secret already exists: $secret_name"
        fi
    done
}

clean_artifacts() {
    log_info "Cleaning up deployment artifacts..."
    
    # Remove build artifacts
    rm -rf .serverless/
    rm -rf terraform/.terraform/
    rm -rf terraform/terraform.tfstate*
    rm -rf terraform/tfplan
    rm -rf terraform/lambda_deployment.zip
    rm -rf __pycache__/
    rm -rf .pytest_cache/
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Parse command line arguments
STAGE=$DEFAULT_STAGE
REGION=$DEFAULT_REGION

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--stage)
            STAGE="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        serverless|terraform|test|clean)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate command
if [ -z "$COMMAND" ]; then
    log_error "No command specified"
    show_usage
    exit 1
fi

# Main execution
case $COMMAND in
    "serverless")
        check_dependencies "serverless"
        install_python_dependencies
        setup_secrets "$STAGE" "$REGION"
        deploy_serverless "$STAGE" "$REGION"
        ;;
    "terraform")
        check_dependencies "terraform"
        install_python_dependencies
        setup_secrets "$STAGE" "$REGION"
        deploy_terraform "$STAGE" "$REGION"
        ;;
    "test")
        install_python_dependencies
        run_tests
        ;;
    "clean")
        clean_artifacts
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac

log_success "Operation completed successfully!"