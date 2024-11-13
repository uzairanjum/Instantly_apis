from src.configurations.instantly import InstantlyAPI
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
import re

open_ai = OpenAiConfig(settings.OPENAI_API_KEY)
db = SupabaseClient()
gs_client = GoogleSheetClient()
logger = get_logger("Utils")


def get_campaign_details(campaign_id:str) -> Union[tuple[str, str, str], None]:
    campaign_details = db.get_campaign_details(campaign_id)
    if campaign_details is None:
        return None, None, None, None
    campaign_name = campaign_details.data[0].get("campaign_name")
    organization_details = campaign_details.data[0].get("organizations")
    organization_name = organization_details.get('name')
    instantly_api_key = organization_details.get('api_key')
    return campaign_name, organization_name, instantly_api_key

def get_csv_details(campaign_id:str, summary_type:str) -> Union[tuple[str, str], None]:
    logger.info("get_csv_details %s - %s", campaign_id, summary_type)
    csv_details = db.get_csv_detail(campaign_id, summary_type)
    if len(csv_details.data) == 0:
        return None, None
    csv_name = csv_details.data[0].get('csv_name')
    worksheet_name = csv_details.data[0].get('worksheet_name')
    return csv_name, worksheet_name

def format_email_history(all_emails: list):

    message_history: list = []
    lead_reply = False
    last_timestamp = None 
    from_account = None
    incoming_count = 0
    outgoing_count = 0
    first_reply_after = 0
    message_uuid = None
    message_uuid = all_emails[0].get('id')
    lead_status = get_status(all_emails[0].get('i_status'))
    all_emails.reverse() 
    last_timestamp = all_emails[0].get('timestamp_created')
    cc =  ''
    bcc =  ''

    for message in all_emails:
        if message['from_address_email'] == message['eaccount']:
            from_account = message['eaccount']
            role = 'assistant'
            outgoing_count += 1
        else:
            lead_reply = True
            role = 'user'
            incoming_count += 1
            cc = message.get('cc_address_email_list')
            bcc = message.get('bcc_address_email_list')
        
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
    return message_history ,lead_reply, last_timestamp,  from_account, incoming_count, outgoing_count, lead_status, first_reply_after, message_uuid, cc, bcc

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


def get_weekly_summary_report(campaign_id: str, client_name: str) -> Union[WeeklyCampaignSummary, None]:
    _, _, instantly_api_key= get_campaign_details(campaign_id)
    if not instantly_api_key:
        return None
    instantly = InstantlyAPI(instantly_api_key)
    response = instantly.get_campaign_details(campaign_id=campaign_id)
    if not response:
        return None
    start_of_week, end_of_week  = get_last_week_start_and_end_of_week()
    positive_reply = db.get_count(campaign_id, start_of_week, end_of_week).count
    domain_health = get_domain_health_count(client_name)
    print(f"domain_health {domain_health}")
    start_of_week = start_of_week.date().strftime("%m/%d/%Y")
    end_of_week = end_of_week.date().strftime("%m/%d/%Y")
    weekly_response = instantly.get_weekly_campaign_details(campaign_id=campaign_id, start_date=start_of_week, end_date=end_of_week)
    if not weekly_response:
        return None
    week  = start_of_week + " - " + end_of_week
    response = WeeklyCampaignSummary(total_leads=response.total_leads,
                                     not_yet_contacted=response.not_yet_contacted,
                                     contacted=weekly_response.new_leads_contacted,
                                     leads_who_replied=weekly_response.leads_replied,
                                     positive_reply=positive_reply, 
                                     domain_health=domain_health, 
                                     week = week)
    return response

def get_domain_health_count(client_name: str):
    total_count = 0
    if client_name == 'packback':
        total_count = 252
    if client_name == 'array':
        total_count = 14
    if client_name == 'havocshield':
        total_count = 10


    start_of_week, end_of_week  = get_last_week_start_and_end_of_week()
    domain_health_count = db.get_domain_health_count(client_name,start_of_week, end_of_week).count
    domain_health = f"{domain_health_count}/{total_count}"
    return domain_health

