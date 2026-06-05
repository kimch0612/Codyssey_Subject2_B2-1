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

    category_add_parser = add_help_option(
        category_subparsers.add_parser("add", add_help=False)
    )
    category_add_parser.set_defaults(handler=budget_service.run_category_add)

    category_remove_parser = add_help_option(
        category_subparsers.add_parser("remove", add_help=False)
    )
    category_remove_parser.set_defaults(handler=budget_service.run_category_remove)

    ################# 거래 #################

    transaction_parser = add_help_option(
        subparsers.add_parser("transaction", add_help=False)
    )
    transaction_subparsers = transaction_parser.add_subparsers(dest="transaction_command")

    transaction_add_parser = add_help_option(
        transaction_subparsers.add_parser("add", add_help=False)
    )
    transaction_add_parser.set_defaults(handler=budget_service.run_transaction_add)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0

    return handler(args)
