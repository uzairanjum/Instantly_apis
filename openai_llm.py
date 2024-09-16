
from openai import OpenAI


class OpenAiConfig():

    def __init__(self, OPENAI_API_KEY ):

        self.client = OpenAI(api_key = OPENAI_API_KEY ,max_retries = 3)

    def generate_response(self, messages:list, model:str, max_tokens:int = 600, temperature:int = 0):
        try:
            response = self.client.chat.completions.create(model = model, messages = messages,  max_tokens = max_tokens, temperature = temperature)
            return response.choices[0].message.content
        except Exception as e:
            return False
