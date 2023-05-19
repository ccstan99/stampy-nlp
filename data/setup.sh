echo "Activating Dev Env"
# wsl
# virtualenv -p /usr/local/bin/python3.8 venv
# source venv/bin/activate

# export CODA_TOKEN=
# export PINECONE_API_KEY=
# export HUGGINGFACE_API_KEY=

# echo "Download Transformer Models"
# git clone https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-cos-v1 ./models
# git clone https://huggingface.co/deepset/electra-base-squad2 ./models
# git clone https://huggingface.co/sentence-transformers/allenai-specter ./models
# mv $PWD/models/retriever $PWD/models/retriever.bak
# mv $PWD/models/reader $PWD/models/reader.bak
# ln -s $PWD/models/multi-qa-mpnet-base-cos-v1 $PWD/models/retriever
# ln -s $PWD/models/electra-base-squad2 $PWD/models/reader

echo "Installing Required Libraries"
# pip install --upgrade pip
pip install -q -r requirements.txt

# export GCLOUD_PROJECT=stampy-nlp
# export GCLOUD_BUCKET=stampy-nlp-resources
# export CLOUD_RUN_SERVICE=stampy-nlp
# export LOCATION=us-west1

# echo "Enabling Google API"
# gcloud services enable iam.googleapis.com
# gcloud services enable run.googleapis.com
# gcloud services enable cloudbuild.googleapis.com
# gcloud services enable logging.googleapis.com
# gcloud config set project $GCLOUD_PROJECT

echo "Project ID: $GCLOUD_PROJECT"