from __future__ import annotations

import json

from .core import diagnostics


def main() -> None:
    """CLI entry point: print JSON diagnostics for bug reports."""

    info = diagnostics()
    print("mpl-nonblock diagnostics")
    print(json.dumps(info, indent=2, sort_keys=True))

    backend = str(info.get("backend", ""))
    _ = backend
