from src.configurations.instantly import InstantlyAPI
from src.configurations.llm import OpenAiConfig
from datetime import datetime, timedelta
from src.common.logger import get_logger
from src.common.prompts import packback_prompt, question_prompt
from src.common.models import WeeklyCampaignSummary
from src.database.supabase import SupabaseClient
from typing import Union
from src.configurations.googleSheet import GoogleSheetClient
import pandas as pd
import re
import pytz
from src.crm.salesforce import SalesforceClient



db = SupabaseClient()
gs_client = GoogleSheetClient()
logger = get_logger("Utils")
ct_timezone = pytz.timezone("US/Central")

def get_campaign_details(campaign_id:str) -> Union[tuple[str, str, str, str], None]:
    campaign_details = db.get_campaign_details(campaign_id)
    if len(campaign_details.data) == 0:
        return None, None, None, None
    campaign_name = campaign_details.data[0].get("campaign_name")
    organization_details = campaign_details.data[0].get("organizations")
    organization_name = organization_details.get('name')
    instantly_api_key = organization_details.get('api_key')
    open_api_key = organization_details.get('llm_api_key', None)
    return campaign_name, organization_name, instantly_api_key, open_api_key

def get_open_ai_key(organization_name:str) -> Union[str, None]:
    logger.info(f"get_open_ai_key :: {organization_name}")
    open_ai_key = db.get_campaign_llm_key_by_name(organization_name)
    if len(open_ai_key.data) == 0:
        return None
    return open_ai_key.data[0].get('llm_api_key')

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

        last_from_account = message['from_address_email']
        last_to_account = message.get('to_address_email_list')

        
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
        
        message_history.append({"role": role, "timestamp": message.get('timestamp_created'), "subject": message.get('subject'),"content": content, "cc": cc, "bcc": bcc, "from_account": last_from_account, "to_account": last_to_account})
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
    _, _, instantly_api_key,_= get_campaign_details(campaign_id)
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
            all_leads = db.get_flag_true_records(campaign_id, start_time,offset=offset, limit=limit).data
            print("all_leads", len(all_leads))
            # all_leads = db.get_all_leads_by_campaign(offset=offset, limit=limit).data 
            if len(all_leads) == 0: 
                break

            worksheet = gs_client.open_sheet(csv_name, worksheet_name)
            all_csv_records = gs_client.get_all_records(worksheet)
            df = pd.DataFrame(all_csv_records)
        
            for index , lead in enumerate(all_leads):
                email_to_check = lead.get('lead_email')
                logger.info(f" {index +1} :: {email_to_check}")
                email_exists =None
                if len(all_csv_records) >0:
                    email_exists = email_to_check in df['Email'].values  # Assuming 'lead_email' is the column name

                if email_exists:
                    logger.info(f"Email exists")
                    columns = ["Campaign Name", "Email", "School Name", "Sent Date","Last Contact","Outgoing","Incoming","Reply","Status","From Account","Inbox Status","First Reply After","Conversation URL"]
                    values = [campaign_name, lead.get('lead_email'), lead.get('university_name'),lead.get('sent_date'),lead.get('last_contact'),lead.get('outgoing'),lead.get('incoming'),lead.get('reply'),
                              lead.get('status'),lead.get('from_account'),lead.get('lead_status'),lead.get('first_reply_after'),lead.get('url')]
                    df.loc[df['Email'] == email_to_check, columns] = values  # Increment outgoing count
                else:
                    logger.info(f"Email not exists")
                    # Append a new row if the email does not exist
                    data = { 
                        "Campaign Name": campaign_name,
                        "Email" :(lead.get('lead_email') or ''),
                        "School Name": (lead.get('university_name') or ''),
                        "Sent Date":(lead.get('sent_date') or ''),
                        "Last Contact":(lead.get('last_contact') or ''),
                        "Outgoing":(lead.get('outgoing') or ''),
                        "Incoming":(lead.get('incoming') or ''),
                        "Reply":(lead.get('reply') or ''),
                        "Status" :(lead.get('status') or ''),
                        "From Account":(lead.get('from_account') or ''),
                        "Inbox Status":(lead.get('lead_status') or ''),
                        "First Reply After":(lead.get('first_reply_after') or ''),
                        "Conversation URL":(lead.get('url') or '')
                    }
                    new_row = pd.DataFrame([data])  # Convert dict to DataFrame
                    df = pd.concat([df, new_row], ignore_index=True) 


            # df = df.fillna('') 
            df = df.infer_objects(copy=False)
            gs_client.update_records(worksheet, df)
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
            df = pd.DataFrame(all_csv_records)
        
            for index , lead in enumerate(all_leads):
                email_to_check = lead.get('lead_email')
                logger.info(f" {index +1} :: {email_to_check}")
                email_exists =None
                if len(all_csv_records) >0:
                    email_exists = email_to_check in df['Email'].values  # Assuming 'lead_email' is the column name

                if email_exists:
                    logger.info(f"Email exists")
                    columns = ["Campaign Name", "Email", "School Name", "Sent Date","Last Contact","Outgoing","Incoming","Reply","Status","From Account","Inbox Status","First Reply After","Conversation URL"]
                    values = [campaign_name, lead.get('lead_email'), lead.get('university_name'),lead.get('sent_date'),lead.get('last_contact'),lead.get('outgoing'),lead.get('incoming'),lead.get('reply'),lead.get('status'),lead.get('from_account'),lead.get('lead_status'),lead.get('first_reply_after'),lead.get('url')]
                    df.loc[df['Email'] == email_to_check, columns] = values  # Increment outgoing count
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
                    df = pd.concat([df, new_row], ignore_index=True) 


            # df = df.fillna('') 
            df = df.infer_objects(copy=False)
            gs_client.update_records(worksheet, df)
            leads_array.extend(all_leads)
            offset += limit 

        logger.info("leads_array %s", len(leads_array))
    except Exception as e:
        logger.error(f"Error three_days_summary_report: {e}")


