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