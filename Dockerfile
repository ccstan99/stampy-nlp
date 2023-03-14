FROM --platform=linux/amd64 python:3.8

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# set a directory for the app
WORKDIR /app

# copy all the files to the container
COPY models ./models
COPY pyproject.toml pyproject.toml

# install dependencies - setuptools use git to find non python files, hence the magic invocation
ARG PSEUDO_VERSION=1
RUN SETUPTOOLS_SCM_PRETEND_VERSION=${PSEUDO_VERSION} pip install --no-cache-dir -e .[test]

COPY src ./src
RUN --mount=source=.git,target=.git,type=bind pip install --no-cache-dir -e .

# tell the port number the container should expose
EXPOSE 8080
ENV PORT 8080

# Use gunicorn as the entrypoint
CMD exec gunicorn --bind :$PORT --workers 1 --threads 1 --timeout 0 'stampy_nlp.main:make_app()'