def get_ae_data_by_email(email:str):
    try:
        sf = SalesforceClient(email)
        lead_ae_manager = sf.get_ae_manager_by_email()
        if not lead_ae_manager:
            return {'lead_email': email, 'ae_first_name': 'Anh', 'ae_last_name': 'Pham', 'ae_email': 'anh@packback.co', 
                    'ae_booking_link': 'https://hello.packback.co/c/salesopspackback-co', 'manager_email': 'salesops@packback.co.invalid'}
        return lead_ae_manager
    except Exception as e:
        logger.error(f"Error get_ae_data_by_email: {e}")
        return {}

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

response_tool = {
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "response",
        "parameters": {
          "type": "object",
          "required": [
            "answer"
          ],
          "properties": {
            "answer": {
              "enum": [
                "Interested",
                "NotInterested",
                "OutOfOffice",
                "Unsubscribe"
                "WrongPerson"
              ],
              "type": "string",
              "description": "Interested if lead is interested, NotInterested if lead is not interested, OutOfOffice if lead is out of office or leaves, Unsubscribe if lead requests to be removed from the contact list, WrongPerson if lead is not the right person"
            }
          }
        },
        "description": "Analyze the conversation and determine lead status"
      }
    }
  ],
  "tool_choice": {
    "type": "function",
    "function": {
      "name": "response"
    }
  }
}


def get_lead_details_history(lead_email: str, campaign_id,  all_emails: list, open_api_key: str):
    logger.info(f"lead_email:: {lead_email}")
    response = ''
    open_ai = OpenAiConfig(open_api_key)
    logger.info(f"Processing lead - {lead_email}")
    timestamp = datetime.now().isoformat()
    answer = ''
    message_history ,lead_reply, last_timestamp, from_email, incoming_count, outgoing_count ,lead_status, first_reply_after, message_uuid, cc, bcc= format_email_history(all_emails)
    if lead_reply:
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in message_history]
        formatted_history = [{"role": "system", "content": packback_prompt}, *ai_message_history]
        response = open_ai.generate_response_using_tools(all_messages= formatted_history, response_tool=response_tool)
        answer = response.get('answer')
    last_timestamp_ = message_history[-1].get('timestamp')
    data = {"last_contact": last_timestamp_,"lead_email": lead_email, "sent_date": last_timestamp, "lead_status": lead_status, "reply": lead_reply, "status": answer.replace(" ", ""), "outgoing": outgoing_count, "incoming": incoming_count,  "from_account": from_email,"conversation": message_history, "updated_at":timestamp, "campaign_id": campaign_id, 
            "first_reply_after":first_reply_after, "url" : f"https://mail-tester-frontend.vercel.app/conversation/{lead_email}" , "message_uuid": message_uuid, "cc": cc, "bcc": bcc, 'recycled': False}
    return data


validate_tool = {
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "response",
        "parameters": {
          "type": "object",
          "required": [
            "answer"
          ],
          "properties": {
            "answer": {
              "enum": [
                "yes",
                "no",
              ],
              "type": "string",
              "description": "validate the last reply of lead is 10 question or not"
            }
          }
        },
        "description": "Analyze the conversation and determine lead reply is 10 question or not"
      }
    }
  ],
  "tool_choice": {
    "type": "function",
    "function": {
      "name": "response"
    }
  }
}

