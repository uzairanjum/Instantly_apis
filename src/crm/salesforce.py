import time
import requests
import jwt
from src.settings import settings
from src.common.logger import get_logger

logger = get_logger(__name__)

class SalesforceClient:

    def __init__(self, email):

        environment = settings.ENVIRONMENT
        if not environment:
            raise Exception("Environment is not set")
        # logger.info(f"Environment: {environment}")
        
        KEY_FILE = 'gepeto.key'
        AUDIENCE = settings.SALESFORCE_SANDBOX_URL if environment == 'sandbox' else settings.SALESFORCE_PROD_URL
        GRANT_TYPE = settings.SALESFORCE_GRANT_TYPE
        SUBJECT = settings.SALESFORCE_SUBJECT
        ISSUER = settings.SALESFORCE_ISSUER


        self.subject = settings.SALESFORCE_TASK_SUBJECT
        self.email = email

        with open(KEY_FILE) as fd:
            private_key = fd.read()
        claim = {
            'iss': ISSUER,
            'exp': int(time.time()) + 30000000,
            'aud': AUDIENCE,
            'sub': SUBJECT,
        }        
        encoded_jwt = jwt.encode(claim, private_key, algorithm='RS256')
        r = requests.post(AUDIENCE + '/services/oauth2/token',
            data = {'grant_type': GRANT_TYPE, 'assertion': encoded_jwt})
        if r.status_code != 200:
            raise Exception(f"Failed to authenticate with Salesforce: {r.status_code} - {r.text}")

        self.token = r.json().get('access_token')
        self.instance_url= r.json().get('instance_url')

        # logger.info(f"Salesforce instance url: {self.instance_url}")
       

        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            "Sforce-Auto-Assign": "false"
        }

    def get_ae_manager_by_email(self):
        try:
            url = f"{self.instance_url}/services/data/v61.0/query/?q=SELECT+Id,Email, Owner.Name,Owner.Email,\
                  Owner.Outreach_Meeting_Link__c,Owner.Manager.Name,Owner.Manager.Email+\
                    FROM+Contact+WHERE+Email='{self.email}'"

            response = requests.get(url, headers=self.headers)
            if response.status_code == 200 and len(response.json().get('records', [])) > 0:
                logger.info(f"response if: {response.json()}")
                return self.extract_lead_info(response.json().get('records', [])[0])
            else:
                logger.info(f"response else: {response.json()}")
                return {'lead_email': self.email, 'ae_first_name': 'Nikki', 'ae_last_name': 'Pulido', 'ae_email': 'nikki.pulido@packback.co',
                        'ae_booking_link': 'https://hello.packback.co/c/Nicole_Pulido', 'manager_email': 'kelsey@packback.co'}
    
        except Exception as e:
            logger.error(f"Error get_ae_manager_by_email: {e}")
            return {'lead_email': self.email, 'ae_first_name': 'Nikki', 'ae_last_name': 'Pulido', 'ae_email': 'nikki.pulido@packback.co',
                        'ae_booking_link': 'https://hello.packback.co/c/Nicole_Pulido', 'manager_email': 'kelsey@packback.co'}
        
    def get_contact_by_email(self):
        try:
            url = f"{self.instance_url}/services/data/v61.0/query/?q=SELECT+Id,Owner.Email,Owner.Id+FROM+Contact+WHERE+Email='{self.email}'"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get('records', [])
            else:
                return None
        except Exception as e:
            print(e)
            return False
        
    def get_contact_tasks(self):
        try:
            contact = self.get_contact_by_email()
            if not contact:
                return None
            contact_id = contact[0].get('Id')
            url = f"{self.instance_url}/services/data/v61.0/query/?q=SELECT+Id,Subject,Status,ActivityDate,Description,Priority+FROM+Task+WHERE+WhoId='{contact_id}'"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                tasks = response.json().get('records', [])
                logger.info(f"total tasks: {len(tasks)}")
                return self.filter_tasks_by_subject(tasks)
            else:
                logger.error(f"Error getting contact tasks: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting contact tasks: {e}")
            return False
    
    def create_task(self, conversation, outcome):
        try:
            contact = self.get_contact_by_email()
            if contact:
                contact_id = contact[0].get('Id')
                owner_id = contact[0].get('Owner', {}).get('Id')
            else:
                return None
            
            payload = {
                "WhoId": contact_id,
                "Subject": self.subject,
                "ActivityDate": time.strftime('%Y-%m-%d', time.localtime(time.time())),
                "Status": "Completed",
                "Priority": "Normal",
                "Description": conversation,
                "Outcome__c": outcome,
                "Type": "Others",
                "OwnerId": owner_id, 
            }
            url = f"{self.instance_url}/services/data/v61.0/sobjects/Task/"
        
            response = requests.post(url, headers=self.headers, json=payload)
            logger.info(f"response: {response.json()}")
            return response.json()
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return False

    def update_task(self, conversation, outcome, task_id):
        try:
            url = f"{self.instance_url}/services/data/v61.0/sobjects/Task/{task_id}"
            response = requests.patch(url, headers=self.headers, json={"Description": conversation, "Outcome__c": outcome})
            if response.status_code == 204:
                return True 
            else:
                logger.error(f"Error updating task: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False
    
    def filter_tasks_by_subject(self, tasks):
        filtered_tasks = [task for task in tasks if task['Subject'] == self.subject]
        return filtered_tasks

    def extract_lead_info(self,data):
        owner_name = data['Owner']['Name'].split(' ')
        return {
            "lead_email": data.get('Email', ''),
            "ae_first_name": owner_name[0] if len(owner_name) > 0 else '',
            "ae_last_name": owner_name[1] if len(owner_name) > 1 else '',
            "ae_email": data.get('Owner', {}).get('Email', ''),
            "ae_booking_link": data.get('Owner', {}).get('Outreach_Meeting_Link__c', ''),
            "manager_email": data.get('Owner', {}).get('Manager', {}).get('Email', '')
        }

    def get_task_id(self):
        try:
            tasks = self.get_contact_tasks()
            if tasks:
                logger.info(f"Related task found for {self.email}")
                return tasks[0].get('Id')
            else:
                logger.info(f"No related tasks found for {self.email}")
                return None
        except Exception as e:
            logger.error(f"Error getting task id: {e}")
            return None
    
    def create_update_task(self, conversation, outcome):
        try:
            task_id = self.get_task_id()
            logger.info(f"task_id: {task_id}")
            if not task_id:
                logger.info(f"Creating task for {self.email}")
                return self.create_task(conversation, outcome)
            else:
                logger.info(f"Updating task for {self.email}")
                return self.update_task(conversation, outcome, task_id)
        except Exception as e:
            logger.error(f"Error creating update task: {e}")
            return None