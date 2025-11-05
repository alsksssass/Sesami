from typing import Optional, Dict, Any


class WebhookService:
    async def handle_github_webhook(
        self,
        event_type: Optional[str],
        signature: Optional[str],
        payload: Dict[str, Any]
    ):
        """
        GitHub Webhook 이벤트 처리

        Args:
            event_type: 이벤트 타입 (push, pull_request 등)
            signature: GitHub 시그니처 (보안 검증용)
            payload: 웹훅 페이로드
        """
        # TODO: 시그니처 검증
        # TODO: 이벤트 타입별 처리 로직
        print(f"Received GitHub webhook: {event_type}")
        return {"status": "received", "event": event_type}

    def verify_signature(self, signature: str, payload: bytes) -> bool:
        """GitHub Webhook 시그니처 검증"""
        # TODO: HMAC SHA256 검증 로직
        return True
