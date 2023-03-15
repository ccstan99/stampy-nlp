import logging
from flask import Flask
from stampy_nlp.routes import frontend, api


def make_app():
    app = Flask(__name__)
    app.register_blueprint(frontend)
    app.register_blueprint(api, url_prefix='/api')
    return app


def run():
    logging.basicConfig(level=logging.INFO)
    app = make_app()
    app.run(debug=True, port=8080)


if __name__ == '__main__':
    run()
