import asyncio
from json import JSONDecodeError
from starlette.responses import JSONResponse
from starlette.routing import Route

from model_server import settings


def verify_fields_exist(*fields):
    """A decorator that checks that the given `fields` are in the send JSON object."""
    def verifier_wrapper(fn):
        # It is assumed that this is going to be used to decorate a handler method, which has
        # this signature
        async def verify(self, payload):
            missing = [field for field in fields if not payload.get(field)]
            if missing:
                return {'error': 'Missing fields in payload', 'missing': missing}, 400
            return await fn(self, payload)
        return verify
    return verifier_wrapper


def handler(fn):
    """Decorate a class method so that it will handle JSON objects."""
    async def handler_fn(self, request):
        try:
            payload = await request.json()
        except JSONDecodeError:
            return JSONResponse({'error': 'invalid JSON provided'}, status_code=400)

        output, status = await fn(self, payload)
        return JSONResponse(output, status_code=status)
    return handler_fn


class ModelType:
    @staticmethod
    def error(text, error_code=400):
        return {'error': text}, error_code

    @staticmethod
    def ok(contents):
        return contents, 200

    def default(self, request):
        raise NotImplementedError('No default route provided')

    def routes(self):
        raise NotImplementedError('Routes must be provided')
