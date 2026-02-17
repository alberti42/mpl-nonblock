from __future__ import annotations

import contextlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from ._helpers import _WARNED_ONCE, _in_ipython, is_interactive, _warn_once
from .backends import _backend_str, _is_gui_backend

__all__ = [
    "ShowStatus",
    "diagnostics",
    "hold_windows",
    "is_interactive",
    "refresh",
    "show",
]


_PROMPT_DEFAULT = object()


@dataclass(frozen=True)
class ShowStatus:
    """Small, explicit status object returned by `show()` / `refresh()`.

    Why it exists:
    - Matplotlib "show" behavior is backend- and environment-dependent (GUI vs Agg,
      IPython vs script, headless vs desktop). Returning a status makes that behavior
      observable without printing/logging.

    How it is used:
    - Internally: tests assert that we do *not* attempt GUI actions on non-GUI
      backends.
    - For users: you can branch on `nonblocking_used` / inspect `reason` when a
      window does not appear or when debugging backend configuration.

    This is part of the public API to provide a stable, structured alternative to
    backend-specific warnings.
    """

    backend: str
    nonblocking_requested: bool
    nonblocking_used: bool
    reason: str


def refresh(
    fig: Any,
    *,
    pause: float = 0.001,
    in_foreground: bool = False,
) -> ShowStatus:
    """Nonblocking refresh of a specific figure.

    This is the "movie frame" primitive: update artists, then call `refresh(fig)`
    to pump the GUI event loop (via `plt.pause`). Optionally, try to bring the
    figure window to the foreground via backend-specific hooks.

    If you are updating multiple Axes in the same Figure (e.g. subplots), call this
    once for that Figure.
    """

    import matplotlib.pyplot as plt

    backend = _backend_str()
    gui = _is_gui_backend(backend)

    if not gui:
        return ShowStatus(
            backend=backend,
            nonblocking_requested=True,
            nonblocking_used=False,
            reason="non-GUI backend; nothing to show",
        )

    try:
        plt.pause(pause)
    except Exception as e:
        _warn_once(
            "refresh:plt_pause",
            "mpl_nonblock.refresh: plt.pause() failed; continuing",
            e,
        )

    if in_foreground:
        try:
            from . import backends

            backends.raise_figure(fig)
        except Exception as e:
            _warn_once(
                "refresh:in_foreground",
                "mpl_nonblock.refresh: in_foreground failed; continuing",
                e,
            )

    return ShowStatus(
        backend=backend,
        nonblocking_requested=True,
        nonblocking_used=True,
        reason="nonblocking refresh",
    )


def show(*, block: bool | None = False, pause: float = 0.001) -> ShowStatus:
    """Drop-in replacement for `matplotlib.pyplot.show()`.

    Defaults to nonblocking behavior (`block=False`) by using `plt.pause(pause)`.

    Note: we intentionally do not call `plt.show(block=False)` here. In practice it
    is not needed for nonblocking refresh, and repeatedly calling `show()` can
    cause focus-stealing behavior on some backends.

    If you are writing a script (not IPython) and you want windows to stay open at
    the end, use `show(block=True)`.

    Implementation note: `show(block=False)` pumps the GUI event loop (via
    `plt.pause`) and therefore affects all open figures. This is convenient as a
    single "GUI tick", but it can add overhead if you have many figures.
    """

    import matplotlib.pyplot as plt

    backend = _backend_str()
    gui = _is_gui_backend(backend)

    if not gui:
        return ShowStatus(
            backend=backend,
            nonblocking_requested=block is not True,
            nonblocking_used=False,
            reason="non-GUI backend; nothing to show",
        )

    if block:
        try:
            plt.show()
        except Exception as e:
            _warn_once(
                "show:plt_show",
                "mpl_nonblock.show: plt.show() failed; continuing",
                e,
            )
        return ShowStatus(
            backend=backend,
            nonblocking_requested=False,
            nonblocking_used=False,
            reason="blocking plt.show()",
        )

    try:
        plt.pause(pause)
    except Exception as e:
        _warn_once(
            "show:plt_pause",
            "mpl_nonblock.show: plt.pause() failed; continuing",
            e,
        )

    return ShowStatus(
        backend=backend,
        nonblocking_requested=True,
        nonblocking_used=True,
        reason="nonblocking show",
    )


