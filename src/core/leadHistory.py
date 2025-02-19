from src.configurations.instantly import InstantlyAPI
from src.database.supabase import SupabaseClient
from src.common.utils import get_lead_details_history, get_campaign_details, construct_email_body_from_history,validate_lead_last_reply
from src.core.responder import generate_ai_response, generate_ai_response_for_third_reply, generate_research_response
from src.common.logger import get_logger
from src.common.models import PackbackTenQuestionsRequest,TenQuestionsGeneratorRequest
from src.configurations.justcall import JustCallService
from pytz import timezone
from src.core.packback import PackbackConfig
from src.core.chicory import ChicoryForwarder
from src.core.gepeto import GepetoForwarder



ct_timezone = timezone('US/Central')
logger = get_logger("LeadHistory")


jc = JustCallService()
db = SupabaseClient()
packback_config = PackbackConfig()


class LeadHistory:
    def __init__(self, lead_email, campaign_id, instantly_api_key):
        self.lead_email = lead_email
        self.campaign_id = campaign_id
        self.instantly = InstantlyAPI(instantly_api_key)

    def get_lead_details(self):
        lead_details = self.instantly.get_lead_details(lead_email = self.lead_email, campaign_id = self.campaign_id)
        if lead_details:
            lead_details = lead_details[0].get('lead_data')
            return {
                    "email" : lead_details.get('email'), 
                    "university_name" : lead_details.get('University Name'),
                    "AE" : lead_details.get('AE'), 
                    "CO":lead_details.get('Contact Owner: Full Name'), 
                    "lead_last_name": lead_details.get('lastName'), 
                    "lead_first_name":lead_details.get('firstName'),
                    "course_name": lead_details.get('Course Name'), 
                    "course_description": lead_details.get('Course Description'), 
                    "course_code":lead_details.get('Course Code') if lead_details.get('Course Code') else lead_details.get('FA24 Course Code'),
                    "question_1" : lead_details.get('Question 1'), 
                    "question_2" : lead_details.get('Question 2'),
                    "question_3" : lead_details.get('Question 3'),
                    "question_4" : lead_details.get('Question 4'),
                    "linkedin_url": lead_details.get('LinkedIn Profile'),
                    "first_sentence": lead_details.get('first_sentence')
                    }
        

        return lead_details

    def get_lead_emails(self):
        all_emails = self.instantly.get_all_emails(lead=self.lead_email, campaign_id=self.campaign_id)
        if not all_emails:
            return None 
        return all_emails

    def save_lead_history(self, data):
        lead_history = db.get(self.lead_email)
        if len(lead_history.data) > 0:
            logger.info("lead updated :: %s", self.lead_email)
            db.update(data, self.lead_email)
        else:
            logger.info("lead inserted :: %s", self.lead_email)
            db.insert(data)

    def validate_lead_conversation(self):
        pass
    
    

def get_data_from_instantly(lead_email, campaign_id, event, index = 1 , flag = False):
    try:
        campaign_name, organization_name, instantly_api_key, open_api_key = get_campaign_details(campaign_id)
        if organization_name is None:
            return None
        
        instantly_lead = LeadHistory(lead_email, campaign_id, instantly_api_key)
        lead_history = instantly_lead.get_lead_details()

        if lead_history is None:
            return None
        
        logger.info("lead found :: %s", lead_email)
        lead_emails = instantly_lead.get_lead_emails()
        if lead_emails is None:
            return None
        logger.info("lead email history found :: %s", lead_email)
        data =  get_lead_details_history(lead_email, campaign_id, lead_emails, open_api_key)
        if data is None:
            return None
    
        data['flag'] = flag
        data['university_name'] = lead_history.get('university_name', None)
        data['recycled'] = False

        if event =='reply_received' and data.get('status') == "Interested":


            logger.info("Interested lead - %s", lead_email)
            jc.send_message(f"New interested lead -\n\n Organization - {organization_name}\n\nCampaign - {campaign_name}\n\nLead Email - {lead_email}\n\nConversation URL - {data['url']}")
            organization_name = str(organization_name.strip()) 
     
            if organization_name == 'packback' :   
                logger.info("incoming :: %s", data.get('incoming'))
                logger.info("outgoing :: %s", data.get('outgoing'))



                if data.get('incoming') == 1 and data.get('outgoing') % 3 == 0:
                    logger.info("third outgoing email")
                    if data.get('campaign_id') == '6c020a71-af8e-421a-bf8d-b024c491b114':
                        send_email_by_lead_email(lead_history, data, open_api_key)
                    else:
                        third_outgoing_email(lead_history, data, open_api_key)
                elif data.get('incoming') == 1 and data.get('outgoing') % 3 != 0:
                    logger.info("sending email")
                    send_email_by_lead_email(lead_history, data, open_api_key)
                else:
                    logger.info("Need to check cc email if not cc'd then forward")
                    send_email_by_lead_email_forwarding(lead_history, data, open_api_key)
        
            if organization_name == str('chicory'):
                logger.info("chicory lead forwarder")
                ChicoryForwarder().forward_email(lead_history, data)

            if organization_name == str('gepeto'):
                logger.info("gepeto lead forwarder")
                GepetoForwarder().forward_email(lead_history, data)
    
        instantly_lead.save_lead_history(data)
        logger.info("lead email processed - %s :: %s", index, lead_email)
        return data
    except Exception as e:
        logger.error(f"Error get_data_from_instantly: {e}")
        return None
    
