from __future__ import annotations


def main() -> None:
    """Demo for mpl_nonblock.hold_windows().

    Run this from a terminal. Close the figure window(s) or press a key to exit.
    """

    import matplotlib.pyplot as plt

    from mpl_nonblock import hold_windows

    fig, ax = plt.subplots(num="hold_windows demo", clear=True)
    ax.plot([0, 1], [0, 1])
    ax.set_title("Close the window or press any key in the terminal")
    fig.show()

    # Nonblocking show; keep script alive via hold_windows().
    plt.show(block=False)
    hold_windows()


if __name__ == "__main__":
    main()
