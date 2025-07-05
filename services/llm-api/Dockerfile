FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl for ROFL socket communication
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary files
COPY main_worldtree.py main.py
COPY snp_analyzer.py snp_analyzer.py

EXPOSE 8080

CMD ["python", "main.py"]
