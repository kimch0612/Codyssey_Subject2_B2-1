"""가계부 앱의 핵심 서비스 모듈."""

from __future__ import annotations

import csv
import heapq
from pathlib import Path
from typing import Iterable

from .budget_helper import (
    BudgetAppError,
    error_handler,
    generate_transaction_id,
    parse_tags,
    validate_amount,
    validate_date_format,
    validate_transaction_type,
)
from .data_struct import Budget, Category, Transaction
from .storage import (
    DEFAULT_DATA_DIR,
    iter_budgets,
    iter_categories,
    iter_transactions,
    iter_transactions_reverse,
    rewrite_budgets,
    rewrite_categories,
    rewrite_transactions,
    init_storage,
)


def _data_dir(args) -> str | Path:
    return getattr(args, "data_dir", DEFAULT_DATA_DIR)


def _transaction_sort_key(transaction: Transaction) -> tuple[str, str]:
    return transaction.date, transaction.id


def _sorted_transactions(transactions: Iterable[Transaction]) -> list[Transaction]:
    return sorted(transactions, key=_transaction_sort_key)


def _rewrite_transactions_sorted(
    transactions: Iterable[Transaction],
    data_dir: str | Path,
) -> None:
    rewrite_transactions(_sorted_transactions(transactions), data_dir)


def _format_transaction_line(transaction: Transaction) -> str:
    return (
        f"{transaction.id} | {transaction.date} | {transaction.type:<7} | "
        f"{transaction.category} | {transaction.amount} | {transaction.memo}"
    )


def _category_names(data_dir: str | Path) -> set[str]:
    return {category.name for category in iter_categories(data_dir)}


def _ensure_category_exists(category_name: str, data_dir: str | Path) -> None:
    if category_name not in _category_names(data_dir):
        raise BudgetAppError(
            "존재하지 않는 카테고리입니다.",
            "먼저 category add로 카테고리를 추가해주세요.",
        )


def _find_transaction_index(transactions: list[Transaction], transaction_id: str) -> int:
    for index, transaction in enumerate(transactions):
        if transaction.id == transaction_id:
            return index
    raise BudgetAppError("해당 id의 거래가 없습니다.", f"id를 확인해주세요: {transaction_id}")


def _filter_transactions(
    transactions: Iterable[Transaction],
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    transaction_type: str | None = None,
    query: str | None = None,
    tag: str | None = None,
) -> Iterable[Transaction]:
    query_lower = query.lower() if query else None
    for transaction in transactions:
        if date_from and transaction.date < date_from:
            continue
        if date_to and transaction.date > date_to:
            continue
        if category and transaction.category != category:
            continue
        if transaction_type and transaction.type != transaction_type:
            continue
        if query_lower and query_lower not in transaction.memo.lower():
            continue
        if tag and tag not in transaction.tags:
            continue
        yield transaction


def _load_budget_map(data_dir: str | Path) -> dict[str, int]:
    return {budget.month: budget.amount for budget in iter_budgets(data_dir)}


################# 카테고리 로직 #################


@error_handler
def run_category_list(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)
    categories_data = list(iter_categories(data_dir))

    if not categories_data:
        print("저장된 카테고리가 없습니다.")
        return 0

    for category in categories_data:
        print(f"- {category.name}")

    return 0


@error_handler
def run_category_add(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)
    categories_data = list(iter_categories(data_dir))
    category_names = {category.name for category in categories_data}

    new_category = input("카테고리명: ").strip()
    if not new_category:
        raise BudgetAppError("카테고리명은 최소 한 글자 이상을 입력해야 합니다.")
    if new_category in category_names:
        raise BudgetAppError("이미 존재하는 카테고리명입니다.")

    categories_data.append(Category(name=new_category))
    rewrite_categories(categories_data, data_dir)

    print(f"[저장 완료] category={new_category}")
    return 0


@error_handler
def run_category_remove(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)
    categories_data = list(iter_categories(data_dir))
    category_names = {category.name for category in categories_data}

    remove_category = input("삭제할 카테고리명: ").strip()
    if not remove_category:
        raise BudgetAppError("카테고리명은 최소 한 글자 이상을 입력해야 합니다.")
    if remove_category not in category_names:
        raise BudgetAppError("존재하지 않는 카테고리명입니다.")

    for transaction in iter_transactions(data_dir):
        if transaction.category == remove_category:
            raise BudgetAppError(
                "사용 중인 카테고리는 삭제할 수 없습니다.",
                "먼저 해당 거래를 수정하거나 다른 카테고리로 옮겨주세요.",
            )

    categories_data = [
        category for category in categories_data if category.name != remove_category
    ]
    rewrite_categories(categories_data, data_dir)

    print(f"[삭제 완료] category={remove_category}")
    return 0


