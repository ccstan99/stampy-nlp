#!/bin/bash
set -e

if [ -z "${AUTH_PASSWORD}" ]; then
    echo "no AUTH_PASSWORD provided!"
    exit 1
fi

NLP_API_URL=https://stampy-nlp-t6p37v2uia-uw.a.run.app/api/encode-faq-titles
# NLP_API_URL=https://test---stampy-nlp-t6p37v2uia-uw.a.run.app/api/encode-faq-titles
# NLP_API_URL=http://localhost:8080/api/encode-faq-titles

curl -X POST -f -u stampy:$AUTH_PASSWORD $NLP_API_URL -H 'Content-Type: application/json' > stampy-duplicates.json

echo "Updated duplicates"
