# PartSelect Agent Case Study

## Project Overview
PartSelect Agent is a conversational AI system designed to help users find, understand, and purchase appliance parts. The agent uses LLM-powered natural language processing to understand user queries, extract relevant parameters, and provide helpful responses for appliance part selection and diagnosis.

## Quick Start Guide

### All-in-One Solution
For the easiest startup experience, use the provided shell script:

```bash
chmod +x run.sh
./run.sh
```

This script will:
1. Check for and activate the virtual environment (or create one if it doesn't exist)
2. Install required packages including pinecone-client, langchain-pinecone, and websockets
3. Check for and kill any processes using ports 9000 and 9003
4. Start the WebSocket server on port 9000
5. Start the HTTP server for the client on port 9003
6. Open your browser to the client URL

### Starting the Server and Client Manually
The fastest way to get up and running manually:

1. **Start the WebSocket Server:**
   ```bash
   cd src/server
   python ws_server_simple.py
   ```
   This will start the WebSocket server on port 9000.

2. **Start the Minimal UI:**
   ```bash
   cd src/client/public
   python -m http.server 9003
   ```
   This will serve the simplified HTML interface on port 9003.

3. **Access the Application:**
   Open your browser and navigate to:
   ```
   http://localhost:9003/index-minimal.html
   ```

4. **Test the RAG Implementation:**
   To test the Retrieval-Augmented Generation functionality:
   ```bash
   cd src/server
   python test_rag.py
   ```

### Troubleshooting
- If you see "Address already in use" errors, kill existing Python processes:
  ```bash
  # For macOS/Linux
  lsof -i :9000,9003 | grep LISTEN | awk '{print $2}' | xargs kill -9
  
  # For Windows
  netstat -ano | findstr :9000
  netstat -ano | findstr :9003
  taskkill /F /PID <PID>
  ```
- Make sure to perform a hard refresh in your browser (Cmd+Shift+R on Mac, Ctrl+F5 on Windows) if you're having connection issues
- The WebSocket server should show "Client connected" messages in the console when the UI connects successfully

### Common Connection Issues

#### WebSocket Support Missing
If you see this error in the server logs:
```
WARNING: Unsupported upgrade request.
WARNING: No supported WebSocket library detected. Please use "pip install 'uvicorn[standard]'", or install 'websockets' or 'wsproto' manually.
```

Install the required WebSocket dependencies:
```bash
pip install 'uvicorn[standard]' websockets
```

#### Port Already in Use
If port 9000 or 9003 is already in use:
1. Find the process using the port:
   ```bash
   # For macOS/Linux
   lsof -i :9000
   lsof -i :9003
   
   # For Windows
   netstat -ano | findstr :9000
   netstat -ano | findstr :9003
   ```
2. Kill the process:
   ```bash
   # macOS/Linux (replace PID with the process ID)
   kill -9 PID
   
   # Windows (replace PID with the process ID)
   taskkill /F /PID PID
   ```

#### Connection Status
The minimal UI will display "Connected" when successfully connected to the WebSocket server. If you see "Disconnected" or no status, check:
1. That the server is running (you should see output in the terminal)
2. That you're using the correct URL (http://localhost:9003/index-minimal.html)
3. That no firewall is blocking WebSocket connections on port 9000

## Using the Minimal UI

After starting both the server and client, you can interact with the PartSelect Agent through the minimal UI. Here are some example queries to try:

### Example Queries to Try

#### Product Lookup
- "I need a water filter for my refrigerator"
- "Do you have any ice makers in stock?"
- "Show me dishwasher parts"

#### Installation Help
- "How do I install a water filter?"
- "Installation instructions for ice maker"
- "How to replace dishwasher control board"

#### Compatibility Checking
- "Is this filter compatible with my Samsung fridge?"
- "Will this part work with model RF263BEAESR?"
- "Do you have parts for GE dishwashers?"

#### Problem Diagnosis
- "My ice maker isn't working properly"
- "My dishwasher isn't draining properly"
- "Refrigerator not cooling but freezer works"

#### Cart Management
- "Add the water filter to my cart"
- "Show me what's in my cart"
- "Remove the ice maker from my cart"

#### Order Status
- "What's the status of my order ORD123456?"
- "When will my order be delivered?"
- "Has my order shipped yet?"

### RAG-Enhanced Responses
The PartSelect Agent uses Retrieval-Augmented Generation (RAG) to provide more detailed and accurate responses for installation and troubleshooting queries. To experience RAG in action, try:

1. **Installation Queries**: When asking about how to install parts, the system will retrieve relevant installation guides, including step-by-step instructions and safety notes.
   
2. **Troubleshooting Queries**: When describing an appliance problem, the system will retrieve diagnostic information, potential causes, and suggest parts that might need replacement.

The RAG system works even without a Pinecone API key by using built-in fallback mock data, but can be enhanced with a real vector database if configured.

## Architecture Components
The application consists of two main components:
- **Server**: A FastAPI-based backend with WebSocket support for real-time communication, NLP engine for intent classification, and a mock part database with API integration
- **Client**: A simple HTML/CSS/JS interface for the minimal UI and a React-based frontend with TypeScript for the full UI, featuring a clean chat interface with real-time messaging

## Key Features
- **Natural language understanding**: Process user queries in conversational language
- **Intent classification with DeepSeek LLM**: Accurately identify user intents using the DeepSeek LLM API
- **Parameter extraction**: Extract relevant parameters from user queries
- **Conversation context**: Maintain context throughout the conversation
- **Real-time chat**: WebSocket-based communication for instant responses
- **Responsive UI**: Clean, user-friendly interface
- **RAG Integration**: Pinecone-based retrieval for accurate installation and troubleshooting information

## Setup Instructions

### Prerequisites
- Python 3.9+ (3.10 or higher recommended)
- Node.js 16 or higher (for full React UI)
- npm or yarn (for full React UI)
- DeepSeek API key (optional, for enhanced intent classification)
- Pinecone API key (optional, for enhanced RAG capabilities)

### Server Setup
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pinecone-client langchain-pinecone websockets
   ```

3. Start the server:
   ```bash
   cd src/server
   python ws_server_simple.py
   ```

### Health Endpoint
The application includes a health endpoint at `/health` that checks the status of:
- MongoDB connection
- Redis connection
- Pinecone service
- DeepSeek API key

In development mode, the system will run even if these services are not available by using mock data instead.

## DeepSeek LLM Integration
This application uses the DeepSeek LLM API for advanced intent classification. The integration:

1. Accurately identifies user intents from 7 categories:
   - **lookup**: Finding or identifying a specific part
   - **compatibility**: Checking if a part is compatible with an appliance
   - **install**: Getting installation instructions
   - **diagnose**: Diagnosing which part may be causing an issue
   - **cart**: Managing shopping cart operations
   - **order**: Checking order status
   - **out_of_scope**: Queries not related to appliance parts

2. Provides fallback to rule-based classification when:
   - No DeepSeek API key is provided
   - The API request fails for any reason

## Pinecone RAG Implementation

The system uses Retrieval-Augmented Generation (RAG) with Pinecone vector database to provide accurate installation guides and troubleshooting information:

1. **Vector Search**: User queries are embedded and used to retrieve relevant documents from Pinecone
2. **Fallback Mechanism**: If Pinecone is unavailable, the system falls back to pre-defined mock data
3. **Context-Aware Responses**: Installation guides and diagnostic information are tailored to specific appliance types
4. **Document Ranking**: Results are ranked by relevance score to ensure the most pertinent information is presented
5. **LLM Enhancement**: Retrieved documents can be further enhanced with the DeepSeek LLM for more coherent responses

## Implementation Details

### Server Architecture
The server uses FastAPI with WebSocket support for real-time communication. Key components include:

- `DeepseekIntentClassifier`: Classifies user intents using the DeepSeek LLM API with fallback to rule-based classification
- `ConnectionManager`: Manages WebSocket connections and user sessions
- `PineconeRetriever`: Handles RAG functionality by retrieving relevant documentation from Pinecone
- WebSocket endpoint for processing messages and returning appropriate responses

The simplified server (`ws_server_simple.py`) includes:
1. Mock data for typical appliance part scenarios
   - Product catalogs with images and pricing
   - Installation guides for different parts
   - Compatibility information
   - Diagnostic troubleshooting
   - Cart and order management

2. Session management for user carts
   - Adding items to cart
   - Viewing cart contents
   - Maintaining cart state during the session

3. Intent-based response handling
   - Each intent type has specific response formatting
   - Suggested actions are generated based on context

### Client Architecture
The minimal client is built with plain HTML, CSS, and JavaScript, while the full client uses React with TypeScript. Both provide a clean chat interface with support for suggested actions based on the conversation context.

## Testing
The repository includes several test scripts:

1. `test_rag.py`: Tests the Pinecone RAG implementation for installation guides and troubleshooting
2. `test_intent_classification.py`: Tests the DeepSeek intent classifier against various queries
3. `test_websocket.py`: Tests the WebSocket server with a variety of user queries

To run the tests:
```bash
# Test the RAG implementation
python src/server/test_rag.py

# Test the WebSocket server
python src/server/test_websocket.py
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.