
from openai import OpenAI
import json
from src.common.logger import get_logger
logger = get_logger("LLM")

response_tool = {
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "response",
        "parameters": {
          "type": "object",
          "required": [
            "answer"
          ],
          "properties": {
            "answer": {
              "enum": [
                "Interested",
                "NotInterested",
                "OutOfOffice",
                "Unsubscribe"
              ],
              "type": "string",
              "description": "interested if lead is interested, not interested if lead is not interested, out of office if lead is out of office or leaves, unsubscribe if lead requests to be removed from the contact list"
            }
          }
        },
        "description": "Analyze the conversation and determine lead status"
      }
    }
  ],
  "tool_choice": {
    "type": "function",
    "function": {
      "name": "response"
    }
  }
}


class OpenAiConfig():

    def __init__(self, OPENAI_API_KEY ):

        self.client = OpenAI(api_key = OPENAI_API_KEY ,max_retries = 3)

    def generate_response(self, messages:list,model:str= "gpt-4o", max_tokens:int = 600, temperature:int = 0):
        try:
            response = self.client.chat.completions.create(model = model, messages = messages,  max_tokens = max_tokens, temperature = temperature)
            return response.choices[0].message.content
        except Exception as e:
            return False
        
    def generate_response_using_tools(self,all_messages: list, model:str= "gpt-4o", max_tokens:int = 600, temperature:int = 0, ):
        try:
            response = self.client.chat.completions.create(model=model ,messages=all_messages, temperature=temperature, max_tokens=max_tokens,tools=response_tool.get('tools'),tool_choice=response_tool.get('tool_choice'))
      
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            if not tool_calls:
                return {}
            response_ = json.loads(tool_calls[0].function.arguments)
            return response_.get('answer')
        except Exception as e:
            logger.error("openai response error %s",e)
            return False
        

