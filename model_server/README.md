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
* `DEFAULT_ACTION` - what should be used when no action is provided (i.e. the `"/"` endpoint is called) - the
default for encoders is to encode, and for pipelines to answer questions
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

# Deployment

There is a `../deploy_model.sh` script in the root folder that can be used to deploy a specific model to Google Cloud run. The syntax is:

    ../deploy_model.sh <service name> <huggingface model> <model type> <default action>

where:

 * `<service name>` is the name of the service in Google Cloud Run - must consist of alphanumerics and dashes (`-`)
 * `<huggingface model>` the name of the model as listed on Huggingface - this will be downloaded, so must match
 * `<model type>` one of `encoder` or `pipeline`
 * `<default action>` - this controls what the `"/"` endpoint will do. It's totally optional, so if unsure, skip it.

An example invocation would be:

    ../deploy_model.sh lit-search-model allenai/specter encoder