################# 거래 로직 #################


@error_handler
def run_transaction_add(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)

    trans_date = input("날짜(YYYY-MM-DD): ").strip()
    if not trans_date:
        raise BudgetAppError("날짜를 입력해야 합니다.")
    trans_date = validate_date_format(1, trans_date)

    trans_type = input("타입(income/expense): ").strip()
    if not trans_type:
        raise BudgetAppError("거래 타입을 입력해야 합니다.")
    trans_type = validate_transaction_type(trans_type)

    trans_category = input("카테고리: ").strip()
    if not trans_category:
        raise BudgetAppError("카테고리를 입력해야 합니다.")
    _ensure_category_exists(trans_category, data_dir)

    trans_amount = input("금액(양수): ").strip()
    if not trans_amount:
        raise BudgetAppError("금액을 입력해야 합니다.")
    trans_amount = validate_amount(trans_amount)

    trans_memo = input("메모(선택): ").strip()
    trans_tags = input("태그(쉼표로 구분, 없으면 엔터): ").strip()

    transactions_data = list(iter_transactions(data_dir))
    trans_id = generate_transaction_id(transactions_data)

    new_transaction = Transaction(
        id=trans_id,
        date=trans_date,
        type=trans_type,
        category=trans_category,
        amount=trans_amount,
        memo=trans_memo,
        tags=parse_tags(trans_tags),
    )

    transactions_data.append(new_transaction)
    _rewrite_transactions_sorted(transactions_data, data_dir)
    print(f"[저장 완료] id={new_transaction.id}")
    return 0


@error_handler
def run_transaction_list(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)

    if args.limit <= 0:
        raise BudgetAppError("--limit은 1 이상의 숫자여야 합니다.")

    transactions_data = heapq.nlargest(
        args.limit,
        iter_transactions(data_dir),
        key=_transaction_sort_key,
    )

    if not transactions_data:
        print("거래 내역이 없습니다.")
        return 0

    for transaction in transactions_data:
        print(_format_transaction_line(transaction))

    return 0


@error_handler
def run_transaction_search(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)

    date_from = validate_date_format(1, args.date_from) if args.date_from else None
    date_to = validate_date_format(1, args.date_to) if args.date_to else None
    if date_from and date_to and date_from > date_to:
        raise BudgetAppError("--from 날짜는 --to 날짜보다 늦을 수 없습니다.")

    transaction_type = (
        validate_transaction_type(args.transaction_type)
        if args.transaction_type
        else None
    )
    if args.category:
        _ensure_category_exists(args.category, data_dir)

    matches = _filter_transactions(
        iter_transactions_reverse(data_dir),
        date_from=date_from,
        date_to=date_to,
        category=args.category,
        transaction_type=transaction_type,
        query=args.query,
        tag=args.tag,
    )

    found = False
    for transaction in matches:
        print(_format_transaction_line(transaction))
        found = True

    if not found:
        print("검색 결과가 없습니다.")
        return 0

    return 0


@error_handler
def run_transaction_update(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)

    transactions_data = list(iter_transactions(data_dir))
    index = _find_transaction_index(transactions_data, args.id)
    transaction = transactions_data[index]

    changed = False
    if args.date is not None:
        transaction.date = validate_date_format(1, args.date)
        changed = True
    if args.transaction_type is not None:
        transaction.type = validate_transaction_type(args.transaction_type)
        changed = True
    if args.category is not None:
        _ensure_category_exists(args.category, data_dir)
        transaction.category = args.category
        changed = True
    if args.amount is not None:
        transaction.amount = validate_amount(args.amount)
        changed = True
    if args.memo is not None:
        transaction.memo = args.memo
        changed = True
    if args.tags is not None:
        transaction.tags = parse_tags(args.tags)
        changed = True

    if not changed:
        raise BudgetAppError("수정할 필드를 1개 이상 입력해야 합니다.")

    transactions_data[index] = transaction
    _rewrite_transactions_sorted(transactions_data, data_dir)
    print(f"[수정 완료] id={transaction.id}")
    return 0


@error_handler
def run_transaction_delete(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)

    transactions_data = list(iter_transactions(data_dir))
    _find_transaction_index(transactions_data, args.id)
    _rewrite_transactions_sorted(
        (transaction for transaction in transactions_data if transaction.id != args.id),
        data_dir,
    )
    print(f"[삭제 완료] id={args.id}")
    return 0


################# 요약/예산 로직 #################


