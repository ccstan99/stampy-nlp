#!/bin/bash
set -e

echo "Activating Dev Env"
virtualenv -p python3.8 venv
source venv/bin/activate

# export CODA_TOKEN=
# export PINECONE_API_KEY=
# export HUGGINGFACE_API_KEY=

echo "Download Transformer Models"
mkdir -p ./models
if [ ! -d ./models/retriever ]; then
    echo "multi-qa-mpnet-base-cos-v1 not found - fetching"
    git clone https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-cos-v1 ./models/retriever
fi
if [ ! -d ./models/reader ]; then
    echo "electra-base-squad2 - fetching"
    git clone https://huggingface.co/deepset/electra-base-squad2 ./models/reader
fi

echo "Installing Required Libraries"
pip install -e .

export GCLOUD_PROJECT=stampy-nlp
export LOCATION=us-west1

echo "Enabling Google API"
gcloud config set project $GCLOUD_PROJECT
gcloud config set run/region $LOCATION
gcloud services enable iam.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable logging.googleapis.com

echo "Project ID: $GCLOUD_PROJECT"
