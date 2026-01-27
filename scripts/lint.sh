#!/bin/bash
# scripts/lint.sh

# This script runs a linter and code formatter.
# We recommend using 'ruff', a fast and popular choice.

# To use this script, first install ruff:
# pip install ruff

set -e

echo "Checking code formatting with ruff..."
ruff format . --check

echo "Linting code with ruff..."
ruff check .

echo "Linting and formatting checks passed."
