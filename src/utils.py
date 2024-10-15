from src.instantly import InstantlyAPI
import json
from src.llm import OpenAiConfig
from datetime import datetime
from src.settings import settings


# campaign_id = "ecdc673c-3d90-4427-a556-d39c8b69ae9f"


instantly = InstantlyAPI(api_key=settings.INSTANTLY_API_KEY)
open_ai = OpenAiConfig(settings.OPENAI_API_KEY)



def format_email_history(all_emails: dict):
    message_history: list = []
    lead_reply = False
    last_timestamp = None 
    from_account = None
    incoming_count = 0
    outgoing_count = 0
    lead_status = get_status(all_emails[0].get('i_status'))
    for message in all_emails:
        if message['from_address_email'] == message['eaccount']:
            from_account = message['eaccount']
            role = 'assistant'
            outgoing_count += 1
        else:
            lead_reply = True
            role = 'user'
            incoming_count += 1
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
        
        message_history.append({"role": role, "content": content})
        last_timestamp = message.get('timestamp_created')
    message_history.reverse()
    return message_history ,lead_reply, last_timestamp,  from_account, incoming_count, outgoing_count, lead_status

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
    print(f"Processing lead - {index + 1} - {lead_email}")
    all_emails = instantly.get_all_emails(lead=lead_email, campaign_id=campaign_id)
    if not all_emails:
        return None
    message_history ,lead_reply, last_timestamp, from_email, incoming_count, outgoing_count ,lead_status= format_email_history(all_emails)
    if lead_reply:
        prompt = """
                You are Steve, a digital assistant tasked with analyzing lead emails to determine their status based on content and tone. Classify each email as Interested, Not Interested, or Out of Office based on the message content. Use the following guidelines and examples for each classification:

                Interested: The lead expresses interest in the product or service, indicates a willingness to continue the conversation, or asks for additional details.

                Interested Example messages:
                "user":"Sure. Thanks."
                "user":"I appreciate your contact. Could you give me a price estimate for a single instructor?"
                "user":"I'm intrigued to hear more."
                "user":"Can we set up a time in the week of 10/22?"
                "user":"I would love to know how other professors are incorporating AI."
                ""
                
                
                
                Not Interested: The lead explicitly states they are not interested, requests to be removed from the contact list, or declines the offer.

                Not Interested Example messages:
                "user":"I already indicated that I am not interested."
                "user":"Please remove me from your list."
                "user":"I’m not interested. Please discontinue these emails."
                "user":"We are not interested at this time."
                "user":"Thank you, but no."
                "user":""
                
                
                
                Out of Office: The lead indicates they are unavailable, either by being out of the office, on leave, or providing an alternative contact due to their absence.

                Out of Office Example messages:
                "user":"I am on sabbatical during the fall 2024 semester."
                "user":"I will be out of the office 12-19 October."
                "user":"I am out of the office at the ACCP annual meeting and will return on 10/16."
                "user":"I am on sabbatical leave till the end of 2024."
                Provide a concise classification output based on this analysis by selecting one of the following responses: Interested, Not Interested, or Out of Office.
                                
                """
        formatted_history = [{"role": "system", "content": prompt}, *message_history]
        response = open_ai.generate_response_using_tools(formatted_history)
    timestamp = datetime.now().isoformat()
    data = {"lead_email": lead_email, "university_name": university_name, "sent_date": last_timestamp, "lead_status": lead_status, "reply": lead_reply, "status": response, "outgoing": outgoing_count, "incoming": incoming_count,  "from_account": from_email,"conversation": json.dumps(message_history), "updated_at":timestamp }
    return data


def get_lead_details_history(lead_email: str, university_name: str, all_emails: list,):
    response = ''
    print(f"Processing lead - {lead_email}")
    timestamp = datetime.now().isoformat()
    message_history ,lead_reply, last_timestamp, from_email, incoming_count, outgoing_count ,lead_status= format_email_history(all_emails)
    if lead_reply:
        prompt = """
                You are Steve, a digital assistant tasked with analyzing lead emails to determine their status based on content and tone. Classify each email as Interested, Not Interested, or Out of Office based on the message content. Use the following guidelines and examples for each classification:

                Interested: The lead expresses interest in the product or service, indicates a willingness to continue the conversation, or asks for additional details.

                Interested Example messages:
                "user":"Sure. Thanks."
                "user":"I appreciate your contact. Could you give me a price estimate for a single instructor?"
                "user":"I'm intrigued to hear more."
                "user":"Can we set up a time in the week of 10/22?"
                "user":"I would love to know how other professors are incorporating AI."
                ""
                
                
                
                Not Interested: The lead explicitly states they are not interested, requests to be removed from the contact list, or declines the offer.

                Not Interested Example messages:
                "user":"I already indicated that I am not interested."
                "user":"Please remove me from your list."
                "user":"I’m not interested. Please discontinue these emails."
                "user":"We are not interested at this time."
                "user":"Thank you, but no."
                "user":""
                
                
                
                Out of Office: The lead indicates they are unavailable, either by being out of the office, on leave, or providing an alternative contact due to their absence.

                Out of Office Example messages:
                "user":"I am on sabbatical during the fall 2024 semester."
                "user":"I will be out of the office 12-19 October."
                "user":"I am out of the office at the ACCP annual meeting and will return on 10/16."
                "user":"I am on sabbatical leave till the end of 2024."
                Provide a concise classification output based on this analysis by selecting one of the following responses: Interested, Not Interested, or Out of Office.
                                
                """
        formatted_history = [{"role": "system", "content": prompt}, *message_history]
        response = open_ai.generate_response_using_tools(formatted_history)
    
    data = {"lead_email": lead_email, "university_name": university_name, "sent_date": last_timestamp, "lead_status": lead_status, "reply": lead_reply, "status": response, "outgoing": outgoing_count, "incoming": incoming_count,  "from_account": from_email,"conversation": json.dumps(message_history), "updated_at":timestamp }
    return data
