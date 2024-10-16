import requests
from src.common.logger import get_logger

logger = get_logger("Instantly")

class InstantlyAPI:
    def __init__(self, api_key: str):
        """
        Initializes the InstantlyAPI class with the API key.
        
        :param api_key: Your Instantly API key.
        """
        self.api_key:str = api_key
        self.headers:dict = {'Content-Type': 'application/json'}
        self.url:str = "https://api.instantly.ai/api/v1"

    def send_reply(self,  **kwargs):
        """
        Sends a reply using the Instantly API.
        
        """
        data = {
            "reply_to_uuid": kwargs.get('uuid'),
            "subject": "Re: TEST",
            "from": kwargs.get('from_email'),
            "to": kwargs.get('to_email'),
            "body": kwargs.get('message'),
            "cc": "",
            "bcc": ""
        }
        try:
            response = requests.post(f'{self.url}/unibox/emails/reply?api_key={self.api_key}', json=data, headers=self.headers)
            return response.json() 
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None
        
# 
    # def get_all_emails(self, **kwargs):
    #     """
    #     Gets all emails details using the Instantly API.
        
    #     """
    #     lead = kwargs.get('lead')
    #     campaign_id = kwargs.get('campaign_id')
    #     all_emails = []
    #     url = f'{self.url}/unibox/emails?api_key={self.api_key}&preview_only=false&lead={lead}&campaign_id={campaign_id}&sent_emails=true&email_type=all&latest_of_thread=true'
    #     try:
    #         while url:
    #             response = requests.get(url, headers=self.headers)
    #             response_json = response.json()
    #             all_emails.extend(response_json.get('data', []))
    #             page_trail = response_json.get('page_trail')
    #             if not page_trail:
    #                 break
    #             url = f'{self.url}/unibox/emails?api_key={self.api_key}&preview_only=false&lead={lead}&campaign_id={campaign_id}&sent_emails=true&email_type=all&latest_of_thread=true&page_trail={page_trail}'
    #         return all_emails  # Return the aggregated emails
    #     except requests.exceptions.RequestException as e:
    #         print(f"An error occurred: {e}")
    #         return None
        

    def get_all_emails(self, **kwargs):
        """
        Gets all emails details using the Instantly API.
        
        """
        lead = kwargs.get('lead')
        campaign_id = kwargs.get('campaign_id')
        all_emails = []
        url = f'{self.url}/unibox/emails?api_key={self.api_key}&preview_only=false&lead={lead}&campaign_id={campaign_id}&sent_emails=true&email_type=all&latest_of_thread=true'
        try:
            while url:
                response = requests.get(url, headers=self.headers)
                response_json = response.json()
                all_emails.extend(response_json.get('data', []))
                page_trail = response_json.get('page_trail')
                if not page_trail:
                    break
                url = f'{self.url}/unibox/emails?api_key={self.api_key}&preview_only=false&lead={lead}&campaign_id={campaign_id}&sent_emails=true&email_type=all&latest_of_thread=true&page_trail={page_trail}'
            return all_emails  # Return the aggregated emails
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None

    def get_lead_details(self, **kwargs):
        """
        Retrieves lead details using the Instantly API.
        
        :param email: The lead's email to retrieve details for.
        :param campaign_id: The campaign ID associated with the lead.
        :return: Response from the API (JSON format).
        """
        lead = kwargs.get('lead')
        campaign_id = kwargs.get('campaign_id')
        url = f"{self.url}/lead/get?api_key={self.api_key}&campaign_id={campaign_id}&email={lead}"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()  # Return the response in JSON format
            else:
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None

    def get_campaign_details(self, **kwargs):
        campaign_id = kwargs.get('campaign_id')
        url = f"https://api.instantly.ai/api/v1/analytics/campaign/summary?api_key={self.api_key}&campaign_id={campaign_id}"


        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()  # Return the response in JSON format
            else:
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None

        