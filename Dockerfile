FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY app_agent.py .

# Expose Streamlit port
EXPOSE 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8503/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app_agent.py", "--server.port=8503", "--server.address=0.0.0.0", "--server.headless=true"]
