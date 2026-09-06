FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create application data directories
RUN mkdir -p data/vectorstore data/uploads data/metadata

# Copy the rest of the backend codebase
COPY . .

# Expose port (Render sets $PORT dynamically)
EXPOSE 8000

# Run FastAPI backend
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
