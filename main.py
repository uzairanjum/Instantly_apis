from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.common.logger import get_logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from typing import List
from src.router import router
from src.settings import settings

logger = get_logger("Main")



def make_middleware() -> List[Middleware]:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
    return middleware

def init_routers(app_: FastAPI) -> None:
    app_.include_router(router)


# App Setup
def create_app() -> FastAPI:
    app_ = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,

    )
    init_routers(app_=app_)
    return app_


app = create_app()

@app.get('/',  tags=['health'], summary='HEALTHY')
def root():
    return JSONResponse(content={"status": "success"}, status_code=200)




