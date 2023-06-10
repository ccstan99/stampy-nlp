#!/bin/bash
set -e

if [[ "$@" == *"-local"* ]]; then
    source venv/bin/activate
    pip install -q -e '.[local_model]'
    RETRIEVER_MODEL_URL=multi-qa-mpnet-base-cos-v1 python src/stampy_nlp/faq_titles.py $@
else
    if [ -z "${AUTH_PASSWORD}" ]; then
        echo "no AUTH_PASSWORD provided!"
        exit 1
    fi
    NLP_API_URL=https://nlp.stampy.ai/api/encode-faq-titles
    curl -X POST -f -u stampy:$AUTH_PASSWORD $NLP_API_URL -H 'Content-Type: application/json' > stampy-duplicates.json
fi

echo "Updated duplicates"
