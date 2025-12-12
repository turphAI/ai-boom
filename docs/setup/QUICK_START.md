# Quick Start Guide

## Running Scripts

On macOS, Python 3 is typically available as `python3`, not `python`.

### Option 1: Use python3 directly
```bash
python3 scripts/run_all_scrapers_safe.py
python3 scripts/diagnose_scraper_status.py
python3 scripts/verify_planetscale_data.py
```

### Option 2: Use virtual environment (Recommended)
If you have a virtual environment set up:

```bash
# Activate virtual environment
source venv/bin/activate

# Now you can use python (it will use the venv's python3)
python scripts/run_all_scrapers_safe.py
```

### Option 3: Create an alias (Optional)
Add this to your `~/.zshrc`:
```bash
alias python=python3
```

Then reload:
```bash
source ~/.zshrc
```

## Common Commands

### Check system status
```bash
python3 scripts/diagnose_scraper_status.py
```

### Run all scrapers
```bash
python3 scripts/run_all_scrapers_safe.py
```

### Verify data storage
```bash
python3 scripts/verify_planetscale_data.py
```

### Check DATABASE_URL setup
```bash
python3 scripts/get_database_url_help.py
```

## Setting Environment Variables

Before running scrapers, you may need to set environment variables:

```bash
export DATABASE_URL="mysql://user:pass@host.connect.psdb.cloud/database?sslaccept=strict"
export ENVIRONMENT="production"
export FRED_API_KEY="your-key-here"  # Optional
```

## Troubleshooting

### "command not found: python"
- Use `python3` instead of `python`
- Or activate your virtual environment first

### "DATABASE_URL not set"
- See `SETUP_DATABASE_URL.md` for instructions
- Must be set in GitHub Secrets for automation to work

### Import errors
- Make sure you're in the project root directory
- Install dependencies: `pip3 install -r requirements.txt`
- Activate virtual environment if you have one

