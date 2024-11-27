

import csv
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.core.packback import PackbackConfig
from src.common.models import PackbackCourseDescriptionRequest
from src.common.logger import get_logger
from src.database.supabase import SupabaseClient

packback_config = PackbackConfig()
logger = get_logger("csv_generator")

db = SupabaseClient()

def process_row(row, index):
    print(f"Processing row {index + 1}")
    email = row['Email']
    firstName = row['firstName']
    lastName = row['lastName']
    courseCode = row['Course Code']
    universityName = row['University Name']

    body = {
        "course_code": courseCode or '',
        "university_name": universityName or '',
        "professor_name": f"{firstName or ''} {lastName or ''}",
        "open_ai_model": "gpt-4o-mini"
    }       
    result = packback_config.packback_four_questions(PackbackCourseDescriptionRequest(**body))
    logger.info(f"result :: {result}")

    try:
        if result:
            new_courseName = result.course_name
            new_courseDescription = result.course_description
            prompt_tokens = result.total_prompt_tokens
            completion_tokens = result.total_completion_tokens
            cost = result.token_cost
            questions = result.questions
            new_questions = [q.question for q in questions]
            return {
                'email': email,
                'courseCode': courseCode,
                'courseName': new_courseName,
                'courseDescription': new_courseDescription,
                'question1': new_questions[0] if len(new_questions) > 0 else '',
                'question2': new_questions[1] if len(new_questions) > 1 else '',
                'question3': new_questions[2] if len(new_questions) > 2 else '',
                'question4': new_questions[3] if len(new_questions) > 3 else '',
                'promptTokens': prompt_tokens,
                'completionTokens': completion_tokens,
                'tokenCost': cost,
            }
        else:
            return None
    except Exception as e:
        print(f"Failed to process row with email: {email}. Error: {e}")
        return None

# def process_csv_with_concurrency():
#     try:
#         logger.info("process_csv_with_concurrency is running")
#         input_file = 'packback_new.csv'

#         # Get offset and limit from the database
#         cap = db.get_offset().data[0]
#         offset = cap['offset']
#         limit = cap['limit']
#         start_row = offset
#         end_row = offset + limit

#         with open(input_file, 'r') as infile:
#             reader = csv.DictReader(infile)

#             # Load all rows from the CSV
#             rows = list(reader)
#             total_rows = len(rows)
#             end_row = min(end_row, total_rows)

#             # Process rows concurrently using ThreadPoolExecutor
#             with ThreadPoolExecutor(max_workers=5) as executor:
#                 futures = {
#                     executor.submit(process_row, row, index): index
#                     for index, row in enumerate(rows[start_row:end_row], start=start_row)
#                 }
#                 for future in as_completed(futures):
#                     try:
#                         result = future.result()
#                         if result:
#                             db.insert_packback_data(result)
#                     except Exception as process_exception:
#                         logger.error(f"Error processing row {futures[future]}: {process_exception}")

#         # Update the offset in the database
#         db.update_offset(offset + limit)
#         logger.info(f"Processing completed for rows {start_row} to {end_row}")
#     except Exception as e:
#         logger.exception("Exception occurred in process_csv_with_concurrency: %s", e)

# # process_csv_with_concurrency()

def process_csv_with_concurrency():
    try:    
        logger.info("process_csv_concurrent is running")
        input_file = 'packback_new.csv'
        batch_size = 10

        cap = db.get_offset().data[0]
        offset = cap['offset']
        limit = cap['limit']
        limit= 10
        start_row = offset
        end_row = offset + limit

        with open(input_file, 'r') as infile:
            reader = csv.DictReader(infile)

            rows = list(reader)
            total_rows = len(rows)
            end_row = min(end_row, total_rows)

            for start in range(start_row, end_row, batch_size):
                end = min(start + batch_size, end_row)
                batch = rows[start:end]
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {executor.submit(process_row, row, index): row for index, row in enumerate(batch, start=start)}
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            db.insert_packback_data(result)

                print(f"Processed batch {start // batch_size + 1} of {(end_row - start_row) // batch_size + 1}")
                time.sleep(1)
        # db.update_offset(offset + limit)
    except Exception as e:
        logger.exception("Exception occurred process_csv_concurrent %s", e)

# process_csv_concurrent()