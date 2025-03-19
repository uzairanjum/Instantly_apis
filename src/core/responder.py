
from src.common.logger import get_logger
from src.common.utils import format_http_url, get_ae_data_by_email
from src.configurations.llm import OpenAiConfig
from src.settings import settings
from src.common.prompts import responder_prompt,third_reply_prompt, research_prompt
from pytz import timezone


logger = get_logger(__name__)    

ct_timezone = timezone('America/Chicago')



def generate_ai_response(lead_history:dict, previous_messages:list ,open_api_key:str):
    
    try:
        open_ai = OpenAiConfig(open_api_key)
        logger.info("Generating AI response")


        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in previous_messages]
        lead_ae_manager = get_ae_data_by_email(lead_history.get('email'))

        prompt = responder_prompt.format(**lead_history, ae_first_name=lead_ae_manager.get('ae_first_name'), calendar_link = lead_ae_manager.get('ae_booking_link'))
        formatted_history = [{"role": "system", "content": prompt}, *ai_message_history]
        response,_,_ = open_ai.generate_response(formatted_history)
        response = format_http_url(response)
        response = response.replace('\n','<br>')
        return {
            "content": response,
            "subject": previous_messages[0].get('subject'),
            "cc": lead_ae_manager.get('ae_email'),
            "bcc": f'{lead_ae_manager.get('manager_email')},uzair@248.ai,mert@248.ai,uzair.anjum@248.ai',
            "timestamp": previous_messages[-1].get('timestamp')
        }  
    except Exception as e:
        logger.error(f"Error responder: {e}")
        return {}

def generate_research_response(lead_history:dict, previous_messages:list, open_api_key:str ):
    
    try:
        open_ai = OpenAiConfig(open_api_key)


        logger.info("Generating research response")
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in previous_messages]
    

        lead_ae_manager = get_ae_data_by_email(lead_history.get('email'))


        prompt = research_prompt.format(**lead_history, ae_first_name=lead_ae_manager.get('ae_first_name'), calendar_link = lead_ae_manager.get('ae_booking_link'))
        formatted_history = [{"role": "system", "content": prompt}, *ai_message_history]
        response,_,_ = open_ai.generate_response(formatted_history)
        response = format_http_url(response)
        response = response.replace('\n','<br>')
        return {
            "content": response,
            "subject": previous_messages[0].get('subject'),
            "cc": lead_ae_manager.get('ae_email'),
            "bcc": f'{lead_ae_manager.get('manager_email')},uzair@248.ai,mert@248.ai, uzair.anjum@248.ai',
            "timestamp": previous_messages[-1].get('timestamp')
        }  
    except Exception as e:
        logger.error(f"Error make_draft_email: {e}")
        return None

def generate_ai_response_for_third_reply(lead_history:dict, previous_messages:list, open_api_key:str):
    try:
        open_ai = OpenAiConfig(open_api_key)


        logger.info("Generating AI response for third reply")
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in previous_messages]
     

        lead_ae_manager = get_ae_data_by_email(lead_history.get('email'))


        prompt = third_reply_prompt.format(**lead_history, ae_first_name=lead_ae_manager.get('ae_first_name'),calendar_link = lead_ae_manager.get('ae_booking_link'))
        formatted_history = [{"role": "system", "content": prompt}, *ai_message_history]
        response,_,_ = open_ai.generate_response(formatted_history)
        response = format_http_url(response)
        response = response.replace('\n','<br>')
        return {
            "content": response,
            "subject": previous_messages[0].get('subject'),
            "cc": lead_ae_manager.get('ae_email'),
            "bcc": f'{lead_ae_manager.get('manager_email')}, uzair@248.ai, mert@248.ai,uzair.anjum@248.ai, seina.shirakura@248.ai',
            "timestamp": previous_messages[-1].get('timestamp')
        }  
    except Exception as e:
        logger.error(f"Error make_draft_email: {e}")
        return {}




   