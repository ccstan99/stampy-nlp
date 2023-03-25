from pathlib import Path
from starlette.config import Config


PIPELINE = 'pipeline'
ENCODER = 'encoder'

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
