![Stampy!](https://github.com/StampyAI/StampyAIAssets/blob/main/profile/stampy-profile-228.png?raw=true)

Stampy NLP performs semantic search and other NLP microservices for [aisafety.info](https://aisafety.info) and [stampy.ai](https://stampy.ai), a database of questions and answers about AGI safety. Contributions will be welcome (once I get the messy things cleaned up), and the code is released under the MIT License.

The demo url is [nlp.stampy.ai](https://nlp.stampy.ai/) or direct link to [stampy-nlp-t6p37v2uia-uw.a.run.app](https://stampy-nlp-t6p37v2uia-uw.a.run.app/). If you're interested in learning more about Natural Language Processing (NLP) and Transformers, the [HuggingFace course](https://huggingface.co/course/chapter1/2?fw=pt) provides an excellent introduction.

# Main Services Overview

![Stampy NLP Overview](images/stampy-nlp.svg)

Our NLP services offer 4 features which depend on 2 key components:

1. Three NLP models from HuggingFace, specifically [SentenceTransformers](https://www.sbert.net/), provide pre-trained models optimized for different types of semantic searches by generating sentence embeddings -- 768-dimension vectors, numerical representations that capture the meaning of the text. Think of it as an 768 element array of floats. In general, we use Python + PyTorch since that gives us the most flexibility to use a variety of models by default.

- Retriever model ([multi-qa-mpnet](https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-cos-v1)) for identifying paraphrased questions.
- [allenai-specter](https://huggingface.co/sentence-transformers/allenai-specter) for searching titles & abstracts of scientific publications.
- Reader model ([electra-base-squad2](https://huggingface.co/deepset/electra-base-squad2)) finds the start & end index of the answer given a question and a context paragraph containing the answer.

2. [Pinecone](https://www.pinecone.io/) is a fully managed, high-performance database for vector search applications. Each data element contains the 768-dimension vector, a unique id (i.e. Coda id for our FAQ) and some metadata (original text, url, other relevant information).

## 1. [Semantic Search for Similar FAQs](https://nlp.stampy.ai/)

Encodes a given `query` string, sends the vector embedding to search pinecone for nearest entries in `faq-titles` namespace, then returns payload as json sorted by score between 0 and 1 indicating the similarity of match.

Sample API usage:

```text
https://nlp.stampy.ai/api/search?query=What+AI+safety%3F`
```

- `query` (required) is the sentence or phrase to be encoded then have nearest entries returned.
- `top` (optional) indicates the number of entries returned. If the value is not specified, the default is to return the 10 nearest entries.
- `showLive=0` (optional) will return only entries with `status` that are NOT "Live on site". The default is `showLive=1` to return only entries that with `status` that are "Live on site".
- `status=all` (optional) returns all entries including those that have not yet been canonically answered. Specify multiple values for `status` to return matching more than one value.
- `getContent=true` (optional) returns the content of answers along with each entry. Otherwise, default is `getContent=false` and only the question titles without answers are returned.

Sample usages:

`showLive=1` returns entries where `status == "Live on site"`

```bash
https://nlp.stampy.ai/api/search?query=What+AI+safety%3F&showLive=1
```

`showLive=0` returns entries where `status != "Live on site"`

```bash
https://nlp.stampy.ai/api/search?query=What+AI+safety%3F&showLive=0
```

`status=all` returns all questions regardless of status

```bash
https://nlp.stampy.ai/api/search?query=Something+random%3F&status=all
```

`status=value` returns entries with status matching whatever value is specified. Multiple values may be listed separately. The example below returns entries with `status == "Not started"` and also `status == "In progress"`

```bash
https://nlp.stampy.ai/api/search?query=Something+random%3F&status=Not%20started&status=In%20progress
```

`getContent=true` returns the content of answers along with each entry.

```bash
https://nlp.stampy.ai/api/search?query=Something+random%3F&getContent=true
```

## 2. [Duplicates Report](https://nlp.stampy.ai/duplicates)

Display a table with top pairs of most similar questions in Coda based on the last time `paraphrase_mining` was called.

## 3. [Literature Abstracts](https://nlp.stampy.ai/literature)

Encodes a given query string, sends the vector embedding to search pinecone for nearest entry in `paper-abstracts` namespace, then returns payload as json sorted by score between 0 and 1 indicating the similarity of match. In an effort to minimize the number of huge models in our app container, this service still uses the external HuggingFace API so it's still a bit slow.

Sample API usage:

```bash
https://nlp.stampy.ai/api/literature?query=What+AI+safety%3F
```

## 4. [Extract QA](https://nlp.stampy.ai/extract)

Encodes a given query string then sends the vector embedding to search pinecone for the 10 nearest entries in `extracted-chunks` namespace. For each entry, run the HuggingFace pipeline task to extract the answer from each content then returns payload as json sorted by score between 0 and 1 indicating the confidence of the answer matches the query question. Since this runs +10 inferences, this can be rather slow.

Sample API usage:

```bash
https://nlp.stampy.ai/api/extract?query=What+AI+safety%3F
```

# Setup Environment

## Run the setup script

```bash
./setup.sh
```

If this is your first run, it will:

- Download the appropriate models from Huggingface
- Write the appropriate API keys/tokens to `.env`
- Create a virtualenv
- Install all requirements

Subsequent runs will skip bits that have already been done, but it does so by simply checking whether the appropriate files exist.
API tokens for [Coda](https://coda.io/account), [Pinecone](https://app.pinecone.io) and [OpenAI](https://platform.openai.com/account/api-keys) are required,
but the script will ask you for them.

### Coda

The Stampy Coda table is `https://coda.io/d/_dfau7sl2hmG`

### Pinecone

When creating a Pinecone project, make sure that the environment is set to us-west1-gcp

### Duplicates generation

There is an `/api/encode-faq-titles` endpoint that will generate a duplicates file and save it to Cloud
Storage. To avoid misusage, the endpoint is password protected. The password is provided via the `AUTH_PASSWORD`
env variable. This is only used for that endpoint - if not set, the endpoint will simply return 401s.

### Remote models

The models used are hosted separately and are provided via the following env variables:

```bash
QA_MODEL_URL=https://qa-model-t6p37v2uia-uw.a.run.app
RETRIEVER_MODEL_URL=https://retriever-model-t6p37v2uia-uw.a.run.app
LIT_SEARCH_MODEL_URL=https://lit-search-model-t6p37v2uia-uw.a.run.app
```

To help with local development you can set up the above model servers via docker-compose:

```bash
docker-compose up
```

This should work, but slowly. If you want faster results, consider either manually running the model that you're
using (check the `model_server` folder for details), or provide a cloud server with the model.

# Deployment

## Install Google [Cloud SDK](https://cloud.google.com/sdk/docs/install)

### Linux

```bash
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install google-cloud-cli
gcloud init
gcloud auth login --no-launch-browser
```

### MacOS

```bash
brew install --cask google-cloud-sdk
gcloud init
```

## Setup Docker

1. Install [Docker](https://docs.docker.com/get-docker/)
2. Authenticate Docker to Google Cloud: `gcloud auth configure-docker us-west1-docker.pkg.dev`

One thing worth remembering here is that Google Cloud Run containers assume that they'll get a Linux x64 image. The
deployment scripts should generate appropriate images, but it might be an issue if your deployments don't want to work
and you're not on a Linux x64 system

## Deploy to Google [Cloud Run](https://cloud.google.com/sdk/gcloud/reference/beta/run/deploy)

```bash
./deploy.sh <service name>
```

If no service name is provided, the script will deploy to `stampy-nlp`. Before actually doing anything, the script will ask to make sure everything is correct.
