# Revolution Pi Connect SE - WMS Deployment
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application files
COPY . .

# Expose ports
EXPOSE 8502 2000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8502/_stcore/health || exit 1

# Environment variables for RevPi
ENV PLC_IP=1.1.1.2
ENV PLC_PORT=2000
ENV HMI_PORT=2001
ENV REVPI_ETH1=1.1.1.185
ENV REVPI_ETH0=192.168.0.12

# Start command
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8502"]
