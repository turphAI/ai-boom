#!/bin/bash
# Next.js build script for the dashboard

echo "Running Next.js build from dashboard directory..."
cd "$(dirname "$0")"

echo "Current directory: $(pwd)"
echo "Installing dependencies..."
npm ci

echo "Running Next.js build..."
npm run build

echo "Build completed successfully!"
