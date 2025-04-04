from src.configurations.instantly import InstantlyAPI
from src.database.supabase import SupabaseClient
from src.tools.base import BaseConfig
from src.common.enum import Client
from src.common.utils import get_lead_details_history, get_campaign_details
from src.common.logger import get_logger
from pytz import timezone



ct_timezone = timezone('US/Central')
logger = get_logger(__name__)


db = SupabaseClient()



class LeadHistory:

    def __init__(self, lead_email, campaign_id, instantly_api_key):
        self.lead_email = lead_email
        self.campaign_id = campaign_id
        self.instantly = InstantlyAPI(instantly_api_key)

    def get_lead_details(self):
        lead_details = self.instantly.get_lead_details(lead_email = self.lead_email, campaign_id = self.campaign_id)
        if lead_details:
            
            lead_details = lead_details[0].get('lead_data')
            return {
                    "email" : lead_details.get('email'), 
                    "university_name" : lead_details.get('University Name'),
                    "AE" : lead_details.get('AE'), 
                    "CO":lead_details.get('Contact Owner: Full Name'), 
                    "lead_last_name": lead_details.get('lastName'), 
                    "lead_first_name":lead_details.get('firstName'),
                    "course_name": lead_details.get('Course Name'), 
                    "course_description": lead_details.get('Course Description'), 
                    "course_code":lead_details.get('Course Code') if lead_details.get('Course Code') else lead_details.get('FA24 Course Code'),
                    "question_1" : lead_details.get('Question 1'), 
                    "question_2" : lead_details.get('Question 2'),
                    "question_3" : lead_details.get('Question 3'),
                    "question_4" : lead_details.get('Question 4'),
                    "linkedin_url": lead_details.get('LinkedIn Profile'),
                    "first_sentence": lead_details.get('first_sentence')
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

    

def get_data_from_instantly(lead_email, campaign_id, event, index = 1 , flag = False):
    try:
        updated_data = None

        campaign_name, organization_name, instantly_api_key, open_api_key = get_campaign_details(campaign_id)
        if organization_name is None:
            return None
        logger.info("campaign name :: %s", campaign_name)
        
        instantly_lead = LeadHistory(lead_email, campaign_id, instantly_api_key)
        lead_history = instantly_lead.get_lead_details()

        if lead_history is None:
            return None
        
        logger.info("lead found :: %s", lead_email)
        lead_emails = instantly_lead.get_lead_emails()
        if lead_emails is None:
            return None
        data =  get_lead_details_history(lead_email, campaign_id, lead_emails, open_api_key)
        if data is None:
            return None
    
        data['flag'] = flag
        data['university_name'] = lead_history.get('university_name', None)
        data['recycled'] = False
        
        base_config = BaseConfig(organization_name, open_api_key, campaign_name, lead_history, data)

        if event =='reply_received' and data.get('status') == "Interested":
            logger.info("Interested lead - %s", lead_email)
            base_config.respond_or_forward()

            if organization_name == Client.PACKBACK.value:
                updated_data = updated_lead_data(lead_email, campaign_id, open_api_key)
                if updated_data is not None:
                    base_config.update_salesforce_task(updated_data)
                else:
                    base_config.update_salesforce_task(data)

        elif event == 'reply_received' and data.get('status') != "Interested":
            logger.info("Not Interested lead - %s", lead_email)
            base_config.update_crm()
            
        if updated_data is not None:
            instantly_lead.save_lead_history(updated_data)
        else:
            instantly_lead.save_lead_history(data)

        logger.info("lead email processed - %s :: %s", index, lead_email)
        return data
    
    except Exception as e:
        logger.error(f"Error get_data_from_instantly: {e}")
        return None
    

def updated_lead_data(lead_email, campaign_id, open_ai_key):
    try:
        instantly_lead = LeadHistory(lead_email, campaign_id, open_ai_key)

        logger.info("lead found :: %s", lead_email)
        lead_emails = instantly_lead.get_lead_emails()
        if lead_emails is None:
            return None
            
        logger.info("lead email history found :: %s", lead_email)
        data =  get_lead_details_history(lead_email, campaign_id, lead_emails, open_ai_key)
        return data
    except Exception as e:
        logger.error(f"Error updated_lead_data: {e}")
        return None