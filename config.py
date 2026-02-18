"""
Load ESO paths and settings from environment. Load .env from project root if present.
Other scripts can: from config import ESO_LIVE_PATH, ESO_INSTALL_PATH
"""
from pathlib import Path
import os

# Load .env from project root (parent of config.py)
try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent
    load_dotenv(_root / ".env")
except ImportError:
    pass

# Paths (set in .env; see .env.example)
ESO_INSTALL_PATH = os.environ.get("ESO_INSTALL_PATH", "").strip() or None
ESO_LIVE_PATH = os.environ.get("ESO_LIVE_PATH", "").strip() or None

# Derived; None if base path not set
ESO_SAVED_VARIABLES_PATH = Path(ESO_LIVE_PATH) / "SavedVariables" if ESO_LIVE_PATH else None
ESO_ADDONS_PATH = Path(ESO_LIVE_PATH) / "AddOns" if ESO_LIVE_PATH else None


def get_eso_live_path() -> Path | None:
    """Return ESO live folder as Path, or None if not set."""
    if not ESO_LIVE_PATH:
        return None
    p = Path(ESO_LIVE_PATH)
    return p if p.exists() else None


def get_eso_install_path() -> Path | None:
    """Return ESO install folder as Path, or None if not set."""
    if not ESO_INSTALL_PATH:
        return None
    p = Path(ESO_INSTALL_PATH)
    return p if p.exists() else None
