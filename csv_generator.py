


import csv
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def process_row(row, api_url, index):
    print(f"Processing row {index + 1}")
    email = row['email']
    firstName = row['firstName']
    lastName = row['lastName']
    question1 = row['Question 1']
    question2 = row['Question 2']
    question3 = row['Question 3']
    question4 = row['Question 4']
    courseCode = row['Course Code']
    courseName = row['Course Name']
    universityName = row['University Name']
    fa24CourseCode = row['FA24 Course Code']
    courseDescription = row['Course Description']

    body = {
        "course_code": (fa24CourseCode or ''),
        "university_name": (universityName or ''),
        "professor_name": (firstName or '') + ' ' + (lastName or ''),
        "open_ai_model": "gpt-4o-mini"
    }

    try:
        response = requests.post(api_url, json=body)
        if response.status_code == 200:
            result = response.json()
            new_courseName = result.get('course_name', '')
            new_courseDescription = result.get('course_description', '')
            new_question1 = result.get('questions', [])[0].get('question', '') if result.get('questions') else ''
            new_question2 = result.get('questions', [])[1].get('question', '') if len(result.get('questions', [])) > 1 else ''
            new_question3 = result.get('questions', [])[2].get('question', '') if len(result.get('questions', [])) > 2 else ''
            new_question4 = result.get('questions', [])[3].get('question', '') if len(result.get('questions', [])) > 3 else ''
            return {
                'email': email, 'firstName': firstName, 'lastName': lastName,
                'courseCode': courseCode, 'fa24CourseCode': fa24CourseCode,
                'courseName': courseName, 'new_courseName': new_courseName,
                'courseDescription': courseDescription, 'new_courseDescription': new_courseDescription,
                'question1': question1, 'new_question1': new_question1,
                'question2': question2, 'new_question2': new_question2,
                'question3': question3, 'new_question3': new_question3,
                'question4': question4, 'new_question4': new_question4,
                'universityName': universityName
            }
        else:
            raise Exception(f"API returned status code {response.status_code}")
    except Exception as e:
        print(f"Failed to process row with email: {email}. Error: {e}")
        return None


def process_csv_concurrent(input_file, output_file, api_url, max_workers=5):
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = [
            'email', 'firstName', 'lastName', 'courseCode', 'fa24CourseCode',
            'courseName', 'new_courseName', 'courseDescription', 'new_courseDescription',
            'question1', 'new_question1', 'question2', 'new_question2',
            'question3', 'new_question3', 'question4', 'new_question4', 'universityName'
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_row, row, api_url, index): row for index, row in enumerate(reader)}

            for future in as_completed(futures):
                result = future.result()
                if result:
                    writer.writerow(result)


# Usage example
input_file = 'sheet1.csv'
output_file = 'output.csv'
api_url = 'https://search-and-crawl-k2jau.ondigitalocean.app/gepeto/packback-four-questions'
process_csv_concurrent(input_file, output_file, api_url, max_workers=3)
