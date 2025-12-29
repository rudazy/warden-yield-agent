FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY langgraph.json .

ENV PYTHONPATH=/app/src
ENV PORT=8000

EXPOSE 8000

CMD python -m uvicorn yield_agent.server:app --host 0.0.0.0 --port 8000