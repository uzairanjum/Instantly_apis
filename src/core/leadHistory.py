from src.configurations.instantly import InstantlyAPI
from src.settings import settings
from src.database.supabase import SupabaseClient
from src.common.utils import get_lead_details_history, get_campaign_details
from src.core.responder import make_draft_email
from src.common.logger import get_logger
from src.configurations.justcall import JustCallService

jc = JustCallService()

db = SupabaseClient()
logger = get_logger("LeadHistory")

class LeadHistory:
    def __init__(self, lead_email, campaign_id, instantly_api_key):
        self.lead_email = lead_email
        self.campaign_id = campaign_id
        self.instantly = InstantlyAPI(instantly_api_key)

    def get_lead_details(self):
        lead_details = self.instantly.get_lead_details(lead = self.lead_email, campaign_id = self.campaign_id)
        if lead_details:
            lead_details = lead_details[0].get('lead_data')
            return {"email" : lead_details.get('email'), "University Name" : lead_details.get('University Name'), "AE" : lead_details.get('AE'), "CO":lead_details.get('Contact Owner: Full Name'), "lead_last_name": lead_details.get('lastName')}
        return lead_details

    def get_lead_emails(self):
        all_emails = self.instantly.get_all_emails(lead=self.lead_email, campaign_id=self.campaign_id)
        if not all_emails:
            return None 
        return all_emails

    def save_lead_history(self, data):
        lead_history = db.get(self.lead_email)
        if len(lead_history.data) > 0:
            logger.info("lead updated :: %s", self.lead_email)
            db.update(data, self.lead_email)
        else:
            logger.info("lead inserted :: %s", self.lead_email)
            db.insert(data)

    def validate_lead_conversation(self):
        pass
    
    

def get_data_from_instantly(lead_email, campaign_id, event, index = 1 , flag = False):


    campaign_name, organization_name, instantly_api_key = get_campaign_details(campaign_id)
    if organization_name is None:
        return None
    instantly_lead = LeadHistory(lead_email, campaign_id, instantly_api_key)


    # Get lead details from instantly
    lead_history = instantly_lead.get_lead_details()
    if lead_history is None:
        return None
    logger.info("lead found :: %s", lead_email)

    # Get lead emails from instantly
    lead_emails = instantly_lead.get_lead_emails()
    if lead_emails is None:
        return None
    logger.info("lead email history found :: %s", lead_email)

    # Get information data by lead email, lead university name and lead emails
    data =  get_lead_details_history(lead_email, campaign_id, lead_emails)
    if data is None:
        return None

    data['flag'] = flag
    data['university_name'] = lead_history.get('University Name')
    
    

    if event =='reply_received' and data.get('status') == "Interested":
        logger.info("Interested lead - %s", lead_email)
        jc.send_message(f"New interested lead -\n\n Organization - {organization_name}\n\nCampaign - {campaign_name}\n\nLead Email - {lead_email}\n\nConversation URL - {data['url']}")
        if organization_name == 'packback':
            draft_email = make_draft_email (lead_history.get('AE') if lead_history.get('AE') else lead_history.get('CO'), lead_history.get('lead_last_name'), data.get('conversation'))
            logger.info("Draft email - %s", draft_email)
            data['draft_email'] = draft_email



    # # Save lead history to supabase
    instantly_lead.save_lead_history(data)
    logger.info("lead email processed - %s :: %s", index, lead_email)

    return data


def send_email_by_lead_email(lead_email):
    try:
        email_data = db.get_by_email(lead_email).data
        if len(email_data) == 0:
            logger.info("No draft email data found for lead - %s", lead_email)
            return False
        if email_data[0].get('draft_email') == {}:
            logger.info("Draft email data is empty for lead - %s", lead_email)
            return False
        
        email_data = email_data[0]
        draft_email = email_data.get('draft_email')
        from_account = email_data.get('from_account')
        message_uuid = email_data.get('message_uuid')
        campaign_id = email_data.get('campaign_id')
        _, _, instantly_api_key = get_campaign_details(campaign_id)
        instantly = InstantlyAPI(instantly_api_key)
        send = instantly.send_reply(
            message=draft_email.get('content'),
            from_email=from_account,
            to_email=lead_email,
            uuid=message_uuid,
            subject=draft_email.get('subject'), 
            cc=draft_email.get('cc'),
            bcc=draft_email.get('bcc')
        )
        if send == 200:
            logger.info("Email sent successfully - %s", lead_email)
            db.update({"draft_email": {}, "flag": False}, lead_email)
        return True
    except Exception as e:
        logger.error("Error sending email - %s", e)
        return False
   



