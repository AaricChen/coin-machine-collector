"""运行时上下文：配置 + Token + HTTP 客户端。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import Settings, load_config
from hfyuwo.client import HfyuwoClient
from paths import PROJECT_ROOT
from token_manager import TokenManager


@dataclass
class HfyuwoContext:
    settings: Settings
    token_manager: TokenManager
    client: HfyuwoClient

    def ensure_token(self) -> str:
        return self.token_manager.get_valid_token()


def create_context(config_path: Optional[str | Path] = None) -> HfyuwoContext:
    path = config_path or PROJECT_ROOT / "config" / "settings.yaml"
    settings = load_config(path)
    token_manager = TokenManager(settings)
    client = HfyuwoClient(settings, token_manager)
    return HfyuwoContext(
        settings=settings,
        token_manager=token_manager,
        client=client,
    )