def trueOrFalse(value:str):
    return True if value == "yes" else False

def validate_lead_last_reply(message_history: list, open_api_key: str):
    open_ai = OpenAiConfig(open_api_key)
    ai_message_history = [{"role": item["role"], "content": item["content"]} for item in message_history]   
    formatted_history = [{"role": "system", "content": question_prompt}, *ai_message_history]
    response = open_ai.generate_response_using_tools(all_messages= formatted_history, response_tool=validate_tool)
    return trueOrFalse(response.get('answer'))
 

def construct_email_body_from_history(messages:list, lead_email:str, account_email:str):
    html = '<div style="font-family: Arial, sans-serif; color: #202124; max-width: 600px; margin: auto; background-color: #f1f3f4; padding: 20px; border-radius: 8px;">'
    indent_level = len(messages)

    data = []

    # Prepare message data
    for message in messages:

        data.append({
            "from": message.get('from_account'),
            "to": message.get('to_account'),
            "body": message.get('content').replace('\n', '<br>'),
            "cc": message.get('cc') or '',
            "bcc": message.get('bcc') or '',
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
                <strong>To:</strong> {message['to']}<br>
                <strong>Cc:</strong> {message['cc']}<br>
                <strong>Bcc:</strong> {message['bcc']}
            </div>
            <div style="font-size: 14px; line-height: 1.6; margin-top: 5px; color: black; white-space: pre-wrap;">
                {re.sub(r'(https?://[^\s<>"]+)', r'<a href="\1">\1</a>', message['body'])}
            </div>
        </div>
        """
        html = html_segment + html
        indent_level -= 1

    # Close the thread container
    html += '</div>'

    return html



def construct_email_text_from_history(messages:list, lead_email:str, account_email:str):
    data = []

    for message in messages:
       

        body = message.get('content', '')
        # Remove any HTML/div tags from the body
        body = body.replace('<br>', '\n')
        body = re.sub(r'<[^>]+>', '', body)
        body = body.replace('&nbsp;', ' ')
        
        body = body.strip()

        data.append({
            "from": message.get('from_account'),
            "to": message.get('to_account'),
            "body": body,
            "cc": message.get('cc') or '',
            "bcc": message.get('bcc') or '',
            "date": convert_timestamp_for_email_thread_history(message['timestamp']),
        })

    # Construct the text for each message, newest to oldest
    thread_text = ""
    for message in data:
        message_text = f"""
        Date: {message['date']}
        From: {message['from']}
        To: {message['to']}
        Cc: {message['cc']}
        Bcc: {message['bcc']}

        {message['body']}

        -------------------

"""
        thread_text = message_text + thread_text

    return thread_text

def convert_timestamp_for_email_thread_history(timestamp):
    try:
        dt = datetime.fromisoformat(timestamp)
        dt = dt.astimezone(ct_timezone)
        formatted_dt = dt.strftime('%a, %b %d, %Y at %I:%M %p')
        return formatted_dt
    except Exception as e:
        return timestamp    
  

def calculate_gpt4o_mini_cost(prompt_tokens, completion_tokens):

    input_cost = (prompt_tokens / 1000000) * 0.150 
    output_cost = (completion_tokens / 1000000) * 0.600
    total_cost = input_cost + output_cost

    return total_cost



def calculate_gpt4o_cost(prompt_tokens, completion_tokens):
    prompt_cost_per_1k = 3.75  # $3.75 per 1,000 prompt tokens
    completion_cost_per_1k = 15.00  # $15.00 per 1,000 completion tokens

    prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
    completion_cost = (completion_tokens / 1000) * completion_cost_per_1k

    total_cost = prompt_cost + completion_cost
    return total_cost

def validate_lead_conversation(conversation):
    total_outgoing_before_incoming = []
    for item in conversation:
        if item["role"] == "assistant":
            total_outgoing_before_incoming.append(item)
        else:
            break

    if len(total_outgoing_before_incoming) > 3 and len(total_outgoing_before_incoming) <= 6:
        conversation = conversation[3:] 
    elif len(total_outgoing_before_incoming) > 6 and len(total_outgoing_before_incoming) <= 9:
        conversation = conversation[6:]
    elif len(total_outgoing_before_incoming) > 9 and len(total_outgoing_before_incoming) <= 12:
        conversation = conversation[9:]
    
    return conversation