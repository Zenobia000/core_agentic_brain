#!/bin/bash
# scripts/test.sh

# This script runs the test suite.

set -e

echo "Running tests with pytest..."

# Activate virtual environment if it exists and is not active
if [ -d ".venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

pytest -v tests/

echo "Tests passed."
