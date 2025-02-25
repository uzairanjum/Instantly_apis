from src.common.utils import get_logger
from src.tools.gepeto import GepetoConfig
from src.tools.chicory import ChicoryConfig
from src.tools.packback import PackbackConfig   
from src.common.enum import Client

logger = get_logger(__name__)


class BaseConfig:
    def __init__(self, organization_name:str, open_ai_key:str, lead_history:dict, data:dict):
        self.organization_name = organization_name
        self.open_ai_key = open_ai_key
        self.lead_history = lead_history
        self.data = data

    def respond_or_forward(self):


        if self.organization_name == Client.GEPETO.value:
            logger.info(f"forwarding email for {self.organization_name}")
            GepetoConfig().forward_email(self.lead_history, self.data)

        if self.organization_name == Client.CHICORY.value:
            logger.info("chicory lead forwarder")
            ChicoryConfig().forward_email(self.lead_history, self.data)

        if self.organization_name == Client.PACKBACK.value:
            packback_config = PackbackConfig(self.open_ai_key)

            if self.data.get('incoming') == 1 and self.data.get('outgoing') % 3 == 0:
                if self.data.get('campaign_id') == '6c020a71-af8e-421a-bf8d-b024c491b114':
                    packback_config.respond_to_lead(self.lead_history, self.data)
                else:
                    packback_config.third_outgoing_email(self.lead_history, self.data)


            elif self.data.get('incoming') == 1 and self.data.get('outgoing') % 3 != 0:
                packback_config.respond_to_lead(self.lead_history, self.data)
            else:
                logger.info("Need to check cc email if not cc'd then forward")
                packback_config.forward_email(self.lead_history, self.data)
    
    def update_crm(self):

        if self.organization_name == Client.PACKBACK.value:
            pass



   

            