from __future__ import annotations

import requests
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class CropRectDto:
    left: int
    top: int
    width: int
    height: int


class _ApiClient:
    """Internal API client for the captcha-platform (createTask + remote-session)."""

    def __init__(self, base_url: str, client_key: str):
        self._base_url = base_url.rstrip("/")
        self._client_key = client_key or ""
        self._session = requests.Session()
        self._session.headers["Cache-Control"] = "no-store"
        self._session.headers["Content-Type"] = "application/json"

    def create_task(self, page_url: Optional[str] = None) -> dict[str, Any]:
        url = f"{self._base_url}/api/createTask"
        body = {
            "clientKey": self._client_key,
            "task": {
                "type": "RemoteCaptchaTask",
                "websiteURL": page_url or "https://accounts.hcaptcha.com/demo",
            },
        }
        r = self._session.post(url, json=body)
        r.raise_for_status()
        return r.json()

    def start_remote_session(
        self,
        task_id: str,
        screenshot: Optional[str],
        page_url: str,
        width: int,
        height: int,
        crop_rect: Optional[CropRectDto] = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}/api/client/remote-session/start"
        body = {
            "clientKey": self._client_key,
            "taskId": task_id,
            "screenshot": screenshot,
            "pageUrl": page_url,
            "width": width,
            "height": height,
            "cropRect": (
                {"left": crop_rect.left, "top": crop_rect.top, "width": crop_rect.width, "height": crop_rect.height}
                if crop_rect
                else None
            ),
        }
        r = self._session.post(url, json=body)
        r.raise_for_status()
        return r.json()

    def get_next_action(self, task_id: str) -> dict[str, Any]:
        url = f"{self._base_url}/api/client/remote-session/{task_id}/next-action"
        r = self._session.get(url, params={"clientKey": self._client_key})
        r.raise_for_status()
        return r.json()

    def update_screenshot(
        self,
        task_id: str,
        screenshot: str,
        width: int,
        height: int,
        crop_rect: Optional[CropRectDto] = None,
    ) -> None:
        url = f"{self._base_url}/api/client/remote-session/{task_id}/screenshot"
        body = {
            "clientKey": self._client_key,
            "screenshot": screenshot,
            "width": width,
            "height": height,
            "cropRect": (
                {"left": crop_rect.left, "top": crop_rect.top, "width": crop_rect.width, "height": crop_rect.height}
                if crop_rect
                else None
            ),
        }
        r = self._session.post(url, json=body)
        r.raise_for_status()

    def notify_solved(self, task_id: str, token: str) -> None:
        url = f"{self._base_url}/api/client/remote-session/{task_id}/solved"
        r = self._session.post(url, json={"clientKey": self._client_key, "token": token})
        r.raise_for_status()
