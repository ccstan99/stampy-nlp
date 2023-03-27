from starlette.routing import Route
from sentence_transformers import SentenceTransformer, util

from model_server.model_types.base_model import ModelType, handler, verify_fields_exist
from model_server.consts import ENCODE, PARAPHRASE_MINING


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
        if self.default_action == ENCODE:
            return await self.encode(request)
        elif self.default_action == PARAPHRASE_MINING:
            return await self.paraphrase_mining(request)
        else:
            return self.error('No valid default action provided')

    def routes(self):
        return [
            Route("/encoding", self.encode, methods=["POST"]),
            Route("/paraphrase_mining", self.paraphrase_mining, methods=["POST"]),
        ]
