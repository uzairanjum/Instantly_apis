from src.database.supabase import SupabaseClient
from src.common.logger import get_logger
from src.configurations.instantly import InstantlyAPI
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.common.utils import get_campaign_details
from datetime import datetime
import requests
import time
logger = get_logger("MailTester")

db = SupabaseClient()

class MailTester():
    def __init__(self, prefix):
        self.url =  f"https://www.mail-tester.com/{prefix}&format=json"

    def get_data(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            data = response.json()
            if not data.get('status'):
                return None
            # Extract and return only the required values
            required_keys = [
                "title",
                "displayedMark",
                "status",
                "mailboxId",
                "messageId",
                "messageInfo"
            ]

            result = {}
            for key in required_keys:
                if key == 'messageInfo':
                    email_info = data.get(key, {})
                    result['domain'] = email_info.get('bounceAddress')
                elif key == 'displayedMark':
                    displayed_mark = data.get(key)
                    if displayed_mark and '/' in displayed_mark:
                        score = displayed_mark.split('/')[0]
                        result['score'] = float(score)
                    else:
                        result['score'] = None
                else:
                    result[key] = data.get(key)
            result['url'] = f"https://www.mail-tester.com/{result['mailboxId']}"
               
            return result
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            return None
                

    



def update_domain_health_by_mailboxId():
    try:
        all_data = db.get_status_false().data
        logger.info(f"all_data: {len(all_data)}")
        def process_mailbox(mailboxId, index):
            tester = MailTester(mailboxId)
            print(f"index: {index} -- {mailboxId} ")
            result = tester.get_data()
            if result:
                result['updated_at'] = datetime.now().isoformat() 
                db.update_by_mailboxId(result, mailboxId)
                print(f"index: {index} -- {mailboxId}")
                return True

        with ThreadPoolExecutor(5) as executor:
            futures = {executor.submit(process_mailbox, data['mailboxId'], index): data for index, data in enumerate(all_data)}
            for future in as_completed(futures):
                mailbox_data = futures[future]
                try:
                    future.result()  # This will raise an exception if the call failed
                except Exception as e:
                    logger.error(f"Error processing mailboxId {mailbox_data['mailboxId']}: {e}")
    except Exception as e:
        logger.error(f"Error get_domain_health_by_mailboxId: {e}")
        return None
    


def add_mail_tester_emails_to_campaign_contacts(campaign_id: str):
    _, organization_name, instantly_api_key, _ = get_campaign_details(campaign_id)
    if organization_name is None:
        return None
    count = 0

    if organization_name == 'packback':
        count = 252
    elif organization_name == 'havocSheild':
        count = 10
    emails = generate_mailboxId(organization_name, count)
    if len(emails) == 0:
        return None
    instantly = InstantlyAPI(instantly_api_key)
    instantly.add_lead_to_campaign(campaign_id=campaign_id, lead_list=emails)


    

def generate_mailboxId(client_name: str, count: int):

    logger.info(f"Generating {count} emails with base_str='{client_name}'")
    timestamp = int(time.time())
    emails = []
    all_domains = []
    for i in range(count):
        mailboxId = f"uqarni-{client_name}{i+1}{timestamp}"
        data = {"mailboxId": mailboxId, "status": False , "client_name" :client_name}
        all_domains.append(data)
        emails.append({"email": f"{mailboxId}@srv1.mail-tester.com", "mailboxId": mailboxId})

    chunk_size = 20
    for start in range(0, len(all_domains), chunk_size):
        end = start + chunk_size
        chunk = all_domains[start:end]
        insert_many_domain_health(chunk)
    logger.info("Email generation completed successfully.")
    return emails


def insert_many_domain_health(result: list):
    try:
        db.insert_many(result)
        return True
    except Exception as e:
        logger.error(f"Error insert_many_domain_health: {e}")
        return False