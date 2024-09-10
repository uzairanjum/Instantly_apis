from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse



app = FastAPI(title = "GEPETO-WEBHOOK")


@app.get('/', tags=['health'], summary="Check server health")
def root():
    return {"message": 'healthy'}


# @app.post('/gepeto/incoming-sms', tags=['Webhook'], summary="Incoming sms webhook")
# def incoming_sms(sms:dict):
#     print("------------webhook,",sms)
#     return JSONResponse(content={"status": "success"}, status_code=200)


# @app.post('/gepeto/case-webhook', tags=['Webhook'], summary="salesforce webhook")
# async def salesforce_webhook(request: Request):
#     try:
#         # Access the JSON payload
#         body = await request.json()
#         print("Received webhook payload:", body)



#         # Process the payload as needed
#         return JSONResponse(content={"status": "success"}, status_code=200)

#     except Exception as e:
#         print("Exception occurred in sales webhook:", e)
#         return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

# @app.post('/gepeto/webflow', tags=['Webhook'], summary="web flow webhook")
# async def gepeto_webhook(request: dict):
#     try:
#         print("Received webhook payload:", request)



#         # Process the payload as needed
#         return JSONResponse(content={"status": "success"}, status_code=200)

#     except Exception as e:
#         print("Exception occurred in sales webhook:", e)
#         return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)



#         {'caseOrigin': 'Email', 'contactEmail': 'robert@hellogepeto.com', 'caseStatus': 'New', 'caseNumber': '00001035', 'caseId': '500IR00001FcfGVYAZ', 'contactPhone': '16469802405'}


# 


@app.post('/gepeto/email-sent', tags=['Webhook'])
def incoming_sms(email:dict):
    print("------------webhook,",email)
    return JSONResponse(content={"status": "success"}, status_code=200)


@app.post('/gepeto/bot', tags=['Webhook'])
def received_sms(data:dict):
    print("------------webhook,",data)
    return JSONResponse(content={"status": "success"}, status_code=200)


from instantly import InstantlyAPI


# Initialize an empty dictionary to store the results



@app.post('/gepeto/instantly/received', tags=['Webhook'])
def received_sms(data:dict):
    if data.get('event_type') == "reply_received":

        instantly = InstantlyAPI(api_key="hxfec34ac1m9z0nk0s96z1den868")


        campaign_id:str = data.get('campaign_id')
        lead_email:str = data.get('lead_email')
        subject:str = data.get('reply_subject')
        from_email:str  = data.get('email_account')
        
        all_emails:list = instantly.get_all_emails(lead=lead_email,campaign_id=campaign_id)
        message_history:list = format_email_history(all_emails)
        latest_uuid = all_emails[0].get('id')
        message:str = "yo yo yo, its working. . . . "
        send_reply = instantly.send_reply(uuid =latest_uuid, from_email = from_email, to_email =lead_email, message =message ,subject=subject )

        print("----", send_reply)
      
        return message_history





        


    return JSONResponse(content={"status": "success"}, status_code=200)




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
