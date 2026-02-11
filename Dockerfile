# Use a Python base image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set environment variables
ENV OLLAMA_BASE_URL=http://localhost:11434
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/user
ENV PATH="/home/user/.local/bin:${PATH}"

# Create a non-root user
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

# Copy the application and data
COPY --chown=user . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose the API port
EXPOSE 7860

# Use the entrypoint script to start Ollama and the app
ENTRYPOINT ["./entrypoint.sh"]
