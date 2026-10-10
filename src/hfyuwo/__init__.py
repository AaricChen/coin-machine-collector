"""
hfyuwo 后台 API 封装：模型 + 可独立调用的 service 函数。

快速开始::

    from hfyuwo import create_context
    from hfyuwo.services.facility import list_facilities_page

    page = list_facilities_page(1, 50)
    print(page.total, page.rows[0].facility_name)
"""

from hfyuwo.context import HfyuwoContext, create_context
from hfyuwo.models import Facility, RuoYiPage, UserInfoResponse

__all__ = [
    "Facility",
    "HfyuwoContext",
    "RuoYiPage",
    "UserInfoResponse",
    "create_context",
]
