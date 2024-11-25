
from src.configurations.instantly import InstantlyAPI
from src.common.logger import get_logger
import concurrent.futures
from src.database.supabase import SupabaseClient
from src.common.utils import get_campaign_details

from src.configurations.justcall import JustCallService


logger = get_logger("RecycleLeads")
db = SupabaseClient()
jc = JustCallService()

import time


class RecycleLeads:

    def __init__(self, lead_list, campaign_id, instantly_api_key):
        self.lead_list = lead_list
        self.campaign_id = campaign_id
        self.instantly = InstantlyAPI(instantly_api_key)
       
    def process_lead(self,lead_email, index, recycled_leads, deleted_leads):
        """
        Function to process a single lead.
        """
        try:
            print(f"Processing lead {index}: {lead_email}")
            lead_details = self.instantly.get_lead_details(lead_email=lead_email, campaign_id=self.campaign_id)
            if len(lead_details) > 0:
                lead_info = lead_details[0].get('lead_data')
                recycled_leads.append({"email": lead_email, "custom_variables": lead_info})
                deleted_leads.append(lead_email)
                db.update({"recycled": True}, lead_email)
            else:
                logger.error(f"Lead details not found for {lead_email}")
        except Exception as e:
            logger.error(f"Error processing lead {lead_email}: {e}")

    def recycle_leads(self):

        try:
            """
            Recycles leads concurrently using ThreadPoolExecutor.
            """
            recycled_leads = []
            deleted_leads = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_lead = {
                    executor.submit(self.process_lead, lead.get('lead_email'), index, recycled_leads, deleted_leads): lead
                    for index, lead in enumerate(self.lead_list)
                }
                for index,future in enumerate(concurrent.futures.as_completed(future_to_lead)):
                    try:
                        future.result() 
                        if (index + 1) % 10 == 0:  
                            time.sleep(2)  # 
                    except Exception as e:
                        lead = future_to_lead[future]
                        logger.error(f"Error in processing lead {lead.get('lead_email')}: {e}")

            logger.info("Deleted leads: %s", deleted_leads)
            logger.info("Recycled leads count: %s", len(recycled_leads))
            logger.info("Deleted leads count: %s", len(deleted_leads))
            if len(deleted_leads) == len(recycled_leads):
                self.instantly .delete_lead_from_campaign(lead_list=deleted_leads, campaign_id=self.campaign_id)
                self.instantly .add_lead_to_campaign(lead_list=recycled_leads, campaign_id=self.campaign_id)
       
        except Exception as e:
            logger.error(f"Error in recycle_leads: {e}")
       

def recycle_leads_from_db(campaign_id):
    try:
        total_leads = 1000
        if campaign_id == "ecdc673c-3d90-4427-a556-d39c8b69ae9f":
            total_leads = 10000
        
        logger.info(f"total_leads {total_leads}")
        campaign_name, organization_name, instantly_api_key = get_campaign_details(campaign_id)
        offset=0
        limit=100
        while offset < total_leads:
            all_leads = db.get_all_recycle_leads(campaign_id=campaign_id, offset=offset, limit=limit).data
            recycle_leads = RecycleLeads(lead_list=all_leads, campaign_id=campaign_id, instantly_api_key=instantly_api_key)
            recycle_leads.recycle_leads()
            offset += limit
            logger.info(f"offset {offset}")
        jc.send_message(f"Lead Recycled -\n\nOrganization - {organization_name}\n\nCampaign - {campaign_name}\n\nTotal Leads Recycled - {offset}")
    except Exception as e:
        logger.error(f"Error in recycle_leads_from_db: {e}")


