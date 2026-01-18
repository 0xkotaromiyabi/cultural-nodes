#!/bin/bash
# Setup script for Ollama models

echo "[START] Setting up Ollama models for Cultural AI RAG..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "[ERROR] Ollama is not installed. Please install it first:"
    echo "   curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

echo "[OK] Ollama is installed"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[WARN] Ollama is not running. Starting..."
    ollama serve &
    sleep 3
fi

echo "[OK] Ollama is running"

# Pull required models
echo ""
echo "[PULL] Pulling llama3.1 (LLM model)..."
ollama pull llama3.1

echo ""
echo "[PULL] Pulling nomic-embed-text (Embedding model)..."
ollama pull nomic-embed-text

echo ""
echo "[DONE] Setup complete! Models available:"
ollama list

echo ""
echo "[INFO] You can now start the Cultural AI RAG system:"
echo "   cd ~/cultural-nodes"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
