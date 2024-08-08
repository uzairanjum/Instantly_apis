from fastapi import FastAPI
from typing import Dict, Union
from fastapi import APIRouter
from fastapi.responses import JSONResponse


app = FastAPI(title = "GEPETO-WEBHOOK")


@app.get('/', tags=['health'], summary="Check server health")
def root():
    return {"message": 'healthy'}


@app.post('/gepeto/incoming-sms', tags=['Webhook'], summary="Incoming sms webhook")
def incoming_sms(sms:dict):
    print("------------webhook,",sms)
    return JSONResponse(content={"status": "success"}, status_code=200)

