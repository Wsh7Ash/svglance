"""Command line interface for svglance."""

from __future__ import annotations

import argparse
import json
import sys

from . import PlanError, build_chart, demo_plan, load_plan, render_svg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="svglance",
        description="Render a self-contained SVG timeline from a JSON plan.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render", help="render a plan file to SVG")
    render.add_argument("path")
    render.add_argument("--out", help="write SVG here instead of stdout")
    render.add_argument("--width", type=int, default=960)

    demo = sub.add_parser("demo", help="render the built-in release plan")
    demo.add_argument("--out", help="write SVG here instead of stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "demo":
            plan = demo_plan()
        else:
            plan = load_plan(args.path)
        chart = build_chart(plan, getattr(args, "width", 960))
        svg = render_svg(chart)
    except (OSError, json.JSONDecodeError, PlanError) as exc:
        print(f"svglance: {exc}", file=sys.stderr)
        return 2

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(svg)
        for warning in chart.warnings:
            print(f"warning: {warning}", file=sys.stderr)
        print(f"wrote {args.out} ({len(chart.bars)} bars, {len(chart.lanes)} lanes)")
    else:
        sys.stdout.write(svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
