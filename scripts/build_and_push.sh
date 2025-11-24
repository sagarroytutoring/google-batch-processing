#!/bin/bash
set -e

docker build -t gcr.io/$PROJECT_ID/$CONTAINER_IMAGE:latest ../container
docker push gcr.io/$PROJECT_ID/$CONTAINER_IMAGE:latest
