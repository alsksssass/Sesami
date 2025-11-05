from fastapi import Request, Header
from typing import Optional

from common.router_registry import FeatureRouter
from .service import WebhookService

router = FeatureRouter(
    name="webhooks",
    version="v1",
    description="GitHub Webhooks"
)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature: Optional[str] = Header(None)
):
    """
    GitHub Webhook 엔드포인트
    저장소의 push, PR 등의 이벤트를 받습니다.
    """
    body = await request.json()
    service = WebhookService()

    return await service.handle_github_webhook(
        event_type=x_github_event,
        signature=x_hub_signature,
        payload=body
    )
