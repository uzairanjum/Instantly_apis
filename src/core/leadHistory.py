from src.configurations.instantly import InstantlyAPI
from src.settings import settings
from src.database.supabase import SupabaseClient
from src.common.utils import get_lead_details_history, get_campaign_details, construct_email_body_from_history
from src.core.responder import generate_ai_response
from src.common.logger import get_logger
from src.configurations.justcall import JustCallService
from datetime import datetime
from pytz import timezone

ct_timezone = timezone('US/Central')

jc = JustCallService()
import json
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
            return {"email" : lead_details.get('email'), "university_name" : lead_details.get('University Name'), "AE" : lead_details.get('AE'), "CO":lead_details.get('Contact Owner: Full Name'), 
                    "lead_last_name": lead_details.get('lastName'), "course_name": lead_details.get('Course Name'), "course_description": lead_details.get('Course Description'),
                    "question_1" : lead_details.get('Question 1'), "question_2" : lead_details.get('Question 2'), "question_3" : lead_details.get('Question 3'), "question_4" : lead_details.get('Question 4')
                    }
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
    try:
        campaign_name, organization_name, instantly_api_key = get_campaign_details(campaign_id)
        if organization_name is None:
            return None
        instantly_lead = LeadHistory(lead_email, campaign_id, instantly_api_key)
        lead_history = instantly_lead.get_lead_details()
        if lead_history is None:
            return None
        logger.info("lead found :: %s", lead_email)
        lead_emails = instantly_lead.get_lead_emails()
        if lead_emails is None:
            return None
        logger.info("lead email history found :: %s", lead_email)
        data =  get_lead_details_history(lead_email, campaign_id, lead_emails)
        if data is None:
            return None
    
        data['flag'] = flag
        data['university_name'] = lead_history.get('university_name')

        if event =='reply_received' and data.get('status') == "Interested":
            logger.info("Interested lead - %s", lead_email)
            jc.send_message(f"New interested lead -\n\n Organization - {organization_name}\n\nCampaign - {campaign_name}\n\nLead Email - {lead_email}\n\nConversation URL - {data['url']}")
            cap = db.get_daily_cap().data[0]
            count = cap.get('count')
            limit = cap.get('limit')
            logger.info("count :: %s", count)
            logger.info("limit :: %s", limit)
            if organization_name == 'packback' and not count >= limit:
                logger.info("count not reached")    
                logger.info("incoming :: %s", data.get('incoming'))
                logger.info("outgoing :: %s", data.get('outgoing'))
                if data.get('incoming') == 1 and data.get('outgoing') == 3:
                    logger.info("forwarding email")
                    forward_email_by_lead_email(lead_history, data, 'uzair@hellogepeto.com')
                elif data.get('incoming') == 1 and data.get('outgoing') in [1,2]:
                    logger.info("sending email")
                    send_email_by_lead_email(lead_history, data)
                else:
                    logger.info("Need to check cc email if not cc'd then forward")
                    send_email_by_lead_email_forwarding(lead_history, data)
                db.cap_update(count + 1)
    
        instantly_lead.save_lead_history(data)
        logger.info("lead email processed - %s :: %s", index, lead_email)
        return data
    except Exception as e:
        logger.error(f"Error get_data_from_instantly: {e}")
        return None
    
def send_email_by_lead_email(lead_history,data):
    try:
        lead_email =  lead_history.get('email')
        conversation =  data.get('conversation')
        response = generate_ai_response (lead_history, conversation)


        subject = response.get('subject')
        content = response.get('content')
        from_account = data.get('from_account')
        campaign_id = data.get('campaign_id')
        message_uuid =  data.get('message_uuid')
        cc = response.get('cc')
        bcc = response.get('bcc')

        email_cc = data['cc']
        email_bcc = data['bcc']

        _, _, instantly_api_key = get_campaign_details(campaign_id)
        instantly = InstantlyAPI(instantly_api_key)


        logger.info("sending email to :: %s", lead_email)
        logger.info("subject :: %s", subject)
        logger.info("content :: %s", content)
        logger.info("from_account :: %s", from_account)
        logger.info("message_uuid :: %s", message_uuid)
        logger.info("cc :: %s", cc)
        logger.info("bcc :: %s", bcc)
        logger.info("email_cc :: %s", email_cc)
        logger.info("email_bcc :: %s", email_bcc)

        logger.info("cc type :: %s", type(cc))
        logger.info("bcc type :: %s", type(bcc))
        logger.info("email_cc type :: %s", type(email_cc))
        logger.info("email_bcc type :: %s", type(email_bcc))




        send = instantly.send_reply(
            message=content,
            from_email=from_account,
            to_email=lead_email,
            uuid=message_uuid,
            subject=subject, 
            cc=cc,
            bcc=response.get('bcc')
        )
        if send == 200:
            logger.info("Email sent successfully - %s", lead_email)
            db.update({"flag": False}, lead_email)
        return True
    except Exception as e:
        logger.error("Error sending email - %s", e)
        return False
   
def forward_email_by_lead_email(lead_history,data, forward_email):
    try:
        logger.info("forwarding email to :: %s", forward_email)
        lead_email = lead_history.get('email')
        from_account = data.get('from_account')
        campaign_id = data.get('campaign_id')
        message_uuid =  data.get('message_uuid')
        conversation = data.get('conversation')
        subject = conversation[0].get('subject')

        _, _, instantly_api_key = get_campaign_details(campaign_id)

        instantly = InstantlyAPI(instantly_api_key)
        email_body = construct_email_body_from_history(conversation, lead_email, from_account)

        

        logger.info("sending email to :: %s", lead_email)
        logger.info("subject :: %s", subject)
        logger.info("from_account :: %s", from_account)
        logger.info("message_uuid :: %s", message_uuid)
        send = instantly.send_reply(
            message=email_body,
            from_email=from_account,
            to_email=forward_email,
            uuid=message_uuid,
            subject=subject, 
        )
        if send == 200:
            logger.info("Email sent successfully - %s", lead_email)
            db.update({"flag": False}, lead_email)
        return True
    except Exception as e:
        logger.error("Error sending email - %s", e)
        return False
    

def send_email_by_lead_email_forwarding(lead_history,data):
    try:
        lead_email =  lead_history.get('email')
        conversation =  data.get('conversation')
        response = generate_ai_response (lead_history, conversation)


        subject = response.get('subject')
        content = response.get('content')
        from_account = data.get('from_account')
        message_uuid =  data.get('message_uuid')
        cc = response.get('cc')
        bcc = response.get('bcc')
        email_cc = data['cc']
        email_bcc = data['bcc']

        logger.info("sending email to :: %s", lead_email)
        logger.info("subject :: %s", subject)
        logger.info("content :: %s", content)
        logger.info("from_account :: %s", from_account)
        logger.info("message_uuid :: %s", message_uuid)
        logger.info("cc :: %s", cc)
        logger.info("bcc :: %s", bcc)


        if email_cc != cc:
            return forward_email_by_lead_email(lead_history, data, cc)
        
        logger.info("No response :: ")
        

        return True
    except Exception as e:
        logger.error("Error sending email - %s", e)
        return False
   
