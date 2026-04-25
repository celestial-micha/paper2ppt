#!/bin/bash

# Start Paper2Slides Backend API Server
# Default port is 8001

PORT=${1:-8001}

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT/api"

echo "=========================================="
echo "Starting Paper2Slides Backend API"
echo "=========================================="
echo ""
echo "Server will run on: http://localhost:${PORT}"
echo "API endpoints: http://localhost:${PORT}/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python server.py ${PORT}

