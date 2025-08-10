#!/bin/bash
# TypeScript type checking script for the dashboard

echo "Running TypeScript type checking from dashboard directory..."
cd "$(dirname "$0")"

echo "Current directory: $(pwd)"
echo "Cleaning TypeScript build cache..."
npx tsc --build --clean

echo "Running TypeScript type check..."
npx tsc --noEmit

echo "TypeScript check completed!"
