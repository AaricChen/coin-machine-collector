"""RuoYi 通用响应与分页模型。"""

from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)


class RuoYiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class RuoYiResult(RuoYiModel):
    code: int
    msg: str = ""


class RuoYiDataResult(RuoYiModel, Generic[T]):
    """RuoYi 单对象响应：{ code, msg, data: {...} }"""

    code: int
    msg: str = ""
    data: T

    @classmethod
    def from_payload(cls, payload: dict[str, Any], data_type: type[T]) -> RuoYiDataResult[T]:
        if payload.get("code") not in (None, 200):
            raise RuntimeError(f"接口失败：{payload.get('msg') or payload}")
        raw = payload.get("data")
        if not isinstance(raw, dict):
            raise RuntimeError(f"响应缺少 data 对象：{payload}")
        return cls(
            code=int(payload.get("code") or 200),
            msg=str(payload.get("msg") or ""),
            data=data_type.model_validate(raw),
        )


class RuoYiPage(RuoYiModel, Generic[T]):
    code: int
    msg: str = ""
    total: int = 0
    rows: list[T] = Field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: dict[str, Any], row_type: type[T]) -> RuoYiPage[T]:
        if payload.get("code") not in (None, 200):
            raise RuntimeError(f"接口失败：{payload.get('msg') or payload}")

        rows_raw = extract_rows(payload)
        rows = [row_type.model_validate(item) for item in rows_raw]
        total = int(payload.get("total") if payload.get("total") is not None else len(rows))
        return cls(
            code=int(payload.get("code") or 200),
            msg=str(payload.get("msg") or ""),
            total=total,
            rows=rows,
        )


def extract_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("rows"), list):
        return [x for x in payload["rows"] if isinstance(x, dict)]
    data = payload.get("data")
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("rows", "list", "records", "machines", "tracks"):
            candidate = data.get(key)
            if isinstance(candidate, list):
                return [x for x in candidate if isinstance(x, dict)]
    return []


def fetch_all_pages(
    fetch_page: Callable[[int, int], RuoYiPage[T]],
    page_size: int = 50,
) -> list[T]:
    first = fetch_page(1, page_size)
    items = list(first.rows)
    total = first.total
    page_num = 2
    while len(items) < total:
        page = fetch_page(page_num, page_size)
        if not page.rows:
            break
        items.extend(page.rows)
        page_num += 1
    return items
