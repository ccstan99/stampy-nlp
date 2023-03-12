FROM python:3.8

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# set a directory for the app
WORKDIR /app

# copy all the files to the container
COPY . .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# tell the port number the container should expose
EXPOSE 8080
ENV PORT 8080

# Use gunicorn as the entrypoint
CMD exec gunicorn --bind :$PORT --workers 1 --threads 1 --timeout 0 main:app
