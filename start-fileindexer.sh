#!/bin/bash

# FileIndexer Startup Script
# This script starts both the backend and frontend servers

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting FileIndexer...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if Ollama is running
echo -e "${YELLOW}Checking Ollama...${NC}"
if ! pgrep -x "ollama" > /dev/null; then
    echo -e "${YELLOW}Ollama is not running. Starting Ollama...${NC}"
    ollama serve &
    sleep 3
fi

# Check if nomic-embed-text model is available
if ! ollama list | grep -q "nomic-embed-text"; then
    echo -e "${YELLOW}Downloading nomic-embed-text model (this may take a few minutes)...${NC}"
    ollama pull nomic-embed-text
fi

echo -e "${GREEN}Ollama is ready!${NC}"

# Start backend
echo -e "${YELLOW}Starting backend server...${NC}"
cd "$SCRIPT_DIR/backend"

# Activate virtual environment if it exists, otherwise create it
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
else
    source venv/bin/activate
fi

# Start backend in background
python main.py &
BACKEND_PID=$!
echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to start...${NC}"
sleep 3

# Start frontend
echo -e "${YELLOW}Starting frontend server...${NC}"
cd "$SCRIPT_DIR/frontend"

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies (this may take a few minutes)...${NC}"
    npm install
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
fi

# Start frontend in background
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"

# Save PIDs to a file for cleanup
echo "$BACKEND_PID" > "$SCRIPT_DIR/.fileindexer.pid"
echo "$FRONTEND_PID" >> "$SCRIPT_DIR/.fileindexer.pid"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FileIndexer is now running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Frontend: ${YELLOW}http://localhost:3000${NC}"
echo -e "Backend:  ${YELLOW}http://localhost:8000${NC}"
echo ""
echo -e "To stop FileIndexer, run: ${YELLOW}./stop-fileindexer.sh${NC}"
echo -e "Or press ${YELLOW}Ctrl+C${NC} to stop (may require running stop script to fully clean up)"
echo ""

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping FileIndexer...${NC}"
    "$SCRIPT_DIR/stop-fileindexer.sh"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