# def forward_email_by_lead_email(lead_email):
#     try:
#         email_data = db.get_by_email(lead_email).data
#         if len(email_data) == 0:
#             logger.info("No draft email data found for lead - %s", lead_email)
#             return False
        
        
#         conversation = email_data[0].get('conversation')
#         if conversation == []:
#             logger.info("Conversation data is empty for lead - %s", lead_email)
#             return False
#         email_data = email_data[0]
#         from_account = email_data.get('from_account')
#         message_uuid = email_data.get('message_uuid')
#         campaign_id = email_data.get('campaign_id')
#         _, _, instantly_api_key = get_campaign_details(campaign_id)
#         instantly = InstantlyAPI(instantly_api_key)
        

#         email_body = construct_email_body_from_history(conversation, lead_email, from_account)


#         print("conversation[0].get('subject')",conversation[0].get('subject'))
#         send = instantly.send_reply(
#             message=email_body,
#             from_email=from_account,
#             to_email='rajpoot.waryah@gmail.com',
#             uuid=message_uuid,
#             subject=conversation[0].get('subject'), 
    
#         )
#         if send == 200:
#             logger.info("Email sent successfully - %s", lead_email)
#             db.update({"draft_email": {}, "flag": False}, lead_email)
#         return True
#     except Exception as e:
#         logger.error("Error sending email - %s", e)
#         return False
    
# from datetime import datetime
# from pytz import timezone

# ct_timezone = timezone('US/Central')


# def construct_email_body_from_history(messages:list, lead_email:str, account_email:str):
#     html = '<div style="font-family: Arial, sans-serif; color: #202124; max-width: 600px; margin: auto; background-color: #f1f3f4; padding: 20px; border-radius: 8px;">'
#     indent_level = len(messages)

#     data = []

#     # Prepare message data
#     for message in messages:
#         if message.get('role') == 'user':
#             from_account = lead_email
#             to_account = account_email
#         else:
#             from_account = account_email
#             to_account = lead_email

#         data.append({
#             "from": from_account,
#             "to": to_account,
#             "body": message['content'],
#             "date": convert_timestamp_for_email_thread_history(message['timestamp']),
#         })

#     # Construct the HTML for each message, newest to oldest
#     for message in data:
#         padding_style = f"padding-left: {indent_level * 10}px; color: black;"
#         html_segment = f"""
#         <div style="border-bottom: 1px solid #e0e0e0; padding: 10px 0; margin-bottom: 10px; {padding_style}">
#             <div style="color: #5f6368; font-size: 12px; margin-bottom: 8px;">
#                 <strong>Date:</strong> {message['date']}<br>
#                 <strong>From:</strong> {message['from']}<br>
#                 <strong>To:</strong> {message['to']}
#             </div>
#             <div style="font-size: 14px; line-height: 1.6; margin-top: 5px; color: black; white-space: pre-wrap;">
#                 {message['body'].replace('\n', '<br>')}
#             </div>
#         </div>
#         """
#         html = html_segment + html
#         indent_level -= 1

#     # Close the thread container
#     html += '</div>'

#     return html



# def convert_timestamp_for_email_thread_history(timestamp):
#     try:
#         dt = datetime.fromisoformat(timestamp)
#         dt = dt.astimezone(ct_timezone)
#         formatted_dt = dt.strftime('%a, %b %d, %Y at %I:%M %p')
#         return formatted_dt
#     except Exception as e:
#         return timestamp    
  