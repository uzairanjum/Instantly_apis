from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
from src.common.logger import get_logger

from src.core.packback import PackbackConfig
from src.common.models import PackbackCourseDescriptionRequest,PackbackCourseDescriptionResponse,PackbackCourseQuestionsResponse,PackbackTenQuestionsRequest
import time
from typing import Union
logger = get_logger("Packback-Router")

packback_router = APIRouter()


@packback_router.post('/packback-four-questions')
def packback_four_questions(request: PackbackCourseDescriptionRequest) -> Union[PackbackCourseQuestionsResponse, None]:
    try:
        logger.info(f"Request: {request}")
        packback_config = PackbackConfig()
        return packback_config.packback_four_questions(request)
    except Exception as e:
        logger.error(f"Error processing packback four questions request: {e}")
        return JSONResponse(content={"status": "error", "message": "Internal server error"}, status_code=500)

@packback_router.post('/packback-course-description')
def packback_course_description(request: PackbackCourseDescriptionRequest) -> Union[PackbackCourseDescriptionResponse, None]:
    try:
        logger.info(f"Request: {request}")
        packback_config = PackbackConfig()
        result = packback_config.packback_course_description(request)
        return result
    except Exception as e:
        logger.error(f"Error processing packback course description request: {e}")
        return JSONResponse(content={"status": "error", "message": "Internal server error"}, status_code=500)

@packback_router.post('/packback-ten-questions')
def packback_ten_questions(request: PackbackTenQuestionsRequest)-> Union[PackbackCourseQuestionsResponse, None]:
    try:
        logger.info(f"Request: {request}")
        packback_config = PackbackConfig()
        return packback_config.packback_ten_questions(request)
    except Exception as e:
        logger.error(f"Error processing packback ten questions request: {e}")
        return JSONResponse(content={"status": "error", "message": "Internal server error"}, status_code=500)