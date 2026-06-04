"""Command-line argument handling."""

from __future__ import annotations

import argparse

from . import budget_service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m budget_app",
        description="File-based household budget console program.",
    )
    subparsers = parser.add_subparsers(dest="command")

    for command_name in (
        "add",
        "list",
        "search",
        "summary",
        "update",
        "delete",
        "import",
        "export",
    ):
        command_parser = subparsers.add_parser(command_name)
        command_parser.set_defaults(handler=budget_service.run_placeholder)

    budget_parser = subparsers.add_parser("budget")
    budget_subparsers = budget_parser.add_subparsers(dest="budget_command")
    budget_set_parser = budget_subparsers.add_parser("set")
    budget_set_parser.set_defaults(handler=budget_service.run_placeholder)

    category_parser = subparsers.add_parser("category")
    category_subparsers = category_parser.add_subparsers(dest="category_command")
    for category_command in ("add", "list", "remove"):
        category_command_parser = category_subparsers.add_parser(category_command)
        category_command_parser.set_defaults(handler=budget_service.run_placeholder)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0

    return handler(args)

