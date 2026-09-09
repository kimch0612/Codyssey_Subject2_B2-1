from collections.abc import Iterator
from datetime import date as Date

from .storage import CategoryStore, TransactionRepository
from .models import Transaction

import re, heapq


class CategoryService:
    def __init__(self, category_store: CategoryStore) -> None:
        self.category_store = category_store

    def add_category(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValueError("카테고리 이름은 빈 문자열일 수 없습니다.")
        elif name in self.iter_categories():
            raise ValueError(f"카테고리 '{name}'은 이미 존재합니다.")

        self.category_store.add(name)

    def iter_categories(self) -> Iterator[str]:
        return self.category_store.iter_categories()

class TransactionService:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        category_store: CategoryStore,
    ) -> None:
        self.transaction_repository = transaction_repository # 기존 ID 확인과 새 거래 저장용
        self.category_store = category_store # 전달받은 카테고리명이 유효한지 검증용

    def validate_transaction_data(
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
        elif re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date) is None:
            raise ValueError("날짜는 YYYY-MM-DD 형식으로 입력해야 합니다.")
        elif category not in self.category_store.iter_categories():
            raise ValueError("존재하지 않는 카테고리 이름입니다.")
        
        try:
            Date.fromisoformat(date)
        except ValueError:
            raise ValueError("존재하지 않는 날짜를 입력했습니다.")

    def add_transaction(
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

    def generate_id(self) -> str:
        highest_number = 0

        for transaction in self.transaction_repository.iter_transactions():
            number = int(transaction.id.removeprefix("TX-"))
            if number > highest_number:
                highest_number = number

        return f"TX-{highest_number + 1:06d}"

    def list_transaction(self, limit: int = 10) -> list[Transaction]:
        if type(limit) is not int or limit <= 0:
            raise ValueError("조회 개수는 1 이상의 정수여야 합니다.")

        data = heapq.nlargest(
            limit,
            self.transaction_repository.iter_transactions(),
            key = lambda transaction: (
                transaction.date,
                int(transaction.id.removeprefix("TX-"))
            )
        )

        return data