#!/bin/bash
set -e

if [ -z "${AUTH_PASSWORD}" ]; then
    echo "no AUTH_PASSWORD provided!"
    exit 1
fi

if [[ "$@" == *"-local"* ]]; then
    source venv/bin/activate
    python src/stampy_nlp/faq_titles.py $@
else
    NLP_API_URL=https://stampy-nlp-t6p37v2uia-uw.a.run.app/api/encode-faq-titles
    curl -X POST -f -u stampy:$AUTH_PASSWORD $NLP_API_URL -H 'Content-Type: application/json' > stampy-duplicates.json
fi

echo "Updated duplicates"
