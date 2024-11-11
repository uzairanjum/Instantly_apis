from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
from src.common.logger import get_logger
from src.common.utils import get_weekly_summary_report, insert_many_domain_health
from pydantic import BaseModel, validator, Field
from typing import List
import time
logger = get_logger("Api")

instantly_api_router = APIRouter()




@instantly_api_router.get('/weekly-summary')
def weekly_summary(campaign_id: str, client_name: str):
    return get_weekly_summary_report(campaign_id, client_name.lower())



class GenerateEmailsRequest(BaseModel):
    count: int = Field(..., gt=0, description="Number of emails to generate")
    client_name: str = Field(..., min_length=3, max_length=50, description="Base string for email generation")

    @validator('client_name')
    def base_str_must_be_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('client_name must be alphanumeric')
        return v

class GenerateEmailsResponse(BaseModel):
    emails: List[str]

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

# @instantly_api_router.post('instantly/received', tags=['API'])
# def received_sms(data: dict):
#     try:
#         if data.get('event_type') == "reply_received":
#             instantly = InstantlyAPI(api_key="hxfec34ac1m9z0nk0s96z1den868")

#             # Get basic lead information from webhook payload
#             campaign_id = data.get('campaign_id')
#             lead_email = data.get('lead_email')
#             subject = data.get('reply_subject')
#             from_email = data.get('email_account')

#             if not all([campaign_id, lead_email, subject, from_email]):
#                 raise ValueError("Missing required fields in the payload")

#             # Generate message history by fetching all lead emails
#             all_emails = instantly.get_all_emails(lead=lead_email, campaign_id=campaign_id)
#             if not all_emails:
#                 raise ValueError("No emails found for the given lead and campaign")

#             message_history = format_email_history(all_emails)
#             latest_uuid = all_emails[0].get('id')

#             # Generate AI response
#             prompt = """    
#                         You are Steve, a digital assistant that helps set up appointments for their teammates at Packback. 
#                         Steve’s ultimate goal is to schedule appointments between prospects and Uzair by sending 
#                         emails to prospective customers for Packback. """
#             formatted_history = [{"role": "system", "content": prompt}, *message_history]
#             # response = open_ai.generate_response(formatted_history, "gpt-4o")

#             # Send AI response to lead
#             instantly.send_reply(uuid=latest_uuid, from_email=from_email, to_email=lead_email, message=response, subject=subject)

#             return JSONResponse(content={"status": "success", "message_history": message_history}, status_code=200)

#         return JSONResponse(content={"status": "ignored", "reason": "Event type not handled"}, status_code=200)

#     except ValueError as ve:
#         return JSONResponse(content={"status": "error", "message": str(ve)}, status_code=400)
#     except Exception as e:
#         return JSONResponse(content={"status": "error", "message": "Internal server error"}, status_code=500)



