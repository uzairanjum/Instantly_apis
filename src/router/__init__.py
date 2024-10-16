from fastapi import APIRouter

from .webhooks import instantly_webhook_router
from .apis import instantly_api_router


router = APIRouter(prefix='/gepeto', tags=['Instantly'])

router.include_router(instantly_webhook_router)
router.include_router(instantly_api_router)