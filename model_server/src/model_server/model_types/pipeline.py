from starlette.routing import Route
from transformers import pipeline

from model_server.consts import QUESTION_ANSWERING
from model_server.model_types.base_model import ModelType, handler, verify_fields_exist


class Pipeline(ModelType):

    def __init__(self, model_path, model_type='question-answering', tokenizer=None):
        self.model = pipeline(model_type, model=model_path, tokenizer=tokenizer or model_path)

    @handler
    @verify_fields_exist('query', 'context')
    async def question_answering(self, payload):
        result = self.model(question=payload.get('query'), context=payload.get('context'))
        return self.ok(result)

    async def default(self, request):
        return await self.question_answering(request)

    def routes(self):
        return [
            Route("/question_answering", self.question_answering, methods=["POST"])
        ]
