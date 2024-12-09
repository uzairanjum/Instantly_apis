
from src.configurations.instantly import InstantlyAPI
from src.database.supabase import SupabaseClient
from src.database.mongodb import MongoDBClient
from datetime import datetime, timedelta
from src.common.logger import get_logger

logger = get_logger('Recycled&RestoredLeads')

db = SupabaseClient()
mongodb_client = MongoDBClient()


class RecycledLeadsV2:

    def __init__(self, campaign_id, instantly_api_key):
        self.campaign_id = campaign_id
        self.instantly = InstantlyAPI(instantly_api_key)


    def get_leads_from_db(self, last_updated_at, offset, limit):
        return db.get_all_recycle_leads_v2(self.campaign_id, last_updated_at, offset, limit).data
    

    def insert_leads_into_mongodb(self, leads):
        return mongodb_client.insert_into_recycled_leads(leads)
    


    def restore_leads(self):
        offset = 0
        limit = 2

        # while True:
        last_updated_at = datetime.now() - timedelta(days=15)
        last_updated_at = last_updated_at.isoformat()  # Changed to ISO format
        restored_leads = []

        leads = self.get_leads_from_db(last_updated_at, offset, limit)

        for lead in leads:
            instantly_lead = self.instantly.get_lead_details(lead_email=lead.get('lead_email'), campaign_id=self.campaign_id)
            if len(instantly_lead) == 0:
                continue    
            instantly_lead = instantly_lead[0]
            if instantly_lead.get('status') != 'Completed' and instantly_lead.get('email_replied') != False:
                continue
            new_lead = {
                "email": lead.get('lead_email'),
                "updated_at": lead.get('updated_at'),
                "campaign_id": self.campaign_id,
                "custom_variables": instantly_lead.get('lead_data')
            }
            self.insert_leads_into_mongodb(new_lead)
            db.update(lead.get('id'), {'recycled': True})

            restored_leads.append(lead.get('lead_email'))

            logger.info(f"Lead {lead.get('lead_email')} restored successfully")

