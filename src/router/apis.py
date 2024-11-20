from fastapi import APIRouter
from src.common.logger import get_logger
from src.common.utils import get_weekly_summary_report, insert_many_domain_health
from src.common.models import GenerateEmailsRequest, GenerateEmailsResponse
import time


logger = get_logger("Api")
instantly_api_router = APIRouter()




@instantly_api_router.get('/weekly-summary')
def weekly_summary(campaign_id: str, client_name: str):
    return get_weekly_summary_report(campaign_id, client_name.lower())




@instantly_api_router.post(
    '/generate-emails',
    summary="Generate a list of emails based on provided integer and string",
    response_model=GenerateEmailsResponse,
    responses={
        200: {"description": "Emails generated successfully"},
        400: {"description": "Invalid input"},
    }
)
async def generate_emails(request: GenerateEmailsRequest):
    """
    Endpoint to generate a specified number of emails based on input string.
    """
    logger.info(f"Generating {request.count} emails with base_str='{request.client_name}'")
    timestamp = int(time.time())
    emails = []
    all_domains = []
    for i in range(request.count):
        mailboxId = f"uqarni-{request.client_name}{i+1}{timestamp}"
        data = {"mailboxId": mailboxId, "status": False , "client_name" : request.client_name}
        all_domains.append(data)
        emails.append(f"{mailboxId}@srv1.mail-tester.com")
        # insert_domain(data)
    # insert_many_domain_health(all_domains)

    chunk_size = 20
    for start in range(0, len(all_domains), chunk_size):
        end = start + chunk_size
        chunk = all_domains[start:end]
        insert_many_domain_health(chunk)

    logger.info("Email generation completed successfully.")
    return GenerateEmailsResponse(emails=emails)
