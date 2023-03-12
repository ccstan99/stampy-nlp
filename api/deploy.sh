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

echo "Deploying to Google Cloud Run"

# gcloud builds submit --tag gcr.io/$GOOGLE_PROJECT_ID/$CLOUD_RUN_SERVICE \
#   --project=$GOOGLE_PROJECT_ID

# gcloud run deploy $CLOUD_RUN_SERVICE \
#   --image gcr.io/$GOOGLE_PROJECT_ID/$CLOUD_RUN_SERVICE \
#   --add-cloudsql-instances $INSTANCE_CONNECTION_NAME \
#   --update-env-vars INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME,DB_PASS=$DB_PASS,DB_USER=$DB_USER,DB_NAME=$DB_NAME \
#   --platform managed \
#   --region us-central1 \
#   --allow-unauthenticated \
#   --project=$GOOGLE_PROJECT_ID

gcloud beta run deploy $CLOUD_RUN_SERVICE --source . \
--min-instances=1 --memory 4G --cpu=2 --platform managed --no-traffic --tag=test \
--service-account=service@stampy-nlp.iam.gserviceaccount.com \
--update-secrets=PINECONE_API_KEY=PINECONE_API_KEY:latest,HUGGINGFACE_API_KEY=HUGGINGFACE_API_KEY:latest,CODA_TOKEN=CODA_TOKEN:latest
