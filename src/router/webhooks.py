from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
from rq import Queue
from src.common.logger import get_logger
from src.core.leadHistory import get_data_from_instantly
from src.database.redis import RedisConfig

logger = get_logger("Webhook")
instantly_webhook_router = APIRouter()



instantly_queue = Queue("instantly_queue", connection=RedisConfig().redis)


@instantly_webhook_router.post('/incoming')
def incoming_sms(data:dict):        
    try:
        if data.get('event_type') == "reply_received":
            logger.info("Incoming webhook  - %s - %s", data.get('lead_email'), data.get('campaign_id'))
            instantly_queue.enqueue(get_data_from_instantly, data.get('lead_email'), data.get('campaign_id'), 'reply_received')
            # return get_data_from_instantly(data.get('lead_email'), data.get('campaign_id'),'reply_received')
    finally:
        return JSONResponse(content={"status": "success"}, status_code=200)

@instantly_webhook_router.post('/outgoing')
def outgoing_sms(data:dict):
    try:    
        if data.get('event_type') == "email_sent":
            logger.info("Outgoing webhook  - %s - %s", data.get('lead_email'), data.get('campaign_id'))
            instantly_queue.enqueue(get_data_from_instantly, data.get('lead_email'), data.get('campaign_id'),'email_sent')
            # return get_data_from_instantly(data.get('lead_email'), data.get('campaign_id'),'email_sent')
    finally:
        return JSONResponse(content={"status": "success"}, status_code=200)

