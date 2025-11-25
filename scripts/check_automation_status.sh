#!/bin/bash

# Check Daily Automation Status for Boom-Bust Sentinel
# This script shows the status of your automated scrapers

echo "🔍 Boom-Bust Sentinel Daily Automation Status"
echo "=============================================="
echo ""

# Check if cron job exists
echo "📅 Cron Job Status:"
if crontab -l 2>/dev/null | grep -q "daily_scraper_automation.py"; then
    echo "   ✅ Daily automation is configured"
    echo "   Schedule:"
    crontab -l | grep "daily_scraper_automation.py" | sed 's/^/      /'
else
    echo "   ❌ Daily automation is NOT configured"
    echo "   Run: ./scripts/setup_daily_automation.sh"
fi

echo ""

# Check recent logs
echo "📋 Recent Daily Logs:"
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOG_DIR="$PROJECT_ROOT/logs"

if [ -d "$LOG_DIR" ]; then
    echo "   Log directory: $LOG_DIR"
    
    # Show recent log files
    RECENT_LOGS=$(ls -t "$LOG_DIR"/daily_scraper_*.log 2>/dev/null | head -5)
    if [ -n "$RECENT_LOGS" ]; then
        echo "   Recent log files:"
        echo "$RECENT_LOGS" | while read -r log; do
            echo "      $(basename "$log") ($(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$log"))"
        done
    else
        echo "   No daily log files found yet"
    fi
    
    # Show recent result files
    RECENT_RESULTS=$(ls -t "$LOG_DIR"/daily_results_*.json 2>/dev/null | head -3)
    if [ -n "$RECENT_RESULTS" ]; then
        echo ""
        echo "   Recent results:"
        echo "$RECENT_RESULTS" | while read -r result; do
            echo "      $(basename "$result") ($(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$result"))"
        done
    fi
else
    echo "   Log directory not found: $LOG_DIR"
fi

echo ""

# Check system log
echo "📊 System Log (last 10 lines):"
if [ -f "/tmp/boom_bust_daily.log" ]; then
    echo "   /tmp/boom_bust_daily.log:"
    tail -10 /tmp/boom_bust_daily.log | sed 's/^/      /'
else
    echo "   No system log found at /tmp/boom_bust_daily.log"
fi

echo ""

# Show next scheduled run
echo "⏰ Next Scheduled Run:"
if crontab -l 2>/dev/null | grep -q "daily_scraper_automation.py"; then
    CRON_LINE=$(crontab -l | grep "daily_scraper_automation.py")
    echo "   Daily at 6:00 AM (based on current cron job)"
    echo "   Cron: $CRON_LINE"
else
    echo "   No automation scheduled"
fi

echo ""
echo "🔧 Quick Commands:"
echo "   Test manually:     cd $PROJECT_ROOT && source venv/bin/activate && python scripts/daily_scraper_automation.py"
echo "   View live logs:    tail -f /tmp/boom_bust_daily.log"
echo "   Setup automation: ./scripts/setup_daily_automation.sh"
echo "   Edit schedule:     crontab -e"





