"""OpenAI Functions

Call OpenAI ChatGPT API.
"""
import openai
import logging
from stampy_nlp.settings import get_openai_key


MODEL = 'gpt-3.5-turbo'
SYSTEM_MSG = "You are a patient and helpful AI safety research assistant. You use a tone that is technical and scientific."
PREFIX_MSG = """Given the following links to resources, extracted parts of longer documents, and a question at the end, create a final answer using the links and content provided. 
    If you don't know the answer, just say that you don't know. Don't try to make up an answer."""
CONSTRAIN_MSG = "Do not add information from outside content."
openai.api_key = get_openai_key()


def generate_answer(query: str, sources: str, past_user_msgs=[], past_generated_msgs=[], max_history: int = 0, constrain: bool = False):
    logging.debug("generate_answer()")

    messages = [{"role": "system", "content": SYSTEM_MSG}]
    num_history = min(len(past_user_msgs), max_history)
    for i in range(-1 * num_history, 0, 1):
        messages.append({"role": "user", "content": past_user_msgs[i]})
        messages.append(
            {"role": "assistant", "content": past_generated_msgs[i]})

    CONTENT = PREFIX_MSG
    if constrain:
        CONTENT += CONSTRAIN_MSG
    CONTENT += sources

    CONTENT += f"\n\nQUESTION: {query}"
    CONTENT += "\n\nFINAL ANSWER:"

    # generated_text = sources
    messages.append({"role": "user", "content": CONTENT})
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages,
        temperature=0,
    )

    generated_text = (response['choices'][0]['message']['content'])
    logging.debug("\n\nmessages %s", messages)
    return generated_text
