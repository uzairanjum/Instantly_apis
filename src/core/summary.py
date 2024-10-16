import csv
import time  
import concurrent.futures  
from src.common.logger import get_logger
from src.database.supabase import SupabaseClient
from src.common.utils import get_lead_details_history_for_csv


logger = get_logger("Worker")
db = SupabaseClient()

# campaign_id = "ecdc673c-3d90-4427-a556-d39c8b69ae9f"



input_csv = "instantly_leads_15_oct.csv"


# output_csv = 'email_data_15_oct.csv' 
# headers = ["Lead Email", "School Name", "Sent Date", "Lead Status","Status", "Reply",  "Outgoing", "Incoming",  "From account", "Conversation"]
        


def get_lead_details_from_csv_new():
        
        campaign_id = "ecdc673c-3d90-4427-a556-d39c8b69ae9f"
        
        data = []
        not_found = []

        try:
            with open(input_csv, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                data = list(reader)  # Read all data at once
        except FileNotFoundError:
            logger.error(f"Error: The file '{input_csv}' was not found.")
            return
        except Exception as e:
            logger.error(f"An error occurred while reading the CSV file: {e}")
            return

        
        logger.info("data %s", len(data))
        lead_data = []

        try:
            # with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            #     writer = csv.DictWriter(file, fieldnames=headers)
            #     writer.writeheader()
                
                # Use ThreadPoolExecutor for concurrent processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(get_lead_details_history_for_csv, row.get("email", None), row.get("University Name", None), campaign_id, index): row for index, row in enumerate(data)}
                for index, future in enumerate(concurrent.futures.as_completed(futures)):
                    try:
                        lead_details = future.result()
                        if lead_details:
                            db.insert(lead_details)
                            # lead_data.append(lead_details)
                            # Write each lead's details to the CSV immediately
                            # writer.writerows(lead_details)  # Write the details directly to the CSV
                        else:
                            not_found.append({"email": futures[future]["email"], "University Name": futures[future]["University Name"]})
                        
                        if (index + 1) % 10 == 0:  # After every 10 requests
                            time.sleep(2)  # Sleep for 2 seconds
                    except Exception as e:
                        logger.error(f"Error processing lead: {futures[future]['email']}. Error: {e}")
                        not_found.append({"email": futures[future]["email"], "University Name": futures[future]["University Name"]})

            # Print summary of results
            # logger.info("lead_data %s", len(lead_data))
            # if len(lead_data) > 0:
            #     db.insert_many(lead_data)
            # logger.info(f"CSV file '{output_csv}' created successfully.")
            # logger.info("not_found %s", json.dumps(not_found))

        except Exception as e:
            logger.error(f"An error occurred while writing to the CSV file: {e}")
       
