from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_from_root(relative: str) -> Path:
    return (PROJECT_ROOT / relative).resolve()
