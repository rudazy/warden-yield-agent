FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY langgraph.json .

# Install Python dependencies
RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir uvicorn fastapi

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Run the FastAPI server
CMD ["python", "-m", "uvicorn", "yield_agent.server:app", "--host", "0.0.0.0", "--port", "8000"]
