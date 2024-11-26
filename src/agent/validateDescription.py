

from src.configurations.llm import OpenAiConfig
from src.common.logger import get_logger
from src.common.models import ValidateDescriptionResponse
logger = get_logger("Validate Description")

openai = OpenAiConfig()


def validate_description_agent(course_code, university_name, course_description, open_ai_model):
    try:  
        messages = [{
            "role": "system",
            "content": f"""
                You are an academic course verification assistant. Your job is to verify if the provided course description matches the actual 
                course offered by the specified institution. 
                Use the official course catalog, website, or other reliable sources to validate the information.
                If the description does not match or you cannot find the course, indicate that the description could not be verified and suggest 
                consulting the institution directly for accuracy.


                Here’s the course details:
                course_code: {course_code}
                university_name: {university_name}
                course_description: {course_description}


            """
        }]

        
        try:
            response ,completion_tokens, prompt_tokens= openai.generate_response(messages=messages, model=open_ai_model)
        except Exception as e:
            logger.error(f"Error in ten_questions response agent: {e}")
            return None, 0,0

        return ValidateDescriptionResponse(course_description=response, total_completion_tokens=completion_tokens, total_prompt_tokens=prompt_tokens)

    except Exception as e:  
        logger.error(f"Error in ten_questions_agent: {e}")  
        return None,0,0
