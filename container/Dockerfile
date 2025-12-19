FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV HF_HOME=/app/models
ENV TRANSFORMERS_CACHE=/app/models

ARG HF_MODEL_DOWNLOADS
ENV HF_MODEL_DOWNLOADS=$HF_MODEL_DOWNLOADS
# Pre-download the Hugging Face embedder
RUN python - <<EOF
import os
from huggingface_hub import snapshot_download

for model in os.environ["HF_MODEL_DOWNLOADS"].split(","):
    snapshot_download(repo_id=model)
EOF

COPY src/ ./src/
