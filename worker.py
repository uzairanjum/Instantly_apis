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





db = SupabaseClient()
redis_config = RedisConfig()

logger = get_logger('WORKER')
ct_timezone = pytz.timezone("US/Central")

instantly_queue = Queue("instantly_queue", connection=redis_config.redis)



##################################################################
##############    function for type form paylaod   ###############
##################################################################


def update_lead_details():
    try:
        logger.info("scheduler is running")
        offset = 0  
        limit = 1000
        leads_array = [] 
        
        while True:
            all_leads = db.get_all_false_flag(offset=offset, limit=limit).data

            if len(leads_array) >= 1000:
                break
            
            if len(all_leads) == 0: 
                break

            leads_array.extend(all_leads)
            
            offset += limit 
        logger.info("leads_array %s", len(leads_array))
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(get_data_from_instantly, row.get("lead_email", None), row.get("campaign_id", None),'cron', index + 1, True): row for index,row in enumerate(leads_array)}
            for index, future in enumerate(concurrent.futures.as_completed(futures)):
                try:
                    if (index + 1) % 10 == 0:  # After every 10 requests
                        time.sleep(2)  # Sleep for 2 seconds
                except Exception as e:
                    logger.error(f"Error processing lead: {futures[future]['email']}. Error: {e}")




    except Exception as e:
        logger.exception("Exception occurred get_lead_details %s", e)




def update_daily_summary_report():
    try:
        logger.info("update_daily_summary_report is running")
        summary = Summary(campaign_id="ecdc673c-3d90-4427-a556-d39c8b69ae9f")
        summary.update_daily_summary()
    except Exception as e:
        logger.exception("Exception occurred update_daily_summary_report %s", e)


def update_weekly_summary_report():
    try:
        logger.info("update_weekly_summary_report is running")
        summary = Summary(campaign_id="ecdc673c-3d90-4427-a556-d39c8b69ae9f")
        summary.update_weekly_summary()
    except Exception as e:
        logger.exception("Exception occurred update_weekly_summary_report %s", e)

##################################################################
##### scheduler for  initial_message/follow_up/send_summary  #####
##################################################################

try:
    scheduler = BackgroundScheduler()
    cron_trigger_at_11pm = CronTrigger( hour=23, minute=0, second=0, day_of_week="tue", timezone=ct_timezone)
    
except Exception as e:
    logger.error(f"Error: {e}")



if __name__ == "__main__":
    try:
        logger.info("scheduler is running")
        scheduler.add_job(update_lead_details, 'interval', hours=3)
        scheduler.add_job(update_daily_summary_report, 'interval', hours=6)
        scheduler.add_job(update_weekly_summary_report,cron_trigger_at_11pm)
        scheduler.start()
        worker = Worker([instantly_queue], connection=redis_config.redis)
        worker.work()
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
# 