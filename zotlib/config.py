"""Configuration management for zotlib."""

import os
from pathlib import Path


def discover_zotero_database() -> Path | None:
    """Attempt to auto-discover Zotero database location.

    Checks common locations across different platforms.
    """
    user = os.environ.get("USER", "")

    candidates = [
        # Linux (native)
        Path.home() / "Zotero" / "zotero.sqlite",
        # WSL accessing Windows
        Path(f"/mnt/c/Users/{user}/Zotero/zotero.sqlite"),
        # macOS
        Path.home() / "Library" / "Zotero" / "zotero.sqlite",
    ]

    # Windows (if APPDATA exists)
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "Zotero" / "Zotero" / "zotero.sqlite")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def get_database_path(explicit_path: Path | str | None = None) -> Path:
    """Get the Zotero database path.

    Priority order:
    1. Explicit path argument
    2. ZOTERO_DATABASE environment variable
    3. Auto-discovered location

    Raises:
        FileNotFoundError: If no database can be found.
    """
    # Check explicit path
    if explicit_path:
        path = Path(explicit_path)
        if path.exists():
            return path
        raise FileNotFoundError(f"Zotero database not found at: {path}")

    # Check environment variable
    env_path = os.environ.get("ZOTERO_DATABASE")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        raise FileNotFoundError(
            f"ZOTERO_DATABASE path does not exist: {path}"
        )

    # Try auto-discovery
    discovered = discover_zotero_database()
    if discovered:
        return discovered

    raise FileNotFoundError(
        "Could not find Zotero database. "
        "Set ZOTERO_DATABASE environment variable or use --database flag."
    )
