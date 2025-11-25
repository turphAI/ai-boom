# Docs Folder Reorganization Plan

## Current Structure

All documentation is in a flat `docs/` folder with many files.

## Proposed Structure

Organize by topic/functionality:

```
docs/
├── agents/                       # Agent documentation
│   ├── scraper_monitoring/      # Scraper monitoring agents
│   ├── website_structure/       # Website structure agents
│   ├── data_quality/            # Data quality agents
│   └── general/                 # General agent docs
│
├── setup/                       # Setup & configuration guides
│   ├── environment/            # Environment setup
│   ├── deployment/             # Deployment guides
│   └── integration/            # Integration guides
│
├── scrapers/                    # Scraper documentation
│   └── improvements/           # Scraper improvements
│
├── architecture/                # System architecture docs
│
└── guides/                      # User guides & tutorials
    ├── quick_start/            # Quick start guides
    └── troubleshooting/        # Troubleshooting guides
```

## File Organization

### Agents Documentation (`docs/agents/`)

**scraper_monitoring/**:
- `SCRAPER_AGENT_EXPLANATION.md`
- `AGENT_IMPLEMENTATION_SUMMARY.md`
- `AGENT_NEXT_STEPS.md`
- `AGENT_AUTOMATION_INTEGRATION.md`

**website_structure/**:
- `WEBSITE_STRUCTURE_AGENT_PLAN.md`
- `WEBSITE_STRUCTURE_AGENT_COMPLETE.md`
- `WEBSITE_STRUCTURE_MONITORING_SCHEDULE.md`

**data_quality/**:
- `DATA_QUALITY_ANOMALY_AGENT_PLAN.md`
- `DATA_QUALITY_AGENT_COMPLETE.md`
- `DATA_QUALITY_INTEGRATION_COMPLETE.md`
- `DATA_QUALITY_INTEGRATION_SUMMARY.md`

**general/**:
- `AGENT_BASED_IMPROVEMENTS.md`
- `AGENT_TRIGGERS_AND_SCHEDULES.md`
- `VIEWING_AGENT_RESULTS.md`
- `VIEWING_RESULTS_EXAMPLES.md`
- `AGENTS_REORGANIZATION_COMPLETE.md`

### Setup Documentation (`docs/setup/`)

**environment/**:
- `ENV_FILE_SETUP.md`
- `ANTHROPIC_SETUP.md`

**deployment/**:
- `DEPLOYMENT_SETUP.md`
- `GITHUB_SETUP_GUIDE.md`

**integration/**:
- `AGENT_AUTOMATION_INTEGRATION.md`

### Scrapers Documentation (`docs/scrapers/`)

**improvements/**:
- `CREDIT_FUND_SCRAPER_IMPROVEMENTS.md`
- `BDC_DATA_SOURCE_UPDATE.md`

### Architecture (`docs/architecture/`)

- `error_handling_implementation.md`
- `integration_testing.md`

### Guides (`docs/guides/`)

**quick_start/**:
- `QUICK_START_CHECKLIST.md`
- `SETUP_GUIDE.md`

**troubleshooting/**:
- `VALIDATION_FIXES_APPLIED.md`
- `FIXES_APPLIED.md`
- `SCRAPER_AUTOMATION_FIX_PLAN.md`

### Email (`docs/email/`)

- `EMAIL_SUMMARY_INVESTIGATION.md`
- `EMAIL_SUMMARY_TODO.md`
- `EMAIL_SUMMARY_SETUP.md`

## Benefits

1. **Easy Navigation**: Find docs by topic
2. **Logical Grouping**: Related docs together
3. **Better Discovery**: Clear structure helps find what you need
4. **Scalability**: Easy to add new docs to appropriate folders

## Migration Plan

1. Create new folder structure
2. Move files to appropriate folders
3. Update any cross-references
4. Create index/README files
5. Test links still work

## Ready to Reorganize?

This will make documentation much easier to navigate and maintain!

