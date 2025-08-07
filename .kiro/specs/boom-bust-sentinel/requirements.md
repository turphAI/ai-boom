# Requirements Document

## Introduction

The Boom-Bust Sentinel is an automated market monitoring service designed to track key financial indicators and alert users when significant market conditions or anomalies are detected. The system will collect data from various financial sources, evaluate predefined rules, and send real-time alerts through multiple channels including Slack, email, and Telegram. The service is built on a serverless architecture to minimize operational overhead while providing reliable, scalable monitoring capabilities.

## Requirements

### Requirement 1

**User Story:** As a financial analyst, I want to monitor weekly investment-grade tech bond issuance automatically, so that I can identify unusual spikes in corporate debt activity that may signal market stress.

#### Acceptance Criteria

1. WHEN the system runs its daily check THEN it SHALL scrape SEC Rule 424B prospectuses for new filings
2. WHEN parsing prospectuses THEN the system SHALL extract CIKs for major tech companies (MSFT, META, AMZN, GOOGL)
3. WHEN extracting bond data THEN the system SHALL capture notional amount and coupon information
4. WHEN weekly issuance exceeds predefined threshold THEN the system SHALL trigger an alert
5. IF SEC data is unavailable THEN the system SHALL attempt to use FINRA TRACE or S&P CapitalIQ APIs as fallback

### Requirement 2

**User Story:** As an investment manager, I want to track Business Development Company (BDC) discount-to-NAV ratios, so that I can identify potential value opportunities or market distress signals.

#### Acceptance Criteria

1. WHEN the system runs nightly THEN it SHALL fetch closing prices for BDCs (ARCC, OCSL, etc.) via Yahoo Finance API
2. WHEN collecting NAV data THEN the system SHALL parse each BDC's investor relations RSS feed for last-reported NAV
3. WHEN calculating discount THEN the system SHALL compute (NAV - Price)/NAV ratio
4. WHEN discount ratio changes significantly from previous period THEN the system SHALL generate an alert
5. IF RSS feed is unavailable THEN the system SHALL log the error and continue with available data

### Requirement 3

**User Story:** As a credit analyst, I want to monitor private credit fund asset marks, so that I can detect early signs of credit stress in the private markets.

#### Acceptance Criteria

1. WHEN quarterly reporting periods occur THEN the system SHALL download Form PF XML filings
2. WHEN processing Form PF data THEN the system SHALL extract "gross asset value" fields
3. WHEN comparing sequential quarters THEN the system SHALL identify drops in asset values
4. WHEN asset value drops exceed threshold THEN the system SHALL alert on potential credit stress
5. IF Form PF data is delayed THEN the system SHALL continue monitoring with last available data

### Requirement 4

**User Story:** As a risk manager, I want to track bank provisioning for non-bank financial exposures, so that I can anticipate potential credit losses in the financial sector.

#### Acceptance Criteria

1. WHEN banks file 10-Q reports THEN the system SHALL scrape XBRL data for "AllowanceForCreditLosses" tables
2. WHEN processing XBRL data THEN the system SHALL extract provisions specifically for "Non-bank Financials"
3. WHEN provision levels increase significantly THEN the system SHALL trigger risk alerts
4. IF XBRL parsing fails THEN the system SHALL attempt to analyze earnings call transcripts using speech-to-text API
5. WHEN analyzing transcripts THEN the system SHALL search for keywords "non-bank financial" and "provision"

### Requirement 5

**User Story:** As a system user, I want to receive alerts through multiple channels, so that I can be notified regardless of which communication platform I'm currently using.

#### Acceptance Criteria

1. WHEN an alert condition is triggered THEN the system SHALL support sending notifications via AWS SNS to email/SMS
2. WHEN sending Slack notifications THEN the system SHALL use Incoming Webhook API
3. WHEN sending Telegram notifications THEN the system SHALL use Telegram Bot API
4. WHEN alert is sent THEN the system SHALL include relevant context data and threshold breach information
5. IF primary notification channel fails THEN the system SHALL attempt backup notification methods

### Requirement 6

**User Story:** As a system administrator, I want the service to run on a serverless architecture, so that I can minimize operational overhead and infrastructure costs.

#### Acceptance Criteria

1. WHEN implementing the system THEN it SHALL use AWS Lambda or Google Cloud Functions for compute
2. WHEN scheduling data collection THEN it SHALL use CloudWatch Events or Cloud Scheduler for cron functionality
3. WHEN storing state data THEN it SHALL use DynamoDB or Firestore for persistence
4. WHEN functions execute THEN they SHALL complete within serverless timeout limits
5. IF serverless limits are exceeded THEN the system SHALL break work into smaller chunks

### Requirement 7

**User Story:** As a system operator, I want comprehensive monitoring and observability, so that I can ensure the system is functioning correctly and troubleshoot issues quickly.

#### Acceptance Criteria

1. WHEN the system runs THEN it SHALL send metrics to Datadog or Grafana Cloud
2. WHEN sending metrics THEN it SHALL use standardized API calls (PUT /api/v1/series)
3. WHEN anomalies are detected in system behavior THEN monitoring SHALL generate operational alerts
4. WHEN errors occur THEN the system SHALL log detailed error information with context
5. IF monitoring service is unavailable THEN the system SHALL continue operating and queue metrics for later delivery

### Requirement 8

**User Story:** As a system maintainer, I want robust error handling and data validation, so that the system remains reliable even when external data sources are unstable.

#### Acceptance Criteria

1. WHEN external APIs fail THEN the system SHALL implement exponential backoff retry logic
2. WHEN data is received THEN the system SHALL validate checksums and data integrity
3. WHEN invalid data is detected THEN the system SHALL log the issue and skip processing to avoid false alerts
4. WHEN API keys are needed THEN the system SHALL retrieve them securely from AWS Secrets Manager or GCP Secret Manager
5. IF data feeds are temporarily unavailable THEN the system SHALL continue with cached data and alert on staleness

### Requirement 9

**User Story:** As a user, I want a web-based dashboard to view current market conditions and historical data, so that I can analyze trends and manage alert settings in one place.

#### Acceptance Criteria

1. WHEN accessing the dashboard THEN it SHALL display current values for all monitored metrics
2. WHEN viewing historical data THEN the dashboard SHALL show trend charts for each data source over configurable time periods
3. WHEN managing alerts THEN users SHALL be able to configure thresholds and notification preferences through the UI
4. WHEN alerts are triggered THEN the dashboard SHALL display alert history and status
5. WHEN system health issues occur THEN the dashboard SHALL show data source status and last update times
6. IF data is stale THEN the dashboard SHALL visually indicate which metrics may be outdated

### Requirement 10

**User Story:** As a developer, I want the system to be testable and maintainable, so that I can confidently make changes and additions over time.

#### Acceptance Criteria

1. WHEN writing scrapers THEN they SHALL be unit tested with pytest and recorded HTML fixtures
2. WHEN adding new data sources THEN the system SHALL follow consistent patterns for data extraction and processing
3. WHEN modifying alert thresholds THEN changes SHALL be configurable without code deployment
4. WHEN extending functionality THEN new components SHALL integrate with existing monitoring and alerting infrastructure
5. IF tests fail THEN the deployment pipeline SHALL prevent broken code from reaching production