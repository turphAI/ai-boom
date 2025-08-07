# Terraform configuration for Boom-Bust Sentinel serverless infrastructure
# This provides an alternative to the Serverless Framework for deployment

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

# Variables
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "boom-bust-sentinel"
}

# Local values
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
  
  function_names = {
    bond_issuance  = "${var.project_name}-${var.environment}-bond-issuance"
    bdc_discount   = "${var.project_name}-${var.environment}-bdc-discount"
    credit_fund    = "${var.project_name}-${var.environment}-credit-fund"
    bank_provision = "${var.project_name}-${var.environment}-bank-provision"
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Create deployment package
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_deployment.zip"
  
  source_dir = "${path.module}/.."
  excludes = [
    ".git",
    ".pytest_cache",
    "__pycache__",
    "*.pyc",
    "tests",
    ".env*",
    "README.md",
    ".vscode",
    "venv",
    ".venv",
    "terraform",
    "*.tf",
    "*.tfstate*",
    ".terraform*"
  ]
}

# IAM role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM policy for Lambda functions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-${var.environment}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      },
      # DynamoDB
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.state_table.arn,
          "${aws_dynamodb_table.state_table.arn}/index/*"
        ]
      },
      # SNS
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          aws_sns_topic.alerts.arn,
          aws_sns_topic.critical_alerts.arn
        ]
      },
      # Secrets Manager
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/${var.environment}/*"
      },
      # CloudWatch Metrics
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      },
      # Lambda (for chunked execution)
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-${var.environment}-*"
      }
    ]
  })
}

# DynamoDB table for state storage
resource "aws_dynamodb_table" "state_table" {
  name           = "${var.project_name}-${var.environment}-state"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "pk"
  range_key      = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  attribute {
    name = "data_source"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name     = "DataSourceIndex"
    hash_key = "data_source"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = local.common_tags
}

# SNS topics
resource "aws_sns_topic" "alerts" {
  name         = "${var.project_name}-${var.environment}-alerts"
  display_name = "Boom-Bust Sentinel Alerts"
  tags         = local.common_tags
}

resource "aws_sns_topic" "critical_alerts" {
  name         = "${var.project_name}-${var.environment}-critical-alerts"
  display_name = "Boom-Bust Sentinel Critical Alerts"
  tags         = local.common_tags
}

# Lambda functions
resource "aws_lambda_function" "bond_issuance" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = local.function_names.bond_issuance
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.bond_issuance_handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900
  memory_size     = 1024
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      STAGE                     = var.environment
      REGION                    = var.region
      DYNAMODB_TABLE           = aws_dynamodb_table.state_table.name
      SNS_TOPIC_ARN            = aws_sns_topic.alerts.arn
      CRITICAL_ALERTS_SNS_TOPIC = aws_sns_topic.critical_alerts.arn
      SECRETS_MANAGER_PREFIX    = "${var.project_name}/${var.environment}"
      SCRAPER_NAME             = "bond-issuance"
    }
  }

  tags = merge(local.common_tags, {
    Scraper  = "bond-issuance"
    Schedule = "weekly"
  })
}

resource "aws_lambda_function" "bond_issuance_chunked" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.function_names.bond_issuance}-chunked"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.bond_issuance_handler.chunked_execution_handler"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 1024
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      STAGE                     = var.environment
      REGION                    = var.region
      DYNAMODB_TABLE           = aws_dynamodb_table.state_table.name
      SNS_TOPIC_ARN            = aws_sns_topic.alerts.arn
      CRITICAL_ALERTS_SNS_TOPIC = aws_sns_topic.critical_alerts.arn
      SECRETS_MANAGER_PREFIX    = "${var.project_name}/${var.environment}"
      SCRAPER_NAME             = "bond-issuance-chunked"
    }
  }

  tags = merge(local.common_tags, {
    Scraper = "bond-issuance"
    Type    = "chunked"
  })
}

resource "aws_lambda_function" "bdc_discount" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = local.function_names.bdc_discount
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.bdc_discount_handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900
  memory_size     = 1024
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      STAGE                     = var.environment
      REGION                    = var.region
      DYNAMODB_TABLE           = aws_dynamodb_table.state_table.name
      SNS_TOPIC_ARN            = aws_sns_topic.alerts.arn
      CRITICAL_ALERTS_SNS_TOPIC = aws_sns_topic.critical_alerts.arn
      SECRETS_MANAGER_PREFIX    = "${var.project_name}/${var.environment}"
      SCRAPER_NAME             = "bdc-discount"
    }
  }

  tags = merge(local.common_tags, {
    Scraper  = "bdc-discount"
    Schedule = "daily"
  })
}

resource "aws_lambda_function" "bdc_discount_chunked" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.function_names.bdc_discount}-chunked"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.bdc_discount_handler.chunked_execution_handler"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 1024
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      STAGE                     = var.environment
      REGION                    = var.region
      DYNAMODB_TABLE           = aws_dynamodb_table.state_table.name
      SNS_TOPIC_ARN            = aws_sns_topic.alerts.arn
      CRITICAL_ALERTS_SNS_TOPIC = aws_sns_topic.critical_alerts.arn
      SECRETS_MANAGER_PREFIX    = "${var.project_name}/${var.environment}"
      SCRAPER_NAME             = "bdc-discount-chunked"
    }
  }

  tags = merge(local.common_tags, {
    Scraper = "bdc-discount"
    Type    = "chunked"
  })
}

resource "aws_lambda_function" "credit_fund" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = local.function_names.credit_fund
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.credit_fund_handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900
  memory_size     = 1024
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      STAGE                     = var.environment
      REGION                    = var.region
      DYNAMODB_TABLE           = aws_dynamodb_table.state_table.name
      SNS_TOPIC_ARN            = aws_sns_topic.alerts.arn
      CRITICAL_ALERTS_SNS_TOPIC = aws_sns_topic.critical_alerts.arn
      SECRETS_MANAGER_PREFIX    = "${var.project_name}/${var.environment}"
      SCRAPER_NAME             = "credit-fund"
    }
  }

  tags = merge(local.common_tags, {
    Scraper  = "credit-fund"
    Schedule = "monthly"
  })
}

resource "aws_lambda_function" "credit_fund_chunked" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.function_names.credit_fund}-chunked"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.credit_fund_handler.chunked_execution_handler"
  runtime         = "python3.9"
  timeout         = 600
  memory_size     = 1024
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      STAGE                     = var.environment
      REGION                    = var.region
      DYNAMODB_TABLE           = aws_dynamodb_table.state_table.name
      SNS_TOPIC_ARN            = aws_sns_topic.alerts.arn
      CRITICAL_ALERTS_SNS_TOPIC = aws_sns_topic.critical_alerts.arn
      SECRETS_MANAGER_PREFIX    = "${var.project_name}/${var.environment}"
      SCRAPER_NAME             = "credit-fund-chunked"
    }
  }

  tags = merge(local.common_tags, {
    Scraper = "credit-fund"
    Type    = "chunked"
  })
}

resource "aws_lambda_function" "bank_provision" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = local.function_names.bank_provision
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.bank_provision_handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900
  memory_size     = 1024
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      STAGE                     = var.environment
      REGION                    = var.region
      DYNAMODB_TABLE           = aws_dynamodb_table.state_table.name
      SNS_TOPIC_ARN            = aws_sns_topic.alerts.arn
      CRITICAL_ALERTS_SNS_TOPIC = aws_sns_topic.critical_alerts.arn
      SECRETS_MANAGER_PREFIX    = "${var.project_name}/${var.environment}"
      SCRAPER_NAME             = "bank-provision"
    }
  }

  tags = merge(local.common_tags, {
    Scraper  = "bank-provision"
    Schedule = "quarterly"
  })
}

resource "aws_lambda_function" "bank_provision_chunked" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.function_names.bank_provision}-chunked"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.bank_provision_handler.chunked_execution_handler"
  runtime         = "python3.9"
  timeout         = 600
  memory_size     = 1024
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      STAGE                     = var.environment
      REGION                    = var.region
      DYNAMODB_TABLE           = aws_dynamodb_table.state_table.name
      SNS_TOPIC_ARN            = aws_sns_topic.alerts.arn
      CRITICAL_ALERTS_SNS_TOPIC = aws_sns_topic.critical_alerts.arn
      SECRETS_MANAGER_PREFIX    = "${var.project_name}/${var.environment}"
      SCRAPER_NAME             = "bank-provision-chunked"
    }
  }

  tags = merge(local.common_tags, {
    Scraper = "bank-provision"
    Type    = "chunked"
  })
}

# CloudWatch Event Rules for scheduling
resource "aws_cloudwatch_event_rule" "bond_issuance_schedule" {
  name                = "${var.project_name}-${var.environment}-bond-issuance-schedule"
  description         = "Weekly bond issuance monitoring"
  schedule_expression = "cron(0 8 ? * MON *)"  # Monday 8 AM UTC
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "bond_issuance_target" {
  rule      = aws_cloudwatch_event_rule.bond_issuance_schedule.name
  target_id = "BondIssuanceTarget"
  arn       = aws_lambda_function.bond_issuance.arn

  input = jsonencode({
    source        = "aws.events"
    detail-type   = "Scheduled Event"
    detail = {
      scraper_name = "bond-issuance"
    }
  })
}

resource "aws_lambda_permission" "bond_issuance_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bond_issuance.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.bond_issuance_schedule.arn
}

resource "aws_cloudwatch_event_rule" "bdc_discount_schedule" {
  name                = "${var.project_name}-${var.environment}-bdc-discount-schedule"
  description         = "Daily BDC discount-to-NAV monitoring"
  schedule_expression = "cron(0 6 * * ? *)"  # Daily 6 AM UTC
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "bdc_discount_target" {
  rule      = aws_cloudwatch_event_rule.bdc_discount_schedule.name
  target_id = "BdcDiscountTarget"
  arn       = aws_lambda_function.bdc_discount.arn

  input = jsonencode({
    source        = "aws.events"
    detail-type   = "Scheduled Event"
    detail = {
      scraper_name = "bdc-discount"
    }
  })
}

resource "aws_lambda_permission" "bdc_discount_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bdc_discount.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.bdc_discount_schedule.arn
}

resource "aws_cloudwatch_event_rule" "credit_fund_schedule" {
  name                = "${var.project_name}-${var.environment}-credit-fund-schedule"
  description         = "Monthly private credit fund monitoring"
  schedule_expression = "cron(0 7 1 * ? *)"  # First day of month, 7 AM UTC
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "credit_fund_target" {
  rule      = aws_cloudwatch_event_rule.credit_fund_schedule.name
  target_id = "CreditFundTarget"
  arn       = aws_lambda_function.credit_fund.arn

  input = jsonencode({
    source        = "aws.events"
    detail-type   = "Scheduled Event"
    detail = {
      scraper_name = "credit-fund"
    }
  })
}

resource "aws_lambda_permission" "credit_fund_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.credit_fund.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.credit_fund_schedule.arn
}

resource "aws_cloudwatch_event_rule" "bank_provision_schedule" {
  name                = "${var.project_name}-${var.environment}-bank-provision-schedule"
  description         = "Quarterly bank provision monitoring"
  schedule_expression = "cron(0 9 1 1,4,7,10 ? *)"  # Quarterly, 9 AM UTC
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "bank_provision_target" {
  rule      = aws_cloudwatch_event_rule.bank_provision_schedule.name
  target_id = "BankProvisionTarget"
  arn       = aws_lambda_function.bank_provision.arn

  input = jsonencode({
    source        = "aws.events"
    detail-type   = "Scheduled Event"
    detail = {
      scraper_name = "bank-provision"
    }
  })
}

resource "aws_lambda_permission" "bank_provision_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bank_provision.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.bank_provision_schedule.arn
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = {
    bond_issuance          = local.function_names.bond_issuance
    bond_issuance_chunked  = "${local.function_names.bond_issuance}-chunked"
    bdc_discount           = local.function_names.bdc_discount
    bdc_discount_chunked   = "${local.function_names.bdc_discount}-chunked"
    credit_fund            = local.function_names.credit_fund
    credit_fund_chunked    = "${local.function_names.credit_fund}-chunked"
    bank_provision         = local.function_names.bank_provision
    bank_provision_chunked = "${local.function_names.bank_provision}-chunked"
  }

  name              = "/aws/lambda/${each.value}"
  retention_in_days = 30
  tags              = local.common_tags
}

# Outputs
output "state_table_name" {
  description = "DynamoDB table name for state storage"
  value       = aws_dynamodb_table.state_table.name
}

output "alerts_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "critical_alerts_topic_arn" {
  description = "SNS topic ARN for critical alerts"
  value       = aws_sns_topic.critical_alerts.arn
}

output "lambda_function_arns" {
  description = "ARNs of all Lambda functions"
  value = {
    bond_issuance          = aws_lambda_function.bond_issuance.arn
    bond_issuance_chunked  = aws_lambda_function.bond_issuance_chunked.arn
    bdc_discount           = aws_lambda_function.bdc_discount.arn
    bdc_discount_chunked   = aws_lambda_function.bdc_discount_chunked.arn
    credit_fund            = aws_lambda_function.credit_fund.arn
    credit_fund_chunked    = aws_lambda_function.credit_fund_chunked.arn
    bank_provision         = aws_lambda_function.bank_provision.arn
    bank_provision_chunked = aws_lambda_function.bank_provision_chunked.arn
  }
}