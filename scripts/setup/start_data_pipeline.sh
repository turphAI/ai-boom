#!/bin/bash

# Boom-Bust Sentinel Data Pipeline
# This script runs scrapers periodically to keep data fresh

echo "🚀 Starting Boom-Bust Sentinel Data Pipeline..."
echo "   This will run scrapers every 30 minutes to keep data fresh"
echo "   Press Ctrl+C to stop"
echo ""

# Function to run scrapers
run_scrapers() {
    echo "$(date): Running scrapers..."
    source venv/bin/activate
    python scripts/run_scrapers.py
    echo "$(date): Scrapers completed"
    echo ""
}

# Run scrapers immediately
run_scrapers

# Then run every 30 minutes
while true; do
    sleep 1800  # 30 minutes
    run_scrapers
done
