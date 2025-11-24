FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Hugging Face embedder
# RUN python - <<EOF
# from huggingface_hub import snapshot_download
# snapshot_download(
#     repo_id="sentence-transformers/all-mpnet-base-v2",
#     local_dir="/app/models",
#     local_dir_use_symlinks=False
# )
# EOF

COPY src/ ./src/

ENV HF_HOME=/app/models
ENV TRANSFORMERS_CACHE=/app/models

