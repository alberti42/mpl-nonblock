from __future__ import annotations

from typing import Any


def test_recommended_backend_defaults(monkeypatch: Any) -> None:
    from mpl_nonblock import recommended_backend

    monkeypatch.setattr(__import__("sys"), "platform", "darwin")
    assert recommended_backend() == "macosx"

    monkeypatch.setattr(__import__("sys"), "platform", "linux")
    assert recommended_backend() == "TkAgg"

    monkeypatch.setattr(__import__("sys"), "platform", "win32")
    assert recommended_backend() == "TkAgg"

    monkeypatch.setattr(__import__("sys"), "platform", "something")
    assert recommended_backend() == "TkAgg"


def test_recommended_backend_overrides(monkeypatch: Any) -> None:
    from mpl_nonblock import recommended_backend

    monkeypatch.setattr(__import__("sys"), "platform", "darwin")
    assert recommended_backend(macos="X") == "X"

    monkeypatch.setattr(__import__("sys"), "platform", "linux")
    assert recommended_backend(linux="Y") == "Y"
