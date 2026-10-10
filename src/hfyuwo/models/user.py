"""用户 / 登录会话相关模型。"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from hfyuwo.models.base import RuoYiModel


class UserProfile(RuoYiModel):
    user_id: Optional[int] = Field(None, alias="userId")
    user_name: Optional[str] = Field(None, alias="userName")
    nick_name: Optional[str] = Field(None, alias="nickName")
    operator_id: Optional[int] = Field(None, alias="operatorId")
    operator_name: Optional[str] = Field(None, alias="operatorName")
    phonenumber: Optional[str] = None
    email: Optional[str] = None
    admin: Optional[bool] = None


class UserInfoResponse(RuoYiModel):
    code: int = 200
    msg: str = ""
    user: Optional[UserProfile] = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: dict) -> UserInfoResponse:
        if payload.get("code") not in (None, 200):
            raise RuntimeError(f"getInfo 失败：{payload.get('msg') or payload}")
        return cls.model_validate(payload)
