# Use official lightweight Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000

# Create a non-root application user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy application code
COPY prompt_builder/ /app/prompt_builder/
COPY app.py /app/app.py

# Prepare data directories with proper permissions
RUN mkdir -p /app/data/prompts /app/data/appendices && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Volumes for persistent prompt storage
VOLUME ["/app/data/prompts", "/app/data/appendices"]

# Expose application port
EXPOSE 8000

# Standard library healthcheck (no curl/wget needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Run the prompt constructor
CMD ["python3", "app.py", "--host", "0.0.0.0", "--port", "8000"]
