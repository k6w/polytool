"""Unit tests for the cross-platform browser-data-dir resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from polytool.core.browsers import (
    ALL_BROWSERS,
    FIREFOX_FORK_DIRS,
    YT_DLP_NATIVE_BROWSERS,
    resolve_firefox_profile_dir,
)


def _seed(root: Path, *, profile_name: str = "default") -> tuple[Path, Path]:
    profile = root / f"abcd1234.{profile_name}"
    profile.mkdir(parents=True)
    (root / "profiles.ini").write_text(
        f"[Profile0]\nName={profile_name}\nIsRelative=1\nPath={profile.name}\nDefault=1\n",
        encoding="utf-8",
    )
    return root, profile


def test_native_browsers_listed() -> None:
    expected = {
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
    assert expected == YT_DLP_NATIVE_BROWSERS


def test_firefox_forks_listed() -> None:
    assert set(FIREFOX_FORK_DIRS) == {"zen", "librewolf", "waterfox", "floorp", "mullvad"}


def test_all_browsers_is_native_plus_forks() -> None:
    assert set(ALL_BROWSERS) == YT_DLP_NATIVE_BROWSERS | set(FIREFOX_FORK_DIRS)


def test_resolve_default(tmp_path) -> None:
    data_dir, profile_dir = _seed(tmp_path / "zen")
    assert resolve_firefox_profile_dir(data_dir) == profile_dir


def test_resolve_named_profile(tmp_path) -> None:
    data_dir, _ = _seed(tmp_path / "zen", profile_name="default")
    extra = data_dir / "xyz789.work"
    extra.mkdir()
    ini = data_dir / "profiles.ini"
    ini.write_text(
        ini.read_text(encoding="utf-8")
        + f"\n[Profile1]\nName=work\nIsRelative=1\nPath={extra.name}\n",
        encoding="utf-8",
    )
    assert resolve_firefox_profile_dir(data_dir, "work") == extra


def test_resolve_install_default_wins(tmp_path) -> None:
    """`[InstallXXX] Default=` should win over `[ProfileN] Default=1`."""
    data_dir = tmp_path / "lw"
    data_dir.mkdir()
    a = data_dir / "aaa.profA"
    b = data_dir / "bbb.profB"
    a.mkdir()
    b.mkdir()
    (data_dir / "profiles.ini").write_text(
        f"[Profile0]\nName=A\nIsRelative=1\nPath={a.name}\nDefault=1\n"
        f"\n[Profile1]\nName=B\nIsRelative=1\nPath={b.name}\n"
        f"\n[Install01]\nDefault={b.name}\nLocked=1\n",
        encoding="utf-8",
    )
    assert resolve_firefox_profile_dir(data_dir) == b


def test_resolve_unknown_profile(tmp_path) -> None:
    data_dir, _ = _seed(tmp_path / "zen")
    with pytest.raises(FileNotFoundError):
        resolve_firefox_profile_dir(data_dir, "nope")


def test_resolve_falls_back_to_profiles_dir(tmp_path) -> None:
    """Missing profiles.ini → scan the Profiles/ directory."""
    data_dir = tmp_path / "zen"
    data_dir.mkdir()
    profile = data_dir / "Profiles" / "abc.default"
    profile.mkdir(parents=True)
    assert resolve_firefox_profile_dir(data_dir) == profile


def test_resolve_no_profiles(tmp_path) -> None:
    """Empty data dir should raise."""
    empty = tmp_path / "zen"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        resolve_firefox_profile_dir(empty)
