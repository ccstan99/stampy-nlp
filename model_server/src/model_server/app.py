from starlette.routing import Route
from starlette.applications import Starlette

from model_server.consts import ENCODER, PIPELINE
from model_server import settings
from model_server.model_types import Encoder, Pipeline


if settings.MODEL_TYPE == ENCODER:
    handler = Encoder(settings.MODEL_PATH, default_action=settings.DEFAULT_ACTION)
elif settings.MODEL_TYPE == PIPELINE:
    handler = Pipeline(
        model_path=str(settings.MODEL_PATH),
        model_type=settings.PIPELINE_TYPE,
        tokenizer=str(settings.MODEL_TOKENIZER),
    )
else:
    raise Exception('No valid model type provided')


base_routes = [
    Route("/", handler.default, methods=["POST"]),
]

app = Starlette(
    debug=settings.DEBUG,
    routes=base_routes + handler.routes(),
)
