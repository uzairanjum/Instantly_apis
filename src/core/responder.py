
from src.common.logger import get_logger
from src.common.utils import get_ae_data, format_http_url
from src.configurations.llm import OpenAiConfig
from src.settings import settings
from src.common.prompts import responder_prompt
from datetime import datetime
from pytz import timezone

open_ai = OpenAiConfig(settings.OPENAI_API_KEY)
logger = get_logger("Responder")    

ct_timezone = timezone('America/Chicago')



def make_draft_email(AE_name:str, last_name:str, previous_messages:list):
    try:
        ai_message_history = [{"role": item["role"], "content": item["content"]} for item in previous_messages]
        ae_data = get_ae_data(AE_name)
        ae_first_name = AE_name.split(" ")[0]
        prompt = responder_prompt.format(ae_first_name=ae_first_name, calendar_link=ae_data.get('calendar_link'), lead_last_name=last_name)
        formatted_history = [{"role": "system", "content": prompt}, *ai_message_history]
        response = open_ai.generate_response(formatted_history)
        response = format_http_url(response)
        response = response.replace('\n','<br>')
        return {
            "content": response,
            "role" :"draft",
            "subject": previous_messages[-1].get('subject'),
            "cc": ae_data.get('cc'), #string
            "bcc": ae_data.get('bcc'), #string
            "timestamp": previous_messages[-1].get('timestamp')
        }  
    except Exception as e:
        logger.error(f"Error make_draft_email: {e}")
        return {}





   