from fastapi import FastAPI
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
def salesforce_webhook(data:dict):
    print("------------webhook,",data)
    return JSONResponse(content={"status": "success"}, status_code=200)

