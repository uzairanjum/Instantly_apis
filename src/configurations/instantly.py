import requests
from src.common.logger import get_logger
from typing import Union
from src.common.models import CampaignSummary, TimeFrameCampaignData
import json
import time
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
            "subject":  kwargs.get('subject'),
            "from": kwargs.get('from_email'),
            "to": kwargs.get('to_email'),
            "body": kwargs.get('message'),
            "cc":   kwargs.get('cc'),
            "bcc":  kwargs.get('bcc') 
        }
        if kwargs.get('to_email') == 'uzairanjum@hellogepeto.com' :
            data['bcc'] = ""
        try:
            response = requests.post(f'{self.url}/unibox/emails/reply?api_key={self.api_key}', json=data, headers=self.headers)
            return response.status_code
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None
        
    def get_all_emails(self, **kwargs):
        """
        Gets all emails details using the Instantly API.
        
        """
        lead = kwargs.get('lead')
        campaign_id = kwargs.get('campaign_id')
        all_emails = []
        url = f'{self.url}/unibox/emails?api_key={self.api_key}&preview_only=false&lead={lead}&campaign_id={campaign_id}&sent_emails=true&email_type=all&latest_of_thread=false'
        try:
            while url:
                response = requests.get(url, headers=self.headers)
                response_json = response.json()
                all_emails.extend(response_json.get('data', []))
                page_trail = response_json.get('page_trail')
                if not page_trail:
                    break
                url = f'{self.url}/unibox/emails?api_key={self.api_key}&preview_only=false&lead={lead}&campaign_id={campaign_id}&sent_emails=true&email_type=all&latest_of_thread=false&page_trail={page_trail}'
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
        lead_email = kwargs.get('lead_email')
        campaign_id = kwargs.get('campaign_id')
        url = f"{self.url}/lead/get?api_key={self.api_key}&campaign_id={campaign_id}&email={lead_email}"
        try:
            response = requests.get(url, headers=self.headers)
            logger.info("response ------>>>:: %s", response)
            if response.status_code == 200:
                logger.info(f"Lead details retrieved for {lead_email}")
                return response.json()  # Return the response in JSON format
            else:
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None
    
    def delete_lead_from_campaign(self, **kwargs):
        """
        Deletes a lead from a campaign using the Instantly API.
        """
        lead_list = kwargs.get('lead_list')
        campaign_id = kwargs.get('campaign_id')
        payload = json.dumps({
        "api_key": self.api_key,
        "campaign_id": campaign_id,
        "delete_all_from_company": False,
        "delete_list": lead_list
        })
        try:
            response = requests.post(f"{self.url}/lead/delete", headers=self.headers, data=payload)
            if response.status_code == 200:
                logger.info(f"Leads deleted from campaign {campaign_id}")
                return response.json()  # Return the response in JSON format
            else:
                logger.error(f"Failed to delete leads from campaign {campaign_id}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred in delete_lead_from_campaign: {e}")
            return None
        
    def add_lead_to_campaign(self, **kwargs):
        """
        Adds a lead to a campaign using the Instantly API.
        """
        campaign_id = kwargs.get('campaign_id')
        lead_list = kwargs.get('lead_list')
        payload = json.dumps({
        "api_key": self.api_key,
        "campaign_id": campaign_id,
        "skip_if_in_workspace": False,
        "skip_if_in_campaign": True,
        "leads": lead_list
        })
        try:
            response = requests.post(f"{self.url}/lead/add", headers=self.headers, data=payload)
            if response.status_code == 200:
                logger.info(f"Leads added to campaign {campaign_id}")
                return response.json()  # Return the response in JSON format
            else:
                logger.error(f"Failed to add leads to campaign {campaign_id}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred in delete_lead_from_campaign: {e}")
            return None

    def get_campaign_details(self, **kwargs) -> Union[CampaignSummary, None]:
        campaign_id = kwargs.get('campaign_id')
        url = f"{self.url}/analytics/campaign/summary?api_key={self.api_key}&campaign_id={campaign_id}"


        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return CampaignSummary(**response.json())  # Return the response in JSON format
            else:
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None
   
    def get_weekly_campaign_details(self, **kwargs) -> Union[TimeFrameCampaignData, None]:
        campaign_id = kwargs.get('campaign_id')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        url = f"{self.url}/analytics/campaign/count?api_key={self.api_key}&campaign_id={campaign_id}&start_date={start_date}&end_date={end_date}"

     
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                if len(response.json()) > 0:
                    return TimeFrameCampaignData(**response.json()[0]) # Return the response in JSON format
                else:
                    return None
            else:
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None