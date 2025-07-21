#!/usr/bin/env bash

# Test runner script for Homepy integration tests
# This script sets up the environment and runs the integration tests

set -e

echo "🧪 Running Homepy Integration Tests"
echo "================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
poetry install --extras test

# Run the tests
echo "🚀 Running integration tests..."
poetry run pytest tests/ -v

echo "✅ All tests completed!"