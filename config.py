from pathlib import Path
from typing import Any, Dict

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def load_config():
    """Load configuration from config.toml"""
    config_path = Path("config.toml")
    if not config_path.exists():
        raise FileNotFoundError(
            "config.toml not found. Copy config.example.toml to config.toml and configure your printer."
        )

    with open(config_path, "rb") as f:
        return tomllib.load(f)


def get_recurring_tasks() -> Dict[str, Any]:
    """Get all recurring tasks from config"""
    try:
        config = load_config()
        return config.get("recurring_tasks", {})
    except Exception:
        return {}
