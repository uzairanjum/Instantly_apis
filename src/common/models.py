# src/common/models.py

from pydantic import BaseModel

class CampaignSummary(BaseModel):
    campaign_id: str
    campaign_name: str
    total_leads: int
    contacted: int
    not_yet_contacted: int
    leads_who_replied: int


class WeeklyCampaignSummary(BaseModel):
    week: str
    total_leads: int
    contacted: int
    not_yet_contacted: int
    leads_who_replied: int
    positive_reply:int
    domain_health: str