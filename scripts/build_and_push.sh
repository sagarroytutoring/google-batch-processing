#!/bin/bash
set -e

docker build --build-arg HF_MODEL_DOWNLOADS=$HF_MODEL_DOWNLOADS -t gcr.io/$PROJECT_ID/$CONTAINER_IMAGE:latest ../container
docker push gcr.io/$PROJECT_ID/$CONTAINER_IMAGE:latest
