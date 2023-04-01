from starlette.routing import Route
from sentence_transformers import SentenceTransformer, util

from model_server.model_types.base_model import ModelType, handler, verify_fields_exist


class Encoder(ModelType):

    def __init__(self, model_path, default_action):
        self.default_action = default_action
        self.model = SentenceTransformer(model_path)

    @handler
    @verify_fields_exist('query')
    async def encode(self, payload):
        query = payload.get('query')
        return self.ok(self.model.encode(query).tolist())

    @handler
    @verify_fields_exist('titles')
    async def paraphrase_mining(self, payload):
        return self.ok(util.paraphrase_mining(self.model, payload.get('titles')))

    async def default(self, request):
        return await self.encode(request)

    def routes(self):
        return [
            Route("/encoding", self.encode, methods=["POST"]),
            Route("/paraphrase_mining", self.paraphrase_mining, methods=["POST"]),
        ]
