from src.configurations.instantly import InstantlyAPI
import json
from src.configurations.llm import OpenAiConfig
from datetime import datetime, timedelta
from src.settings import settings
from src.common.logger import get_logger
from src.common.prompts import packback_prompt
from src.common.models import WeeklyCampaignSummary
from src.database.supabase import SupabaseClient
from typing import Union
from src.configurations.googleSheet import GoogleSheetClient
import pandas as pd


instantly = InstantlyAPI(api_key=settings.INSTANTLY_API_KEY)
open_ai = OpenAiConfig(settings.OPENAI_API_KEY)
db = SupabaseClient()
gs_client = GoogleSheetClient()
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
    if not lead_reply:
        first_reply_after = 0
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
    
    data = {"lead_email": lead_email, "university_name": university_name, "sent_date": last_timestamp, "lead_status": lead_status, "reply": lead_reply, "status": response, "outgoing": outgoing_count, "incoming": incoming_count,  "from_account": from_email,"conversation": message_history, "updated_at":timestamp, "campaign_id": campaign_id, "first_reply_after":first_reply_after, "url" : f"https://mail-tester-frontend.vercel.app/conversation/{lead_email}" }
    return data




def get_weekly_summary_report(campaign_id: str, client_name: str) -> Union[WeeklyCampaignSummary, None]:
    response = instantly.get_campaign_details(campaign_id=campaign_id)
    if not response:
        return None
    positive_reply = db.get_count(campaign_id).count
    start_of_week, end_of_week = get_last_week_start_and_end_of_week()
    print("start", start_of_week, end_of_week)
    domain_health_count = db.get_domain_health_count(client_name,start_of_week, end_of_week).count
    domain_health = f"{domain_health_count}/252"
    week  = get_week_start_and_end_of_week()
    response = WeeklyCampaignSummary(**response.dict(), positive_reply=positive_reply, domain_health=domain_health, week = week)
    print("=res", response)
    return response


def get_last_week_start_and_end_of_week():
    today = datetime.now()
    # Calculate start of the previous week (Monday)
    start_of_last_week = today - timedelta(days=today.weekday() + 7)
    # Calculate end of the previous week (Sunday)
    end_of_last_week = start_of_last_week + timedelta(days=6)
    return start_of_last_week.date(), end_of_last_week.date()


def get_week_start_and_end_of_week():
    today = datetime.now()
    # Calculate start of the previous week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    # Calculate end of the previous week (Sunday)
    end_of_week = start_of_week + timedelta(days=6)
    week  = start_of_week.date().strftime("%m/%d/%Y") + " - " + end_of_week.date().strftime("%m/%d/%Y")
    return week


def get_daily_summary_report(campaign_id: str):
    today, start_time = last_24_hours_time()
    offset = 0  
    limit = 1000
    leads_array = []   
    while True:
        all_leads = db.get_last_twenty_four_records(campaign_id, start_time, today,offset=offset, limit=limit).data
        if len(all_leads) == 0: 
            break
        leads_array.extend(all_leads)
        offset += limit 
    logger.info("leads_array %s", len(leads_array))
    return leads_array

def last_24_hours_time():
    today = datetime.now()
    if today.weekday() == 0:  # Monday
        # If today is Monday, set the start to Friday
        start_time = today - timedelta(days=3)  # Go back to Friday
    elif today.weekday() == 5:  # Saturday
        start_time = today - timedelta(days=1)  # Go back to Friday
    elif today.weekday() == 6:  # Sunday
        start_time = today - timedelta(days=2)  # Go back to Friday
    else:
        start_time = today - timedelta(days=1)  # Normal case for other weekdays
    return today, start_time


def append_weekly_summary_report():
    worksheet = gs_client.open_sheet("Packback Summary", "weekly")
    data = get_weekly_summary_report("ecdc673c-3d90-4427-a556-d39c8b69ae9f", "packback")

    new_row = [
        f"{data.week}",  
        f"{data.total_leads}",                
        f"{data.contacted}",         
        f"{data.leads_who_replied}",              
        f"{data.positive_reply}",           
        f"{data.not_yet_contacted}",          
        f"{data.domain_health}"               
    ]
    logger.info("Weekly report data %s", new_row)

    try:
        worksheet.append_row(new_row)
    except Exception as e:
        logger.error(f"Error appending row: {e}")

def update_daily_summary_report():
    today, start_time = last_24_hours_time()
    campaign_id = "ecdc673c-3d90-4427-a556-d39c8b69ae9f"
    offset = 0  
    limit = 800
    leads_array = []   

    while True:
        all_leads = db.get_last_twenty_four_records(campaign_id, start_time, today,offset=offset, limit=limit).data
        if len(all_leads) == 0: 
            break

        worksheet = gs_client.open_sheet("Packback Summary", "daily")
        all_csv_records = gs_client.get_all_records(worksheet)
        dataframe = pd.DataFrame(all_csv_records)
      
        for index , lead in enumerate(all_leads):
            email_to_check = lead.get('lead_email')
            logger.info(f" {index +1} :: {email_to_check}")
            email_exists =None
            if len(all_csv_records) >0:
                email_exists = email_to_check in dataframe['Email'].values  # Assuming 'lead_email' is the column name

            if email_exists:
                logger.info(f"Email exists")
                columns = ["Email", "School Name", "Sent Date","Outgoing","Incoming","Reply","Status","From Account","Inbox Status","First Reply After","Conversation URL"]
                values = [ lead.get('lead_email'), lead.get('university_name'),lead.get('sent_date'),lead.get('outgoing'),lead.get('incoming'),lead.get('reply'),lead.get('status'),lead.get('from_account'),lead.get('lead_status'),lead.get('first_reply_after'),lead.get('url')]
                dataframe.loc[dataframe['Email'] == email_to_check, columns] = values  # Increment outgoing count
            else:
                logger.info(f"Email not exists")
                # Append a new row if the email does not exist
                data = { 
                    "Email" :lead.get('lead_email'),
                    "School Name": lead.get('university_name'),
                    "Sent Date":lead.get('sent_date'),
                    "Outgoing":lead.get('outgoing'),
                    "Incoming":lead.get('incoming'),
                    "Reply":lead.get('reply'),
                    "Status" :lead.get('status'),
                    "From Account":lead.get('from_account'),
                    "Inbox Status":lead.get('lead_status'),
                    "First Reply After":lead.get('first_reply_after'),
                    "Conversation URL":lead.get('url')
                }
                new_row = pd.DataFrame([data])  # Convert dict to DataFrame
                dataframe = pd.concat([dataframe, new_row], ignore_index=True) 


        dataframe = dataframe.fillna('') 
        gs_client.update_records(worksheet, dataframe)
        leads_array.extend(all_leads)
        offset += limit 

    logger.info("leads_array %s", len(leads_array))
