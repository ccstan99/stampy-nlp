#!/bin/bash
echo "$(date +%F_%T)"
cd "$(dirname "$0")"
export PATH="$PATH:/home/cheng2/.local/bin"
export CODA_TOKEN=ee236c9d-6392-43b0-b7e4-2f227f6f3744
export PINECONE_API_KEY=040b0588-32b2-4195-b234-63e068540253
export HUGGINGFACE_API_KEY=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

echo "Setup Environment"
pip install -q -r requirements.txt

echo "Generate FAQ Encodings for Cron Using Local GPU"
python3 ../src/stampy_nlp/faq_titles_local.py $1

echo "Uploading Duplicates JSON to Cloud Bucket"
gcloud storage cp stampy-duplicates.json gs://stampy-nlp-resources
