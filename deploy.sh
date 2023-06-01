#!/bin/bash
set -e

LOCATION=us-west1
GCLOUD_PROJECT=stampy-nlp
GCLOUD_PROJECT_ID=t6p37v2uia
CLOUD_RUN_SERVICE=${1:-stampy-nlp} # Allow the service name to be provided as a parameter
IMAGE=$LOCATION-docker.pkg.dev/$GCLOUD_PROJECT/cloud-run-source-deploy/$CLOUD_RUN_SERVICE

# Model URLs
QA_MODEL_URL=https://qa-model-$GCLOUD_PROJECT_ID-uw.a.run.app
RETRIEVER_MODEL_URL=https://retriever-model-$GCLOUD_PROJECT_ID-uw.a.run.app
LIT_SEARCH_MODEL_URL=https://lit-search-model-$GCLOUD_PROJECT_ID-uw.a.run.app
export ALLOWED_ORIGINS=

echo "Running tests:"
pytest --runlive

echo
echo "Will execute the following actions:"
echo "--> Build a docker image"
echo "--> Push the image as $IMAGE"
echo "--> Deploy the image as the $CLOUD_RUN_SERVICE service"
read -r -p "Is that correct? [y/N] " response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    exit 1
fi

GCLOUD_PROJECT=stampy-nlp
echo
echo "Enabling Google API"
gcloud config set project $GCLOUD_PROJECT
gcloud config set run/region $LOCATION
gcloud services enable iam.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable logging.googleapis.com
gcloud auth configure-docker us-west1-docker.pkg.dev

echo "Building image"

docker pull --platform linux/amd64 python:3.8
docker buildx build --platform linux/amd6 -t $IMAGE .
docker push $IMAGE\:latest

echo "Deploying to Google Cloud Run"

gcloud beta run deploy $CLOUD_RUN_SERVICE --image $IMAGE\:latest \
--min-instances=1 --memory 256M --cpu=2 --platform managed --no-traffic --tag=test \
--service-account=service@stampy-nlp.iam.gserviceaccount.com \
--update-env-vars "^@^QA_MODEL_URL=$QA_MODEL_URL@RETRIEVER_MODEL_URL=$RETRIEVER_MODEL_URL@LIT_SEARCH_MODEL_URL=$LIT_SEARCH_MODEL_URL@ALLOWED_ORIGINS=$ALLOWED_ORIGINS@" \
--update-secrets=PINECONE_API_KEY=PINECONE_API_KEY:latest,CODA_TOKEN=CODA_TOKEN:latest,AUTH_PASSWORD=AUTH_PASSWORD:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest

echo
echo "Project ID: $GCLOUD_PROJECT"
