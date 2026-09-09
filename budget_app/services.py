from collections.abc import Iterator
from datetime import date as Date

from .storage import CategoryStore, TransactionRepository

import re


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