def hold_windows(
    *,
    poll: float = 0.05,
    prompt: str | None | object = _PROMPT_DEFAULT,
    trigger: Literal["AnyKey", "Enter"] = "AnyKey",
    only_if_tty: bool = True,
) -> None:
    """Keep Matplotlib windows alive at the end of a terminal-run script.

    This is a convenience for the common pattern:

    - you used `refresh(fig)` / `show(block=False)` during the script
    - when the script ends, the Python process would exit and windows would close

    `hold_windows()` waits until the user presses Enter / any key (configurable)
    or all windows are closed, while keeping the GUI responsive.

    Parameters:
    - poll: seconds to wait between GUI event processing steps.
    - prompt: message printed before waiting.
      - If omitted, a default prompt is printed based on `trigger`.
      - If None, nothing is printed.
    - trigger: "AnyKey" (default) or "Enter".
    - only_if_tty: if True (default), do nothing when stdin is not a TTY.
      This avoids blocking in non-interactive environments (CI, piped input).
    """

    import threading

    import matplotlib.pyplot as plt

    backend = _backend_str()
    if not _is_gui_backend(backend):
        return

    if only_if_tty:
        try:
            if not sys.stdin.isatty():
                return
        except Exception:
            return

    if trigger not in ("Enter", "AnyKey"):
        raise ValueError(f"Unknown trigger: {trigger!r}. Expected 'Enter' or 'AnyKey'.")

    if prompt is _PROMPT_DEFAULT:
        prompt = (
            "Press any key to exit..."
            if trigger == "AnyKey"
            else "Press Enter to exit..."
        )
    if prompt is not None:
        print(str(prompt), flush=True)

    entered = threading.Event()

    def _wait_for_enter() -> None:
        try:
            sys.stdin.readline()
        except Exception:
            return
        entered.set()

    def _make_anykey_checker() -> tuple[
        contextlib.AbstractContextManager[None], Callable[[], bool], bool
    ]:
        """Return (context_manager, checker) for 'any key' detection.

        The context manager exists to restore terminal settings on POSIX.
        """

        # Windows (msvcrt) path.
        if sys.platform.startswith("win"):
            try:
                import msvcrt  # type: ignore
            except Exception as e:
                _warn_once(
                    "hold_windows:anykey_import",
                    "mpl_nonblock.hold_windows: AnyKey trigger unavailable; falling back to Enter",
                    e,
                )
                return contextlib.nullcontext(), lambda: False, False

            def _pressed() -> bool:
                try:
                    kbhit = getattr(msvcrt, "kbhit", None)
                    getwch = getattr(msvcrt, "getwch", None)
                    if callable(kbhit) and callable(getwch) and kbhit():
                        getwch()
                        return True
                except Exception:
                    return False
                return False

            return contextlib.nullcontext(), _pressed, True

        # POSIX path.
        try:
            import select
            import termios
            import tty
        except Exception as e:
            _warn_once(
                "hold_windows:anykey_import",
                "mpl_nonblock.hold_windows: AnyKey trigger unavailable; falling back to Enter",
                e,
            )
            return contextlib.nullcontext(), lambda: False, False

        try:
            fd = sys.stdin.fileno()
        except Exception as e:
            _warn_once(
                "hold_windows:anykey_fileno",
                "mpl_nonblock.hold_windows: AnyKey trigger unavailable; falling back to Enter",
                e,
            )
            return contextlib.nullcontext(), lambda: False, False

        @contextlib.contextmanager
        def _cbreak() -> Any:
            try:
                old = termios.tcgetattr(fd)
            except Exception:
                old = None

            try:
                tty.setcbreak(fd)
                yield
            finally:
                if old is not None:
                    try:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old)
                    except Exception:
                        pass

        def _pressed() -> bool:
            try:
                r, _, _ = select.select([sys.stdin], [], [], 0)
                if r:
                    sys.stdin.read(1)
                    return True
            except Exception:
                return False
            return False

        return _cbreak(), _pressed, True

    if trigger == "Enter":
        threading.Thread(target=_wait_for_enter, daemon=True).start()
        key_ctx: contextlib.AbstractContextManager[None] = contextlib.nullcontext()
        key_pressed = lambda: False
    else:
        key_ctx, key_pressed, supported = _make_anykey_checker()

        # If AnyKey is not available, fall back to Enter semantics.
        if not supported:
            threading.Thread(target=_wait_for_enter, daemon=True).start()
            key_ctx = contextlib.nullcontext()
            key_pressed = lambda: False

    def _any_figures_open() -> bool:
        try:
            return bool(plt.get_fignums())
        except Exception:
            return False

    with key_ctx:
        while not entered.is_set() and _any_figures_open():
            if trigger == "AnyKey" and key_pressed():
                entered.set()
                break

            # Keep processing GUI events without repeatedly calling plt.show().
            try:
                fignums = plt.get_fignums()
                fig = None
                if fignums:
                    fig = plt.figure(fignums[0])
                start_loop = (
                    getattr(getattr(fig, "canvas", None), "start_event_loop", None)
                    if fig is not None
                    else None
                )
                if callable(start_loop):
                    start_loop(poll)
                else:
                    plt.pause(poll)
            except Exception:
                plt.pause(poll)


def diagnostics() -> dict[str, Any]:
    """Return a small diagnostics dictionary for troubleshooting.

    Intended for CLI reporting (`mpl-nonblock-diagnose`) and bug reports.
    """

    out: dict[str, Any] = {}
    out["sys.executable"] = sys.executable
    out["sys.platform"] = sys.platform
    out["cwd"] = str(Path.cwd())
    out["interactive"] = is_interactive()
    out["ipython"] = _in_ipython()
    out["backend"] = _backend_str()
    out["mplbackend_env"] = bool(os.environ.get("MPLBACKEND"))
    out["display_env"] = os.environ.get("DISPLAY")
    out["wayland_env"] = os.environ.get("WAYLAND_DISPLAY")
    return out
