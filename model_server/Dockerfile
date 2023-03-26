FROM --platform=linux/amd64 python:3.8 AS base

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# set a directory for the app
WORKDIR /app

# install dependencies - setuptools use git to find non python files, hence the magic invocation
RUN apt update && apt-get install -y git-lfs
COPY pyproject.toml pyproject.toml
ARG PSEUDO_VERSION=1
RUN SETUPTOOLS_SCM_PRETEND_VERSION=${PSEUDO_VERSION} pip install --no-cache-dir -e .[test]

# Install the app
COPY src ./src
RUN pip install --no-cache-dir -e .

FROM base

ARG MODEL_NAME
ARG MODEL_TYPE
ARG DEFAULT_ACTION

# Setup the configuration defaults
RUN echo "MODEL_NAME=${MODEL_NAME}\n\
MODEL_TYPE=${MODEL_TYPE}\n\
DEFAULT_ACTION=${DEFAULT_ACTION}" >> .env

# Fetch the appropriate model
RUN mkdir models
RUN git clone https://huggingface.co/${MODEL_NAME} ./models/${MODEL_NAME}
RUN cd ./models/${MODEL_NAME} && git lfs install && git lfs pull

# tell the port number the container should expose
EXPOSE 8080
ENV PORT 8080

# Use gunicorn as the entrypoint
CMD exec uvicorn model_server.app:app --host 0.0.0.0 --port $PORT
