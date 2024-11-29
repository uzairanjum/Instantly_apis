import instructor
from pydantic import BaseModel
from openai import OpenAI
from src.settings import settings

# Define your desired output structure
class ExtractCourseInformation(BaseModel):
    course_name: str
    course_description: str




class ExtractOpenAI():

    def __init__(self):
        self.client = instructor.from_openai(OpenAI(api_key=settings.OPENAI_API_KEY))


    def extract_data(self, value):
        res = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=ExtractCourseInformation,
            messages=[{"role": "user", "content": value}],
        ) 
        return  {"course_name": res.course_name, "course_description": res.course_description}


