#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Ensure uv is available
if ! command -v uv &> /dev/null
then
    echo "uv could not be found. Please install it (e.g., pip install uv)."
    exit 1
fi

# Create a virtual environment if it doesn't exist and install dependencies
echo "Creating virtual environment and installing dependencies with uv..."
uv venv
source .venv/bin/activate
uv pip install -e .

# Run the FastAPI application
echo "Starting FastAPI mock server..."
uvicorn main:app --host 0.0.0.0 --port 8000
