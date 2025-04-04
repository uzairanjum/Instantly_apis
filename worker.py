import pytz
import time
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from src.core.leadHistory import get_data_from_instantly
from src.common.logger import get_logger
from src.database.supabase import SupabaseClient
from src.database.redis import RedisConfig
import concurrent.futures
from rq import Queue, Worker
from src.core.summary import Summary
from src.core.restoreLeads import restore_leads_from_db
from src.core.mailtester import update_domain_health_by_mailboxId, add_mail_tester_emails_to_campaign_contacts
from src.crm.salesforce import SalesforceClient
from src.common.utils import construct_email_text_from_history
from datetime import datetime, timedelta


db = SupabaseClient()
redis_config = RedisConfig()

logger = get_logger('WORKER')
ct_timezone = pytz.timezone("US/Central")

instantly_queue = Queue("instantly_queue", connection=redis_config.redis)



##################################################################
##############    function for type form payload   ###############
##################################################################


def update_lead_details():
    try:
        logger.info("scheduler is running")
        offset = 0  
        limit = 500
        
        while True:
            all_leads = db.get_all_false_flag(offset=offset, limit=limit).data
            print(len(all_leads))
            # all_leads = db.get_all_leads_by_campaign(offset=offset, limit=limit).data

            if len(all_leads) == 0: 
                break
            offset += limit 
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(get_data_from_instantly, row.get("lead_email", None), row.get("campaign_id", None),'cron', index + 1, True): row for index,row in enumerate(all_leads)}
                
                for index, future in enumerate(concurrent.futures.as_completed(futures)):
                    try:
                        if (index + 1) % 10 == 0:  
                            time.sleep(2)  # 
                    except Exception as e:
                        logger.error(f"Error processing lead: {futures[future]['email']}. Error: {e}")

            if len(all_leads) == 0: 
                break  # This line ensures the loop exits when no more leads are available

    except Exception as e:
        logger.exception("Exception occurred get_lead_details %s", e)




def check_campaign_contacts():
    try:
        logger.info("check_campaign_contacts is running")

        campaign_details = [{'campaign_id': 'ecdc673c-3d90-4427-a556-d39c8b69ae9f', 'higher_value': 5000, 'lower_value': 2500}, 
         {'campaign_id': 'fd0630c6-7aa1-471c-acae-0a77a8a63b1a', 'higher_value': 140, 'lower_value': 70}, 
         {'campaign_id': '6c020a71-af8e-421a-bf8d-b024c491b114', 'higher_value': 400, 'lower_value': 200}]



        for campaign_detail in campaign_details:            
            campaign_id:str = campaign_detail.get('campaign_id')
            higher_value:int = campaign_detail.get('higher_value')
            lower_value:int = campaign_detail.get('lower_value')
            summary = Summary(campaign_id=campaign_id)
            summary.notify_internally(higher_value, lower_value)
    except Exception as e:
        logger.exception("Exception occurred check_campaign_contacts %s", e)




def restore_leads():
    try:
        logger.info("restore_leads is running")
        for campaign_id in ["ecdc673c-3d90-4427-a556-d39c8b69ae9f"]:
            logger.info(f"campaign_id {campaign_id}")
            restore_leads_from_db(campaign_id)
    except Exception as e:
        logger.exception("Exception occurred restore_leads %s", e)



def add_mail_tester_emails_to_campaign():
    try:
        logger.info("add_mail_tester_emails_to_campaign_contacts is running")
        for campaign_id in ['7e974d72-6c9e-40f1-9979-dd69ba5876c3']:
            logger.info(f"campaign_id {campaign_id}")
            add_mail_tester_emails_to_campaign_contacts(campaign_id)
    except Exception as e:
        logger.exception("Exception occurred add_mail_tester_emails_to_campaign_contacts %s", e)


def update_salesforce_tasks():
    try:
        logger.info("update_salesforce_tasks is running")
        updated_at = (datetime.now() - timedelta(hours=24)).isoformat()
        db = SupabaseClient()
        for campaign_id in ['7df15bbb-4743-4856-a419-dca02803cec7', 'bda49631-4c89-4fb2-a860-2800df0f223f']:
            result = db.get_all_by_campaign_id(campaign_id, updated_at).data
            print(len(result))
            for row in result:
                email = row.get('lead_email')
                status = row.get('status').replace(" ", "")
                from_account = row.get('from_account')
                conversation = row.get('conversation')
                
                sf = SalesforceClient(email)
                try:
                    conversation = construct_email_text_from_history(conversation)
                    sf.create_update_task(conversation, status)
                except Exception as e:
                    conversation = conversation[:2]
                    conversation = construct_email_text_from_history(conversation)
                    sf.create_update_task(conversation, status)
                    logger.error("Error creating update task %s", e)
                time.sleep(1)

    except Exception as e:
        logger.exception("Exception occurred update_salesforce_tasks %s", e)

##################################################################
##### scheduler for  initial_message/follow_up/send_summary  #####
##################################################################

try:
    scheduler = BackgroundScheduler()
    cron_trigger_at_11_sun_pm = CronTrigger( hour=23, minute=0, second=0, day_of_week="sun", timezone=ct_timezone)
    cron_trigger_at_11_tue_pm = CronTrigger( hour=23, minute=0, second=0, day_of_week="tue", timezone=ct_timezone)
    cron_trigger_at_11_pm_daily = CronTrigger( hour=23, minute=0, second=0, day_of_week="mon-sun", timezone=ct_timezone)
    cron_trigger_at_09am = CronTrigger( hour="09", minute=0, second=0, day_of_week="sat-sun", timezone=ct_timezone )
    cron_trigger_at_12pm = CronTrigger( hour="12", minute=0, second=0, day_of_week="fri", timezone=ct_timezone )
    
except Exception as e:
    logger.error(f"Error: {e}")



if __name__ == "__main__":
    try:
        logger.info("scheduler is running")
        scheduler.add_job(update_lead_details, 'interval', minutes=30)
        scheduler.add_job(update_salesforce_tasks, 'interval', minutes=40)
        scheduler.start()
        worker = Worker([instantly_queue], connection=redis_config.redis)
        worker.work()
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


# {
#     "lead_email": "reginarhymes@aol.com",
#     "event_type": "reply_received",
#     "campaign_id": "7df15bbb-4743-4856-a419-dca02803cec7"
# }

# michelelahaie@gmail.com
# 7df15bbb-4743-4856-a419-dca02803cec7