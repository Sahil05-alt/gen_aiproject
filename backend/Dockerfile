FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
# We use CPU PyTorch to save enormous amounts of space and memory
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create application data directories
RUN mkdir -p data/vectorstore data/uploads data/metadata

# Copy the rest of the application
COPY . .

# Hugging Face Spaces expects the app to run on port 7860
EXPOSE 7860

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
