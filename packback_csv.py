

import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.core.packback import PackbackCourseGenerator
from src.common.models import PackbackCourseDescriptionRequest
from src.common.logger import get_logger
from src.database.supabase import SupabaseClient

packback_course_generator = PackbackCourseGenerator()
logger = get_logger("csv_generator")

db = SupabaseClient()

def process_row(row, index):
    print(f"Processing row {index + 1}")
    email = row['Email']
    firstName = row['First Name']
    lastName = row['Last Name']
    courseCode = row['FA24 Course Code']
    universityName = row['University Name']
    ae = row['Contact Owner']



    body = {
        "course_code": courseCode or '',
        "university_name": universityName or '',
        "professor_name": f"{firstName or ''} {lastName or ''}",
        "open_ai_model": "gpt-4o-mini"
    }       
    result = packback_course_generator.packback_four_questions(PackbackCourseDescriptionRequest(**body))
    logger.info(f"result from packback_four_questions :: {result}")

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
                'firstName': firstName,
                'lastName': lastName,
                'universityName': universityName,
                'courseDescription': new_courseDescription,
                'question1': new_questions[0] if len(new_questions) > 0 else '',
                'question2': new_questions[1] if len(new_questions) > 1 else '',
                'question3': new_questions[2] if len(new_questions) > 2 else '',
                'question4': new_questions[3] if len(new_questions) > 3 else '',
                'promptTokens': prompt_tokens,
                'completionTokens': completion_tokens,
                'tokenCost': cost,
                'ae': ae,

            }
        else:
            return None
    except Exception as e:
        print(f"Failed to process row with email: {email}. Error: {e}")
        return None



def process_csv_with_concurrency():
    try:
        logger.info("process_csv_with_concurrency is running")
        input_file = 'packback_2025_03.csv'

        # Get offset and limit from the database
        cap = db.get_offset().data[0]
        offset = cap['offset']
        limit = cap['limit']
        start_row = offset
        end_row = offset + limit

        if limit == 0:
            return

        with open(input_file, 'r') as infile:
            reader = csv.DictReader(infile)

            # Load all rows from the CSV
            rows = list(reader)
            total_rows = len(rows)
            end_row = min(end_row, total_rows)

            if total_rows < offset:
                return
            # Process rows concurrently using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {}
                call_count = 0  # Counter to track how many calls have been submitted

                for index, row in enumerate(rows[start_row:end_row], start=start_row):
                    futures[executor.submit(process_row, row, index)] = index
                    call_count += 1
                    
                    # Sleep for 3 seconds after every 3 calls
                    if call_count % 5 == 0:
                        time.sleep(1)

                # Wait for all futures to complete
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            logger.info(f"<<-- result-->>")
                            db.insert_packback_data(result)
                    except Exception as process_exception:
                        logger.error(f"Error processing row {futures[future]}: {process_exception}")

        # Update the offset in the database
        db.update_offset(offset + limit)
        logger.info(f"Processing completed for rows {start_row} to {end_row}")
    except Exception as e:
        logger.exception("Exception occurred in process_csv_with_concurrency: %s", e)

