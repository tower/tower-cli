import sys

from ._native import _run_cli


def main():
    _run_cli(sys.argv)
