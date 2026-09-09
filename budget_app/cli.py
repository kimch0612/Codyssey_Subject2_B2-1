# 가계부 프로그램 main entry
from pathlib import Path

from .services import CategoryService, TransactionService
from .storage import CategoryStore, TransactionRepository

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

    add_parser = subparsers.add_parser("add")

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
    elif args.command == "add":
        service = TransactionService( TransactionRepository(data_dir), CategoryStore(data_dir) )

        try:
            amount = int(input("금액(0보다 큰 정수): "))
        except ValueError:
            print("[오류] 입력값이 잘못 되었습니다.")
            print("[힌트] 원이나 쉼표 없이 숫자로 입력하세요. 예: 8000")
            return 1

        plane_tags = input("태그(쉼표로 구분, 생략 가능): ")
        tags = [
            tag.strip()
            for tag in plane_tags.split(",")
            if tag.strip()
        ]
        date = input("날짜(YYYY-MM-DD): ").strip()
        transaction_type = input("income/expense: ").strip()
        category = input("카테고리: ").strip()
        memo = input("메모(생략 가능): ").strip()

        try:
            transaction = service.add_transaction(
                date,
                transaction_type,
                category,
                amount,
                memo,
                tags
            )
            print(f"[저장 완료] id: {transaction.id}")
            return 0
        except ValueError as error:
            print(f"[오류] {error}")
            print(
                "[힌트] 날짜·타입·양수 금액을 확인하고, "
                "카테고리는 category list에서 등록 여부를 확인하세요."
            )
            return 1

    return 0