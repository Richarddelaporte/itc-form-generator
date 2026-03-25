# ITC Form Generator - Nest Deployment with MetaGen Support
# Uses Meta's internal Python image with MetaGen pre-installed

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
# Note: metagen will be installed from Meta's internal PyPI
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY webapp.py .
COPY src/ ./src/

# Copy sample files (optional, for testing)
COPY sample_soo.md .
COPY sample_points_list.csv .

# Create directories for persistent data
RUN mkdir -p /app/data

# Set environment variables for Nest
ENV PORT=3000
ENV HOSTNAME="::"
ENV PYTHONUNBUFFERED=1
ENV METAGEN_ENABLED=true

# Expose port 3000 (Nest default)
EXPOSE 3000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/api/health')" || exit 1

# Run the web application
CMD ["python", "webapp.py"]
