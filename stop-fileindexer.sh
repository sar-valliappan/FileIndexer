#!/bin/bash

# FileIndexer Stop Script
# This script stops both the backend and frontend servers

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping FileIndexer...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$SCRIPT_DIR/.fileindexer.pid"

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    # Read PIDs and kill processes
    while IFS= read -r pid; do
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping process $pid...${NC}"
            kill "$pid" 2>/dev/null || true
        fi
    done < "$PID_FILE"
    
    # Remove PID file
    rm "$PID_FILE"
else
    echo -e "${YELLOW}No PID file found. Attempting to find and stop processes...${NC}"
fi

# Kill any remaining python main.py processes (backend)
pkill -f "python main.py" 2>/dev/null || true

# Kill any remaining Next.js dev server processes (frontend)
pkill -f "next dev" 2>/dev/null || true
pkill -f "node.*next-server" 2>/dev/null || true

# Also clean up any orphaned Node processes on port 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Clean up any orphaned Python processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

echo -e "${GREEN}FileIndexer stopped successfully!${NC}"
