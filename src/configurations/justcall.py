import requests
from src.common.logger import get_logger
from src.settings import settings
logger = get_logger('JustCall')



class JustCallService():
    def __init__(self ):

        self.url:str  = "https://api.justcall.io/v1/texts/new"

        self.api_key:str  = settings.JUSTCALL_API_KEY
        self.api_secret:str  = settings.JUSTCALL_API_SECRET
        self.headers:dict = {"Accept": "application/json",'Authorization': f'{self.api_key}:{self.api_secret}',}

    def send_message(self, message):
        try:
            for send_to in ["+17372740771", "+17736206534", '+923369897217']:
                send_from:str = "+14156926240"
                content:str = message

                payload = {"from": send_from,"to": send_to,"body": content}
                logger.info("Sending SMS via justcall content - %s - to %s - from %s", content,  send_to, send_from) 
                response = requests.post(self.url, headers=self.headers, json=payload)
                logger.info("JUSTCALL API STATUS CODE :: %s", response.status_code)
                logger.info("JUSTCALL API RESPONSE :: %s", response.json())
            return True
        except Exception as e:
            logger.exception("Exception in sending message justcall %s", e)    
            return False
    
    

