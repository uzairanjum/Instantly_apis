from supabase import create_client, Client
from typing import Optional, Union, Dict
from src.common.enum import SummaryType
from src.settings import settings
from src.common.logger import get_logger

import time
import functools

logger = get_logger(__name__)

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
        self.organizations = "organizations"
        self.csv_details = "csvs"
        self.db: Client = create_client(supabase_url , supabase_key)

    def __repr__(self) -> Client:
        return self.db
    
    @retry(max_attempts=5, delay=2)
    def insert(self, row: dict)-> Union[Dict, None]:
        return self.db.table(self.summary).insert([row]).execute()
    

    @retry(max_attempts=3, delay=2)
    def insert_packback_data(self, row: dict)-> Union[Dict, None]:
        try:
            return self.db.table('leads').insert([row]).execute()
        except Exception as e:
            logger.error(f"Error inserting packback data: {e}")
            return None
    
    @retry(max_attempts=5, delay=2)
    def get(self, email: str)-> Union[Dict, None]:
        return self.db.table(self.summary).select("lead_email").eq('lead_email', email).execute()
    
    @retry(max_attempts=5, delay=2)
    def get_by_email(self, email: str)-> Union[Dict, None]:
        return self.db.table(self.summary).select("draft_email, from_account, message_uuid, campaign_id, conversation").eq('lead_email', email).execute()

    @retry(max_attempts=5, delay=2)
    def get_all_by_campaign_id(self, campaign_id: str, updated_at: str)-> Union[Dict, None]:
        return self.db.table(self.summary).select("from_account, conversation, lead_email, status").gte('updated_at', updated_at).eq('campaign_id', campaign_id).eq('reply', True).execute()

    @retry(max_attempts=5, delay=2)
    def get_campaign_details(self, campaign_id: str)-> Union[Dict, None]:
        return self.db.table(self.campaigns) \
            .select("campaign_id, campaign_name, organizations(name, api_key, llm_api_key)") \
            .eq('campaign_id', campaign_id) \
            .execute()
    
    @retry(max_attempts=5, delay=2)
    def get_campaign_llm_key_by_name(self, name: str)-> Union[Dict, None]:
        return self.db.table(self.organizations).select("llm_api_key").eq('name', name).execute()
    
    @retry(max_attempts=5, delay=2)
    def get_all_campaigns(self, organization_id: str)-> Union[Dict, None]:
        return self.db.table(self.campaigns).select("campaign_id, campaign_name").eq('organization_id', organization_id).eq('active', True).execute()
    
    @retry(max_attempts=5, delay=2)
    def get_csv_detail(self, campaign_id: str, summary_type: SummaryType)-> Union[Dict, None]:
        return self.db.table(self.csv_details).select("csv_name, worksheet_name").eq('campaign_id', campaign_id).eq('summary_type', summary_type).execute()
  
    @retry(max_attempts=5, delay=2)
    def get_all_false_flag(self, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table(self.summary).select("lead_email, campaign_id").eq('flag', False).range(offset, offset + limit - 1).order('sent_date', desc=False).execute()
    
    @retry(max_attempts=5, delay=2)
    def get_all_true_flag_leads(self,start_date: str, end_date: str, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table(self.summary).select("lead_email, campaign_id").eq('flag', True).gt('sent_date', start_date).lt('sent_date', end_date).range(offset, offset + limit - 1).order('sent_date', desc=False).execute()
    
    @retry(max_attempts=5, delay=2)
    def get_all_leads(self, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table(self.summary).select("lead_email, university_name, sent_date, outgoing,incoming,reply,status,from_account, lead_status,first_reply_after,url").eq('flag', True).range(offset, offset + limit - 1).order('sent_date', desc=False).execute()
    

    @retry(max_attempts=5, delay=2)
    def get_all_leads_last_contact(self, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table(self.summary).select("lead_email , conversation").eq('last_contact', 'X').range(offset, offset + limit - 1).order('sent_date', desc=False).execute()
    

    @retry(max_attempts=5, delay=2)
    def get_all_interested_leads(self, campaign_id: str) -> Union[Dict, None]:
        return self.db.table(self.summary).select("lead_email , conversation").eq('campaign_id', campaign_id).eq('status', 'Interested').neq("first_reply_after", 3).order('sent_date', desc=False).execute()

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
    def get_flag_true_records(self, campaign_id: str, last_date: str,offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        try:
            logger.info("get_flag_true_records %s - %s ", campaign_id, last_date)
            return self.db.table(self.summary).select( "lead_email, university_name, sent_date, last_contact, outgoing,incoming,reply,status,from_account, lead_status,first_reply_after,url").eq('campaign_id', campaign_id).gte('last_contact', last_date).eq('flag', True).range(offset, offset + limit - 1).execute()
        except Exception as e:
            logger.error(f"Error get_flag_true_records: {e}")
            return None
    
        
    @retry(max_attempts=5, delay=2)
    def get_offset(self ):
        return self.db.table('cap').select("limit, offset").execute()
    

    def update_offset(self, offset: int):
        return self.db.table('cap').update({"offset": offset}).eq('id', 1).execute()
    




    @retry(max_attempts=5, delay=2)
    def get_all_leads_by_campaign(self, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table(self.summary).select( "lead_email, university_name, sent_date, last_contact, outgoing,incoming,reply,status,from_account, lead_status,first_reply_after,url").eq('campaign_id', 'ecdc673c-3d90-4427-a556-d39c8b69ae9f').eq('reply', True).range(offset, offset + limit - 1).order('sent_date', desc=False).execute()
    

    @retry(max_attempts=5, delay=2)
    def get_all_recycle_leads(self,campaign_id: str, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table(self.summary).select( "lead_email").eq('campaign_id',campaign_id).eq('reply', False).eq('outgoing', 3).eq('recycled', False).range(offset, offset + limit - 1).order('updated_at', desc=False).execute()
    

    @retry(max_attempts=3, delay=2)
    def get_all_recycle_leads_v2(self, campaign_id: str, last_updated_at, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        try:
            return self.db.table(self.summary).select("id, lead_email, updated_at") \
                .eq('campaign_id', campaign_id) \
                .eq('reply', False).in_('outgoing', [3,6,9]) \
                .eq('recycled', False) \
                .lte('updated_at', last_updated_at) \
                .range(offset, offset + limit - 1) \
                .order('updated_at', desc=False) \
                .execute()
        except Exception as e:
            logger.error(f"Error getting all recycle leads: {e}")
            return None
        
    @retry(max_attempts=5, delay=2)
    def get_new_enriched_leads(self, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table('leads').select("*").eq('downloaded', False).eq('approved', True).range(offset, offset + limit - 1).order('id', desc=False).execute()
    
    @retry(max_attempts=5, delay=2)
    def update_new_enrich_leads(self, row, email) -> Union[Dict, None]:
        try:
            return self.db.table('leads').update([row]).eq('email', email).execute()
        except Exception as e:
            logger.error(f"Error updating new enriched leads: {e}")
            time.sleep(1)
            logger.info(f"Retrying update_new_enrich_leads for {email}")
            return self.db.table('leads').update([row]).eq('email', email).execute()
        
    @retry(max_attempts=5, delay=2)
    def get_status_false(self)-> Union[Dict, None]:
        return self.db.table(self.domain_health).select("*").eq("status", False).execute()

    @retry(max_attempts=5, delay=2)
    def update_by_mailboxId(self, row: dict, mailboxId: str)-> Union[Dict, None]:
        return self.db.table(self.domain_health).update(row).eq('mailboxId', mailboxId).execute()
    

    @retry(max_attempts=5, delay=2)
    def insert_many(self, rows: list)-> Union[Dict, None]:
        try:
            return self.db.table(self.domain_health).insert(rows).execute()
        except Exception as e:
            logger.error(f"Error inserting many rows: {e}")
            return None
        
    @retry(max_attempts=5, delay=2)
    def get_leads(self, offset: int = 0, limit: int = 100) -> Union[Dict, None]:
        return self.db.table('leads').select( "email").range(offset, offset + limit - 1).execute()
