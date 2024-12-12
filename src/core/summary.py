
from src.common.logger import get_logger
from src.database.supabase import SupabaseClient  
from src.configurations.instantly import InstantlyAPI
from src.common.utils import update_daily_summary_report, update_weekly_summary_report, three_days_summary_report,get_campaign_details, get_csv_details
from src.common.enum import SummaryType
from src.configurations.justcall import JustCallService
from src.core.uploadLeads import added_leads_to_campaign

logger = get_logger("Summary")
db = SupabaseClient()

jc = JustCallService()
class Summary:
    def __init__(self, campaign_id):
        self.campaign_id = campaign_id
        self.campaign_name, self.organization_name = self.get_campaign_details_()

    def update_weekly_summary(self):
        try:
            if self.organization_name is None:
                return None
            csv_name, worksheet_name = self.get_weekly_summary_csv_and_sheet()
            logger.info(f"organization_name: {self.organization_name}, csv_name: {csv_name}, worksheet_name: {worksheet_name}")
            update_weekly_summary_report(self.campaign_id, self.campaign_name, self.organization_name, csv_name, worksheet_name)
        except Exception as e:
            logger.error(f"Error update_weekly_summary: {e}")

    def update_daily_summary(self):
        try:
            if self.organization_name is None:
                return None
            csv_name, worksheet_name = self.get_daily_summary_csv_and_sheet()
            if csv_name is None:
                return None
            logger.info(f"organization_name: {self.organization_name}, csv_name: {csv_name}, worksheet_name: {worksheet_name}")
            update_daily_summary_report(self.campaign_id, self.campaign_name, self.organization_name, csv_name, worksheet_name)
        except Exception as e:
            logger.error(f"Error update_daily_summary: {e}")

    def three_days_summary_report(self):
        try:
            if self.organization_name is None:
                return None
            csv_name, worksheet_name = self.get_daily_summary_csv_and_sheet()
            if csv_name is None:
                return None
            logger.info(f"organization_name: {self.organization_name}, csv_name: {csv_name}, worksheet_name: {worksheet_name}")
            three_days_summary_report(self.campaign_id, self.campaign_name, self.organization_name, csv_name, worksheet_name)
        except Exception as e:
            logger.error(f"Error three_days_summary_report: {e}")

    def get_daily_summary_csv_and_sheet(self):
        try:
            csv_name, worksheet_name = get_csv_details(self.campaign_id, SummaryType.DAILY.value )
            return csv_name, worksheet_name
        except Exception as e:
            logger.error(f"Error get_daily_summary_csv_and_sheet: {e}")
            return None, None

    def get_weekly_summary_csv_and_sheet(self):
        try:
            csv_name, worksheet_name = get_csv_details(self.campaign_id, SummaryType.WEEKLY.value)
            return csv_name, worksheet_name
        except Exception as e:
            logger.error(f"Error get_weekly_summary_csv_and_sheet: {e}")
            return None, None

    def get_campaign_details_(self):
        try:
            campaign_name, organization_name, _ = get_campaign_details(self.campaign_id)
            logger.info(f"Organization name: {organization_name}")
            return campaign_name, organization_name
        except Exception as e:
            logger.error(f"Error get_campaign_details_: {e}")
            return None, None
        

    def notify_internally(self):
        try:
            higher_value:int = 1000
            lower_value:int = 250
            if self.campaign_id == "ecdc673c-3d90-4427-a556-d39c8b69ae9f":
                higher_value:int = 5000
                lower_value:int = 2500

            logger.info(f"higher_value: {higher_value}, lower_value: {lower_value}")
            _, organization_name, instantly_api_key= get_campaign_details(self.campaign_id)
            if not instantly_api_key:
                return None
            instantly = InstantlyAPI(instantly_api_key)
            response = instantly.get_campaign_details(campaign_id=self.campaign_id)
            if not response:
                return None
            not_yet_contacts = response.not_yet_contacted
            campaign_name=response.campaign_name
            
            logger.info(f"not_yet_contacts: {not_yet_contacts}")
            logger.info(f"send email to the team for {campaign_name}")
            
            if not_yet_contacts >= higher_value and not_yet_contacts <= lower_value:
                jc.send_message(f"Reminder for leads -\n\nOrganization - {organization_name}\n\nCampaign - {campaign_name}\n\nTotal lead left - {not_yet_contacts}\n\nPlease approved these leads : https://packback-leads-fe.vercel.app/")
                logger.info(f"send message total leads not yer contacted for {campaign_name}")
            elif not_yet_contacts <= lower_value:
                jc.send_message(f"Reminder for leads -\n\nOrganization - {organization_name}\n\nCampaign - {campaign_name}\n\nTotal lead left - {not_yet_contacts} \n\nStart recycling leads")
                logger.info(f"send message and start recycling leads for {campaign_name}")
                # added_leads_to_campaign(self.campaign_id)
        except Exception as e:
            logger.error(f"Error notify_internally: {e}")

        
          

