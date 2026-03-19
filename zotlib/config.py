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


def _windows_to_wsl_path(win_path: str) -> Path:
    """Convert a Windows path like 'I:\\My Drive\\zotero-pdfs' to WSL '/mnt/i/My Drive/zotero-pdfs'."""
    from pathlib import PureWindowsPath
    p = PureWindowsPath(win_path)
    drive = p.drive.rstrip(":").lower()
    return Path(f"/mnt/{drive}") / p.relative_to(p.anchor)


def discover_pdfs_dir(db_path: Path | None = None) -> Path | None:
    """Discover the linked attachments directory from Zotero preferences.

    Reads baseAttachmentPath from prefs.js in the Zotero profile directory.
    """
    user = os.environ.get("USER", "")

    profile_dirs = [
        # WSL
        Path(f"/mnt/c/Users/{user}/AppData/Roaming/Zotero/Zotero/Profiles"),
        # Linux
        Path.home() / ".zotero" / "zotero" / "Profiles",
        # macOS
        Path.home() / "Library" / "Application Support" / "Zotero" / "Profiles",
    ]

    for profile_dir in profile_dirs:
        if not profile_dir.exists():
            continue
        for prefs_file in profile_dir.glob("*/prefs.js"):
            for line in prefs_file.read_text(errors="ignore").splitlines():
                if "extensions.zotero.baseAttachmentPath" in line and "better-bibtex" not in line:
                    # Extract value from: user_pref("...", "value");
                    value = line.split('"')[-2]
                    # Convert Windows path if needed
                    if "\\" in value or (len(value) > 1 and value[1] == ":"):
                        path = _windows_to_wsl_path(value)
                    else:
                        path = Path(value)
                    if path.exists():
                        return path

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
