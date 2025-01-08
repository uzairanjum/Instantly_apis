# 

from src.common.logger import get_logger
from src.common.utils import get_campaign_details, construct_email_body_from_history
from src.configurations.instantly import InstantlyAPI
from src.database.supabase import SupabaseClient


db = SupabaseClient()


logger = get_logger("Chicory")



class ChicoryForwarder:
    def __init__(self):
        self.to_email = 'rajpoot.waryah@gmail.com'

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

            email_body = construct_email_body_from_history(conversation, lead_email, from_account)

        
            logger.info("sending email to :: %s", lead_email)
            logger.info("subject :: %s", subject)
            logger.info("from_account :: %s", from_account)
            logger.info("message_uuid :: %s", message_uuid)
            logger.info("linkedin_url :: %s", linkedin_url)

            message_content = f"<div> <br><br><strong>Interested Lead</strong><br><br>Email: {lead_email}<br>LinkedIn Profile: {linkedin_url}<br><br><br><strong>Email Conversation History</strong><br><br>{email_body}</div>"

            logger.info("message_content :: %s", message_content)



            send = instantly.send_reply(
                message=message_content,
                from_email=from_account,
                to_email=self.to_email,
                uuid=message_uuid,
                subject=subject, 
                # bcc='uzair@hellogepeto.com, mert@hellogepeto.com'

            )
            if send == 200:
                logger.info("Email sent successfully - %s", self.to_email)
                db.update({"flag": False}, lead_email)
            return True
        except Exception as e:
            logger.error("Error sending email - %s", e)
            return False
        