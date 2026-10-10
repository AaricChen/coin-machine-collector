"""RuoYi 算术验证码：拉取图片并解析表达式结果。"""

from __future__ import annotations

import ast
import base64
import io
import operator
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

import httpx
from loguru import logger

from config import Settings

_MATH_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.floordiv,
}


def _safe_eval_math(expr: str) -> int:
    expr = expr.strip().replace("×", "*").replace("÷", "/").replace("x", "*").replace("X", "*")
    expr = re.sub(r"[^0-9+\-*/().]", "", expr)
    if not expr:
        raise ValueError("empty expression")
    node = ast.parse(expr, mode="eval").body
    return int(_eval_ast(node))


def _eval_ast(node: ast.AST) -> int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return int(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_ast(node.operand)
    if isinstance(node, ast.BinOp) and type(node.op) in _MATH_OPS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return _MATH_OPS[type(node.op)](left, right)
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def _normalize_ocr_text(raw: str) -> str:
    text = raw.replace(" ", "").replace("?", "").replace("=", "")
    text = text.replace("×", "*").replace("÷", "/").replace("x", "*").replace("X", "*")
    text = re.sub(r"[^0-9+\-*/().]", "", text)
    if text:
        return text
    # 常见 OCR 粘连：9*427 -> 9*4
    m = re.search(r"(\d{1,2})([\+\-\*\/])(\d{1,2})", raw.replace(" ", ""))
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}"
    return text


def _solve_from_ocr_text(raw: str) -> str:
    text = _normalize_ocr_text(raw)
    if not text:
        raise ValueError(f"OCR empty: {raw!r}")
    return str(_safe_eval_math(text))


def _ocr_with_ddddocr(img_bytes: bytes) -> str:
    try:
        import cv2  # noqa: F401
    except ImportError as e:
        raise RuntimeError("opencv 未安装，无法使用 ddddocr") from e
    import ddddocr

    ocr = ddddocr.DdddOcr(show_ad=False)
    return ocr.classification(img_bytes)


def _preprocess_for_ocr(img_bytes: bytes) -> bytes:
    from PIL import Image, ImageOps

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    # 算术验证码为蓝字浅底，放大后二值化便于 OCR
    w, h = img.size
    img = img.resize((w * 4, h * 4), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(img)
    gray = ImageOps.autocontrast(gray)
    bw = gray.point(lambda p: 0 if p < 160 else 255)
    out = io.BytesIO()
    bw.save(out, format="PNG")
    return out.getvalue()


def _ocr_with_macos_vision(img_bytes: bytes) -> str:
    if sys.platform != "darwin":
        raise RuntimeError("macOS Vision OCR only available on darwin")
    script = Path(__file__).resolve().parents[1] / "scripts" / "ocr_captcha.swift"
    if not script.exists():
        raise FileNotFoundError(script)

    tmp = Path("/tmp/coin_machine_captcha.jpg")
    tmp.write_bytes(img_bytes)
    proc = subprocess.run(
        ["/usr/bin/swift", str(script), str(tmp)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "Vision OCR failed")
    return proc.stdout.strip()


def solve_math_captcha_image(img_bytes: bytes) -> str:
    errors: list[str] = []
    candidates = [
        ("ddddocr", lambda: _ocr_with_ddddocr(img_bytes)),
        ("macos_vision", lambda: _ocr_with_macos_vision(img_bytes)),
        ("macos_vision_preprocessed", lambda: _ocr_with_macos_vision(_preprocess_for_ocr(img_bytes))),
    ]
    for name, fn in candidates:
        try:
            raw = fn()
            code = _solve_from_ocr_text(raw)
            logger.debug("验证码 OCR ({}) 原文 {} -> {}", name, raw, code)
            return code
        except Exception as e:
            errors.append(f"{name}: {e}")
    raise RuntimeError("无法识别验证码: " + "; ".join(errors))


class CaptchaClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        api = self.settings.api
        return {
            "isToken": "false",
            "Accept": "application/json",
            **api.extra_headers,
        }

    def fetch(self, client: httpx.Client) -> tuple[str, bytes]:
        api = self.settings.api
        url = f"{api.base_url.rstrip('/')}{api.captcha_path}"
        resp = client.get(url, headers=self._headers())
        resp.raise_for_status()
        payload: dict[str, Any] = resp.json()
        if payload.get("code") != 200:
            raise RuntimeError(f"获取验证码失败: {payload}")
        uuid = payload.get("uuid")
        img_b64 = payload.get("img")
        if not uuid or not img_b64:
            raise RuntimeError(f"验证码响应缺少 uuid/img: {payload}")
        return str(uuid), base64.b64decode(str(img_b64))

    def solve(self, img_bytes: bytes, manual_code: Optional[str] = None) -> str:
        if manual_code:
            return manual_code.strip()
        return solve_math_captcha_image(img_bytes)