def get_last_week_start_and_end_of_week():
    start_of_week = datetime.now() - timedelta(days=7) 
    end_of_week = start_of_week + timedelta(days=7) 
    
    return start_of_week, end_of_week
# def get_last_week_start_and_end_of_week():
#     today = datetime.now()
#     # Shift the weekday calculation to make Wednesday the start of the week
#     days_since_wednesday = (today.weekday() - 2) % 7  # 2 corresponds to Wednesday
#     start_of_week = today - timedelta(days=days_since_wednesday + 7)  # Go back to the previous Wednesday
#     end_of_week = start_of_week + timedelta(days=6)  # End of the week is Tuesday
#     return start_of_week, end_of_week


def get_daily_summary_report(campaign_id: str):
    today, start_time = last_24_hours_time()
    offset = 0  
    limit = 1000
    leads_array = []   
    while True:
        all_leads = db.get_flag_true_records(campaign_id, start_time, today,offset=offset, limit=limit).data
        if len(all_leads) == 0: 
            break
        leads_array.extend(all_leads)
        offset += limit 
    logger.info("leads_array %s", len(leads_array))
    return leads_array

def last_24_hours_time():
    today = datetime.utcnow()
    if today.weekday() == 0: 
        start_time = today - timedelta(days=3) 
    elif today.weekday() == 5: 
        start_time = today - timedelta(days=1) 
    elif today.weekday() == 6:  
        start_time = today - timedelta(days=2)  
    else:
        start_time = today - timedelta(days=1)  
    return today, start_time

def get_last_three_days_start_and_end_of_day():
    today = datetime.utcnow()
    start_date = today - timedelta(days=3)
    end_date = today
    return start_date, end_date

def update_weekly_summary_report(campaign_id: str, campaign_name: str, organization_name: str, csv_name: str, worksheet_name: str):
    try:
        worksheet = gs_client.open_sheet(csv_name, worksheet_name)
        data = get_weekly_summary_report(campaign_id, organization_name)
        if data is None:
            return []

        new_row = [
            campaign_name,
            data.week,  
            data.total_leads,                
            data.contacted,         
            data.leads_who_replied,              
            data.positive_reply,           
            data.not_yet_contacted,          
            data.domain_health,              
            
        ]
        logger.info("Weekly report data %s", new_row)

        try:
            worksheet.append_row(new_row)
        except Exception as e:
            logger.error(f"Error appending row: {e}")
    except Exception as e:
        logger.error(f"Error update_weekly_summary_report: {e}")

