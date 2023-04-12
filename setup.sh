#!/bin/bash
set -e

echo
echo "Setting up Dev Env..."
if [ -d venv ]; then
    echo '-> Using existing virtualenv'
elif [ `whereis -b python3.8` ]; then
    virtualenv -p python3.8 venv
elif [ `whereis -b python3.9` ]; then
    virtualenv -p python3.9 venv
else
    echo 'No Python 3.8 or 3.9 found - aborting'  >> /dev/stderr
    exit 1
fi
source venv/bin/activate

if [ ! -f .env ]; then
    echo
    echo "Setup env variables..."
    echo
    echo "Create a read only Coda token at https://coda.io/account, for the https://coda.io/d/_dfau7sl2hmG table"
    read -p "Coda token: " CODA_TOKEN

    echo
    echo "Create a Pinecode token (https://app.pinecone.io), but make sure the environment is 'us-west1-gcp'"
    read -p "Pinecode API key: " PINECONE_TOKEN

    echo
    echo "Create an OpenAI secret key (https://platform.openai.com/account/api-keys)"
    read -p "OpenAI API key: " OPENAI_TOKEN

    cat << EOT > .env
CODA_TOKEN=$CODA_TOKEN
PINECONE_API_KEY=$PINECONE_TOKEN
OPENAI_API_KEY=$OPENAI_TOKEN

GCLOUD_PROJECT_ID=t6p37v2uia
QA_MODEL_URL=https://qa-model-$GCLOUD_PROJECT_ID-uw.a.run.app
RETRIEVER_MODEL_URL=https://retriever-model-$GCLOUD_PROJECT_ID-uw.a.run.app
LIT_SEARCH_MODEL_URL=https://lit-search-model-$GCLOUD_PROJECT_ID-uw.a.run.app
EOT
    echo "-> Tokens written to ./.env"
fi

echo
echo "Installing Required Libraries..."
pip install -e '.[tests]'

echo
echo "Run 'source venv/bin/activate' to use the virtualenv"
