from collections.abc import Iterator
from datetime import date as Date
from dataclasses import replace
from pathlib import Path

from .storage import CategoryStore, TransactionRepository, BudgetStore, CsvTransactionStore
from .models import Transaction, MonthlySummary

import re, heapq


class CategoryService:
    def __init__(
        self,
        category_store: CategoryStore,
        transaction_repository: TransactionRepository,
    ) -> None:
        self.category_store = category_store
        self.transaction_repository = transaction_repository

    def add_category(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValueError("카테고리 이름은 빈 문자열일 수 없습니다.")
        elif name in self.iter_categories():
            raise ValueError(f"카테고리 '{name}'은 이미 존재합니다.")

        self.category_store.add(name)

    def iter_categories(self) -> Iterator[str]:
        return self.category_store.iter_categories()

    def remove_category(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValueError("카테고리 이름은 빈 문자열일 수 없습니다.")
        elif name not in self.iter_categories():
            raise ValueError(f"카테고리 '{name}'은 존재하지 않습니다.")

        for transaction in self.transaction_repository.iter_transactions():
            if transaction.category == name:
                raise ValueError("사용 중인 카테고리는 삭제할 수 없습니다.")
        
        self.category_store.replace_all(
            cat for cat in self.iter_categories() if cat != name
        )

class TransactionService:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        category_store: CategoryStore,
    ) -> None:
        self.transaction_repository = transaction_repository # 기존 ID 확인과 새 거래 저장용
        self.category_store = category_store # 전달받은 카테고리명이 유효한지 검증용

    def validate_transaction_data( # 거래 데이터 검증
        self,
        date: str,
        transaction_type: str,
        category: str,
        amount: int,
    ) -> None:
        if type(amount) is not int or amount <= 0:
            raise ValueError("금액은 정수이면서 0원을 초과해야 합니다.")
        elif transaction_type not in ("income", "expense"):
            raise ValueError("transaction_type은 income 또는 expense만 허용됩니다.")
        elif category not in self.category_store.iter_categories():
            raise ValueError("존재하지 않는 카테고리 이름입니다.")
        
        self.validate_date_data(date)
    
    def validate_date_data(
        self,
        date: str
    ) -> None:
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date) is None:
            raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다.")
        
        try:
            Date.fromisoformat(date)
        except ValueError:
            raise ValueError("존재하지 않는 날짜를 입력했습니다.")

    def add_transaction( # 거래내역 추가
        self,
        date: str,
        transaction_type: str,
        category: str,
        amount: int,
        memo: str = "",
        tags: list[str] | None = None,
    ) -> Transaction:
        date = date.strip()
        transaction_type = transaction_type.strip()
        category = category.strip()
        memo = memo.strip()
        if tags is None: tags = []

        self.validate_transaction_data(
            date,
            transaction_type,
            category,
            amount
        )

        new_id = self.generate_id()

        transaction = Transaction(
            id=new_id,
            type=transaction_type,
            date=date,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags,
        )
        self.transaction_repository.add(transaction)

        return transaction

    def generate_id(self) -> str: # 거래 id 생성용 함수 (최대+1)
        highest_number = 0

        for transaction in self.transaction_repository.iter_transactions():
            number = int(transaction.id.removeprefix("TX-"))
            if number > highest_number:
                highest_number = number

        return f"TX-{highest_number + 1:06d}"

    def list_transaction(self, limit: int = 10) -> list[Transaction]: # 날짜 내림차순, 같은 날짜는 ID 내림차순; 최대 n개 추출
        if type(limit) is not int or limit <= 0:
            raise ValueError("조회 개수는 1 이상의 정수여야 합니다.")

        data = heapq.nlargest(
            limit,
            self.transaction_repository.iter_transactions(),
            key = self.transaction_sort_key
        )

        return data

    def filter_transactions( # 조건에 맞는 거래만 추출
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        query: str | None = None,
        tag: str | None = None,
    ) -> Iterator[Transaction]:
        self.validate_search_conditions(
            date_from,
            date_to,
            transaction_type
        )

        for transaction in self.transaction_repository.iter_transactions():
            if date_from is not None and transaction.date < date_from: # 특정 날짜 이후인가
                continue
            if date_to is not None and transaction.date > date_to: # 특정 날짜 이전인가
                continue
            if category is not None and transaction.category != category: # 특정 카테고리인가
                continue
            if transaction_type is not None and transaction.type != transaction_type: # 특정 거래 타입인가
                continue
            if query is not None and query not in transaction.memo: # 특정 단어가 메모에 포함됐는가
                continue
            if tag is not None and tag not in transaction.tags: # 특정 태그가 포함됐는가
                continue
            yield transaction

    def validate_search_conditions( # filter_transactions에서 사용할 수 있는 조건인지 검증
        self,
        date_from: str | None,
        date_to: str | None,
        transaction_type: str | None,
    ) -> None:
        if date_from is not None:
            self.validate_date_data(date_from)
        if date_to is not None:
            self.validate_date_data(date_to)

        if transaction_type is not None and transaction_type not in ("income", "expense"):
            raise ValueError("transaction_type은 income 또는 expense만 허용됩니다.")

        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError("시작일은 종료일보다 더 미래일 수 없습니다.")

    def transaction_sort_key(
        self,
        transaction: Transaction,
    ) -> tuple[str, int]:
        return (
            transaction.date,
            int(transaction.id.removeprefix("TX-")),
        )

    def search_transactions(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        query: str | None = None,
        tag: str | None = None,
    ) -> Iterator[Transaction]:
        # 근데 거래 데이터를 모두 메모리에 올리는거면 스트리밍의 의미가 없는 거 아닌가.. 모르겠음
        batch_size = 100
        last_key: tuple[str, int] | None = None

        while True:
            candidates = self.filter_transactions(
                date_from=date_from,
                date_to=date_to,
                category=category,
                transaction_type=transaction_type,
                query=query,
                tag=tag,
            )

            if last_key is not None:
                candidates = (
                    transaction
                    for transaction in candidates
                    if self.transaction_sort_key(transaction) < last_key
                )
            
            batch = heapq.nlargest(
                batch_size, # 모든 후보를 훑되, 최신 batch_size건만 메모리에 유지하는 식으로 구현
                candidates,
                key=self.transaction_sort_key,
            )

            if not batch:
                return
            
            for transaction in batch:
                yield transaction

            last_key = self.transaction_sort_key(batch[-1])

    def delete_transaction(self, transaction_id: str) -> None:
        found = any(
            transaction.id == transaction_id
            for transaction in self.transaction_repository.iter_transactions()
        )

        if not found:
            raise ValueError("존재하지 않는 거래 ID입니다.")

        remaining = (
            transaction
            for transaction in self.transaction_repository.iter_transactions()
            if transaction.id != transaction_id
        )

        self.transaction_repository.replace_all(remaining)

    def update_transaction(
        self,
        transaction_id: str,
        date: str | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        amount: int | None = None,
        memo: str | None = None,
        tags: list[str] | None = None,
    ) -> Transaction:
        original = None

        for transaction in self.transaction_repository.iter_transactions():
            if transaction.id == transaction_id:
                original = transaction
                break
        if original is None:
            raise ValueError("존재하지 않는 거래 ID입니다.")

        updated = replace(
            original,
            date=date.strip() if date is not None else original.date,
            type=(
                transaction_type.strip()
                if transaction_type is not None
                else original.type
            ),
            category=category.strip() if category is not None else original.category,
            amount=amount if amount is not None else original.amount,
            memo=memo.strip() if memo is not None else original.memo,
            tags=tags if tags is not None else original.tags,
        )

        self.validate_transaction_data(
            date=updated.date,
            transaction_type=updated.type,
            category=updated.category,
            amount=updated.amount,
        )

        transactions = (
            updated if transaction.id == transaction_id else transaction
            for transaction in self.transaction_repository.iter_transactions()
        )
        self.transaction_repository.replace_all(transactions)
        
        return updated

