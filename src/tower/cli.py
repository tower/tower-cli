import signal
import sys

from ._native import _run_cli


def main():
    # When invoked via Python, SIGINT defaults to raising KeyboardInterrupt
    # in the interpreter instead of terminating the process immediately.
    # Restore default SIGINT behavior so Ctrl+C reliably cancels interactive
    # CLI flows (matching behavior of the standalone Rust binary).
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    _run_cli(sys.argv)
