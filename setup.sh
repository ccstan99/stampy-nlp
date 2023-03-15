#!/bin/bash
set -e

echo "Download Transformer Models..."
mkdir -p ./models
if [ ! -d ./models/retriever ]; then
    echo "multi-qa-mpnet-base-cos-v1 not found - fetching"
    git clone https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-cos-v1 ./models/retriever
fi
if [ ! -d ./models/reader ]; then
    echo "electra-base-squad2 - fetching"
    git clone https://huggingface.co/deepset/electra-base-squad2 ./models/reader
fi
echo "-> Models downloaded to ./models"

echo
echo "Setting up Dev Env..."
if [ -d venv ]; then
    echo '-> Using existing virtualenv'
elif [ `whereis -bq python3.8` ]; then
    virtualenv -p python3.8 venv
elif [ `whereis -bq python3.9` ]; then
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
    echo "Create a Huggingface token at https://huggingface.co/settings/tokens"
    read -p "Huggingface API key: " HUGGINGFACE_TOKEN

    cat << EOT > .env
CODA_TOKEN=$CODA_TOKEN
PINECONE_API_KEY=$PINECONE_TOKEN
HUGGINGFACE_API_KEY=$HUGGINGFACE_TOKEN
EOT
    echo "-> Tokens written to ./.env"
fi

echo
echo "Installing Required Libraries..."
pip install -e '.[tests]'

echo
echo "Run 'source venv/bin/activate' to use the virtualenv"
