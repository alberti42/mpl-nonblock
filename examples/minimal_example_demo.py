from __future__ import annotations


def main() -> None:
    """Minimal example: persist window position+size across runs (macosx backend).

    Run this script twice:
    1) Move/resize the windows.
    2) Exit (close windows or press any key in the terminal).
    3) Run again: windows should restore to the last saved geometry.

    This example keeps everything Matplotlib-native and adds a single explicit
    call per window:

        track_position_size(fig, tag="...")
    """

    import matplotlib

    matplotlib.use("macosx")
    import matplotlib.pyplot as plt

    from matplotlib_window_tracker import hold_windows, track_position_size

    fig1, ax1 = plt.subplots(num="Window A", clear=True)
    ax1.plot([0, 1], [0, 1])
    ax1.set_title("A: move/resize me")

    fig2, ax2 = plt.subplots(num="Window B", clear=True)
    ax2.plot([0, 1], [1, 0])
    ax2.set_title("B: move/resize me")

    track_position_size(fig1, tag="window_a")
    track_position_size(fig2, tag="window_b")

    plt.show(block=False)
    hold_windows()


if __name__ == "__main__":
    main()
