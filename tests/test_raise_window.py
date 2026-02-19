from __future__ import annotations

from typing import Any


def test_raise_window_prefers_manager_raise_window() -> None:
    from matplotlib_window_tracker import backends

    called: list[str] = []

    class Mgr:
        def raise_window(self) -> None:
            called.append("raise_window")

    class Canvas:
        manager = Mgr()

    class Fig:
        canvas = Canvas()

    backends.raise_window(Fig())
    assert called == ["raise_window"]


def test_raise_window_is_best_effort_on_missing_manager(monkeypatch: Any) -> None:
    from matplotlib_window_tracker import backends

    class Fig:
        canvas = None

    # Should not raise.
    backends.raise_window(Fig())
