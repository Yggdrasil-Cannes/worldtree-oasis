FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl for ROFL socket communication
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bridge-aware version
COPY main_with_bridge.py main.py

EXPOSE 8080

CMD ["python", "main.py"]
