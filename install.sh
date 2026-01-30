#!/bin/bash

# FileIndexer Installation Script
# This script sets up FileIndexer on your Mac

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=========================================="
echo "  FileIndexer Installation Script"
echo "=========================================="
echo -e "${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if Homebrew is installed
echo -e "${YELLOW}Checking for Homebrew...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "${RED}Homebrew is not installed.${NC}"
    echo -e "${YELLOW}Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo -e "${GREEN}Homebrew is installed!${NC}"
fi

# Check if Python 3 is installed
echo -e "${YELLOW}Checking for Python 3...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Installing Python 3...${NC}"
    brew install python@3.11
else
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}$PYTHON_VERSION is installed!${NC}"
fi

# Check if Node.js is installed
echo -e "${YELLOW}Checking for Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Installing Node.js...${NC}"
    brew install node
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}Node.js $NODE_VERSION is installed!${NC}"
fi

# Check if Ollama is installed
echo -e "${YELLOW}Checking for Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Installing Ollama...${NC}"
    brew install ollama
else
    echo -e "${GREEN}Ollama is installed!${NC}"
fi

# Make scripts executable
echo -e "${YELLOW}Making scripts executable...${NC}"
chmod +x "$SCRIPT_DIR/start-fileindexer.sh"
chmod +x "$SCRIPT_DIR/stop-fileindexer.sh"

# Set up Python backend
echo -e "${YELLOW}Setting up Python backend...${NC}"
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
deactivate

# Set up Node.js frontend
echo -e "${YELLOW}Setting up Node.js frontend...${NC}"
cd "$SCRIPT_DIR/frontend"

if [ ! -f ".env.local" ]; then
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
    echo -e "${GREEN}Created .env.local${NC}"
fi

echo -e "${YELLOW}Installing npm dependencies (this may take a few minutes)...${NC}"
npm install

# Create data directory for ChromaDB
mkdir -p "$SCRIPT_DIR/data/chroma_db"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Start FileIndexer: ${YELLOW}./start-fileindexer.sh${NC}"
echo -e "2. Open your browser to: ${YELLOW}http://localhost:3000${NC}"
echo -e "3. Stop FileIndexer: ${YELLOW}./stop-fileindexer.sh${NC}"
echo ""
echo -e "${BLUE}Optional: Create a desktop launcher${NC}"
echo -e "Run: ${YELLOW}./create-launcher.sh${NC}"
echo ""
