# 가계부 프로그램 main entry
from pathlib import Path

from .services import CategoryService
from .storage import CategoryStore

import argparse


def main() -> int:
    data_dir = Path("data/")
    parser = argparse.ArgumentParser() # 인자를 받을 수 있게 관련 기능 활성화
    subparsers = parser.add_subparsers(dest="command", required=True) # 인자를 받을 수 있게 준비

    category_parser = subparsers.add_parser("category")
    category_subparsers = category_parser.add_subparsers(
        dest="category_command",
        required=True,
    )

    category_subparsers.add_parser("add")
    category_subparsers.add_parser("list")
    args = parser.parse_args()

    if args.command == "category":
        service = CategoryService(CategoryStore(data_dir))
        try:
            if args.category_command == "add":
                name = input("카테고리 이름을 입력해주세요: ")
                service.add_category(name)
                print(f"[저장 완료] category={name.strip()}")
            elif args.category_command == "list":
                for name in service.iter_categories():
                    print(f"- {name}")
        except ValueError as error:
            print(f"[오류] {error}")
            print("[힌트] 비어 있지 않은 새 카테고리 이름을 입력하세요.")
            return 1

    return 0