def update_daily_summary_report(campaign_id: str, campaign_name: str, organization_name: str, csv_name: str, worksheet_name: str):
    try:    
        today, start_time = last_24_hours_time()
        offset = 0  
        limit = 500
        leads_array = []    

        logger.info(f"csv_name {csv_name}")
        logger.info(f"worksheet_name {worksheet_name}")

        while True:
            all_leads = db.get_flag_true_records(campaign_id, start_time, today,offset=offset, limit=limit).data
            if len(all_leads) == 0: 
                break

            worksheet = gs_client.open_sheet(csv_name, worksheet_name)
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
                    columns = ["Campaign Name", "Email", "School Name", "Sent Date","Last Contact","Outgoing","Incoming","Reply","Status","From Account","Inbox Status","First Reply After","Conversation URL"]
                    values = [campaign_name, lead.get('lead_email'), lead.get('university_name'),lead.get('sent_date'),lead.get('last_contact'),lead.get('outgoing'),lead.get('incoming'),lead.get('reply'),lead.get('status'),lead.get('from_account'),lead.get('lead_status'),lead.get('first_reply_after'),lead.get('url')]
                    dataframe.loc[dataframe['Email'] == email_to_check, columns] = values  # Increment outgoing count
                else:
                    logger.info(f"Email not exists")
                    # Append a new row if the email does not exist
                    data = { 
                        "Campaign Name": campaign_name,
                        "Email" :lead.get('lead_email'),
                        "School Name": lead.get('university_name'),
                        "Sent Date":lead.get('sent_date'),
                        "Last Contact":lead.get('last_contact'),
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


            # dataframe = dataframe.fillna('') 
            dataframe = dataframe.infer_objects(copy=False)
            gs_client.update_records(worksheet, dataframe)
            leads_array.extend(all_leads)
            offset += limit 

        logger.info("leads_array %s", len(leads_array))
    except Exception as e:
        logger.error(f"Error update_daily_summary_report: {e}")

def three_days_summary_report(campaign_id: str, campaign_name: str, organization_name: str, csv_name: str, worksheet_name: str):
    try:
        start_time, _ = get_last_three_days_start_and_end_of_day()
        offset = 0  
        limit = 500
        leads_array = []    

        logger.info(f"csv_name {csv_name}")
        logger.info(f"worksheet_name {worksheet_name}")
        logger.info(f"start_time {start_time}")

        while True:
            all_leads = db.get_flag_true_records(campaign_id, start_time,offset=offset, limit=limit).data
            if len(all_leads) == 0: 
                break

            worksheet = gs_client.open_sheet(csv_name, worksheet_name)
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
                    columns = ["Campaign Name", "Email", "School Name", "Sent Date","Last Contact","Outgoing","Incoming","Reply","Status","From Account","Inbox Status","First Reply After","Conversation URL"]
                    values = [campaign_name, lead.get('lead_email'), lead.get('university_name'),lead.get('sent_date'),lead.get('last_contact'),lead.get('outgoing'),lead.get('incoming'),lead.get('reply'),lead.get('status'),lead.get('from_account'),lead.get('lead_status'),lead.get('first_reply_after'),lead.get('url')]
                    dataframe.loc[dataframe['Email'] == email_to_check, columns] = values  # Increment outgoing count
                else:
                    logger.info(f"Email not exists")
                    # Append a new row if the email does not exist
                    data = { 
                        "Campaign Name": campaign_name,
                        "Email" :lead.get('lead_email'),
                        "School Name": lead.get('university_name'),
                        "Sent Date":lead.get('sent_date'),
                        "Last Contact":lead.get('last_contact'),
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


            # dataframe = dataframe.fillna('') 
            dataframe = dataframe.infer_objects(copy=False)
            gs_client.update_records(worksheet, dataframe)
            leads_array.extend(all_leads)
            offset += limit 

        logger.info("leads_array %s", len(leads_array))
    except Exception as e:
        logger.error(f"Error three_days_summary_report: {e}")

def get_ae_data(ae_full_name):
    try:
        df = pd.read_csv("manager_ae_bdr.csv")
        ae_calendar_link = df.loc[df["AE Full Name"] == ae_full_name, "AE Calendar Links"].values[0]
        bdr_email = df.loc[df["AE Full Name"] == ae_full_name, "BDR Email"].values[0]
        manager_email = df.loc[df["AE Full Name"] == ae_full_name, "Manager Email"].values[0]

        return {
            "bcc": f"{manager_email}, jimmy.montchal@packback.co",
            "cc": f"{bdr_email}",
            "calendar_link": ae_calendar_link
        }
    except Exception as e:
        logger.error(f"Error get_ae_data: {e}")
        return { "bcc": f" jimmy.montchal@packback.co", "cc": "", "calendar_link": ""}

def format_http_url(s):
    try:
        pattern = r'\[(.*?)\]\((.*?)\)'
        match = re.search(pattern, s)
        
        if match:
            link_text = match.group(1)
            url = match.group(2)
            
            if f'<a href="{url}">' in s:
                return s
            return re.sub(pattern, f'<a href="{url}">{link_text}</a>', s)
        return s
    except Exception as e:
        return s

def get_lead_details_history_for_csv(lead_email: str, campaign_id: str, index: int):
    response = ''
    logger.info(f"Processing lead - {index + 1} - {lead_email} ")
    instantly = InstantlyAPI("hxfec34ac1m9z0nk0s96z1den868")
    all_emails = instantly.get_all_emails(lead=lead_email, campaign_id=campaign_id)
    if not all_emails:
        return None
    timestamp = datetime.now().isoformat()
    message_history ,lead_reply, last_timestamp, from_email, incoming_count, outgoing_count ,lead_status, first_reply_after, message_uuid= format_email_history(all_emails)
    if lead_reply:
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in message_history]
        formatted_history = [{"role": "system", "content": packback_prompt}, *ai_message_history]
        response = open_ai.generate_response_using_tools(formatted_history)
    last_timestamp_ = message_history[-1].get('timestamp')
    data = {"last_contact": last_timestamp_,"lead_email": lead_email, "sent_date": last_timestamp, "lead_status": lead_status, "reply": lead_reply, "status": response, "outgoing": outgoing_count, "incoming": incoming_count,  "from_account": from_email,"conversation": message_history, "updated_at":timestamp, "campaign_id": campaign_id, "first_reply_after":first_reply_after, "url" : f"https://mail-tester-frontend.vercel.app/conversation/{lead_email}" , "message_uuid": message_uuid, "flag":True}
    return data


def get_lead_details_history(lead_email: str, campaign_id,  all_emails: list):
    response = ''
    logger.info(f"Processing lead - {lead_email}")
    timestamp = datetime.now().isoformat()
    message_history ,lead_reply, last_timestamp, from_email, incoming_count, outgoing_count ,lead_status, first_reply_after, message_uuid, cc, bcc= format_email_history(all_emails)
    if lead_reply:
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in message_history]
        formatted_history = [{"role": "system", "content": packback_prompt}, *ai_message_history]
        response = open_ai.generate_response_using_tools(formatted_history)
    last_timestamp_ = message_history[-1].get('timestamp')
    data = {"last_contact": last_timestamp_,"lead_email": lead_email, "sent_date": last_timestamp, "lead_status": lead_status, "reply": lead_reply, "status": response, "outgoing": outgoing_count, "incoming": incoming_count,  "from_account": from_email,"conversation": message_history, "updated_at":timestamp, "campaign_id": campaign_id, 
            "first_reply_after":first_reply_after, "url" : f"https://mail-tester-frontend.vercel.app/conversation/{lead_email}" , "message_uuid": message_uuid, "cc": cc, "bcc": bcc}
    return data



