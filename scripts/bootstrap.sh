#!/bin/bash
# scripts/bootstrap.sh

# This script sets up the development environment.

set -e # Exit immediately if a command exits with a non-zero status.

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment in $VENV_DIR..."
  python3 -m venv $VENV_DIR
else
  echo "Virtual environment already exists."
fi

echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Bootstrap complete. Environment is ready."
echo "Run 'source $VENV_DIR/bin/activate' to use the environment."