class BudgetService:
    def __init__(self, budget_store: BudgetStore) -> None:
        self.budget_store = budget_store

    def validate_data(self, month: str, amount: int) -> None:
        if type(month) is not str or re.fullmatch(
            r"[0-9]{4}-[0-9]{2}", month
        ) is None:
            raise ValueError("월 데이터는 YYYY-MM 형식이어야 합니다.")

        try:
            Date.fromisoformat(f"{month}-01")
        except ValueError:
            raise ValueError("실제로 존재하는 연월을 입력하세요.") from None

        if type(amount) is not int or amount < 0:
            raise ValueError("예산은 0 이상의 정수여야 합니다.")

    def set_budget(self, month: str, amount: int) -> None:
        self.validate_data(month, amount)

        exists = any(
            budget["month"] == month
            for budget in self.budget_store.iter_budgets()
        )

        if exists:
            self.update_budget(month, amount)
        else:
            self.add_budget(month, amount)
        
    def add_budget(self, month: str, amount: int) -> None:
        # set_budget에서 이미 validate_data를 했으니 중복으로 할 필요는 없을듯
        self.budget_store.add(month, amount)
        
    def update_budget(self, month: str, amount: int) -> None:
        updated = {"month": month, "amount": amount}

        budgets = (
            updated if budget["month"] == month else budget
            for budget in self.budget_store.iter_budgets()
        )

        self.budget_store.replace_all(budgets)