def insert_many_domain_health(result: list):
    try:
        insertion = db.insert_many('domain_health', result)
        print(f"insert_many_domain_health: {insertion}")
        return True
    except Exception as e:
        logger.error(f"Error insert_many_domain_health: {e}")
        return False
    


def construct_email_body_from_history(messages:list, lead_email:str, account_email:str):
    html = '<div style="font-family: Arial, sans-serif; color: #202124; max-width: 600px; margin: auto; background-color: #f1f3f4; padding: 20px; border-radius: 8px;">'
    indent_level = len(messages)

    data = []

    # Prepare message data
    for message in messages:
        if message.get('role') == 'user':
            from_account = lead_email
            to_account = account_email
        else:
            from_account = account_email
            to_account = lead_email

        data.append({
            "from": from_account,
            "to": to_account,
            "body": message['content'],
            "date": convert_timestamp_for_email_thread_history(message['timestamp']),
        })

    # Construct the HTML for each message, newest to oldest
    for message in data:
        padding_style = f"padding-left: {indent_level * 10}px; color: black;"
        html_segment = f"""
        <div style="border-bottom: 1px solid #e0e0e0; padding: 10px 0; margin-bottom: 10px; {padding_style}">
            <div style="color: #5f6368; font-size: 12px; margin-bottom: 8px;">
                <strong>Date:</strong> {message['date']}<br>
                <strong>From:</strong> {message['from']}<br>
                <strong>To:</strong> {message['to']}
            </div>
            <div style="font-size: 14px; line-height: 1.6; margin-top: 5px; color: black; white-space: pre-wrap;">
                {message['body'].replace('\n', '<br>')}
            </div>
        </div>
        """
        html = html_segment + html
        indent_level -= 1

    # Close the thread container
    html += '</div>'

    return html

def convert_timestamp_for_email_thread_history(timestamp):
    try:
        dt = datetime.fromisoformat(timestamp)
        dt = dt.astimezone(ct_timezone)
        formatted_dt = dt.strftime('%a, %b %d, %Y at %I:%M %p')
        return formatted_dt
    except Exception as e:
        return timestamp    
  