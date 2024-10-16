from src.configurations.instantly import InstantlyAPI
import json
from src.configurations.llm import OpenAiConfig
from datetime import datetime
from src.settings import settings
from src.common.logger import get_logger
from src.common.prompts import packback_prompt

# campaign_id = "ecdc673c-3d90-4427-a556-d39c8b69ae9f"


instantly = InstantlyAPI(api_key=settings.INSTANTLY_API_KEY)
open_ai = OpenAiConfig(settings.OPENAI_API_KEY)
logger = get_logger("Utils")


def format_email_history(all_emails: list):

    message_history: list = []
    lead_reply = False
    last_timestamp = None 
    from_account = None
    incoming_count = 0
    outgoing_count = 0
    first_reply_after = 0
    lead_status = get_status(all_emails[0].get('i_status'))
    all_emails.reverse() 
    last_timestamp = all_emails[0].get('timestamp_created')
    for message in all_emails:
        if message['from_address_email'] == message['eaccount']:
            from_account = message['eaccount']
            role = 'assistant'
            outgoing_count += 1
        else:
            lead_reply = True
            role = 'user'
            incoming_count += 1
        
        if not lead_reply:
            first_reply_after = outgoing_count

        # Check for 'body.text' first, then use 'body.html' directly if 'text' is not found
        text_content = message.get('body', {}).get('text')
        if text_content:
            content = text_content.strip()
        else:
            # Fallback to 'body.html' if 'text' is not found
            html_content = message.get('body', {}).get('html')
            if html_content:
                content = html_content.strip()  # Use the raw HTML content
            else:
                content = ''
        
        message_history.append({"role": role, "timestamp": message.get('timestamp_created'), "subject": message.get('subject'),"content": content })
    return message_history ,lead_reply, last_timestamp,  from_account, incoming_count, outgoing_count, lead_status, first_reply_after

def get_status(value):
    status_mapping = {
        None: "Lead",
        1: "Interested",
        2: "Meeting Booked",
        3: "Meeting Completed",
        4: "Won",
        0: "Out of Office",
        -1 : "Not Interested",
        -2: "Wrong Person",
        -3:"Lost"
    }
    return status_mapping.get(value, "Lead")

def get_lead_details_history_for_csv(lead_email: str, university_name: str, campaign_id: str, index: int):
    response = ''
    logger.info(f"Processing lead - {index + 1} - {lead_email}")
    all_emails = instantly.get_all_emails(lead=lead_email, campaign_id=campaign_id)
    if not all_emails:
        return None
    message_history ,lead_reply, last_timestamp, from_email, incoming_count, outgoing_count ,lead_status= format_email_history(all_emails)
    if lead_reply:
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in message_history]
        formatted_history = [{"role": "system", "content": packback_prompt}, *ai_message_history]
        response = open_ai.generate_response_using_tools(formatted_history)
    timestamp = datetime.now().isoformat()
    data = {"lead_email": lead_email, "university_name": university_name, "sent_date": last_timestamp, "lead_status": lead_status, "reply": lead_reply, "status": response, "outgoing": outgoing_count, "incoming": incoming_count,  "from_account": from_email,"conversation": json.dumps(message_history), "updated_at":timestamp }
    return data

def get_lead_details_history(lead_email: str, university_name: str,campaign_id,  all_emails: list):
    response = ''
    logger.info(f"Processing lead - {lead_email}")
    timestamp = datetime.now().isoformat()
    message_history ,lead_reply, last_timestamp, from_email, incoming_count, outgoing_count ,lead_status, first_reply_after= format_email_history(all_emails)
    if lead_reply:
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in message_history]
        formatted_history = [{"role": "system", "content": packback_prompt}, *ai_message_history]
        response = open_ai.generate_response_using_tools(formatted_history)
    
    data = {"lead_email": lead_email, "university_name": university_name, "sent_date": last_timestamp, "lead_status": lead_status, "reply": lead_reply, "status": response, "outgoing": outgoing_count, "incoming": incoming_count,  "from_account": from_email,"conversation": message_history, "updated_at":timestamp, "campaign_id": campaign_id, "first_reply_after":first_reply_after }
    return data
