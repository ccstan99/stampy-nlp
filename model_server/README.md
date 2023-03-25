# Stampy NLP models

A microservice to host LLM models. This allows the Stampy NLP service to be a lot smaller. It
also results in speed ups and/or lower costs relative to using a dedicated Huggingface instance.

# Setup

    pip install -e .

# Configuration

Configuration is done via environment variables. These can also be provided with
an `.env` file.
The following variables are available. Each model **must** have its type and name provided.

* `MODEL_NAME` - the name of the model. This is assumed to be the same as the Huggingface path, but doesn't have to be
* `MODEL_TYPE` - one of `encoder` (used to generate encodings) or `pipeline` (for search)
* `MODEL_PATH` - the path to the model. If not provided will be assumed to be `./models/<MODEL_NAME>`
* `MODEL_TOKENIZER` - the path to the tokenizer. If not provided will assume it's the same as `MODEL_PATH`
* `DEBUG` - debug mode - (True/False) - by default disabled

There are also model type specific options:

* `PIPELINE_TYPE` - the type of pipeline to be used. The default is `question-answering`

# Run model server

Use the following to run locally

    uvicorn model_server.app:app --port 8123 --reload

The `--reload` option will cause the server to reload if any file changes are noticed.

# Docker build

The docker build needs to be provided the model name and type, e.g.:

    docker build -t model_server \
      --build-arg MODEL_NAME=sentence-transformers/multi-qa-mpnet-base-cos-v1 \
      --build-arg MODEL_TYPE=encoder \
      .
