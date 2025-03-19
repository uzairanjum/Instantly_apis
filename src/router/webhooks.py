from fastapi import APIRouter
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
        logger.info("Incoming webhook  - %s - %s - %s", data.get('lead_email'), data.get('campaign_id'), data.get('event_type'))
        if data.get('event_type') == "reply_received":
            instantly_queue.enqueue(get_data_from_instantly, data.get('lead_email'), data.get('campaign_id'), 'reply_received')
            # return get_data_from_instantly(data.get('lead_email'), data.get('campaign_id'),'reply_received')
    finally:
        return JSONResponse(content={"status": "success"}, status_code=200)


@instantly_webhook_router.post('/outgoing')
def outgoing_sms(data:dict):
    try:    
        if data.get('event_type') == "email_sent":
            logger.info("Outgoing webhook  - %s - %s", data.get('lead_email'), data.get('campaign_id'))
            # instantly_queue.enqueue(get_data_from_instantly, data.get('lead_email'), data.get('campaign_id'),'email_sent')
            # return get_data_from_instantly(data.get('lead_email'), data.get('campaign_id'),'email_sent')
    finally:
        return JSONResponse(content={"status": "success"}, status_code=200)
    
@instantly_webhook_router.post('/all-events')
def all_events(data:dict):        
    try:
        logger.info("All events webhook  - %s - %s - %s", data.get('lead_email'), data.get('campaign_id'), data.get('event_type'))
        if data.get('event_type') == "lead_out_of_office":
            # logger.info("All events webhook  - %s - %s - %s", data.get('lead_email'), data.get('campaign_id'), data.get('event_type'))
            instantly_queue.enqueue(get_data_from_instantly, data.get('lead_email'), data.get('campaign_id'), 'reply_received')

    finally:
        return JSONResponse(content={"status": "success"}, status_code=200)

@instantly_webhook_router.post('/test-redis')
def test_redis(request:dict):
    try:    

        lead_email = request.get('lead_email')
        logger.info("Test redis webhook  - %s ", lead_email)
        instantly_queue.enqueue(test_redis_queue, lead_email)
    finally:
        return JSONResponse(content={"status": "success"}, status_code=200)

def test_redis_queue(lead_email):
    logger.info("Redis queue working - %s ", lead_email)
    