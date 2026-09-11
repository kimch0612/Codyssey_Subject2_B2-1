# 가계부 프로그램 main entry
from os import path
from pathlib import Path

from .services import CategoryService, TransactionService, BudgetService, SummaryService, ExportService, ImportService
from .storage import CategoryStore, TransactionRepository, BudgetStore, CsvTransactionStore

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    parser.add_argument("--data-dir", "-data-dir", type=Path,
        default=Path("data"), help="데이터 저장 폴더 (기본값: ./data)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    category_parser = subparsers.add_parser("category")
    category_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    category_subparsers = category_parser.add_subparsers(
        dest="category_command",
        required=True,
    )
    category_add_parser = category_subparsers.add_parser("add")
    category_add_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    category_list_parser = category_subparsers.add_parser("list")
    category_list_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    category_remove_parser = category_subparsers.add_parser("remove")
    category_remove_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    list_parser.add_argument("--limit", "-limit", type=int, default=10)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    search_parser.add_argument("--from", "-from", dest="date_from")
    search_parser.add_argument("--to", "-to", dest="date_to")
    search_parser.add_argument("--category", "-category")
    search_parser.add_argument("--type", "-type", dest="transaction_type")
    search_parser.add_argument("--q", "-q", dest="query")
    search_parser.add_argument("--tag", "-tag")

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    delete_parser.add_argument("--id", "-id", required=True)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    update_parser.add_argument("--id", "-id", required=True)
    update_parser.add_argument("--date", "-date")
    update_parser.add_argument("--type", "-type", dest="transaction_type")
    update_parser.add_argument("--category", "-category")
    update_parser.add_argument("--amount", "-amount", type=int)
    update_parser.add_argument("--memo", "-memo")
    update_parser.add_argument("--tags", "-tags")

    budget_parser = subparsers.add_parser("budget")
    budget_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    budget_subparsers = budget_parser.add_subparsers(
        dest="budget_command",
        required=True,
    )
    budget_set_parser = budget_subparsers.add_parser("set")
    budget_set_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    budget_set_parser.add_argument("--month", "-month", required=True)
    budget_set_parser.add_argument("--amount", "-amount", type=int, required=True)

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    summary_parser.add_argument("--month", "-month", required=True)
    summary_parser.add_argument("--top", "-top", type=int, default=3)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    export_parser.add_argument("--out", "-out", type=Path, required=True)
    export_parser.add_argument("--month", "-month")
    export_parser.add_argument("--from", "-from", dest="date_from")
    export_parser.add_argument("--to", "-to", dest="date_to")

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("-help", action="help", help="도움말을 출력하고 종료")
    import_parser.add_argument(
        "--from", "-from",
        dest="input_path",
        type=Path,
        required=True,
    )

    args = parser.parse_args()
    data_dir = args.data_dir

    if args.command == "category":
        service = CategoryService( CategoryStore(data_dir), TransactionRepository(data_dir) )
        try:
            if args.category_command == "add":
                name = input("카테고리 이름을 입력해주세요: ")
                service.add_category(name)
                print(f"[저장 완료] category={name.strip()}")
            elif args.category_command == "list":
                count = 0
                for name in service.iter_categories():
                    print(f"- {name}")
                    count += 1
                if count == 0:
                    print("[안내] 등록된 카테고리가 없습니다.")
                    print("[힌트] category add로 카테고리를 먼저 등록하세요.")
            elif args.category_command == "remove":
                name = input("카테고리 이름을 입력해주세요: ")
                service.remove_category(name)
                print(f"[삭제 완료] category={name.strip()}")
        except ValueError as error:
            print(f"[오류] {error}")
            if args.category_command == "remove":
                print(
                    "[힌트] category list로 이름을 확인하고, "
                    "사용 중이면 해당 거래를 먼저 수정하거나 삭제하세요."
                )
            else:
                print("[힌트] 비어 있지 않은 새 카테고리 이름을 입력하세요.")
            return 1

    elif args.command == "add":
        category_store = CategoryStore(data_dir)
        service = TransactionService( TransactionRepository(data_dir), category_store )

        if next(category_store.iter_categories(), None) is None:
            print("[오류] 등록된 카테고리가 없어 거래를 추가할 수 없습니다.")
            print("[힌트] category add로 카테고리를 먼저 등록하세요.")
            return 1

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
                "카테고리는 category list로 확인하고, 새 이름은 category add로 등록하세요."
            )
            return 1

    elif args.command == "list":
        service = TransactionService( TransactionRepository(data_dir), CategoryStore(data_dir) )
        try:
            transactions = service.list_transaction(args.limit)
        except ValueError as error:
            print(f"[오류] {error}")
            print("[힌트] 조회 개수는 1 이상의 정수여야 합니다.")
            return 1

        if not transactions:
            print("거래 내역이 없습니다.")
            return 0

        for transaction in transactions:
            print(transaction)

        return 0

    elif args.command == "search":
        count = 0
        service = TransactionService( TransactionRepository(data_dir), CategoryStore(data_dir) )

        try:
            transactions = service.search_transactions(
                args.date_from,
                args.date_to,
                args.category,
                args.transaction_type,
                args.query,
                args.tag
            )
            for transaction in transactions:
                print(transaction)
                count += 1
        except ValueError as error:
            print(f"[오류] {error}")
            print("[힌트] 날짜 형식, 타입, 카테고리 이름을 확인하세요.")
            return 1
        
        if count == 0:
            print("검색 결과가 없습니다.")
        
        return 0

    elif args.command == "delete":
        service = TransactionService( TransactionRepository(data_dir), CategoryStore(data_dir) )

        try:
            service.delete_transaction(args.id)
            print(f"[삭제 완료] id: {args.id}")
            return 0
        except ValueError as error:
            print(f"[오류] {error}")
            print("[힌트] 삭제하려는 거래 ID를 확인하세요.")
            return 1

    elif args.command == "update":
        if all(value is None for value in (args.date, args.transaction_type, args.category, args.amount, args.memo, args.tags)):
            print("[오류] 수정할 항목이 없습니다.")
            print("[힌트] --date, --type, --category, --amount, --memo, --tags 중 하나 이상을 지정하세요.")
            return 1

        service = TransactionService( TransactionRepository(data_dir), CategoryStore(data_dir) )
        tags = None
        if args.tags is not None:
            tags = [
                tag.strip()
                for tag in args.tags.split(",")
                if tag.strip()
            ]

        try:
            transaction = service.update_transaction(
                args.id,
                args.date,
                args.transaction_type,
                args.category,
                args.amount,
                args.memo,
                tags
            )
            print(f"[수정 완료] id: {transaction.id}")
            return 0
        except ValueError as error:
            print(f"[오류] {error}")
            print(
                "[힌트] 거래 ID와 날짜 형식, 타입, 등록된 카테고리, "
                "1 이상의 정수 금액을 확인하세요."
            )
            return 1

    elif args.command == "budget":
        service = BudgetService(BudgetStore(data_dir))
        try:
            if args.budget_command == "set":
                service.set_budget(args.month, args.amount)
                print(f"[저장 완료] {args.month} 예산 {args.amount}원")
        except ValueError as error:
            print(f"[오류] {error}")
            print("[힌트] 월은 YYYY-MM 형식, 예산은 0 이상의 정수로 입력하세요.")
            return 1

    elif args.command == "summary":
        service = SummaryService(
            TransactionRepository(data_dir),
            BudgetStore(data_dir),
        )
        try:
            summary = service.summarize_month(args.month)
            top_categories = service.top_categories(
                summary.category_expenses,
                args.top,
            )
        except ValueError as error:
            print(f"[오류] {error}")
            print("[힌트] 월은 YYYY-MM 형식, 조회 개수는 1 이상의 정수로 입력하세요.")
            return 1

        if summary.transaction_count == 0:
            print(f"[안내] {summary.month} 데이터 없음")

        print(f"총 수입: {summary.total_income}원")
        print(f"총 지출: {summary.total_expense}원")
        print(f"잔액: {summary.balance}원")

        if summary.budget_amount is not None:
            if summary.budget_usage_rate is None:
                print(f"예산: {summary.budget_amount}원 (사용률 계산 불가: 예산 0원)")
            else:
                print(
                    f"예산: {summary.budget_amount}원 "
                    f"(사용률 {summary.budget_usage_rate:.1f}%)"
                )

            if summary.budget_exceeded_amount is not None and summary.budget_exceeded_amount > 0:
                print(f"[경고] 예산을 {summary.budget_exceeded_amount}원 초과했습니다.")

        print(f"\n지출 TOP {args.top}")
        if not top_categories:
            print("지출 내역이 없습니다.")
        for rank, (category, amount) in enumerate(top_categories, start=1):
            print(f"{rank}) {category} {amount}원")

    elif args.command == "export":
        service = ExportService(
            TransactionService( TransactionRepository(data_dir), CategoryStore(data_dir) ),
            CsvTransactionStore()
        )
        try:
            count = service.export_transactions(
                output_path=args.out,
                month=args.month,
                date_from=args.date_from,
                date_to=args.date_to,
            )
            print(f"[완료] {args.out} ({count} records)")
        except ValueError as error:
            print(f"[오류] {error}")
            print("[힌트] 날짜 형식, 월 범위, 기간 조건을 확인하세요.")
            return 1
        except FileExistsError:
            print(f"[오류] 출력 파일이 이미 존재합니다: {args.out}")
            print("[힌트] 다른 출력 파일명을 지정하세요.")
            return 1

    elif args.command == "import":
        service = ImportService( TransactionService(TransactionRepository(data_dir),CategoryStore(data_dir)), CsvTransactionStore() )
        try:
            imported, skipped = service.import_transactions(args.input_path)
            print(f"[완료] imported={imported}, skipped={skipped}")
            if skipped != 0: return 1
        except ValueError as error:
            print(f"[오류] {error}")
            print("[힌트] CSV의 필수 헤더와 각 행의 열 개수, 혹은 중복된 헤더값은 없는지 확인하세요.")
            return 1
        except FileNotFoundError:
            print(f"[오류] 입력 CSV 파일을 찾을 수 없습니다: {args.input_path}")
            print("[힌트] 파일 경로와 이름을 확인하세요.")
            return 1

    return 0
