

from src.common.logger import get_logger
from src.common.models import PackbackCourseQuestionsResponse, QuestionGeneratorRequest, TenQuestionsGeneratorRequest, PackbackTenQuestionsRequest,PackbackCourseDescriptionRequest,PackbackCourseDescriptionResponse
import requests
from typing import Union
from src.agent.fourQuestion import four_questions_agent
from src.agent.tenQuestion import ten_questions_agent
from src.settings import settings
logger = get_logger("PACKBACK_CONFIG")
import time



class PackbackConfig:
    def __init__(self):
        pass

   
    
    def packback_four_questions(self, request: PackbackCourseDescriptionRequest) -> Union[PackbackCourseQuestionsResponse, None]:
        course_description_response = self.packback_course_description(request)
        if course_description_response:
            return self.four_questions_generator(QuestionGeneratorRequest(course_name=course_description_response.course_name, course_description=course_description_response.course_description, open_ai_model=request.open_ai_model))
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
                questions = four_questions_agent(request.course_name, request.course_description, request.open_ai_model)
                return PackbackCourseQuestionsResponse(course_name=request.course_name, course_description=request.course_description, questions=questions.questions)
        except Exception as e:
            logger.error(f"Error processing packback four questions request: {e}")
            return None  
           
    def ten_questions_generator(self, request: TenQuestionsGeneratorRequest) -> Union[PackbackCourseQuestionsResponse, None]:
        try:
            if request.course_name and request.course_description:
                questions = ten_questions_agent(request.course_name, request.course_description, request.question1, \
                                            request.question2, request.question3, request.question4, request.open_ai_model)
                return PackbackCourseQuestionsResponse(course_name=request.course_name, course_description=request.course_description, questions=questions.questions)
        except Exception as e:
            logger.error(f"Error processing packback ten questions request: {e}")
            return None   

    def packback_course_description(self, request: PackbackCourseDescriptionRequest) -> Union[PackbackCourseDescriptionResponse, None]:
        try:
            query_templates = [
                # f"{request.professor_name} {request.course_code} {request.university_name} syllabus course description",
                f"{request.course_code} {request.university_name} syllabus course description",
                f"{request.course_code} syllabus course description"
            ]
            for idx, query in enumerate(query_templates):
                response = self.call_search_url_api(query)
                logger.info(f"response :: {idx+1} ------------->>>: {response}")
                if not response:
                    continue
                course_name = None
                course_description = None
                for objective in response.get('completedObjectives'):
                    if objective.get('objective') == "course_name":
                        course_name = objective.get('value')
                    elif objective.get('objective') == "course_description":
                        course_description = objective.get('value')
                if course_name and course_description:
                   logger.info(f"Course Name: {course_name}")
                   logger.info(f"Course Description: {course_description}")
                   return PackbackCourseDescriptionResponse(course_name=course_name, course_description=course_description)
        except Exception as e:
            logger.error(f"Error processing packback course description request: {e}")
            return None

    def call_search_url_api(self, query, max_attempts=3, retry_delay=5):
        url = "https://search-and-crawl-k2jau.ondigitalocean.app/gepeto/search-url"
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
                    "description": "I need a course name or course title?"
                },
                {
                    "name": "course_description",
                    "type": "string",
                    "description": "I need a detailed course description?"
                }
            ],
            "maxIterations": 3,
            "verboseMode": False
        }

        while attempts < max_attempts:
            try:
                logger.info(f"Attempt {attempts + 1} to call {url}")
                response = requests.post(url, json=payload, headers=headers, timeout=60)
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