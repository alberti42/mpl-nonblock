from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "backend",
    [
        # Official interactive GUI backends.
        "GTK3Agg",
        "GTK3Cairo",
        "GTK4Agg",
        "GTK4Cairo",
        "MacOSX",
        "QtAgg",
        "QtCairo",
        "Qt5Agg",
        "Qt5Cairo",
        "TkAgg",
        "TkCairo",
        "WX",
        "WXAgg",
        "WXCairo",
    ],
)
def test_is_gui_backend_true(backend: str) -> None:
    from mpl_nonblock.backends import _is_gui_backend

    assert _is_gui_backend(backend) is True


@pytest.mark.parametrize(
    "backend",
    [
        "Agg",
        "cairo",
        "pdf",
        "pgf",
        "ps",
        "inline",
        "module://matplotlib_inline.backend_inline",
        "nbAgg",
        "notebook",
        "WebAgg",
        "svg",
    ],
)
def test_is_gui_backend_false(backend: str) -> None:
    from mpl_nonblock.backends import _is_gui_backend

    assert _is_gui_backend(backend) is False
