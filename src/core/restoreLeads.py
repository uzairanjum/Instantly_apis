
from src.configurations.instantly import InstantlyAPI
from src.database.supabase import SupabaseClient
from src.database.mongodb import MongoDBClient
from datetime import datetime, timedelta
import concurrent.futures
from src.common.logger import get_logger
from src.common.utils import get_campaign_details
import time
logger = get_logger('Recycled&RestoredLeads')

db = SupabaseClient()
mongodb_client = MongoDBClient()


class RestoreLeads:

    def __init__(self, campaign_id, instantly_api_key):
        self.campaign_id = campaign_id
        self.instantly = InstantlyAPI(instantly_api_key)


    def insert_leads_into_mongodb(self, leads):
        return mongodb_client.insert_into_recycled_leads(leads)
    
    def update_lead_in_db(self, lead_email):
        return db.update({'recycled': True}, lead_email)
    

    def process_lead(self,lead, index, restored_leads):
        """
        Function to process a single lead.
        """
        try:
            lead_email = lead.get('lead_email')
            print(f"Processing lead {index+1}: {lead_email}")
            instantly_lead = self.instantly.get_lead_details(lead_email=lead_email, campaign_id=self.campaign_id)
            if len(instantly_lead) == 0:
                return None    
            instantly_lead = instantly_lead[0]
            if instantly_lead.get('status') != 'Completed' and instantly_lead.get('email_replied') != False:
                return None
            new_lead = {
                "email": lead_email,
                "updated_at": lead.get('updated_at'),
                "campaign_id": self.campaign_id,
                "custom_variables": instantly_lead.get('lead_data')
            }
            self.insert_leads_into_mongodb(new_lead)

            self.update_lead_in_db(lead_email)
            restored_leads.append(lead_email)
            logger.info(f"Lead {lead_email} restored successfully")
        except Exception as e:
            logger.error(f"Error processing lead {lead_email}: {e}")
    

    def restore_leads(self, all_leads):
        try:
            """
            Restores leads concurrently using ThreadPoolExecutor.
            """
            restored_leads = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_lead = {
                    executor.submit(self.process_lead, lead, index, restored_leads): lead
                    for index, lead in enumerate(all_leads)
                }
                for index,future in enumerate(concurrent.futures.as_completed(future_to_lead)):
                    try:
                        future.result() 
                        if (index + 1) % 10 == 0:  
                            time.sleep(2)  # 
                    except Exception as e:
                        lead = future_to_lead[future]
                        logger.error(f"Error in processing lead {lead.get('lead_email')}: {e}")
            logger.info("Restored leads count: %s", len(restored_leads))
            if len(restored_leads) > 0 :
                logger.info(f"Deleting leads from campaign {self.campaign_id}")
                self.instantly.delete_lead_from_campaign(lead_list=restored_leads, campaign_id=self.campaign_id)
       
        except Exception as e:
            logger.error(f"Error in recycle_leads: {e}")
       
        
        

def restore_leads_from_db(campaign_id):
    try:
        total_leads = 1000
        if campaign_id == "ecdc673c-3d90-4427-a556-d39c8b69ae9f":
            total_leads = 2000
        
        logger.info(f"total_leads {total_leads}")
        _, _, instantly_api_key = get_campaign_details(campaign_id)
        offset = 0
        limit = 100

        # while True:
        last_updated_at = datetime.now() - timedelta(days=15)
        last_updated_at = last_updated_at.isoformat()  
        while offset < total_leads:
            all_leads = db.get_all_recycle_leads_v2(campaign_id, last_updated_at, offset, limit).data
            recycle_leads = RestoreLeads(campaign_id=campaign_id, instantly_api_key=instantly_api_key)
            recycle_leads.restore_leads(all_leads)
            offset += limit
            logger.info(f"offset {offset}")

        logger.info(f"total leads restored {offset}/{total_leads}")

    except Exception as e:
        logger.error(f"Error in recycle_leads_from_db: {e}")