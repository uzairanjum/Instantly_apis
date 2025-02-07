
from openai import OpenAI
import json
from src.common.logger import get_logger
from src.settings import settings
logger = get_logger("LLM")



class OpenAiConfig():

    def __init__(self, open_api_key: str):

        if not open_api_key:
             raise ValueError("Missing OpenAI API Key in settings.")

        try:
            self.client = OpenAI(api_key = open_api_key, max_retries = 3)
        except Exception as e:
            logger.error(f" OpenAiConfig configuration error :: {e}")



    def generate_response(self, messages:list,model:str= "gpt-4o-mini", max_tokens:int = 600, temperature:int = 0):
        try:
            response = self.client.chat.completions.create(model = model, messages = messages,  max_tokens = max_tokens, temperature = temperature)
            logger.info(f" OpenAiConfig response :: {response}")
            completion_tokens = response.usage.completion_tokens
            prompt_tokens = response.usage.prompt_tokens
            return response.choices[0].message.content, completion_tokens, prompt_tokens
        except Exception as e:
            logger.error(f" OpenAiConfig response error :: {e}")
            return False
        
    def generate_response_using_tools(self,all_messages: list, model:str= "gpt-4o-mini", max_tokens:int = 600, temperature:int = 0, response_tool:dict = {}):
        try:
            response = self.client.chat.completions.create(model=model ,messages=all_messages, temperature=temperature, max_tokens=max_tokens,tools=response_tool.get('tools'),tool_choice=response_tool.get('tool_choice'))
            logger.info(f" OpenAiConfig response using tools:: {response}")
      
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            if not tool_calls:
                return {}
            response_ = json.loads(tool_calls[0].function.arguments)
            return response_
        except Exception as e:
            logger.error(f" OpenAiConfig response error :: {e}")
            return False
        


