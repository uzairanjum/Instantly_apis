
from src.common.logger import get_logger
from src.common.utils import get_ae_data, format_http_url
from src.configurations.llm import OpenAiConfig
from src.settings import settings
from src.common.prompts import responder_prompt,third_reply_prompt, research_prompt
from pytz import timezone


logger = get_logger("Responder")    

ct_timezone = timezone('America/Chicago')



def generate_ai_response(lead_history:dict, previous_messages:list ,open_api_key:str):
    
    try:

        open_ai = OpenAiConfig(open_api_key)


        logger.info("Generating AI response")
        AE_name = lead_history.get('AE') if lead_history.get('AE') else lead_history.get('CO')
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in previous_messages]
        ae_data = get_ae_data(AE_name)
        ae_first_name = AE_name.split(" ")[0]
        prompt = responder_prompt.format(**lead_history, ae_first_name=ae_first_name, bdr_name = ae_data.get('bdr_name'), calendar_link = ae_data.get('calendar_link'))
        formatted_history = [{"role": "system", "content": prompt}, *ai_message_history]
        response,_,_ = open_ai.generate_response(formatted_history)
        response = format_http_url(response)
        response = response.replace('\n','<br>')
        return {
            "content": response,
            "subject": previous_messages[0].get('subject'),
            "cc": ae_data.get('cc'), 
            "bcc": f'{ae_data.get('bcc')}, uzair.anjum@hellogepeto.com, uzair@hellogepeto.com, mert@hellogepeto.com',
            "timestamp": previous_messages[-1].get('timestamp')
        }  
    except Exception as e:
        logger.error(f"Error make_draft_email: {e}")
        return {}

def generate_research_response(lead_history:dict, previous_messages:list, open_api_key:str ):
    
    try:
        open_ai = OpenAiConfig(open_api_key)


        logger.info("Generating research response")
        AE_name = lead_history.get('AE') if lead_history.get('AE') else lead_history.get('CO')
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in previous_messages]
        ae_data = get_ae_data(AE_name)
        ae_first_name = AE_name.split(" ")[0]
        prompt = research_prompt.format(**lead_history, ae_first_name=ae_first_name, bdr_name = ae_data.get('bdr_name'), calendar_link = ae_data.get('calendar_link'))
        formatted_history = [{"role": "system", "content": prompt}, *ai_message_history]
        response,_,_ = open_ai.generate_response(formatted_history)
        response = format_http_url(response)
        response = response.replace('\n','<br>')
        return {
            "content": response,
            "subject": previous_messages[0].get('subject'),
            "cc": ae_data.get('cc'), 
            "bcc": ae_data.get('bcc'),
            "timestamp": previous_messages[-1].get('timestamp')
        }  
    except Exception as e:
        logger.error(f"Error make_draft_email: {e}")
        return None

def generate_ai_response_for_third_reply(lead_history:dict, previous_messages:list, open_api_key:str):
    try:
        open_ai = OpenAiConfig(open_api_key)


        logger.info("Generating AI response for third reply")
        AE_name = lead_history.get('AE') if lead_history.get('AE') else lead_history.get('CO')
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in previous_messages]
        ae_data = get_ae_data(AE_name)
        ae_first_name = AE_name.split(" ")[0]
        prompt = third_reply_prompt.format(**lead_history, ae_first_name=ae_first_name,  bdr_name = ae_data.get('bdr_name'),calendar_link = ae_data.get('calendar_link'))
        formatted_history = [{"role": "system", "content": prompt}, *ai_message_history]
        response,_,_ = open_ai.generate_response(formatted_history)
        response = format_http_url(response)
        response = response.replace('\n','<br>')
        return {
            "content": response,
            "subject": previous_messages[0].get('subject'),
            "cc": ae_data.get('cc'), 
            "bcc": f'{ae_data.get('bcc')}, uzair.anjum@hellogepeto.com, uzair@hellogepeto.com, mert@hellogepeto.com',
            "timestamp": previous_messages[-1].get('timestamp')
        }  
    except Exception as e:
        logger.error(f"Error make_draft_email: {e}")
        return {}




   