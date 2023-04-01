import logging
from flask import Flask
from stampy_nlp.routes import frontend, api
from stampy_nlp.settings import check_required_vars
from stampy_nlp.models import connect_pinecone
from stampy_nlp.utilities.pinecone_utils import get_index


def make_app():
    # Make sure all required env variables are set, and blow up if not
    check_required_vars()

    app = Flask(__name__)
    app.register_blueprint(frontend)
    app.register_blueprint(api, url_prefix='/api')
    connect_pinecone(get_index())
    return app


def run():
    logging.basicConfig(level=logging.INFO)
    app = make_app()
    app.run(debug=True, port=8080)


if __name__ == '__main__':
    run()
