from pathlib import Path
from starlette.config import Config

from model_server import consts

# How to map model type to default actions
DEFAULT_ACTIONS = {
    consts.PIPELINE: consts.QUESTION_ANSWERING,
    consts.ENCODER: consts.ENCODE,
}


config = Config(".env")
DEBUG = config('DEBUG', cast=bool, default=False)

# Parameters used by all models
MODEL_TYPE = config('MODEL_TYPE')
MODEL_NAME = config('MODEL_NAME')
MODEL_PATH = Path(config('MODEL_PATH', default=Path('models/') / MODEL_NAME))

if not MODEL_PATH.exists():
    raise Exception(f'The provided model cannot be found: {MODEL_PATH.absolute()}')

# Model specific settings
MODEL_TOKENIZER = Path(config('MODEL_TOKENIZER', default=MODEL_PATH))
PIPELINE_TYPE = config('PIPELINE_TYPE', default='question-answering')

if MODEL_TYPE == consts.PIPELINE:
    if not MODEL_TOKENIZER or not MODEL_TOKENIZER.exists():
        raise Exception(
            f'No model tokenizer provided! MODEL_TOKENIZER must point to a valid path: {MODEL_PATH.absolute()}'
        )
    if not PIPELINE_TYPE:
        raise Exception('No PIPELINE_TYPE provided')
elif MODEL_TYPE == consts.ENCODER:
    pass


DEFAULT_ACTION = config('DEFAULT_ACTION', default=None) or DEFAULT_ACTIONS.get(MODEL_TYPE)
if DEFAULT_ACTION not in consts.ALL_ACTIONS:
    raise Exception(f'An invalid default action provided. Must be one of {", ".join(consts.ALL_ACTIONS)}')