def third_outgoing_email(lead_history, data, open_api_key):

    try:
        conversation = data.get('conversation')
        ten_question_prompt = validate_lead_last_reply(conversation, open_api_key)
        packback_response = None

        logger.info("ten_question_prompt for lead - %s :: %s", lead_history.get('email'), ten_question_prompt)
        if not ten_question_prompt:
            logger.info("sending email to :: %s", lead_history.get('email'))
            logger.info("no ten question prompt found")
            return send_email_by_lead_email(lead_history,data, open_api_key)

        if lead_history.get('course_description') is None:
                packback_response = packback_config.packback_ten_questions(PackbackTenQuestionsRequest(
                course_code=lead_history.get('course_code', ''),
                university_name=lead_history.get('university_name', ''),
                professor_name=f"{lead_history.get('lead_first_name', '')} {lead_history.get('lead_last_name', '')}",
                open_ai_model="gpt-4o-mini",
                question1=lead_history.get('question_1', ''),
                question2=lead_history.get('question_2', ''),
                question3=lead_history.get('question_3', ''),
                question4=lead_history.get('question_4', '')
            ))
        else:
            packback_response = packback_config.ten_questions_generator(TenQuestionsGeneratorRequest(course_name=lead_history.get('course_name'), \
                course_description=lead_history.get('course_description'), open_ai_model="gpt-4o-mini", \
                question1=lead_history.get('question_1'), question2=lead_history.get('question_2'), question3=lead_history.get('question_3'), question4=lead_history.get('question_4')))
            
        if packback_response is None:
            logger.info("no response from search and crawl. Now forwarding email")
            return forward_email_by_lead_email(lead_history,data, 'uzair@hellogepeto.com')
    
        questions = packback_response.questions
        for idx in range(len(questions)):   
            lead_history[f'q{idx + 1}'] = questions[idx].question if idx < len(questions) else ''
        return send_email_for_third_reply(lead_history, data, open_api_key)
    except Exception as e:
        logger.error("Error in third_outgoing_email - %s", e)
        return False
            
def send_email_for_third_reply(lead_history,data, open_api_key:str):
    try:
        lead_email =  lead_history.get('email')
        conversation =  data.get('conversation')
        conversation = validate_lead_conversation(conversation)
        conversation.pop()
        response = generate_ai_response_for_third_reply (lead_history, conversation, open_api_key)


        subject = response.get('subject')
        content = response.get('content')
        from_account = data.get('from_account')
        campaign_id = data.get('campaign_id')
        message_uuid =  data.get('message_uuid')
        cc = response.get('cc')
        bcc = response.get('bcc')

        email_cc = data['cc']
        email_bcc = data['bcc']

        _, _, instantly_api_key,_ = get_campaign_details(campaign_id)
        instantly = InstantlyAPI(instantly_api_key)


        logger.info("sending email to :: %s", lead_email)
        logger.info("subject :: %s", subject)
        logger.info("content :: %s", content)
        logger.info("from_account :: %s", from_account)
        logger.info("message_uuid :: %s", message_uuid)
        logger.info("cc :: %s", cc)
        logger.info("bcc :: %s", bcc)
        logger.info("email_cc :: %s", email_cc)
        logger.info("email_bcc :: %s", email_bcc)

        email_body = construct_email_body_from_history(conversation, lead_email, from_account)

        merged_email = f"""
        <div>
            {content}
            <br>
            <br>
            {email_body}
        </div>
        """



        send = instantly.send_reply(
            message=merged_email,
            from_email=from_account,
            to_email=lead_email,
            uuid=message_uuid,
            subject=subject, 
            cc=cc,
            bcc=bcc
        )
        if send == 200:
            logger.info("Email sent successfully - %s", lead_email)
            db.update({"flag": False}, lead_email)
        return True
    except Exception as e:
        logger.error("Error sending email - %s", e)
        return False
   
