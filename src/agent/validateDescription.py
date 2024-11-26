

from src.configurations.llm import OpenAiConfig
from src.common.logger import get_logger
from src.common.utils import trueOrFalse
from src.common.models import ValidateDescriptionResponse
logger = get_logger("Validate Description")

openai = OpenAiConfig()


validate_tool = {
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
                "yes",
                "no",
              ],
              "type": "string",
              "description": "validate the course description is correct or not"
            }
          }
        },
        "description": "Analyze the course description and determine if it is correct or not"
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




def validate_description_agent(course_code, course_description, open_ai_model):
    try:  
        messages = [{
            "role": "user",
            "content": f"""
                You are an academic course verification assistant. Your job is to verify if the provided course description matches the actual 
                course offered by the specified institution. 

                A course description must include a detailed summary of the course, including its objectives, topics covered, prerequisites, and relevance to the curriculum.
            
                if not then return false

                Here’s the course details:
                course_code: {course_code}
                course_description: {course_description}
            """
        }]

        

        response = openai.generate_response_using_tools(messages=messages, model=open_ai_model, response_tool=validate_tool)
        return trueOrFalse(response.get('answer'))

    except Exception as e:  
        logger.error(f"Error in validate description agent: {e}")  
        return False
