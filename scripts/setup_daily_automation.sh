#!/bin/bash

# Setup Daily Scraper Automation for Boom-Bust Sentinel
# This script sets up a cron job to run all scrapers once per day

echo "🚀 Setting up daily scraper automation for Boom-Bust Sentinel"
echo ""

# Get the current directory (project root)
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
echo "📁 Project root: $PROJECT_ROOT"

# Get the Python path
PYTHON_PATH=$(which python3)
echo "🐍 Python path: $PYTHON_PATH"

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"
echo "📁 Created logs directory: $PROJECT_ROOT/logs"

# Create the cron job entry (runs at 6 AM daily)
CRON_JOB="0 6 * * * cd $PROJECT_ROOT && source venv/bin/activate && $PYTHON_PATH scripts/daily_scraper_automation.py >> /tmp/boom_bust_daily.log 2>&1"

echo ""
echo "📅 Cron job to be added (runs daily at 6:00 AM):"
echo "   $CRON_JOB"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "daily_scraper_automation.py"; then
    echo "⚠️  Daily cron job already exists"
    echo "   Current daily cron jobs:"
    crontab -l | grep "daily_scraper_automation.py"
    echo ""
    echo "🔄 Do you want to update it? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Remove existing daily automation cron job
        crontab -l 2>/dev/null | grep -v "daily_scraper_automation.py" | crontab -
        echo "🗑️  Removed existing daily cron job"
    else
        echo "ℹ️  Keeping existing cron job"
        exit 0
    fi
fi

echo "➕ Adding daily cron job..."
# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Daily cron job added successfully!"
    echo ""
    echo "📋 Current cron jobs:"
    crontab -l | grep "daily_scraper_automation.py"
else
    echo "❌ Failed to add cron job"
    exit 1
fi

echo ""
echo "🎉 Daily automation setup complete!"
echo ""
echo "📋 What this does:"
echo "   • Runs all scrapers (bond issuance, BDC discount, credit fund, bank provision) daily at 6:00 AM"
echo "   • Collects fresh data from SEC EDGAR, FRED API, and BDC feeds"
echo "   • Logs results to /tmp/boom_bust_daily.log and project logs/ directory"
echo "   • Saves detailed results to logs/daily_results_YYYYMMDD.json"
echo ""
echo "🔍 To check daily logs:"
echo "   tail -f /tmp/boom_bust_daily.log"
echo "   ls -la $PROJECT_ROOT/logs/"
echo ""
echo "🧪 To test manually:"
echo "   cd $PROJECT_ROOT && source venv/bin/activate && python scripts/daily_scraper_automation.py"
echo ""
echo "⏰ To change the schedule:"
echo "   crontab -e  # then modify the time (0 6 * * * = 6 AM daily)"
echo "   # Examples: 0 9 * * * = 9 AM daily, 0 6 * * 1 = 6 AM Mondays only"
echo ""
echo "🗑️  To remove the cron job:"
echo "   crontab -e  # then delete the line with daily_scraper_automation.py"
echo ""
echo "📊 Your scrapers will now run automatically every day!"





