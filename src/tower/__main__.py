import io
import sys

_CLEAN_GLOBALS = globals().copy()


def run_program(filename):
    ns = dict(
        _CLEAN_GLOBALS,
        # Make sure the __file__ variable is usable
        # by the script we're profiling
        __file__=filename,
    )

    with io.open(filename, encoding="utf-8") as f:
        exec(compile(f.read(), filename, "exec"), ns, ns)


def parse_args():
    from argparse import REMAINDER, ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "program",
        nargs=REMAINDER,
        help="python script or module followed by command line arguments to run",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if len(args.program) == 0:
        print("A program to run must be provided. Use -h for help")
        sys.exit(1)

    run_program(args.program[0])
