from pathlib import Path
from starlette.config import Config


# The possible model types
PIPELINE = 'pipeline'
ENCODER = 'encoder'

# Available model actions (not all models can handle all of them)
DEFAULT = 'default'
ENCODE = 'encode'
QUESTION_ANSWERING = 'question_answering'
PARAPHRASE_MINING = 'paraphrase_mining'

ALL_ACTIONS = [ENCODE, QUESTION_ANSWERING, PARAPHRASE_MINING]

# How to map model type to default actions
DEFAULT_ACTIONS = {
    PIPELINE: QUESTION_ANSWERING,
    ENCODER: ENCODE,
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

if MODEL_TYPE == PIPELINE:
    if not MODEL_TOKENIZER or not MODEL_TOKENIZER.exists():
        raise Exception(
            f'No model tokenizer provided! MODEL_TOKENIZER must point to a valid path: {MODEL_PATH.absolute()}'
        )
    if not PIPELINE_TYPE:
        raise Exception('No PIPELINE_TYPE provided')
elif MODEL_TYPE == ENCODER:
    pass


DEFAULT_ACTION = config('DEFAULT_ACTION', default=None) or DEFAULT_ACTIONS.get(MODEL_TYPE)
if DEFAULT_ACTION not in ALL_ACTIONS:
    raise Exception(f'An invalid default action provided. Must be one of {", ".join(ALL_ACTIONS)}')
