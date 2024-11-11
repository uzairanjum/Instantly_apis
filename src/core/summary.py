
from src.common.logger import get_logger
from src.database.supabase import SupabaseClient 
from src.common.utils import  get_campaign_details, get_csv_details
from src.common.utils import update_daily_summary_report, update_weekly_summary_report, three_days_summary_report
from src.common.enum import SummaryType
logger = get_logger("Summary")
db = SupabaseClient()


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

