
import csv
import requests
import time

from concurrent.futures import ThreadPoolExecutor, as_completed

def process_row(row, api_url, index):
    print(f"Processing row {index + 1}")
    email = row['Email']
    firstName = row['firstName']
    lastName = row['lastName']
    full_name = row['Professor: Full Name']
    ae = row['AE']
    courseCode = row['CourseCode']
    universityName = row['University Name']

    body = {
        "course_code": courseCode or '',
        "university_name": universityName or '',
        "professor_name": f"{firstName or ''} {lastName or ''}",
        "open_ai_model": "gpt-4o-mini"
    }

    try:
        response = requests.post(api_url, json=body, timeout=300)
        print("status_code", response.status_code)
        if response.status_code == 200:
            result = response.json()
            new_courseName = result.get('course_name', '')
            new_courseDescription = result.get('course_description', '')
            prompt_tokens = result.get('total_prompt_tokens', 0)
            completion_tokens = result.get('total_completion_tokens', 0)
            cost = result.get('token_cost', 0)
            questions = result.get('questions', [])
            new_questions = [q.get('question', '') for q in questions]
            return {
                'Professor: Full Name': full_name,
                'Email': email,
                'firstName': firstName,
                'lastName': lastName,
                'University Name': universityName,
                'AE': ae,
                'CourseCode': courseCode,
                'courseName': new_courseName,
                'courseDescription': new_courseDescription,
                'question1': new_questions[0] if len(new_questions) > 0 else '',
                'question2': new_questions[1] if len(new_questions) > 1 else '',
                'question3': new_questions[2] if len(new_questions) > 2 else '',
                'question4': new_questions[3] if len(new_questions) > 3 else '',
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'cost': cost,
            }
        else:
            return {
                'Professor: Full Name': full_name,
                'Email': email,
                'firstName': firstName,
                'lastName': lastName,
                'University Name': universityName,
                'AE': ae,
                'CourseCode': courseCode,
                'courseName': '',
                'courseDescription': '',
                'question1': '',
                'question2': '',
                'question3': '',
                'question4': '',
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'cost': 0,
            }
    except Exception as e:
        print(f"Failed to process row with email: {email}. Error: {e}")
        return {
            'Professor: Full Name': full_name,
            'Email': email,
            'firstName': firstName,
            'lastName': lastName,
            'University Name': universityName,
            'AE': ae,
            'CourseCode': courseCode,
            'courseName': '',
            'courseDescription': '',
            'question1': '',
            'question2': '',
            'question3': '',
            'question4': '',
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'cost': 0,
        }

def process_csv_concurrent(input_file, output_file, api_url, batch_size=20, delay=1, max_workers=4):
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = [
            'Professor: Full Name', 'Email', 'firstName', 'lastName', 'University Name', 'AE', 'CourseCode',
            'courseName', 'courseDescription', 'question1', 'question2', 'question3', 'question4',
            'prompt_tokens', 'completion_tokens', 'cost'
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        rows = list(reader)
        total_rows = len(rows)
        for start in range(0, total_rows, batch_size):
            end = min(start + batch_size, total_rows)
            batch = rows[start:end]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(process_row, row, api_url, index): row for index, row in enumerate(batch, start=start)}
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        writer.writerow(result)
            print(f"Processed batch {start // batch_size + 1} of {total_rows // batch_size + 1}")
            time.sleep(delay)

# Usage example
input_file = 'testing.csv'
output_file = 'output_2.csv'
api_url = 'https://instantly-analytics-n37uf.ondigitalocean.app/gepeto/packback-four-questions'
process_csv_concurrent(input_file, output_file, api_url, batch_size=20, delay=1, max_workers=3)
