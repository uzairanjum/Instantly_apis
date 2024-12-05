

from src.common.logger import get_logger
from src.common.models import PackbackCourseQuestionsResponse, QuestionGeneratorRequest, TenQuestionsGeneratorRequest, PackbackTenQuestionsRequest,PackbackCourseDescriptionRequest,PackbackCourseDescriptionResponse
import requests
from typing import Union
from src.agent.fourQuestion import four_questions_agent
from src.agent.tenQuestion import ten_questions_agent
from src.agent.validateDescription import validate_description_agent
from src.settings import settings
from src.common.utils import calculate_gpt4o_mini_cost,calculate_gpt4o_cost
from src.configurations.instructor import ExtractOpenAI

logger = get_logger("PACKBACK_CONFIG")
import time



class PackbackConfig:
    def __init__(self):
        pass

   
    
    def packback_four_questions(self, request: PackbackCourseDescriptionRequest) -> Union[PackbackCourseQuestionsResponse, None]:
        course_description_response = self.packback_course_description(request)
        if course_description_response:
            return self.four_questions_generator(QuestionGeneratorRequest(course_name=course_description_response.course_name, course_description=course_description_response.course_description, open_ai_model=request.open_ai_model, total_completion_tokens=course_description_response.total_completion_tokens, total_prompt_tokens=course_description_response.total_prompt_tokens))
        return None

    def packback_ten_questions(self, request: PackbackTenQuestionsRequest) -> Union[PackbackCourseQuestionsResponse, None]:
        course_description_response = self.packback_course_description(request)
        if course_description_response:
            return self.ten_questions_generator(TenQuestionsGeneratorRequest(course_name=course_description_response.course_name, \
                course_description=course_description_response.course_description, open_ai_model=request.open_ai_model, \
                question1=request.question1, question2=request.question2, question3=request.question3, question4=request.question4))
        return None

    def four_questions_generator(self, request: QuestionGeneratorRequest) -> Union[PackbackCourseQuestionsResponse, None]:
        try:
            if request.course_name and request.course_description:
                completion_tokens = request.total_completion_tokens
                prompt_tokens = request.total_prompt_tokens
                questions_response = four_questions_agent(request.course_name, request.course_description, request.open_ai_model)
                completion_tokens += questions_response.total_completion_tokens
                prompt_tokens += questions_response.total_prompt_tokens
                cost = 0
                if request.open_ai_model == "gpt-4o-mini":
                    cost = calculate_gpt4o_mini_cost(prompt_tokens, completion_tokens)
                return PackbackCourseQuestionsResponse(course_name=request.course_name, course_description=request.course_description, questions=questions_response.questions, total_completion_tokens=completion_tokens, total_prompt_tokens=prompt_tokens, open_ai_model=request.open_ai_model, token_cost=f'${cost}')
        except Exception as e:
            logger.error(f"Error processing packback four questions request: {e}")
            return None  
           
    def ten_questions_generator(self, request: TenQuestionsGeneratorRequest) -> Union[PackbackCourseQuestionsResponse, None]:
        try:
            if request.course_name and request.course_description:
                completion_tokens = request.total_completion_tokens
                prompt_tokens = request.total_prompt_tokens
                questions_response = ten_questions_agent(request.course_name, request.course_description, request.question1, \
                                            request.question2, request.question3, request.question4, request.open_ai_model)
                completion_tokens += questions_response.total_completion_tokens
                prompt_tokens += questions_response.total_prompt_tokens
                cost = 0
                if request.open_ai_model == "gpt-4o-mini":
                    cost = calculate_gpt4o_mini_cost(prompt_tokens, completion_tokens)
                return PackbackCourseQuestionsResponse(course_name=request.course_name, course_description=request.course_description, questions=questions_response.questions, total_completion_tokens=completion_tokens, total_prompt_tokens=prompt_tokens, open_ai_model=request.open_ai_model, token_cost=f'${cost}')
        except Exception as e:
            logger.error(f"Error processing packback ten questions request: {e}")
            return None   

    def packback_course_description(self, request: PackbackCourseDescriptionRequest) -> Union[PackbackCourseDescriptionResponse, None]:
        try:
            query_templates = [
                # f"{request.professor_name} {request.course_code} {request.university_name} syllabus course description",
                f"{request.course_code} {request.university_name} course outline and description",
                f"{request.course_code} detailed syllabus and objectives"
            ]
            for idx, query in enumerate(query_templates):
                response = self.call_search_url_api(query, request.open_ai_model)
                logger.info(f"response :: {idx+1}")
                if not response:
                    continue
                course_name = None
                course_description = None

                if not response.get('completedObjectives'):
                    continue

                for objective in response.get('completedObjectives'):
                    if objective.get('objective') == "course_name":
                        course_name = objective.get('value')
                    elif objective.get('objective') == "course_description":
                        course_description = objective.get('value')
                        break

                if course_name and course_description:
                   validate_description_response = validate_description_agent(request.course_code , course_description,request.open_ai_model)
                   if not validate_description_response:
                       continue
                   return PackbackCourseDescriptionResponse(course_name=course_name, course_description=course_description, total_completion_tokens=response.get('total_completion_tokens'), total_prompt_tokens=response.get('total_prompt_tokens'), open_ai_model=request.open_ai_model)
        except Exception as e:
            logger.error(f"Error processing packback course description request: {e}")
            return None
    

    def call_search_url_api(self, query, open_ai_model, max_attempts=1, retry_delay=1):
        url = "https://search-and-crawl-k2jau.ondigitalocean.app/gepeto/search-url-v2"
        # url = "http://127.0.0.1:8000/gepeto/search-url-v2"
        attempts = 0
        headers = {
            "x-api-key": settings.PACKBACK_API_KEY,  
            "Content-Type": "application/json" 
        }
        payload = {
            "searchStatement": query,
            "objectives": [
                   {
                    "name": "course_name",
                    "type": "string",
                    "description": "The official name or title of the course as listed in the institution's catalog(short name)."
                    },
                    {
                    "name": "course_description",
                    "type": "string",
                    "description": "A detailed summary of the course, including its objectives, topics covered and relevance to the curriculum."
                    }
            ],
            "maxIterations": 2,
            "verboseMode": False,
            "open_ai_model": open_ai_model

        }

        while attempts < max_attempts:
            try:
                logger.info(f"Attempt {attempts + 1} to call {url}")
                response = requests.post(url, json=payload, headers=headers, timeout=600)
                response.raise_for_status()  # Raise an exception for HTTP errors

                logger.info(f"API call successful: {response.status_code}")
                return response.json()  # Return the response JSON
            except requests.exceptions.RequestException as e:
                logger.error(f"Attempt {attempts + 1} failed: {e}")
                attempts += 1
                if attempts < max_attempts:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)

        logger.error(f"All {max_attempts} attempts to call the API failed.")
        return None
