from fastapi import APIRouter
from src.common.logger import get_logger
from src.common.utils import get_weekly_summary_report
from src.common.models import GenerateEmailsRequest, GenerateEmailsResponse
import time


logger = get_logger("Api")
instantly_api_router = APIRouter()




@instantly_api_router.get('/weekly-summary')
def weekly_summary(campaign_id: str, client_name: str):
    return get_weekly_summary_report(campaign_id, client_name.lower())



