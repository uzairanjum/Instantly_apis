from supabase import create_client, Client
from typing import Optional, Union, Dict
from src.settings import settings
from src.logger import get_logger

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
        self.table_name = "summary"
        self.db: Client = create_client(supabase_url , supabase_key)

    def __repr__(self) -> Client:
        return self.db
    
    @retry(max_attempts=5, delay=2)
    def insert(self, row: dict)-> Union[Dict, None]:
        return self.db.table(self.table_name).insert([row]).execute()
    
    @retry(max_attempts=5, delay=2)
    def get(self, email: str)-> Union[Dict, None]:
        return self.db.table(self.table_name).select("lead_email").eq('lead_email', email).execute()
    
    @retry(max_attempts=5, delay=2)
    def update(self, row: dict, email: str)-> Union[Dict, None]:
        return self.db.table(self.table_name).update(row).eq('lead_email', email).execute()
    
    @retry(max_attempts=5, delay=2)
    def insert_many(self, rows: list)-> Union[Dict, None]:
        try:
            return self.db.table(self.table_name).insert(rows).execute()
        except Exception as e:
            logger.error(f"Error inserting many rows: {e}")
            return None
