import argparse
import csv
import os
import sys

from .core import load_spans, to_html, to_markdown


def build_parser():
    ap = argparse.ArgumentParser(prog="agent-replay")
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("md")
    m.add_argument("trace")
    h = sub.add_parser("html")
    h.add_argument("trace")
    h.add_argument("-o", "--out", default="replay.html")
    return ap


def _run(argv=None):
    ap = build_parser()
    a = ap.parse_args(argv)
    spans = load_spans(a.trace)
    if a.cmd == "md":
        sys.stdout.write(to_markdown(spans))
    else:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(to_html(spans))
        print(f"wrote {a.out}")
    return 0


def main(argv=None):
    """Run the CLI; a bad input file or argument exits 2 with a one-line error instead of a traceback.

    Set AGENT_ECONOMY_DEBUG=1 to see the full traceback.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    try:
        return _run(argv)
    except (OSError, ValueError, KeyError, csv.Error) as e:
        if os.environ.get("AGENT_ECONOMY_DEBUG"):
            raise
        msg = e.args[0] if isinstance(e, KeyError) and e.args else e
        print(f"error: {msg}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
