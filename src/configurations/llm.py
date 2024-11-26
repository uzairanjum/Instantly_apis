
from openai import OpenAI
import json
from src.common.logger import get_logger
from src.settings import settings
logger = get_logger("LLM")



class OpenAiConfig():

    def __init__(self ):

        self.client = OpenAI(api_key = settings.OPENAI_API_KEY ,max_retries = 3)

    def generate_response(self, messages:list,model:str= "gpt-4o", max_tokens:int = 600, temperature:int = 0):
        try:
            response = self.client.chat.completions.create(model = model, messages = messages,  max_tokens = max_tokens, temperature = temperature)
            completion_tokens = response.usage.completion_tokens
            prompt_tokens = response.usage.prompt_tokens
            return response.choices[0].message.content, completion_tokens, prompt_tokens
        except Exception as e:
            return False
        
    def generate_response_using_tools(self,all_messages: list, model:str= "gpt-4o", max_tokens:int = 600, temperature:int = 0, response_tool:dict = {}):
        try:
            response = self.client.chat.completions.create(model=model ,messages=all_messages, temperature=temperature, max_tokens=max_tokens,tools=response_tool.get('tools'),tool_choice=response_tool.get('tool_choice'))
      
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            if not tool_calls:
                return {}
            response_ = json.loads(tool_calls[0].function.arguments)
            return response_
        except Exception as e:
            logger.error("openai response error %s",e)
            return False
        

