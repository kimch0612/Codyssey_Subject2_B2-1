"""Command-line argument handling."""

from __future__ import annotations

import argparse

from . import budget_service


def add_help_option(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--help",
        action="help",
        help="show this help message and exit",
    )
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = add_help_option(argparse.ArgumentParser(
        prog="python -m budget_app",
        description="File-based household budget console program.",
        add_help=False,
    ))
    subparsers = parser.add_subparsers(dest="command")

    ################# 카테고리 #################

    category_parser = add_help_option(
        subparsers.add_parser("category", add_help=False)
    )
    category_subparsers = category_parser.add_subparsers(dest="category_command")
    category_list_parser = add_help_option(
        category_subparsers.add_parser("list", add_help=False)
    )
    category_list_parser.set_defaults(handler=budget_service.run_category_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0

    return handler(args)
