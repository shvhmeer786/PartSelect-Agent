#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting PartSelect Agent...${NC}"

# Check if virtual environment exists and activate it
if [ -d ".venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
    echo -e "${GREEN}Installing required packages...${NC}"
    pip install -r requirements.txt
    pip install pinecone-client langchain-pinecone websockets
fi

# Check for any existing processes using the ports
echo -e "${YELLOW}Checking for existing processes on ports 9000 and 9003...${NC}"
PORTS_IN_USE=$(lsof -i :9000,9003 | grep LISTEN)
if [ -n "$PORTS_IN_USE" ]; then
    echo -e "${RED}Processes already using ports 9000 or 9003:${NC}"
    echo "$PORTS_IN_USE"
    echo -e "${YELLOW}Attempting to kill these processes...${NC}"
    lsof -i :9000,9003 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null
    echo -e "${GREEN}Processes killed.${NC}"
fi

# Start the WebSocket server in the background
echo -e "${GREEN}Starting WebSocket server on port 9000...${NC}"
cd src/server
python ws_server_simple.py &
WS_SERVER_PID=$!
cd ../..

# Wait a moment for the server to start
sleep 2

# Start the HTTP server in the background
echo -e "${GREEN}Starting HTTP server on port 9003...${NC}"
cd src/client/public
python -m http.server 9003 &
HTTP_SERVER_PID=$!
cd ../../..

# Wait a moment for the server to start
sleep 2

# Check if the servers are running
echo -e "${YELLOW}Checking if servers are running...${NC}"
WS_RUNNING=$(lsof -i :9000 | grep LISTEN)
HTTP_RUNNING=$(lsof -i :9003 | grep LISTEN)

if [ -n "$WS_RUNNING" ] && [ -n "$HTTP_RUNNING" ]; then
    echo -e "${GREEN}Both servers are running!${NC}"
    echo -e "${GREEN}WebSocket server: http://localhost:9000${NC}"
    echo -e "${GREEN}Client: http://localhost:9003/index-minimal.html${NC}"
    
    # Open the client in the default browser
    echo -e "${YELLOW}Opening browser to client URL...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:9003/index-minimal.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open http://localhost:9003/index-minimal.html
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        start http://localhost:9003/index-minimal.html
    fi
    
    echo -e "${YELLOW}Both applications are running. Press Ctrl+C to stop.${NC}"
    
    # Wait for Ctrl+C
    trap "echo -e '${RED}Stopping servers...${NC}'; kill $WS_SERVER_PID $HTTP_SERVER_PID 2>/dev/null; exit" INT
    wait
else
    echo -e "${RED}Failed to start one or more servers.${NC}"
    if [ -z "$WS_RUNNING" ]; then
        echo -e "${RED}WebSocket server is not running.${NC}"
    fi
    if [ -z "$HTTP_RUNNING" ]; then
        echo -e "${RED}HTTP server is not running.${NC}"
    fi
    
    # Kill any processes that might have started
    kill $WS_SERVER_PID $HTTP_SERVER_PID 2>/dev/null
    exit 1
fi 