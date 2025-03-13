
from src.common.utils import get_logger, validate_lead_last_reply, validate_lead_conversation, get_campaign_details, construct_email_body_from_history
from src.core.packback import PackbackCourseGenerator
from src.configurations.instantly import InstantlyAPI
from src.database.supabase import SupabaseClient
from src.common.models import PackbackTenQuestionsRequest,TenQuestionsGeneratorRequest
from src.core.responder import generate_ai_response, generate_ai_response_for_third_reply, generate_research_response
from src.common.utils import get_logger

logger = get_logger(__name__)


packback_course_generator = PackbackCourseGenerator()
db = SupabaseClient()



class PackbackConfig:
    def __init__(self, open_ai_key:str):
        self.open_api_key= open_ai_key

    def third_outgoing_email(self,lead_history, data):
        try:
            conversation = data.get('conversation')
            ten_question_prompt = validate_lead_last_reply(conversation, self.open_api_key)
            packback_response = None

            logger.info("ten_question_prompt for lead - %s :: %s", lead_history.get('email'), ten_question_prompt)
            if not ten_question_prompt:
                logger.info("sending email to :: %s", lead_history.get('email'))
                logger.info("no ten question prompt found")
                return self.respond_to_lead(lead_history,data)

            if lead_history.get('course_description') is None:
                    packback_response = packback_course_generator.packback_ten_questions(PackbackTenQuestionsRequest(
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
                packback_response = packback_course_generator.ten_questions_generator(TenQuestionsGeneratorRequest(course_name=lead_history.get('course_name'), \
                    course_description=lead_history.get('course_description'), open_ai_model="gpt-4o-mini", \
                    question1=lead_history.get('question_1'), question2=lead_history.get('question_2'), question3=lead_history.get('question_3'), question4=lead_history.get('question_4')), open_ai_key = self.open_api_key
                    
                    )
                
            if packback_response is None:
                logger.info("no response from search and crawl. Now forwarding email")
                return self.forward_email_by_lead_email(lead_history,data, 'uzair@248.ai')
        
            questions = packback_response.questions
            for idx in range(len(questions)):   
                lead_history[f'q{idx + 1}'] = questions[idx].question if idx < len(questions) else ''
            return self.send_email_for_third_reply(lead_history, data)
        except Exception as e:
            logger.error("Error in third_outgoing_email - %s", e)
            return False
                
    def send_email_for_third_reply(self,lead_history,data):
        try:
            lead_email =  lead_history.get('email')
            conversation =  data.get('conversation')
            # conversation = validate_lead_conversation(conversation)
            # conversation.pop()
            response = generate_ai_response_for_third_reply (lead_history, conversation, self.open_api_key)


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

            if email_cc is not None:
                all_cc = f"{cc},{email_cc}"
            else:
                all_cc = cc
            if email_bcc is not None:
                all_bcc = f"{bcc},{email_bcc}"
            else:
                all_bcc = bcc

            send = instantly.send_reply(
                message=merged_email,
                from_email=from_account,
                to_email=lead_email,
                uuid=message_uuid,
                subject=subject, 
                cc=all_cc,
                bcc=all_bcc
            )
            if send == 200:
                logger.info("Email sent successfully - %s", lead_email)
                db.update({"flag": False}, lead_email)
            return merged_email
        except Exception as e:
            logger.error("Error sending email - %s", e)
            return False
    
    def respond_to_lead(self,lead_history,data):
        try:
            lead_email =  lead_history.get('email')
            conversation =  data.get('conversation')

            # conversation = validate_lead_conversation(conversation)

            response = generate_ai_response (lead_history, conversation, self.open_api_key)
            logger.info("response :: %s", response)
  
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
            if email_cc is not None:
                all_cc = f"{cc},{email_cc}"
            else:
                all_cc = cc
            if email_bcc is not None:
                all_bcc = f"{bcc},{email_bcc}"
            else:
                all_bcc = bcc

            send = instantly.send_reply(
                message=merged_email,
                from_email=from_account,
                to_email=lead_email,
                uuid=message_uuid,
                subject=subject, 
                cc=all_cc,
                bcc=all_bcc
            )
            logger.info("send ------------------->>>>> :: %s", send)
            if send == 200:
                logger.info("Email sent successfully - %s", lead_email)
                db.update({"flag": False}, lead_email)
            return merged_email
        except Exception as e:
            logger.error("Error sending email - %s", e)
            return False
    
    def forward_email(self,lead_history,data):
        try:
            lead_email =  lead_history.get('email')
            conversation =  data.get('conversation')
            response = generate_ai_response(lead_history, conversation, self.open_api_key)
            cc = response.get('cc')
            email_cc = data['cc']
            if email_cc != cc:
                return self.forward_email_by_lead_email(lead_history, data, cc)
            logger.info("No response to lead :: %s", lead_email)
            return True
        except Exception as e:
            logger.error("Error sending email - %s", e)
            return False
    
    def forward_email_by_lead_email(self, lead_history, data, forward_email):
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
            return email_body
        except Exception as e:
            logger.error("Error sending email - %s", e)
            return False
        


