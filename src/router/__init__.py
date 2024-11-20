from fastapi import APIRouter

from .webhooks import instantly_webhook_router
from .apis import instantly_api_router
from .packback import packback_router

router = APIRouter(prefix='/gepeto')

router.include_router(instantly_webhook_router,tags=['Instantly'])
router.include_router(instantly_api_router,tags=['Instantly'])
router.include_router(packback_router,tags=['Packback'])