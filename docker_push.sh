#!/bin/bash
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker tag ml-api_api_app:latest top2know/api_app:latest
docker push top2know/api_app:latest
docker tag ml-api_models_app:latest top2know/models_app:latest
docker push top2know/models_app