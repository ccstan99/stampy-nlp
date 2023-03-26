import asyncio
from json import JSONDecodeError
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from transformers import pipeline

from model_server import settings
from model_server.handler import server_loop


def handler(command):
    """Make a command specific handler."""
    async def handle(request):
        try:
            payload = await request.json()
        except JSONDecodeError:
            return JSONResponse({'error': 'invalid JSON provided'}, status_code=400)

        # The model should only be loaded into memory once, seeing it's large.
        # Use a queue to send/receive messages from it.
        response_q = asyncio.Queue()
        await request.app.model_queue.put((command, payload, response_q))
        output, status = await response_q.get()
        return JSONResponse(output, status_code=status)

    return handle


routes = [
    Route("/", handler(settings.DEFAULT), methods=["POST"]),
    Route("/encoding", handler(settings.ENCODE), methods=["POST"]),
    Route("/question_answering", handler(settings.QUESTION_ANSWERING), methods=["POST"]),
    Route("/paraphrase_mining", handler(settings.PARAPHRASE_MINING), methods=["POST"]),
]


app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
)


@app.on_event('startup')
async def startup_event():
    """Make sure the event loop gets initialized and the model loaded."""
    q = asyncio.Queue()
    app.model_queue = q
    asyncio.create_task(server_loop(q))
