import logging
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
from model_server import settings


logger = logging.getLogger(__name__)


ENCODE = 'encode'
QUESTION_ANSWERING = 'question_answering'
PARAPHRASE_MINING = 'paraphrase_mining'
DEFAULT = 'default'


def error(text, error_code=400):
    return {'error': text}, error_code


def ok(contents):
    return contents, 200


def verify_fields_exist(payload, *fields):
    missing = [field for field in fields if not payload.get(field)]
    if missing:
        return {'error': 'Missing fields in payload', 'missing': missing}, 400
    return None


def get_model():
    """Loads the model file into memory and returns a model type specific python class."""
    model_type = settings.MODEL_TYPE
    logger.info('Loading %s model from %s', model_type, settings.MODEL_PATH)

    if model_type == settings.PIPELINE:
        return pipeline(
            settings.PIPELINE_TYPE,
            model=str(settings.MODEL_PATH),
            tokenizer=str(settings.MODEL_TOKENIZER)
        )

    elif model_type == settings.ENCODER:
        return SentenceTransformer(settings.MODEL_PATH)

    else:
        raise Exception(f'Could not initialize model: model_type={model_type}')


def get_default_command(model_type):
    """The command should be provided in the URL path, but if not, then each model has a natural command."""
    if model_type == settings.PIPELINE:
        return QUESTION_ANSWERING
    elif model_type == settings.ENCODER:
        return ENCODE


def handle_command(model, command, payload):
    logger.info('Handling "%s"', command)
    logger.debug('Payload: %s', payload)

    query = payload.get('query')

    if command == ENCODE:
        result = verify_fields_exist(payload, 'query') or model.encode(query).tolist()

    elif command == QUESTION_ANSWERING:
        result = verify_fields_exist(payload, 'query', 'context') or model(question=query, context=payload.get('context'))

    elif command == PARAPHRASE_MINING:
        result = verify_fields_exist(payload, 'titles') or util.paraphrase_mining(model, payload.get('titles'))

    elif command == DEFAULT:
        return handle_command(model, get_default_command(settings.MODEL_TYPE), payload)

    else:
        return error('Unknown command provided')

    return ok(result)


async def server_loop(q):
    model = get_model()
    while True:
        command, payload, response_q = await q.get()
        try:
            out = handle_command(model, command, payload)
        except Exception as e:
            logger.exception('Error while handling command')
            out = error('Could not process command')

        await response_q.put(out)
