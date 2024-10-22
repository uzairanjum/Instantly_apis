# src/common/models.py

from pydantic import BaseModel

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