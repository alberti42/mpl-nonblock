---
name: mpl-nonblock
description: Integrate mpl-nonblock for tagged Matplotlib windows and nonblocking figure refresh in interactive Python sessions.
license: MIT
metadata:
  author: Andrea Alberti (2026)
  package_repo: https://github.com/alberti42/mpl-nonblock
---

# Skill: mpl-nonblock

Use this skill when integrating `mpl-nonblock` into Python code that uses
Matplotlib interactively (IPython, Jupyter, REPL scripts). It provides tagged
window reuse and nonblocking figure refresh.

## Agent defaults (important)

- **Assume mpl-nonblock is required** for plotting in the target codebase.
- **Do not implement matplotlib fallbacks** unless the user explicitly requests
  an optional dependency mode.
- **Avoid duplicated plotting code**. The plotting logic must be written once.
  If a fallback is needed (only if the user asks), implement a small compatibility
  layer that provides the same function names (`subplots`, `show`) so the same
  plot code runs unchanged.
- **Ask about holding windows open** at program end for non-interactive runs
  (otherwise figures may close immediately when the process exits).

Suggested question to ask the user (only when relevant):

- "When the script is run non-interactively (e.g. `python script.py`), should it
  wait once at the end (press Enter) to keep plot windows open?"

## Install

Only install if the user explicitly asks for it; the package may already be available in the environment. Ask the user whether a specific release should be pinned (recommended for reproducibility and to avoid future incompatibilities). If unsure, prefer pinning the latest known-good release.

# Pinned release (recommended)

```bash
pip install "mpl-nonblock @ git+https://github.com/alberti42/mpl-nonblock.git@v1.0.0"
# or
uv pip install "mpl-nonblock @ git+https://github.com/alberti42/mpl-nonblock.git@v1.0.0"
```

# Unpinned (installs current default-branch HEAD; not recommended for reproducibility)

```bash
pip install "mpl-nonblock @ git+https://github.com/alberti42/mpl-nonblock.git"
```

## Critical Rule

`ensure_backend()` **must** be called before `import matplotlib.pyplot`.
If `pyplot` is already imported, backend switching is impossible.

Practical implication: call `ensure_backend()` at the top of your plotting code,
before importing `matplotlib.pyplot` anywhere.

## API Reference

### `ensure_backend(preferred=None, *, fallbacks=None, honor_user=True)`

Best-effort GUI backend selection. Call once, early.

- **Default policy** (when `preferred` is `None`):
  - macOS: tries `macosx`, falls back to `TkAgg`
  - Linux: tries `QtAgg`, falls back to `TkAgg`
- **`honor_user=True`** (default): does not override `MPLBACKEND` env var or an
  already-active GUI backend.
- Returns a `BackendStatus` dataclass (`backend`, `selected`, `can_switch`,
  `tried`, `reason`).

### `subplots(tag, *, clear=True, nrows=1, ncols=1, **kwargs)`

Create or reuse a figure keyed by the string `tag` (maps to Matplotlib `num=`).
Reusing the same tag keeps the OS window in the same position across reruns.

- `clear=True`: clears the figure before returning (default).
- Extra `**kwargs` are forwarded to `plt.subplots` (e.g. `figsize`, `constrained_layout`).
- Returns `(fig, ax)` just like `plt.subplots`.

### `show(fig, *, nonblocking=True, raise_window=False, pause=0.001)`

Display/refresh a figure.

- `nonblocking=True` (default): uses `ion` + `show(block=False)` + `pause`
  recipe. Keeps the prompt responsive.
- `raise_window=True`: attempts to bring the window to front (backend-dependent).
- On non-GUI backends (Agg, inline): safely does nothing (no warnings).
- Returns a `ShowStatus` dataclass (`backend`, `nonblocking_requested`,
  `nonblocking_used`, `reason`).

### `is_interactive()`

Returns `True` when running inside IPython/Jupyter or a REPL-ish session.
Checks IPython, `sys.ps1`, and `sys.flags.interactive`.

### `diagnostics()`

Returns a dict with backend info, IPython state, and environment variables
(`DISPLAY`, `WAYLAND_DISPLAY`). Useful for debugging "nothing shows up" problems.

## Patterns

### Clean integration (no duplication)

Write plotting code once using `mpl_nonblock.subplots(...)` and
`mpl_nonblock.show(...)`. Do not branch the actual plotting logic.

If and only if the user explicitly requests a fallback mode, prefer a small
alias layer that keeps function names consistent, instead of duplicating plots:

```python
try:
    from mpl_nonblock import ensure_backend, subplots, show
    ensure_backend()  # before any pyplot import
except ImportError:
    import matplotlib.pyplot as plt

    def subplots(tag, *, clear=True, **kwargs):
        return plt.subplots(num=tag, clear=clear, **kwargs)

    def show(_fig, *, nonblocking=True, **kwargs):
        plt.show()
```

### Minimal nonblocking plot

```python
from mpl_nonblock import ensure_backend, subplots, show

ensure_backend()  # before any pyplot import

fig, ax = subplots("My Plot", figsize=(8, 4))
ax.plot([1, 2, 3], [1, 4, 9])
show(fig)
```

### Multiple tagged windows (stable positions)

```python
from mpl_nonblock import ensure_backend, subplots, show

ensure_backend()

fig1, ax1 = subplots("Signal", clear=True, figsize=(10, 4))
ax1.plot(t, signal)
show(fig1)

fig2, ax2 = subplots("Spectrum", clear=True, figsize=(10, 4))
ax2.plot(freq, magnitude)
show(fig2)
```

Each call to `subplots("Signal", ...)` reuses the same OS window, so it stays
where the user positioned it.

### Update loop (live refresh)

```python
from mpl_nonblock import ensure_backend, subplots, show

ensure_backend()

for i in range(100):
    fig, ax = subplots("Live", clear=True)
    ax.plot(data[: i + 1])
    ax.set_title(f"Step {i}")
    show(fig)
```

### Script that works both interactively and standalone

```python
from mpl_nonblock import ensure_backend, is_interactive, subplots, show

ensure_backend()

fig, ax = subplots("Result", clear=True)
ax.plot(x, y)

if is_interactive():
    show(fig, nonblocking=True)
else:
    # Non-interactive script runs: nonblocking windows would close when the
    # process exits. Hold once at the end.
    show(fig, nonblocking=True)
    input("Press Enter to close plots and exit...")
```

### Specifying a preferred backend

```python
from mpl_nonblock import ensure_backend

status = ensure_backend(preferred="QtAgg", fallbacks=["TkAgg"])
if not status.selected:
    print(f"Could not switch backend: {status.reason}")
```

### Subplots with multiple axes

```python
from mpl_nonblock import ensure_backend, subplots, show

ensure_backend()

fig, axes = subplots("Grid", nrows=2, ncols=2, figsize=(10, 8),
                     constrained_layout=True)
for ax, data in zip(axes.flat, datasets):
    ax.plot(data)
show(fig)
```

## Troubleshooting

If nothing shows up, run:

```python
from mpl_nonblock import diagnostics
print(diagnostics())
```

Or from the command line:

```bash
mpl-nonblock-diagnose
```

Common fixes:
- **IPython on macOS**: run `%matplotlib macosx` before your script.
- **IPython on Linux**: run `%matplotlib qt` (or `%matplotlib tk`).
- **Headless / Agg backend**: no window can open; use `fig.savefig(...)` instead.
- **macOS + `simple_prompt`**: start IPython with
  `ipython --TerminalInteractiveShell.simple_prompt=False`.
