

import gspread
from google.oauth2.service_account import Credentials
from src.settings import settings
from src.common.logger import get_logger
logger = get_logger("GoogleSheet")

import json
import base64

credentials_json = base64.b64decode(settings.GOOGLE_CREDENTIALS).decode('utf-8')
credentials = json.loads(credentials_json)


class GoogleSheetClient:
    def __init__(self):
        self.service_account_file = credentials
        self.client = self._authenticate()

    def _authenticate(self):
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(self.service_account_file, scopes=scopes)  # Changed this line
        return gspread.authorize(creds)

    def open_sheet(self, spreadsheet_name, worksheet_name):
        try:
            spreadsheet = self.client.open(spreadsheet_name)
            return spreadsheet.worksheet(worksheet_name)
        except Exception as e:
            logger.error(f"Error opening sheet: {e}")
            return None

    def get_all_records(self, worksheet):
        try:
            return worksheet.get_all_records()
        except Exception as e:
            logger.error(f"Error getting all records: {e}")
            return None

    def append_row(self, worksheet, new_row):
        try:
            worksheet.append_row(new_row)
            print(f"New row added: {new_row}")
        except Exception as e:
            logger.error(f"Error appending row: {e}")
    
    def ensure_sheet_size(self,worksheet, target_row_count):
        try:
            current_row_count = worksheet.row_count
            if current_row_count < target_row_count:
                additional_rows = target_row_count - current_row_count
                worksheet.add_rows(additional_rows)
                logger.info(f"Added {additional_rows} rows to the worksheet to accommodate data.")
        except Exception as e:
            logger.error(f"Error ensuring sheet size: {e}")

    def update_records(self, worksheet, dataframe):
        try:
            self.ensure_sheet_size(worksheet, len(dataframe) + 1)  

            data = []
            for index, row in dataframe.iterrows():
                data.append({
                    'range': f'A{index + 2}:M{index + 2}',  
                    'values': [row.tolist()[:13]] 
                })

            worksheet.batch_update(data)
        except Exception as e:
            logger.error(f"Error updating records: {e}")
