"""
config.py -- Configuration loader for Bureaucracy Copilot.
"""
import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_CONFIG = {
    "anthropic_model": "claude-opus-4-5",
    "gmail_max_results": 100,
    "calendar_timezone": "America/Santiago",
    "currency": "CLP",
    "language": "es",
    "data_dir": "~/.bureaucracy_copilot",
    "insurers": ["Esencial", "BICE VIDA", "Clinica Alemana"],
    "banks": ["Tenpo", "BICE", "BancoEstado"],
}

CONFIG_PATH = Path("~/.bureaucracy_copilot/config.json").expanduser()


def load_config(path: Optional[Path] = None) -> dict:
    """Load configuration from file, merging with defaults."""
    cfg = DEFAULT_CONFIG.copy()
    config_file = path or CONFIG_PATH

    if config_file.exists():
        with open(config_file) as f:
            user_cfg = json.load(f)
        cfg.update(user_cfg)

    # Allow env var overrides
    if "ANTHROPIC_API_KEY" in os.environ:
        cfg["anthropic_api_key"] = os.environ["ANTHROPIC_API_KEY"]
    if "BC_DATA_DIR" in os.environ:
        cfg["data_dir"] = os.environ["BC_DATA_DIR"]

    return cfg


def save_config(cfg: dict, path: Optional[Path] = None) -> None:
    """Save configuration to file."""
    config_file = path or CONFIG_PATH
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_data_dir(cfg: dict) -> Path:
    """Return the resolved data directory path."""
    return Path(cfg.get("data_dir", "~/.bureaucracy_copilot")).expanduser()
