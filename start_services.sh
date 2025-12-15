#!/bin/bash
set -e

# Start Elasticsearch as non-root
su elasticsearch -c "/usr/share/elasticsearch/bin/elasticsearch -Ediscovery.type=single-node" &

sleep 15

# Start FastAPI backend
python3 -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit frontend (foreground)
python3 -m streamlit run app.frontend.app.py \
  --server.port 8501 \
  --server.address 0.0.0.0
