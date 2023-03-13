#!/bin/bash
set -e

echo "Exporting GCLOUD_PROJECT, CLOUD_RUN_SERVICE and LOCATION"
export GCLOUD_PROJECT=stampy-nlp
export CLOUD_RUN_SERVICE=stampy-nlp
export LOCATION=us-west1

IMAGE=$LOCATION-docker.pkg.dev/$GCLOUD_PROJECT/cloud-run-source-deploy/$CLOUD_RUN_SERVICE

echo "Building image"

docker pull --platform linux/amd64 python:3.8
docker buildx build --platform linux/amd6 -t $IMAGE .
docker push $IMAGE:latest

echo "Deploying to Google Cloud Run"

gcloud beta run deploy $CLOUD_RUN_SERVICE --image $IMAGE:latest \
--min-instances=1 --memory 4G --cpu=2 --platform managed --tag=test \
--service-account=service@stampy-nlp.iam.gserviceaccount.com \
--update-secrets=PINECONE_API_KEY=PINECONE_API_KEY:latest,HUGGINGFACE_API_KEY=HUGGINGFACE_API_KEY:latest,CODA_TOKEN=CODA_TOKEN:latest
