from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse



app = FastAPI(title = "GEPETO-WEBHOOK")


@app.get('/', tags=['health'], summary="Check server health")
def root():
    return {"message": 'healthy'}


@app.post('/gepeto/incoming-sms', tags=['Webhook'], summary="Incoming sms webhook")
def incoming_sms(sms:dict):
    print("------------webhook,",sms)
    return JSONResponse(content={"status": "success"}, status_code=200)


@app.post('/gepeto/case-webhook', tags=['Webhook'], summary="salesforce webhook")
async def salesforce_webhook(request: Request):
    try:
        # Access the JSON payload
        body = await request.json()
        print("Received webhook payload:", body)



        # Process the payload as needed
        return JSONResponse(content={"status": "success"}, status_code=200)

    except Exception as e:
        print("Exception occurred in sales webhook:", e)
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)