def send_email_by_lead_email(lead_history,data, open_api_key:str):
    try:
        lead_email =  lead_history.get('email')
        conversation =  data.get('conversation')

        conversation = validate_lead_conversation(conversation)

        response = None


        if data.get('campaign_id') == 'ecdc673c-3d90-4427-a556-d39c8b69ae9f':
            print("generating ai response")
            response = generate_ai_response (lead_history, conversation, open_api_key)

        elif data.get('campaign_id') == '6c020a71-af8e-421a-bf8d-b024c491b114':
            print("generating research response")
            response = generate_research_response(lead_history, conversation, open_api_key)
        
        
        if response is None:
            return False



        subject = response.get('subject')
        content = response.get('content')
        from_account = data.get('from_account')
        campaign_id = data.get('campaign_id')
        message_uuid =  data.get('message_uuid')
        cc = response.get('cc')
        bcc = response.get('bcc')

        email_cc = data['cc']
        email_bcc = data['bcc']

        _, _, instantly_api_key,_ = get_campaign_details(campaign_id)
        instantly = InstantlyAPI(instantly_api_key)


        logger.info("sending email to :: %s", lead_email)
        logger.info("subject :: %s", subject)
        logger.info("content :: %s", content)
        logger.info("from_account :: %s", from_account)
        logger.info("message_uuid :: %s", message_uuid)
        logger.info("cc :: %s", cc)
        logger.info("bcc :: %s", bcc)
        logger.info("email_cc :: %s", email_cc)
        logger.info("email_bcc :: %s", email_bcc)


       


        email_body = construct_email_body_from_history(conversation, lead_email, from_account)

        merged_email = f"""
        <div>
            {content}
            <br>
            <br>
            {email_body}
        </div>
        """



        send = instantly.send_reply(
            message=merged_email,
            from_email=from_account,
            to_email=lead_email,
            uuid=message_uuid,
            subject=subject, 
            cc=cc,
            bcc=bcc
        )
        if send == 200:
            logger.info("Email sent successfully - %s", lead_email)
            db.update({"flag": False}, lead_email)
        return True
    except Exception as e:
        logger.error("Error sending email - %s", e)
        return False
   
def send_email_by_lead_email_forwarding(lead_history,data, open_api_key):
    try:
        lead_email =  lead_history.get('email')
        conversation =  data.get('conversation')
        response = generate_ai_response (lead_history, conversation, open_api_key)
        cc = response.get('cc')
        email_cc = data['cc']
        if email_cc != cc:
            return forward_email_by_lead_email(lead_history, data, cc)
        logger.info("No response to lead :: %s", lead_email)

        return True
    except Exception as e:
        logger.error("Error sending email - %s", e)
        return False
   
def forward_email_by_lead_email(lead_history,data, forward_email):
    try:
        logger.info("forwarding email to :: %s", forward_email)
        lead_email = lead_history.get('email')
        from_account = data.get('from_account')
        campaign_id = data.get('campaign_id')
        message_uuid =  data.get('message_uuid')
        conversation = data.get('conversation')
        subject = conversation[0].get('subject')

        _, _, instantly_api_key,_ = get_campaign_details(campaign_id)

        instantly = InstantlyAPI(instantly_api_key)
        email_body = construct_email_body_from_history(conversation, lead_email, from_account)

        

        logger.info("sending email to :: %s", lead_email)
        logger.info("subject :: %s", subject)
        logger.info("from_account :: %s", from_account)
        logger.info("message_uuid :: %s", message_uuid)
        send = instantly.send_reply(
            message=email_body,
            from_email=from_account,
            to_email=forward_email,
            uuid=message_uuid,
            subject=subject, 
        )
        if send == 200:
            logger.info("Email sent successfully - %s", lead_email)
            db.update({"flag": False}, lead_email)
        return True
    except Exception as e:
        logger.error("Error sending email - %s", e)
        return False
    
def validate_lead_conversation(conversation):
    total_outgoing_before_incoming = []
    for item in conversation:
        if item["role"] == "assistant":
            total_outgoing_before_incoming.append(item)
        else:
            break

    if len(total_outgoing_before_incoming) > 3 and len(total_outgoing_before_incoming) <= 6:
        conversation = conversation[3:] 
    elif len(total_outgoing_before_incoming) > 6 and len(total_outgoing_before_incoming) <= 9:
        conversation = conversation[6:]
    elif len(total_outgoing_before_incoming) > 9 and len(total_outgoing_before_incoming) <= 12:
        conversation = conversation[9:]
    
    return conversation