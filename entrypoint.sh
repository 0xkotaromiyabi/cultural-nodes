#!/bin/bash

# Start Ollama service in the background
echo "Starting Ollama service..."
ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 1
done

echo "Ollama is ready."

# Pull models if they don't exist
echo "Pulling models (if needed)..."
ollama pull llama3.1
ollama pull nomic-embed-text

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 7860
