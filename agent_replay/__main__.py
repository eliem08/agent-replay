import argparse
import sys

from .core import load_spans, to_html, to_markdown


def main(argv=None):
    ap = argparse.ArgumentParser(prog="agent-replay")
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("md")
    m.add_argument("trace")
    h = sub.add_parser("html")
    h.add_argument("trace")
    h.add_argument("-o", "--out", default="replay.html")
    a = ap.parse_args(argv)
    spans = load_spans(a.trace)
    if a.cmd == "md":
        sys.stdout.write(to_markdown(spans))
    else:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(to_html(spans))
        print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
