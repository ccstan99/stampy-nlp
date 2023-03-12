# echo "Activating Dev Env"
# virtualenv -p /usr/local/bin/python3.8 venv
# source venv/bin/activate

# export CODA_TOKEN=
# export PINECONE_API_KEY=
# export HUGGINGFACE_API_KEY=

echo "Exporting GCLOUD_PROJECT, CLOUD_RUN_SERVICE and LOCATION"
export GCLOUD_PROJECT=stampy-nlp
export GCLOUD_BUCKET=stampy-nlp-resources
export CLOUD_RUN_SERVICE=stampy-nlp
export LOCATION=us-west1

echo "Setup Environment"
pip install -q -r requirements.txt

echo "Generate FAQ Encodings for Pinecone"
python3 encode-faq-titles.py

echo "Uploading Duplicates JSON to Cloud Bucket"
gcloud storage cp stampy-duplicates.json gs://stampy-nlp-resources
