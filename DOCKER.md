# Docker Setup for PartSelect Agent

This directory contains Docker configuration for running the PartSelect Agent in containers. The setup includes:

- FastAPI backend server with WebSocket support
- React frontend with a minimal UI
- MongoDB for storing product and documentation data
- Redis for session and cart management
- Pinecone vector database emulator for RAG (Retrieval-Augmented Generation)

## Prerequisites

- Docker and Docker Compose installed on your system
- At least 4GB of RAM available for Docker
- Git repository cloned locally

## Quick Start

1. **Set up environment variables**

   Copy the template environment file and adjust as needed:

   ```bash
   cp env.template .env
   ```
   
   Edit the `.env` file to set your DeepSeek API key if you have one:
   
   ```
   DEEPSEEK_API_KEY=your_api_key
   ```
   
   If you want to use a real Pinecone instance instead of the emulator, set the Pinecone API key:
   
   ```
   PINECONE_API_KEY=your_pinecone_api_key
   ```

2. **Start the services**

   Launch all services with Docker Compose:

   ```bash
   docker-compose up -d
   ```
   
   The first startup may take a few minutes as Docker builds the images.

3. **Access the application**

   Once all services are running, access the PartSelect Agent at:
   
   ```
   http://localhost:9003/index-minimal.html
   ```

4. **Check service health**

   Verify the health of all services:
   
   ```bash
   curl http://localhost:9000/health
   ```

## Accessing Individual Services

- **FastAPI Server**: http://localhost:9000
- **React Client**: http://localhost:9003
- **MongoDB**: mongodb://localhost:27017 (username: partselect, password: password)
- **Redis**: redis://localhost:6379
- **Pinecone Emulator**: http://localhost:8080

## Development Workflow

If you want to develop while running the Docker services:

1. **Mount volumes for development**

   The Docker Compose file includes volume mounts for development:
   
   - The server code is mounted at `/app/server`
   - The client code is mounted at `/usr/share/nginx/html`
   
   Changes to these files will be reflected immediately.

2. **Rebuild a specific service**

   If you make changes to a Dockerfile or dependencies:
   
   ```bash
   docker-compose build server  # Replace 'server' with the service name
   docker-compose up -d
   ```

3. **View logs**

   To watch logs from all services:
   
   ```bash
   docker-compose logs -f
   ```
   
   Or for a specific service:
   
   ```bash
   docker-compose logs -f server
   ```

## Troubleshooting

- **Connection issues**: Check if all services are running with `docker-compose ps`
- **Failed health checks**: View service logs with `docker-compose logs [service]`
- **WebSocket errors**: Ensure that the CORS configuration is correct
- **MongoDB connection issues**: Verify MongoDB credentials in `.env`

## Shutting Down

To stop all services:

```bash
docker-compose down
```

To stop services and remove data volumes (this will delete all data):

```bash
docker-compose down -v
```

## Architecture

The Docker setup implements a microservices architecture:

- **server**: FastAPI server with WebSocket support for real-time chat
- **client**: Nginx server serving the React frontend
- **mongodb**: Database for storing product and documentation data
- **redis**: Key-value store for session management and cart data
- **pinecone**: Vector database emulator for RAG implementation

Communication between services happens over the `partselect-network` Docker network. 