
from src.tools.gepeto import GepetoConfig
from src.tools.chicory import ChicoryConfig
from src.tools.packback import PackbackConfig   
from src.common.enum import Client
from src.crm.salesforce import SalesforceClient
from src.common.utils import construct_email_text_from_history
from src.common.logger import get_logger
from src.configurations.justcall import JustCallService

jc = JustCallService()
logger = get_logger(__name__)


class BaseConfig:
    def __init__(self, organization_name:str, open_ai_key:str,campaign_name:str, lead_history:dict, data:dict):
        self.organization_name = str(organization_name.strip()) 
        self.open_ai_key = open_ai_key
        self.campaign_name = str(campaign_name.strip())
        self.lead_history = lead_history
        self.data = data

    def respond_or_forward(self):
        # jc.send_message(f"New interested lead -\n\n Organization - {self.organization_name}\n\nCampaign - {self.campaign_name}\n\nLead Email - {self.data['lead_email']}\n\nConversation URL - {self.data['url']}")
    
        if self.organization_name == Client.GEPETO.value:
            logger.info(f"forwarding email for {self.organization_name}")
            GepetoConfig().forward_email(self.lead_history, self.data)

        if self.organization_name == Client.CHICORY.value:
            logger.info("chicory lead forwarder")
            ChicoryConfig().forward_email(self.lead_history, self.data)

        if self.organization_name == Client.PACKBACK.value:
            logger.info("Packback responder")
            packback_config = PackbackConfig(self.open_ai_key)
            if self.data.get('incoming') == 1 and self.data.get('outgoing') % 3 == 0:
                logger.info("Packback respond to lead after 3rd reply")
                packback_config.third_outgoing_email(self.lead_history, self.data)
            elif self.data.get('incoming') == 1 and self.data.get('outgoing') % 3 != 0:
                logger.info("Packback respond to lead after 1-2 reply")
                packback_config.respond_to_lead(self.lead_history, self.data)
            else:
                logger.info("Need to check cc email if not cc'd then forward")
                packback_config.forward_email(self.lead_history, self.data)

            


    
        
    def update_crm(self):

        if self.organization_name == Client.PACKBACK.value:
            self.update_salesforce_task(self.data)
        
        if self.organization_name == Client.GEPETO.value:
            pass

        if self.organization_name == Client.CHICORY.value:
            pass


    def update_salesforce_task(self, updated_data):
        salesforce_client = SalesforceClient(updated_data.get('lead_email'))
        conversation =  updated_data.get('conversation')
        conversation = construct_email_text_from_history(conversation, updated_data.get('lead_email'), updated_data.get('from_account'))
        salesforce_client.create_update_task(conversation, updated_data.get('status'))




   

            