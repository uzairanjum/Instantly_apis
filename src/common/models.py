# src/common/models.py
from typing import List
from pydantic import BaseModel, Field, validator

class CampaignSummary(BaseModel):
    campaign_id: str
    campaign_name: str
    total_leads: int
    contacted: int
    not_yet_contacted: int
    leads_who_replied: int


class TimeFrameCampaignData(BaseModel):
    emails_sent: int
    emails_read: int
    new_leads_contacted: int
    leads_replied: int
    leads_read: int
    campaign_id: str
    campaign_name: str



class WeeklyCampaignSummary(BaseModel):
    week: str
    total_leads: int
    contacted: int
    not_yet_contacted: int
    leads_who_replied: int
    positive_reply:int
    domain_health: str


class DiscussionQuestion(BaseModel):
    question: str

class DiscussionQuestionsResponse(BaseModel):
    questions: List[DiscussionQuestion]






class PackbackCourseQueryRequest(BaseModel):
    query: str
    open_ai_model: str = "gpt-4o-mini"




class PackbackCourseDescriptionResponse(BaseModel):
    course_name: str
    course_description: str

class PackbackCourseDescriptionRequest(BaseModel):
    course_code: str
    university_name: str
    professor_name: str
    open_ai_model: str = "gpt-4o-mini"


class PackbackTenQuestionsRequest(PackbackCourseDescriptionRequest):
    question1: str
    question2: str
    question3: str
    question4: str


class PackbackCourseQuestionsResponse(PackbackCourseDescriptionResponse):
    questions: List[DiscussionQuestion]

class QuestionGeneratorRequest(BaseModel):
    course_name: str
    course_description: str
    open_ai_model: str = "gpt-4o-mini"


class TenQuestionsGeneratorRequest(BaseModel):
    course_name: str
    course_description: str
    open_ai_model: str = "gpt-4o-mini"
    question1: str
    question2: str
    question3: str
    question4: str


class GenerateEmailsRequest(BaseModel):
    count: int = Field(..., gt=0, description="Number of emails to generate")
    client_name: str = Field(..., min_length=3, max_length=50, description="Base string for email generation")

    @validator('client_name')
    def base_str_must_be_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('client_name must be alphanumeric')
        return v

class GenerateEmailsResponse(BaseModel):
    emails: List[str]
