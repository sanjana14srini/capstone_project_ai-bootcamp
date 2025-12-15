# Use Ubuntu base for JVM support
FROM ubuntu:22.04

# Set noninteractive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, Java (required for Elasticsearch), curl
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    openjdk-17-jdk curl unzip wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Install Elasticsearch
ENV ES_VERSION=8.10.2
RUN wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ES_VERSION}-linux-x86_64.tar.gz \
    && tar -xzf elasticsearch-${ES_VERSION}-linux-x86_64.tar.gz \
    && mv elasticsearch-${ES_VERSION} /usr/share/elasticsearch \
    && rm elasticsearch-${ES_VERSION}-linux-x86_64.tar.gz

# Create elasticsearch user
RUN useradd -m elasticsearch \
    && chown -R elasticsearch:elasticsearch /usr/share/elasticsearch

# Expose ports: FastAPI, Streamlit, Elasticsearch
EXPOSE 8001 8501 9200 9300

# Copy startup script
COPY start_services.sh .

# Make it executable
RUN chmod +x start_services.sh

# Start backend, frontend, and Elasticsearch
CMD ["bash","./start_services.sh"]
