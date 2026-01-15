FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p input output temp_sessions

# Expose port (5000 is default Flask, we use 5001 usually but cloud uses PORT env)
ENV PORT=8080
EXPOSE 8080

# Run with Gunicorn
CMD ["sh", "-c", "gunicorn web:app_server --bind 0.0.0.0:$PORT --workers 4 --timeout 120"]
