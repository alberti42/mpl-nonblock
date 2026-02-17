from __future__ import annotations

import os
import sys
import types
from typing import Any


def _force_agg_backend() -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib

    matplotlib.use("Agg", force=True)


def test_hold_windows_returns_immediately_on_non_gui_backend(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt

    from mpl_nonblock import core

    monkeypatch.setattr(core, "_backend_str", lambda: "Agg")
    called: list[float] = []
    monkeypatch.setattr(plt, "pause", lambda dt: called.append(dt))

    core.hold_windows(poll=0.0)
    assert called == []


def test_hold_windows_exits_on_enter(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt

    from mpl_nonblock import core

    # Pretend we are on a GUI backend.
    monkeypatch.setattr(core, "_backend_str", lambda: "TkAgg")
    monkeypatch.setattr(core, "_is_gui_backend", lambda backend: True)

    # One fake figure exists.
    monkeypatch.setattr(plt, "get_fignums", lambda: [1])

    class DummyCanvas:
        def start_event_loop(self, dt: float) -> None:
            return

    class DummyFig:
        canvas = DummyCanvas()

    monkeypatch.setattr(plt, "figure", lambda n: DummyFig())

    # Make stdin look like a TTY and return immediately.
    monkeypatch.setattr(core.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(core.sys.stdin, "readline", lambda: "\n")

    core.hold_windows(poll=0.0, prompt=None, trigger="Enter")


def test_hold_windows_only_if_tty(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt

    from mpl_nonblock import core

    monkeypatch.setattr(core, "_backend_str", lambda: "TkAgg")
    monkeypatch.setattr(core, "_is_gui_backend", lambda backend: True)
    monkeypatch.setattr(core.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(plt, "get_fignums", lambda: [1])

    # Should return immediately without waiting.
    core.hold_windows(poll=0.0)


def test_hold_windows_exits_on_any_key_windows_path(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt

    from mpl_nonblock import core

    # Pretend we are on a GUI backend.
    monkeypatch.setattr(core, "_backend_str", lambda: "TkAgg")
    monkeypatch.setattr(core, "_is_gui_backend", lambda backend: True)

    # Use the Windows (msvcrt) code path even on non-Windows test runners.
    monkeypatch.setattr(core.sys, "platform", "win32")

    # One fake figure exists.
    monkeypatch.setattr(plt, "get_fignums", lambda: [1])

    # Make stdin look like a TTY.
    monkeypatch.setattr(core.sys.stdin, "isatty", lambda: True)

    # Provide a fake msvcrt module.
    msvcrt = types.ModuleType("msvcrt")
    msvcrt.kbhit = lambda: True  # type: ignore[attr-defined]
    msvcrt.getwch = lambda: "a"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "msvcrt", msvcrt)

    # Should return immediately without pumping GUI events.
    called: list[float] = []
    monkeypatch.setattr(plt, "pause", lambda dt: called.append(dt))

    core.hold_windows(poll=0.0, trigger="AnyKey", prompt=None)
    assert called == []