class SummaryService:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        budget_store: BudgetStore,
    ) -> None:
        self.transaction_repository = transaction_repository
        self.budget_store = budget_store

    def validate_data(self, month: str) -> None:
        if type(month) is not str or re.fullmatch(
            r"[0-9]{4}-[0-9]{2}", month
        ) is None:
            raise ValueError("월 데이터는 YYYY-MM 형식이어야 합니다.")

        try:
            Date.fromisoformat(f"{month}-01")
        except ValueError:
            raise ValueError("실제로 존재하는 연월을 입력하세요.") from None
    
    def summarize_month(self, month: str) -> MonthlySummary:
        self.validate_data(month)
        budget_amount = None

        for budget in self.budget_store.iter_budgets():
            if budget["month"] == month:
                budget_amount = budget["amount"]
                break

        transactions = (
            transaction
            for transaction in self.transaction_repository.iter_transactions()
            if transaction.date.startswith(month + "-")
        )

        transaction_count = 0
        total_income = 0
        total_expense = 0
        category_expenses: dict[str, int] = {}

        for transaction in transactions:
            transaction_count += 1

            if transaction.type == "income":
                total_income += transaction.amount
            elif transaction.type == "expense":
                total_expense += transaction.amount
                category_expenses[transaction.category] = (
                    category_expenses.get(transaction.category, 0)
                    + transaction.amount
                )

        budget_usage_rate = None
        budget_exceeded_amount = None

        if budget_amount is not None:
            budget_exceeded_amount = max(total_expense - budget_amount, 0)
            if budget_amount > 0:
                budget_usage_rate = total_expense / budget_amount * 100

        return MonthlySummary(
            month=month,
            transaction_count=transaction_count,
            total_income=total_income,
            total_expense=total_expense,
            balance=total_income - total_expense,
            category_expenses=category_expenses,
            budget_amount=budget_amount,
            budget_usage_rate=budget_usage_rate,
            budget_exceeded_amount=budget_exceeded_amount
        )

    def top_categories(
        self,
        category_expenses: dict[str, int],
        top: int = 3,
    ) -> list[tuple[str, int]]:
        if type(top) is not int or top < 1:
            raise ValueError("top은 1 이상의 정수여야 합니다.")

        return heapq.nlargest(
            top,
            category_expenses.items(),
            key=lambda item: item[1],
        )

class ExportService:
    def __init__(
        self,
        transaction_service: TransactionService,
        csv_store: CsvTransactionStore,
    ) -> None:
        self.transaction_service = transaction_service
        self.csv_store = csv_store

    def validate_data(self, month: str) -> None:
        if type(month) is not str or re.fullmatch(
            r"[0-9]{4}-[0-9]{2}", month
        ) is None:
            raise ValueError("월 데이터는 YYYY-MM 형식이어야 합니다.")

        try:
            Date.fromisoformat(f"{month}-01")
        except ValueError:
            raise ValueError("실제로 존재하는 연월을 입력하세요.") from None

    def export_transactions(
        self,
        output_path: Path,
        month: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> int:
        if month is None and date_from is None and date_to is None:
            raise ValueError("월 또는 시작일·종료일을 지정해주세요.")

        if (date_from is None) != (date_to is None):
            raise ValueError("시작일과 종료일은 함께 지정해야 합니다.")

        if month is not None:
            self.validate_data(month)

        self.transaction_service.validate_search_conditions(
            date_from=date_from,
            date_to=date_to,
            transaction_type=None,
        )

        transactions = self.transaction_service.filter_transactions(
            date_from=date_from,
            date_to=date_to,
        )

        if month is not None:
            transactions = (
                transaction
                for transaction in transactions
                if transaction.date.startswith(month + "-")
            )

        return self.csv_store.export(output_path, transactions)

class ImportService:
    def __init__(
        self,
        transaction_service: TransactionService,
        csv_store: CsvTransactionStore,
    ) -> None:
        self.transaction_service = transaction_service
        self.csv_store = csv_store

    def import_transactions(self, input_path: Path) -> tuple[int, int]: # (imported, skipped)
        imported_count, skipped_count = 0, 0
        
        for row in self.csv_store.iter_rows(input_path):
            try:
                amount = int(row["amount"])

                tags = [
                    tag.strip()
                    for tag in row.get("tags", "").split(",")
                    if tag.strip()
                ]

                self.transaction_service.add_transaction(
                    date=row["date"],
                    transaction_type=row["type"],
                    category=row["category"],
                    amount=amount,
                    memo=row.get("memo", ""),
                    tags=tags,
                )

            except ValueError:
                skipped_count += 1
                continue

            imported_count += 1

        return imported_count, skipped_count