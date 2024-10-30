from supabase import create_client, Client
from typing import Optional, Union, Dict
from src.common.enum import SummaryType
from src.settings import settings
from src.common.logger import get_logger

import time
import functools

logger = get_logger("Supabase")

def retry(max_attempts, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            retries = 0
            while retries < max_attempts:
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    # logging.exception(f"Exception occurred. Retrying... {e}")
                    retries += 1
                    # logging.info(f"Exception occurred. Retrying <{func.__name__}>")
                    time.sleep(delay)
            pass
        return wrapper
    return decorator


class SupabaseClient():

    def __init__(self):
        supabase_url: str= settings.SUPABASE_URL
        supabase_key: str = settings.SUPABASE_KEY
        self.max_retries = 3
        self.summary = "summary"
        self.domain_health = "domain_health"
        self.campaigns = "campaigns"
        self.csv_details = "csvs"
        self.db: Client = create_client(supabase_url , supabase_key)

    def __repr__(self) -> Client:
        return self.db
    
    @retry(max_attempts=5, delay=2)
    def insert(self, row: dict)-> Union[Dict, None]:
        return self.db.table(self.summary).insert([row]).execute()
    
    @retry(max_attempts=5, delay=2)
    def get(self, email: str)-> Union[Dict, None]:
        return self.db.table(self.summary).select("lead_email").eq('lead_email', email).execute()
    
    @retry(max_attempts=5, delay=2)
    def get_by_email(self, email: str)-> Union[Dict, None]:
        return self.db.table(self.summary).select("draft_email, from_account, message_uuid, campaign_id").eq('lead_email', email).execute()

    @retry(max_attempts=5, delay=2)
    def get_campaign_details(self, campaign_id: str)-> Union[Dict, None]:
        return self.db.table(self.campaigns) \
            .select("campaign_id, campaign_name, organizations(name, api_key, zapier_url)") \
            .eq('campaign_id', campaign_id) \
            .execute()
    
    @retry(max_attempts=5, delay=2)
    def get_all_campaigns(self)-> Union[Dict, None]:
        return self.db.table(self.campaigns).select("campaign_id, campaign_name").eq('active', True).execute()
    
    @retry(max_attempts=5, delay=2)
    def get_csv_detail(self, campaign_id: str, summary_type: SummaryType)-> Union[Dict, None]:
        return self.db.table(self.csv_details).select("csv_name, worksheet_name").eq('campaign_id', campaign_id).eq('summary_type', summary_type).execute()
  
    @retry(max_attempts=5, delay=2)
    def get_all_false_flag(self, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table(self.summary).select("lead_email, campaign_id").eq('flag', False).range(offset, offset + limit - 1).order('sent_date', desc=False).execute()
    
    
    @retry(max_attempts=5, delay=2)
    def get_all_leads(self, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table(self.summary).select("lead_email, university_name, sent_date, outgoing,incoming,reply,status,from_account, lead_status,first_reply_after,url").eq('flag', True).range(offset, offset + limit - 1).order('sent_date', desc=False).execute()
    

    @retry(max_attempts=5, delay=2)
    def get_all_leads_last_contact(self, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table(self.summary).select("lead_email , conversation").eq('last_contact', 'X').range(offset, offset + limit - 1).order('sent_date', desc=False).execute()

    @retry(max_attempts=5, delay=2)
    def update(self, row: dict, email: str)-> Union[Dict, None]:
        return self.db.table(self.summary).update(row).eq('lead_email', email).execute()
    
    @retry(max_attempts=5, delay=2)
    def get_count(self, campaign_id: str, start_of_week: str, end_of_week: str) -> Union[Dict, None]:
        return self.db.table(self.summary).select("campaign_id", count="exact").eq('campaign_id', campaign_id).gt('last_contact', start_of_week).lt('last_contact', end_of_week).eq('status', 'Interested').execute()
    
    @retry(max_attempts=5, delay=2)
    def get_domain_health_count(self, client_name: str, start_of_week: str, end_of_week: str) -> Union[Dict, None]:
        return self.db.table(self.domain_health).select("score", count="exact").gt('score', 8).eq('client_name', client_name).gt('updated_at', start_of_week).lt('updated_at', end_of_week).execute()
    
    @retry(max_attempts=5, delay=2)
    def get_last_twenty_four_records(self, campaign_id: str, last_date: str, end_date: str,offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        logger.info("get_last_twenty_four_records %s - %s - %s", campaign_id, last_date, end_date)
        return self.db.table(self.summary).select( "lead_email, university_name, sent_date, last_contact, outgoing,incoming,reply,status,from_account, lead_status,first_reply_after,url").eq('campaign_id', campaign_id).gte('last_contact', last_date).eq('flag', True).range(offset, offset + limit - 1).execute()
    
    @retry(max_attempts=5, delay=2)
    def insert_many(self, rows: list)-> Union[Dict, None]:
        try:
            return self.db.table(self.summary).insert(rows).execute()
        except Exception as e:
            logger.error(f"Error inserting many rows: {e}")
            return None
