from __future__ import annotations

import contextlib
import sys
from typing import Any, Callable, Literal

from ._helpers import _warn_once

__all__ = [
    "hold_windows",
]


_PROMPT_DEFAULT = object()


def hold_windows(
    *,
    poll: float = 0.05,
    prompt: str | None | object = _PROMPT_DEFAULT,
    trigger: Literal["AnyKey", "Enter"] = "AnyKey",
    only_if_tty: bool = True,
) -> None:
    """Keep Matplotlib figures alive until the user continues.

    This is a terminal-run convenience: at the end of a script that created
    Matplotlib figures, prevent the Python process from exiting immediately while
    keeping the GUI responsive.

    The function returns when:
    - the user presses the configured key trigger, or
    - all figures are closed (no fignums remain).

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

    if only_if_tty:
        try:
            if not sys.stdin.isatty():
                return
        except Exception:
            return

    try:
        if not plt.get_fignums():
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
        """Return (context_manager, checker, supported) for 'any key' detection."""

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
        if not supported:
            threading.Thread(target=_wait_for_enter, daemon=True).start()
            key_ctx = contextlib.nullcontext()
            key_pressed = lambda: False

    with key_ctx:
        while not entered.is_set():
            try:
                if not plt.get_fignums():
                    return
            except Exception:
                return

            if trigger == "AnyKey" and key_pressed():
                entered.set()
                return

            # Keep processing GUI events without repeatedly calling plt.show().
            try:
                fignums = plt.get_fignums()
                fig = plt.figure(fignums[0]) if fignums else None
                start_loop = getattr(
                    getattr(fig, "canvas", None), "start_event_loop", None
                )
                if callable(start_loop):
                    start_loop(poll)
                else:
                    plt.pause(poll)
            except Exception:
                plt.pause(poll)
