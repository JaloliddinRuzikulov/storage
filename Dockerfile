FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
	ffmpeg \
	curl \
	--no-install-recommends && \
	rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
	pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/uploads

# Expose port
EXPOSE 9005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
	CMD curl -f http://localhost:9005/ || exit 1

# Run the application
CMD ["python", "start.py"]
