FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV HF_HOME=/app/models
ENV TRANSFORMERS_CACHE=/app/models

# Pre-download the Hugging Face embedder
RUN python - <<EOF
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="facebook/esm2_t6_8M_UR50D",
    local_dir="/app/models"
)
EOF

COPY src/ ./src/
