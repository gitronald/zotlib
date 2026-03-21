"""Configuration management for zotlib."""

import os
from pathlib import Path

CONFIG_FILE = "zotlib.toml"


def load_config() -> dict:
    """Load configuration from zotlib.toml if it exists.

    Returns a dict with keys like 'database', 'pdfs_dir' or empty dict.
    """
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        return {}

    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    text = config_path.read_text()
    data = tomllib.loads(text)
    return data.get("zotlib", {})


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


def discover_pdfs_dir(db_path: Path | None = None, check_exists: bool = True) -> Path | None:
    """Discover the linked attachments directory from Zotero preferences.

    Reads baseAttachmentPath from prefs.js in the Zotero profile directory.
    Set check_exists=False to return the path even if not currently accessible.
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
                    if not check_exists or path.exists():
                        return path

    return None


def get_database_path(explicit_path: Path | str | None = None) -> Path:
    """Get the Zotero database path.

    Priority order:
    1. Explicit path argument (CLI flag)
    2. ZOTERO_DATABASE environment variable
    3. zotlib.toml config file
    4. Auto-discovery

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

    # Check config file
    config = load_config()
    if "database" in config:
        path = Path(config["database"])
        if path.exists():
            return path

    # Try auto-discovery
    discovered = discover_zotero_database()
    if discovered:
        return discovered

    raise FileNotFoundError(
        "Could not find Zotero database. "
        "Run 'zotlib init', set ZOTERO_DATABASE, or use --database flag."
    )


def get_pdfs_dir(explicit_path: Path | str | None = None) -> Path | None:
    """Get the linked PDFs directory.

    Priority order:
    1. Explicit path argument (CLI flag)
    2. zotlib.toml config file
    3. Auto-discovery from Zotero preferences

    Returns None if no directory can be found.
    """
    if explicit_path:
        path = Path(explicit_path)
        if path.exists():
            return path
        return None

    # Check config file
    config = load_config()
    if "pdfs_dir" in config:
        path = Path(config["pdfs_dir"])
        if path.exists():
            return path

    # Try auto-discovery
    return discover_pdfs_dir()


def write_config(database: Path, pdfs_dir: Path | None = None) -> Path:
    """Write configuration to zotlib.toml.

    Returns the path to the config file.
    """
    config_path = Path(CONFIG_FILE)
    lines = ["[zotlib]", f'database = "{database}"']
    if pdfs_dir:
        lines.append(f'pdfs_dir = "{pdfs_dir}"')
    lines.append("")  # trailing newline
    config_path.write_text("\n".join(lines))
    return config_path
