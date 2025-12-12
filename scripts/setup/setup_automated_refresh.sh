#!/bin/bash

# Setup Automated Data Refresh Script
# This script sets up a cron job to refresh financial data every hour

echo "🚀 Setting up automated data refresh for Boom-Bust Sentinel"
echo ""

# Get the current directory (project root)
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
echo "📁 Project root: $PROJECT_ROOT"

# Get the Python path
PYTHON_PATH=$(which python3)
echo "🐍 Python path: $PYTHON_PATH"

# Create the cron job entry
CRON_JOB="0 * * * * cd $PROJECT_ROOT && $PYTHON_PATH scripts/refresh_real_data.py >> /tmp/boom_bust_refresh.log 2>&1"

echo ""
echo "📅 Cron job to be added:"
echo "   $CRON_JOB"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "refresh_real_data.py"; then
    echo "⚠️  Cron job already exists for data refresh"
    echo "   Current cron jobs:"
    crontab -l | grep "refresh_real_data.py"
else
    echo "➕ Adding cron job for hourly data refresh..."
    
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    
    if [ $? -eq 0 ]; then
        echo "✅ Cron job added successfully!"
        echo ""
        echo "📋 Current cron jobs:"
        crontab -l | grep "refresh_real_data.py"
    else
        echo "❌ Failed to add cron job"
        exit 1
    fi
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 What this does:"
echo "   • Refreshes credit fund and bank provision data every hour"
echo "   • Uses real FRED API data for financial indicators"
echo "   • Keeps System Health view showing healthy status"
echo "   • Logs to /tmp/boom_bust_refresh.log"
echo ""
echo "🔍 To check logs:"
echo "   tail -f /tmp/boom_bust_refresh.log"
echo ""
echo "🗑️  To remove the cron job:"
echo "   crontab -e  # then delete the line with refresh_real_data.py"
echo ""
echo "🧪 To test manually:"
echo "   cd $PROJECT_ROOT && source venv/bin/activate && python scripts/refresh_real_data.py"
