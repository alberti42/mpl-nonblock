from __future__ import annotations

import contextlib
import sys
from typing import Any, Callable

from ._helpers import _warn_once

__all__ = [
    "_make_anykey_checker",
    "_make_enterkey_checker",
]


def _make_enterkey_checker() -> tuple[
    contextlib.AbstractContextManager[None], Callable[[], bool], bool
]:
    """Return (context_manager, checker, supported) for Enter detection.

    Implementation uses a background thread blocked on sys.stdin.readline().
    """

    import threading

    entered = threading.Event()

    def _wait_for_enter() -> None:
        try:
            sys.stdin.readline()
        except Exception:
            return
        entered.set()

    try:
        threading.Thread(target=_wait_for_enter, daemon=True).start()
    except Exception as e:
        _warn_once(
            "hold_windows:enter_thread",
            "mpl_nonblock.hold_windows: Enter trigger unavailable; ignoring keypress",
            e,
        )
        return contextlib.nullcontext(), lambda: False, False

    return contextlib.nullcontext(), entered.is_set, True


def _make_anykey_checker() -> tuple[
    contextlib.AbstractContextManager[None], Callable[[], bool], bool
]:
    """Return (context_manager, checker, supported) for 'any key' detection.

    The returned context manager exists to restore terminal settings on POSIX.
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
