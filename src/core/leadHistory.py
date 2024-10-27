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


    campaign_name, organization_name, instantly_api_key, zapier_url = get_campaign_details(campaign_id)
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
    data =  get_lead_details_history(lead_email, lead_history.get('University Name'), campaign_id, lead_emails)
    if data is None:
        return None

    data['flag'] = flag
    
    

    if event =='reply_received' and data.get('status') == "Interested":
        logger.info("reply received - %s", lead_email)
        # jc.send_message(f"New interested lead -\n\nCampaign - {campaign_name}\n\nLead Email - {lead_email}\n\nConversation URL - {data['url']}")

        draft_email = make_draft_email (lead_history.get('AE') if lead_history.get('AE') else lead_history.get('CO'), lead_history.get('lead_last_name'), data.get('conversation'))
        data['draft_email'] = draft_email



    # # Save lead history to supabase
    instantly_lead.save_lead_history(data)
    logger.info("lead email processed - %s :: %s", index, lead_email)

    return data


def send_email_by_lead_email(lead_email):
    try:
        email_data = db.get_by_email(lead_email).data
        if len(email_data) == 0:
            return None
        email_data = email_data[0]
        draft_email = email_data.get('draft_email')
        from_account = email_data.get('from_account')
        message_uuid = email_data.get('message_uuid')
        campaign_id = email_data.get('campaign_id')
        _, _, instantly_api_key, _ = get_campaign_details(campaign_id)
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
            db.update({"draft_email": {}, "flag": False}, lead_email)
        return True
    except Exception as e:
        logger.error("Error sending email - %s", e)
        return False
   