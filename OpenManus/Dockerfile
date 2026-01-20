FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && (command -v uv >/dev/null 2>&1 || pip install --no-cache-dir uv)

# Copy requirements first for better caching
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Install additional dependencies for web server
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    websockets \
    python-multipart

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/workspace /app/logs

# Expose port
EXPOSE 8000

# Run the web server
CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
