

import gspread
from google.oauth2.service_account import Credentials
from src.settings import settings

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
        spreadsheet = self.client.open(spreadsheet_name)
        return spreadsheet.worksheet(worksheet_name)

    def get_all_records(self, worksheet):
        return worksheet.get_all_records()

    def append_row(self, worksheet, new_row):
        worksheet.append_row(new_row)
        print(f"New row added: {new_row}")
    
    def update_records(self,worksheet, dataframe):
    # Prepare the data for batch update
        data = []
        for index, row in dataframe.iterrows():
            # Assuming the first column is the row index and the rest are the values
            data.append({
                'range': f'A{index + 2}:Z{index + 2}',  # Adjust the range as needed
                'values': [row.tolist()]
            })

        # Perform the batch update
        worksheet.batch_update(data)
