# Scripts Directory

This directory contains operational scripts for the Boom-Bust Sentinel system.

## Directory Structure

```
scripts/
├── health/              # Health check and monitoring scripts
├── scrapers/            # Scraper execution and management
├── setup/               # Setup and configuration scripts
├── testing/             # Test and validation scripts
├── data/                # Data management scripts
└── agents/              # Agent-related scripts
```

## Scripts by Category

### Health & Monitoring (`health/`)
| Script | Description |
|--------|-------------|
| `health_check.py` | Comprehensive system health check |
| `lambda_health_check.py` | AWS Lambda function health check |
| `db_health_check.py` | Database connectivity check |
| `vercel_health_check.py` | Vercel deployment health check |
| `diagnose_scraper_status.py` | Diagnose scraper issues |
| `check_automation_status.sh` | Check cron/automation status |

### Scraper Execution (`scrapers/`)
| Script | Description |
|--------|-------------|
| `run_all_scrapers_safe.py` | Run all scrapers with error handling |
| `run_scrapers.py` | Basic scraper runner |
| `run_scrapers_for_health.py` | Run scrapers for health metrics |
| `run_scrapers_with_agents.py` | Run scrapers with AI agent monitoring |
| `run_bank_provision_scraper.py` | Run bank provision scraper only |
| `run_credit_fund_scraper.py` | Run credit fund scraper only |
| `daily_scraper_automation.py` | Daily automated scraper runs |

### Setup & Configuration (`setup/`)
| Script | Description |
|--------|-------------|
| `setup-database.sh` | Database schema setup |
| `setup_automated_refresh.sh` | Set up automated data refresh |
| `setup_daily_automation.sh` | Set up daily cron jobs |
| `setup_grafana.py` | Configure Grafana dashboards |
| `simple_aws_setup.py` | Basic AWS configuration |
| `startup_complete_system.sh` | Full system startup script |
| `start_data_pipeline.sh` | Start data pipeline |

### Testing & Validation (`testing/`)
| Script | Description |
|--------|-------------|
| `test_deployment.py` | Test deployment configuration |
| `test_aws_permissions.py` | Verify AWS permissions |
| `test_planetscale_connection.py` | Test PlanetScale connectivity |
| `test_planetscale_scrapers.py` | Test scrapers with PlanetScale |
| `test_scrapers_locally.py` | Local scraper testing |
| `test_enhanced_anomaly_detection.py` | Test anomaly detection |
| `run_complete_validation.py` | Run full system validation |
| `final_system_validation.py` | Final deployment validation |
| `deployment_readiness_check.py` | Pre-deployment checks |
| `load_testing.py` | Load/stress testing |

### Data Management (`data/`)
| Script | Description |
|--------|-------------|
| `populate_planetscale_data.py` | Populate PlanetScale with initial data |
| `populate-historical-data.js` | Populate historical data |
| `sync_scraped_data_to_planetscale.py` | Sync scraped data to DB |
| `verify_planetscale_data.py` | Verify data integrity |
| `refresh_real_data.py` | Refresh real-time data |

### Agent Scripts (`agents/`)
| Script | Description |
|--------|-------------|
| `view_agent_report.py` | View individual agent reports |
| `view_all_agent_results.py` | View all agent results |
| `send_agent_summary_email.py` | Send agent summary emails |
| `monitor_website_structures.py` | Monitor website structure changes |

### Utilities
| Script | Description |
|--------|-------------|
| `cost_monitor.py` | Monitor AWS costs |
| `system_integration.py` | System integration utilities |
| `demo_local_system.py` | Demo the system locally |
| `get_database_url_help.py` | Help with DATABASE_URL setup |
| `create-test-users.js` | Create test user accounts |
| `setup-test-data.js` | Setup test data |

### One-Time/Deprecated
| Script | Description | Status |
|--------|-------------|--------|
| `fix_datetime_deprecation.py` | Fix datetime deprecation | One-time fix |

## Usage Examples

```bash
# Run all scrapers safely
python scripts/run_all_scrapers_safe.py

# Check system health
python scripts/health_check.py

# Test PlanetScale connection
python scripts/test_planetscale_connection.py

# View agent results
python scripts/view_all_agent_results.py
```

