#!/bin/bash
# scripts/start.sh

# This script starts the web server.

set -e

echo "Starting the Core Agentic Brain web server..."

# Activate virtual environment if it exists and is not active
if [ -d ".venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the FastAPI server
# The reload flag is good for development
export PYTHONPATH=$PYTHONPATH:.
python web/server.py

echo "Web server stopped."
