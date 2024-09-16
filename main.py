from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse

from openai_llm import OpenAiConfig

open_ai = OpenAiConfig("key")

app = FastAPI(title = "GEPETO-WEBHOOK")


@app.get('/', tags=['health'], summary="Check server health")
def root():
    return {"message": 'healthy'}


@app.post('/gepeto/email-sent', tags=['Webhook'])
def incoming_sms(email:dict):
    print("------------webhook,",email)
    return JSONResponse(content={"status": "success"}, status_code=200)


@app.post('/gepeto/bot', tags=['Webhook'])
def received_sms(data:dict):
    print("------------webhook,",data)
    return JSONResponse(content={"status": "success"}, status_code=200)


from instantly import InstantlyAPI


@app.post('/gepeto/instantly/received', tags=['Webhook'])
def received_sms(data: dict):
    try:
        if data.get('event_type') == "reply_received":
            instantly = InstantlyAPI(api_key="hxfec34ac1m9z0nk0s96z1den868")

            # Get basic lead information from webhook payload
            campaign_id = data.get('campaign_id')
            lead_email = data.get('lead_email')
            subject = data.get('reply_subject')
            from_email = data.get('email_account')

            if not all([campaign_id, lead_email, subject, from_email]):
                raise ValueError("Missing required fields in the payload")

            # Generate message history by fetching all lead emails
            all_emails = instantly.get_all_emails(lead=lead_email, campaign_id=campaign_id)
            if not all_emails:
                raise ValueError("No emails found for the given lead and campaign")

            message_history = format_email_history(all_emails)
            latest_uuid = all_emails[0].get('id')

            # Generate AI response
            prompt = """    
                        You are Steve, a digital assistant that helps set up appointments for their teammates at Packback. 
                        Steve’s ultimate goal is to schedule appointments between prospects and Uzair by sending 
                        emails to prospective customers for Packback. """
            formatted_history = [{"role": "system", "content": prompt}, *message_history]
            response = open_ai.generate_response(formatted_history, "gpt-4o")

            # Send AI response to lead
            instantly.send_reply(uuid=latest_uuid, from_email=from_email, to_email=lead_email, message=response, subject=subject)

            return JSONResponse(content={"status": "success", "message_history": message_history}, status_code=200)

        return JSONResponse(content={"status": "ignored", "reason": "Event type not handled"}, status_code=200)

    except ValueError as ve:
        return JSONResponse(content={"status": "error", "message": str(ve)}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": "Internal server error"}, status_code=500)





def format_email_history(all_emails:dict):
    message_history:list = []
    # Extract the latest message
      # Assuming messages is the list of threads sorted by timestamp


    for message in all_emails:
        if message['from_address_email'] == message['eaccount']:
            role = 'assistant'
        else:
            role = 'user'
        content = message.get('content_preview') or message.get('body', {}).get('html')
        message_history.append({ "role": role,"content": content})

    message_history.reverse()
    return message_history
