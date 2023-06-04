#!/bin/bash
set -e

if [ -z "${AUTH_PASSWORD}" ] && [[ "$@" != *"-local"* ]]; then
    echo "no AUTH_PASSWORD provided!"
    exit 1
fi

if [[ "$@" == *"-local"* ]]; then
    source venv/bin/activate
    pip install -e '.[local_model]'
    RETRIEVER_MODEL_URL='./model_server/models/multi-qa-mpnet-base-cos-v1/' python src/stampy_nlp/faq_titles.py $@
else
    NLP_API_URL=https://nlp.stampy.ai/api/encode-faq-titles
    curl -X POST -f -u stampy:$AUTH_PASSWORD $NLP_API_URL -H 'Content-Type: application/json' > stampy-duplicates.json
fi

echo "Updated duplicates"
