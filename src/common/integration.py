import requests
import json
from src.common.logger import get_logger

logger = get_logger('Integration')

class Integration():
    def __init__(self, **kwargs):
        self.url = kwargs.get('url', None)
        self.data = kwargs.get('data', None)
        self.headers = kwargs.get('headers', {'Content-Type':'application/json'})

    def post(self):
        try:
            print(self.data)
            response =  requests.post(url = self.url, json= self.data ,headers=self.headers)
            logger.info("response %s",response)
            return response.json()
        except Exception as e:
            logger.error(f"Error occurred while post call, {e}")
            return {'error':str(e)}

