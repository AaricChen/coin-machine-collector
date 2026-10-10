"""用户信息服务（可独立 import 调用）。"""

from __future__ import annotations

from typing import Optional

from hfyuwo.context import HfyuwoContext, create_context
from hfyuwo.models.user import UserInfoResponse


def get_user_info(*, ctx: Optional[HfyuwoContext] = None) -> UserInfoResponse:
    """
    GET /getInfo，返回结构化用户信息。

    示例:
        from hfyuwo.services.user import get_user_info
        info = get_user_info()
        print(info.user.nick_name if info.user else None)
    """
    ctx = ctx or create_context()
    path = ctx.settings.api.user_info_path.lstrip("/")
    payload = ctx.client.get_json(path)
    return UserInfoResponse.from_payload(payload)
