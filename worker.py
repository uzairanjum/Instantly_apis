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


def update_daily_summary_report():
    try:
        logger.info("update_daily_summary_report is running")
        for organization_id in [1, 2, 3]:
            all_campaigns = db.get_all_campaigns(organization_id).data
            for campaign in all_campaigns:
                logger.info(f"campaign {campaign.get("campaign_id")}, {campaign.get("campaign_name")}, {organization_id}")
                summary = Summary(campaign_id=campaign.get("campaign_id"))
                summary.update_daily_summary()
    except Exception as e:
        logger.exception("Exception occurred update_daily_summary_report %s", e)

def three_days_summary_report():
    try:
        logger.info("three_days_summary_report is running")
        for organization_id in [1,2,3]:
            all_campaigns = db.get_all_campaigns(organization_id).data
            for campaign in all_campaigns:
                logger.info(f"campaign {campaign.get("campaign_id")}, {campaign.get("campaign_name")}, {organization_id}\n\n")
                summary = Summary(campaign_id=campaign.get("campaign_id"))
                summary.three_days_summary_report()
    except Exception as e:
        logger.exception("Exception occurred update_daily_summary_report %s", e)

def update_weekly_summary_report(organization_id):
    try:
        logger.info("update_weekly_summary_report is running")
        all_campaigns = db.get_all_campaigns(organization_id).data
        for campaign in all_campaigns:
            print(f"campaign {campaign.get("campaign_id")}, {campaign.get("campaign_name")}, {organization_id}")
            # if campaign.get("campaign_id") in ["01ed88d3-e261-4026-b0a2-b65a2e100394", "612488c7-dc53-4bc6-a645-25fc5cb60b37" ] :
            # if campaign.get("campaign_id") in ["ba6b3507-c26c-484e-a773-dd36a4c07b65", "dedbd915-f18a-4aaf-9ce5-89d2442be355", "25acb19a-ef31-4028-ade1-a0a822654007"] :
            summary = Summary(campaign_id=campaign.get("campaign_id"))
            summary.update_weekly_summary()
    except Exception as e:
        logger.exception("Exception occurred update_weekly_summary_report %s", e)


def check_campaign_contacts():
    try:
        logger.info("check_campaign_contacts is running")
        for campaign_id in ["ecdc673c-3d90-4427-a556-d39c8b69ae9f"]:
            logger.info(f"campaign_id {campaign_id}")
            summary = Summary(campaign_id=campaign_id)
            summary.notify_internally()
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

        # update lead details
        scheduler.add_job(update_lead_details, 'interval', hours=1)

        # update daily summary report
        scheduler.add_job(update_daily_summary_report, 'interval', hours=3)

        # packback
        scheduler.add_job(update_weekly_summary_report, cron_trigger_at_11_tue_pm, args=[1]) 

        # havocSheild
        scheduler.add_job(update_weekly_summary_report, cron_trigger_at_11_sun_pm, args=[3]) 


        # old leads dumps into mongodb
        scheduler.add_job(restore_leads, 'interval', hours=24)

        # check domain health
        scheduler.add_job(update_domain_health_by_mailboxId, cron_trigger_at_09am)


        # add mail tester emails to campaign
        scheduler.add_job(add_mail_tester_emails_to_campaign, cron_trigger_at_12pm)


        # check campaign contacts
        scheduler.add_job(check_campaign_contacts, cron_trigger_at_11_pm_daily)
        
        scheduler.start()
        worker = Worker([instantly_queue], connection=redis_config.redis)
        worker.work()
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

