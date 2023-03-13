#!/bin/bash
set -e

GCLOUD_PROJECT=stampy-nlp
LOCATION=us-west1
CLOUD_RUN_SERVICE=stampy-nlp-dev
IMAGE=$LOCATION-docker.pkg.dev/$GCLOUD_PROJECT/cloud-run-source-deploy/$CLOUD_RUN_SERVICE

echo
echo "Enabling Google API"
gcloud config set project $GCLOUD_PROJECT
gcloud config set run/region $LOCATION
gcloud services enable iam.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable logging.googleapis.com

echo "Building image"

docker pull --platform linux/amd64 python:3.8
docker buildx build --platform linux/amd6 -t $IMAGE .
docker push $IMAGE:latest

echo "Deploying to Google Cloud Run"

gcloud beta run deploy $CLOUD_RUN_SERVICE --image $IMAGE:latest \
--min-instances=1 --memory 4G --cpu=2 --platform managed --no-traffic --tag=test \
--service-account=service@stampy-nlp.iam.gserviceaccount.com \
--update-secrets=PINECONE_API_KEY=PINECONE_API_KEY:latest,HUGGINGFACE_API_KEY=HUGGINGFACE_API_KEY:latest,CODA_TOKEN=CODA_TOKEN:latest

echo
echo "Project ID: $GCLOUD_PROJECT"
