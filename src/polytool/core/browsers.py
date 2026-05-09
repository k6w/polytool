"""Cross-platform helpers for finding browser data directories.

yt-dlp natively supports a fixed set of browsers (chrome / firefox / edge /
brave / chromium / opera / safari / vivaldi / whale). This module fills in
the gap for **Firefox forks** that aren't in yt-dlp's list — Zen Browser,
LibreWolf, Waterfox, Floorp, and Mullvad Browser — by:

1. Locating the fork's data directory cross-platform.
2. Reading its ``profiles.ini`` (standard Firefox format) to find the
   default profile (or the named profile the user asked for).
3. Returning the absolute profile path.

We then hand that path to yt-dlp's ``firefox`` extractor, which accepts a
profile *directory path* (not just a name) — so cookies from Zen et al.
work transparently.
"""

from __future__ import annotations

import configparser
import os
import sys
from pathlib import Path

# Browsers that yt-dlp's `cookiesfrombrowser` understands natively.
YT_DLP_NATIVE_BROWSERS: frozenset[str] = frozenset(
    {
        "chrome",
        "firefox",
        "edge",
        "brave",
        "chromium",
        "opera",
        "safari",
        "vivaldi",
        "whale",
    }
)

# Firefox forks → list of platform basenames to probe (in order).
# Different installers/distros use different casings, hence the multiple options.
FIREFOX_FORK_DIRS: dict[str, tuple[str, ...]] = {
    "zen": ("zen",),
    "librewolf": ("librewolf", "LibreWolf"),
    "waterfox": ("waterfox", "Waterfox"),
    "floorp": ("floorp", "Floorp"),
    "mullvad": ("MullvadBrowser", "mullvadbrowser"),
}

# All browser names we accept on the CLI (for help text / interactive picker /
# validation). Order is stable: native first, then forks.
ALL_BROWSERS: tuple[str, ...] = (
    "chrome",
    "firefox",
    "edge",
    "brave",
    "chromium",
    "opera",
    "safari",
    "vivaldi",
    "whale",
    "zen",
    "librewolf",
    "waterfox",
    "floorp",
    "mullvad",
)


def _platform_data_dirs(basename: str) -> list[Path]:
    """Return candidate data dirs for *basename* on the current OS."""
    home = Path.home()
    if sys.platform == "win32":
        appdata = Path(os.environ.get("APPDATA") or str(home / "AppData/Roaming"))
        local = Path(os.environ.get("LOCALAPPDATA") or str(home / "AppData/Local"))
        return [appdata / basename, local / basename]
    if sys.platform == "darwin":
        return [home / "Library/Application Support" / basename]
    # Linux / BSD / other unix
    return [home / f".{basename}", home / ".config" / basename]


def find_firefox_fork_data_dir(name: str) -> Path | None:
    """Return the data dir of a Firefox fork, or ``None`` if not installed.

    >>> # find_firefox_fork_data_dir("zen") → e.g. PosixPath('/home/u/.zen')
    """
    basenames = FIREFOX_FORK_DIRS.get(name.lower())
    if not basenames:
        return None
    for basename in basenames:
        for candidate in _platform_data_dirs(basename):
            if candidate.is_dir():
                return candidate
    return None


def resolve_firefox_profile_dir(data_dir: Path, profile_name: str | None = None) -> Path:
    """Resolve a Firefox-style profile directory inside *data_dir*.

    Reads ``data_dir/profiles.ini`` and returns the absolute path of:

    * the profile whose ``Name=`` matches *profile_name* (if given), or
    * the install's ``Default=`` profile (preferred), or
    * the first profile with ``Default=1``, or
    * the first profile listed.

    Falls back to scanning ``data_dir/Profiles/`` directly if ``profiles.ini``
    is missing — useful for the rare case where a fork doesn't ship one yet.

    Raises ``FileNotFoundError`` if nothing matches.
    """
    ini = data_dir / "profiles.ini"
    if ini.exists():
        cp = configparser.ConfigParser(strict=False)
        cp.read(ini, encoding="utf-8")

        profile_sections: list[tuple[str, str, bool, bool]] = []
        install_default: str | None = None
        for section in cp.sections():
            low = section.lower()
            if low.startswith("profile"):
                name = cp.get(section, "Name", fallback="")
                path = cp.get(section, "Path", fallback="")
                is_relative = cp.getboolean(section, "IsRelative", fallback=True)
                is_default = cp.getint(section, "Default", fallback=0) == 1
                if path:
                    profile_sections.append((name, path, is_relative, is_default))
            elif low.startswith("install") and install_default is None:
                d = cp.get(section, "Default", fallback="")
                if d:
                    install_default = d

        if profile_name:
            for name, path, is_relative, _ in profile_sections:
                if profile_name in (name, path):
                    return data_dir / path if is_relative else Path(path)
            raise FileNotFoundError(f"No Firefox profile named {profile_name!r} in {ini}")

        if install_default:
            return data_dir / install_default
        for _name, path, is_relative, is_default in profile_sections:
            if is_default:
                return data_dir / path if is_relative else Path(path)
        if profile_sections:
            _name, path, is_relative, _ = profile_sections[0]
            return data_dir / path if is_relative else Path(path)
        raise FileNotFoundError(f"No profiles listed in {ini}")

    # No profiles.ini — try the Profiles/ directory directly.
    profiles_root = data_dir / "Profiles"
    if profiles_root.is_dir():
        children = sorted(p for p in profiles_root.iterdir() if p.is_dir())
        if profile_name:
            for c in children:
                # Profile directories look like xxxxxxxx.<name>
                if c.name.endswith(f".{profile_name}") or c.name == profile_name:
                    return c
            raise FileNotFoundError(f"No Firefox-style profile {profile_name!r} in {profiles_root}")
        if children:
            return children[0]
    raise FileNotFoundError(f"Could not find profiles.ini or Profiles/ in {data_dir}")
