# 

from src.common.logger import get_logger
from src.common.utils import get_campaign_details
from src.configurations.instantly import InstantlyAPI
from src.database.supabase import SupabaseClient


db = SupabaseClient()


logger = get_logger("HavocShieldForwarder")



class HavocShieldForwarder:
    def __init__(self):
        self.to_email = 'dbutkunas@havocshield.com'

    def forward_email(self, lead_history, data):

        linkedin_url = lead_history.get('linkedin_url')

        try:
            logger.info("forwarding email to :: %s",  self.to_email)
            lead_email = lead_history.get('email')
            from_account = data.get('from_account')
            campaign_id = data.get('campaign_id')
            message_uuid =  data.get('message_uuid')
            conversation = data.get('conversation')
            subject = conversation[0].get('subject')

            _, _, instantly_api_key = get_campaign_details(campaign_id)

            instantly = InstantlyAPI(instantly_api_key)

        
            logger.info("sending email to :: %s", lead_email)
            logger.info("subject :: %s", subject)
            logger.info("from_account :: %s", from_account)
            logger.info("message_uuid :: %s", message_uuid)
            logger.info("linkedin_url :: %s", linkedin_url)
            send = instantly.send_reply(
                message="""\n\n
                Interested Lead: {lead_email}\n
                LinkedIn Profile: {linkedin_url}""",
                from_email=from_account,
                to_email=self.to_email,
                uuid=message_uuid,
                subject=subject, 
                bcc='uzair@hellogepeto.com, mert@hellogepeto.com'

            )
            if send == 200:
                logger.info("Email sent successfully - %s", lead_email)
                db.update({"flag": False}, lead_email)
            return True
        except Exception as e:
            logger.error("Error sending email - %s", e)
            return False
        