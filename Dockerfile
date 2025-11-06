# Use official Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and scientific libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY facenet/requirements.txt /app/facenet/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r facenet/requirements.txt

# Copy application code
COPY facenet/ /app/facenet/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Expose port
EXPOSE 5000

# Change to facenet directory and run with gunicorn
WORKDIR /app/facenet
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--timeout", "300", "--worker-class", "sync", "app:app"]