@error_handler
def run_summary(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)

    month = validate_date_format(2, args.month)
    if args.top <= 0:
        raise BudgetAppError("--top은 1 이상의 숫자여야 합니다.")

    total_income = 0
    total_expense = 0
    expense_by_category: dict[str, int] = {}
    has_transaction = False

    for transaction in iter_transactions(data_dir):
        if not transaction.date.startswith(month):
            continue
        has_transaction = True
        if transaction.type == "income":
            total_income += transaction.amount
        elif transaction.type == "expense":
            total_expense += transaction.amount
            expense_by_category[transaction.category] = (
                expense_by_category.get(transaction.category, 0) + transaction.amount
            )

    if not has_transaction:
        print("데이터 없음")
        return 0

    print(f"총 수입: {total_income}원")
    print(f"총 지출: {total_expense}원")
    print(f"잔액: {total_income - total_expense}원")

    budgets = _load_budget_map(data_dir)
    if month in budgets:
        budget_amount = budgets[month]
        usage_rate = total_expense * 100 / budget_amount if budget_amount else 0
        print(f"예산: {budget_amount}원 (사용률 {usage_rate:.1f}%)")
        if total_expense > budget_amount:
            print("[경고] 예산을 초과했습니다.")

    print()
    print(f"지출 TOP {args.top}")
    top_expenses = sorted(
        expense_by_category.items(),
        key=lambda item: item[1],
        reverse=True,
    )[: args.top]
    if not top_expenses:
        print("지출 데이터 없음")
    else:
        for index, (category, amount) in enumerate(top_expenses, 1):
            print(f"{index}) {category} {amount}원")

    return 0


@error_handler
def run_budget_set(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)

    month = validate_date_format(2, args.month)
    amount = validate_amount(args.amount)

    budgets_data = list(iter_budgets(data_dir))
    updated = False
    for budget in budgets_data:
        if budget.month == month:
            budget.amount = amount
            updated = True
            break
    if not updated:
        budgets_data.append(Budget(month=month, amount=amount))

    rewrite_budgets(budgets_data, data_dir)
    print(f"[저장 완료] {month} 예산 {amount}원")
    return 0


################# 가져오기/내보내기 로직 #################


@error_handler
def run_import(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)

    import_path = Path(args.import_from)
    if not import_path.exists():
        raise BudgetAppError("가져올 CSV 파일이 없습니다.", str(import_path))

    category_names = _category_names(data_dir)
    transactions_data = list(iter_transactions(data_dir))
    imported = 0
    skipped = 0

    with import_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"date", "type", "category", "amount"}
        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            raise BudgetAppError(
                "CSV 헤더가 올바르지 않습니다.",
                "필수 헤더: date,type,category,amount,memo,tags",
            )

        for row in reader:
            try:
                category = (row.get("category") or "").strip()
                if category not in category_names:
                    raise BudgetAppError("등록되지 않은 카테고리입니다.")

                transaction = Transaction(
                    id=generate_transaction_id(transactions_data),
                    date=validate_date_format(1, row.get("date") or ""),
                    type=validate_transaction_type(row.get("type") or ""),
                    category=category,
                    amount=validate_amount(row.get("amount") or ""),
                    memo=(row.get("memo") or "").strip(),
                    tags=parse_tags(row.get("tags") or ""),
                )
            except BudgetAppError:
                skipped += 1
                continue

            transactions_data.append(transaction)
            imported += 1

    if imported:
        _rewrite_transactions_sorted(transactions_data, data_dir)

    print(f"[완료] imported={imported}, skipped={skipped}")
    return 0


@error_handler
def run_export(args) -> int:
    data_dir = _data_dir(args)
    init_storage(data_dir)

    month = validate_date_format(2, args.month) if args.month else None
    date_from = validate_date_format(1, args.date_from) if args.date_from else None
    date_to = validate_date_format(1, args.date_to) if args.date_to else None

    if not month and not (date_from and date_to):
        raise BudgetAppError(
            "export 조건이 필요합니다.",
            "--month YYYY-MM 또는 --from YYYY-MM-DD --to YYYY-MM-DD를 입력해주세요.",
        )
    if date_from and date_to and date_from > date_to:
        raise BudgetAppError("--from 날짜는 --to 날짜보다 늦을 수 없습니다.")

    def in_export_range(transaction: Transaction) -> bool:
        if month and not transaction.date.startswith(month):
            return False
        if date_from and transaction.date < date_from:
            return False
        if date_to and transaction.date > date_to:
            return False
        return True

    export_path = Path(args.out)
    if export_path.parent != Path("."):
        export_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with export_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["date", "type", "category", "amount", "memo", "tags"],
        )
        writer.writeheader()
        for transaction in iter_transactions(data_dir):
            if not in_export_range(transaction):
                continue
            writer.writerow(
                {
                    "date": transaction.date,
                    "type": transaction.type,
                    "category": transaction.category,
                    "amount": transaction.amount,
                    "memo": transaction.memo,
                    "tags": ",".join(transaction.tags),
                }
            )
            count += 1

    print(f"[완료] {export_path} ({count} records)")
    return 0
