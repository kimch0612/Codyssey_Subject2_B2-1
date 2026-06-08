"""Command-line argument handling."""

from __future__ import annotations

import argparse
import sys

from . import budget_service


class BudgetArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"[오류] {message}", file=sys.stderr)
        print("[힌트] --help 옵션으로 사용 방법을 확인해주세요.", file=sys.stderr)
        raise SystemExit(2)


def add_help_option(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--help",
        action="help",
        help="show this help message and exit",
    )
    return parser


def add_data_dir_option(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--data-dir",
        default="data",
        help="data storage directory",
    )
    return parser


def add_command_parser(subparsers, name: str) -> argparse.ArgumentParser:
    return add_data_dir_option(
        add_help_option(subparsers.add_parser(name, add_help=False))
    )


def build_parser() -> argparse.ArgumentParser:
    parser = add_help_option(BudgetArgumentParser(
        prog="python -m budget_app",
        description="File-based household budget console program.",
        add_help=False,
    ))
    subparsers = parser.add_subparsers(
        dest="command",
        parser_class=BudgetArgumentParser,
    )

    ################# 카테고리 #################

    category_parser = add_help_option(
        subparsers.add_parser("category", add_help=False)
    )
    category_subparsers = category_parser.add_subparsers(
        dest="category_command",
        parser_class=BudgetArgumentParser,
    )

    category_add_parser = add_command_parser(category_subparsers, "add")
    category_add_parser.set_defaults(handler=budget_service.run_category_add)

    category_list_parser = add_command_parser(category_subparsers, "list")
    category_list_parser.set_defaults(handler=budget_service.run_category_list)

    category_remove_parser = add_command_parser(category_subparsers, "remove")
    category_remove_parser.set_defaults(handler=budget_service.run_category_remove)

    ################# 거래 #################

    add_parser = add_command_parser(subparsers, "add")
    add_parser.set_defaults(handler=budget_service.run_transaction_add)

    list_parser = add_command_parser(subparsers, "list")
    list_parser.add_argument("--limit", type=int, default=10)
    list_parser.set_defaults(handler=budget_service.run_transaction_list)

    search_parser = add_command_parser(subparsers, "search")
    search_parser.add_argument("--from", dest="date_from")
    search_parser.add_argument("--to", dest="date_to")
    search_parser.add_argument("--category")
    search_parser.add_argument("--type", dest="transaction_type")
    search_parser.add_argument("--q", dest="query")
    search_parser.add_argument("--tag")
    search_parser.set_defaults(handler=budget_service.run_transaction_search)

    update_parser = add_command_parser(subparsers, "update")
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--date")
    update_parser.add_argument("--type", dest="transaction_type")
    update_parser.add_argument("--category")
    update_parser.add_argument("--amount")
    update_parser.add_argument("--memo")
    update_parser.add_argument("--tags")
    update_parser.set_defaults(handler=budget_service.run_transaction_update)

    delete_parser = add_command_parser(subparsers, "delete")
    delete_parser.add_argument("--id", required=True)
    delete_parser.set_defaults(handler=budget_service.run_transaction_delete)

    ################# 요약/예산 #################

    summary_parser = add_command_parser(subparsers, "summary")
    summary_parser.add_argument("--month", required=True)
    summary_parser.add_argument("--top", type=int, default=3)
    summary_parser.set_defaults(handler=budget_service.run_summary)

    budget_parser = add_help_option(subparsers.add_parser("budget", add_help=False))
    budget_subparsers = budget_parser.add_subparsers(
        dest="budget_command",
        parser_class=BudgetArgumentParser,
    )

    budget_set_parser = add_command_parser(budget_subparsers, "set")
    budget_set_parser.add_argument("--month", required=True)
    budget_set_parser.add_argument("--amount", required=True)
    budget_set_parser.set_defaults(handler=budget_service.run_budget_set)

    ################# 가져오기/내보내기 #################

    import_parser = add_command_parser(subparsers, "import")
    import_parser.add_argument("--from", dest="import_from", required=True)
    import_parser.set_defaults(handler=budget_service.run_import)

    export_parser = add_command_parser(subparsers, "export")
    export_parser.add_argument("--out", required=True)
    export_parser.add_argument("--month")
    export_parser.add_argument("--from", dest="date_from")
    export_parser.add_argument("--to", dest="date_to")
    export_parser.set_defaults(handler=budget_service.run_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0

    return handler(args)
