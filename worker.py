from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from src.summary import get_lead_details_from_csv_new
from src.logger import get_logger
import pytz

logger = get_logger('WORKER')
ct_timezone = pytz.timezone("US/Central")


##################################################################
##############    function for type form paylaod   ###############
##################################################################


def get_lead_details():
    try:
        logger.info("scheduler is running")
        get_lead_details_from_csv_new()
    except Exception as e:
        logger.exception("Exception occurred get_domain_health_by_mailboxId", e)



##################################################################
##### scheduler for  initial_message/follow_up/send_summary  #####
##################################################################

# try:
#     scheduler = BackgroundScheduler()
#     cron_trigger_at_12pm = CronTrigger( hour="09", minute=0, second=0, day_of_week="sat-sun", timezone=ct_timezone )
    
# except Exception as e:
#     print(f"Error: {e}")

# if __name__ == "__main__":
#     try:
#         # get_domain_health_by_mailboxId()
#         # scheduler.add_job(get_lead_details, cron_trigger_at_12pm)
#         scheduler.start()
#         while True:
#             pass
#     except (KeyboardInterrupt, SystemExit):
#         scheduler.shutdown()


#
# https://c753-2400-adc5-105-8200-c0a6-b6f7-fe06-9f6c.ngrok-free.app/gepeto/outgoing

# outgoing message
# {'timestamp': '2024-10-15T17:08:33.049Z', 'event_type': 'email_sent', 'workspace': 'e55c02d4-5a33-4d5f-a219-83d8c2542336', 'campaign_id': 'ee128a07-2870-4685-a8d3-6dedb9e82609', 'unibox_url': None, 'campaign_name': 'TestWebhookCampaign', 'email_account': 'pat.j@allpackback.com', 'is_first': True, 'lead_email': 'uzairanjum@hellogepeto.com', 'email': 'uzairanjum@hellogepeto.com', 'step': 1, 'variant': 1}

# incoming message
# {'timestamp': '2024-10-15T17:19:19.128Z', 'event_type': 'reply_received', 'workspace': 'e55c02d4-5a33-4d5f-a219-83d8c2542336', 'campaign_id': 'ee128a07-2870-4685-a8d3-6dedb9e82609', 'unibox_url': 'https://app.instantly.ai/app/unibox?thread_search=uzairanjum@hellogepeto.com&selected_wks=e55c02d4-5a33-4d5f-a219-83d8c2542336', 'campaign_name': 'TestWebhookCampaign', 'email_account': 'pat.j@allpackback.com', 'reply_text_snippet': '\n\n\n', 'is_first': True, 'lead_email': 'uzairanjum@hellogepeto.com', 'step': 1, 'email': 'uzairanjum@hellogepeto.com', 'variant': 1, 'reply_subject': 'Re: 1st Email', 'reply_text': 'On Tue, Oct 15, 2024 at 10:08\u202fPM Pat Johnson <pat.j@allpackback.com> wrote:\n\n> HI Uzair\n>\n>\n', 'reply_html': '<div dir="ltr"><br></div><br><div class="gmail_quote"><div dir="ltr" class="gmail_attr">On Tue, Oct 15, 2024 at 10:08\u202fPM Pat Johnson &lt;<a href="mailto:pat.j@allpackback.com">pat.j@allpackback.com</a>&gt; wrote:<br></div><blockquote class="gmail_quote" style="margin:0px 0px 0px 0.8ex;border-left:1px solid rgb(204,204,204);padding-left:1ex"><div>HI Uzair<br><br></div></blockquote></div>\n'}

# import json
# from src.utils import get_lead_details_history

# data = get_lead_details_history("uzairanjum@hellogepeto.com", "University of California, Berkeley", "ee128a07-2870-4685-a8d3-6dedb9e82609", 0)
# print("------------", json.dumps(data))


# get_lead_details()