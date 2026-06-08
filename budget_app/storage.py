"""파일 핸들링 및 데이터 직렬화/역직렬화 관련 함수들을 모아놓은 모듈"""

from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Iterable, Iterator, TypeVar
from .data_struct import Transaction, Category, Budget
from .budget_helper import BudgetAppError

import json
import os

T = TypeVar("T")

################# 상수 및 파일 경로 처리 파트 #################

DEFAULT_DATA_DIR = Path("./data")
TRANSACTIONS_FILE_NAME = "transactions.jsonl"
CATEGORIES_FILE_NAME = "categories.jsonl"
BUDGETS_FILE_NAME = "budgets.jsonl"
DEFAULT_CATEGORIES = ["외식", "교통비", "쇼핑", "월급", "기타"]

def get_data_dir(data_dir: str | Path = DEFAULT_DATA_DIR) -> Path:
    return Path(data_dir)

def get_transactions_file_path(data_dir: str | Path = DEFAULT_DATA_DIR) -> Path:
    return get_data_dir(data_dir) / TRANSACTIONS_FILE_NAME

def get_categories_file_path(data_dir: str | Path = DEFAULT_DATA_DIR) -> Path:
    return get_data_dir(data_dir) / CATEGORIES_FILE_NAME

def get_budgets_file_path(data_dir: str | Path = DEFAULT_DATA_DIR) -> Path:
    return get_data_dir(data_dir) / BUDGETS_FILE_NAME

################# I/O 함수 파트 #################

def init_storage(data_dir: str | Path = DEFAULT_DATA_DIR) -> None:
    # 데이터 디렉토리와 파일이 존재하지 않으면 생성하는 함수
    data_dir = get_data_dir(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    for file_path in [get_transactions_file_path(data_dir), get_categories_file_path(data_dir), get_budgets_file_path(data_dir)]:
        if not file_path.exists(): 
            file_path.touch()
        if file_path == get_categories_file_path(data_dir):
            # 카테고리 파일이 비어있으면 기본 카테고리들로 초기화
            if file_path.stat().st_size == 0:
                with file_path.open("w", encoding="utf-8") as f:
                    for category_name in DEFAULT_CATEGORIES:
                        category = Category(name=category_name)
                        f.write(serialize_category(category) + "\n")

def serialize_transaction(transaction: Transaction) -> str:
    # Transaction 객체를 JSONL 형식의 문자열로 직렬화하는 함수
    return json.dumps(asdict(transaction), ensure_ascii=False)

def deserialize_transaction(jsonl_str: str) -> Transaction:
    # JSONL 형식의 문자열을 Transaction 객체로 역직렬화하는 함수
    data = json.loads(jsonl_str)
    return Transaction(**data)

def serialize_category(category: Category) -> str:
    # Category 객체를 JSONL 형식의 문자열로 직렬화하는 함수
    return json.dumps(asdict(category), ensure_ascii=False)

def deserialize_category(jsonl_str: str) -> Category:
    # JSONL 형식의 문자열을 Category 객체로 역직렬화하는 함수
    data = json.loads(jsonl_str)
    return Category(**data)

def serialize_budget(budget: Budget) -> str:
    # Budget 객체를 JSONL 형식의 문자열로 직렬화하는 함수
    return json.dumps(asdict(budget), ensure_ascii=False)

def deserialize_budget(jsonl_str: str) -> Budget:
    # JSONL 형식의 문자열을 Budget 객체로 역직렬화하는 함수
    data = json.loads(jsonl_str)
    return Budget(**data)

def iter_transactions(data_dir: str | Path = DEFAULT_DATA_DIR) -> Iterator[Transaction]:
    # transactions.jsonl 파일에서 Transaction 객체들을 순회하는 제너레이터 함수
    with get_transactions_file_path(data_dir).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip(): # 빈 줄 무시
                yield deserialize_transaction(line)

def iter_jsonl_lines_reverse(file_path: Path, chunk_size: int = 8192) -> Iterator[str]:
    # JSONL 파일을 뒤에서 앞으로 읽는 제너레이터 함수
    with file_path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        position = f.tell()
        buffer = b""

        while position > 0:
            read_size = min(chunk_size, position)
            position -= read_size
            f.seek(position)
            buffer = f.read(read_size) + buffer
            lines = buffer.split(b"\n")
            buffer = lines[0]

            for line in reversed(lines[1:]):
                if line.strip():
                    yield line.decode("utf-8").rstrip("\r")

        if buffer.strip():
            yield buffer.decode("utf-8").rstrip("\r")

def iter_transactions_reverse(data_dir: str | Path = DEFAULT_DATA_DIR) -> Iterator[Transaction]:
    # transactions.jsonl 파일에서 Transaction 객체들을 역순으로 순회하는 제너레이터 함수
    for line in iter_jsonl_lines_reverse(get_transactions_file_path(data_dir)):
        yield deserialize_transaction(line)

def rewrite_jsonl_file(target_path: Path, items: Iterable[T], serializer: Callable[[T], str]) -> None:
    # 데이터를 원자적으로 jsonl 파일에 저장하는 공통 함수
    temp_file_path = target_path.with_suffix(".tmp")
    try:
        with temp_file_path.open("w", encoding="utf-8") as f:
            for item in items:
                f.write(serializer(item) + "\n")
            f.flush()
            os.fsync(f.fileno())
        temp_file_path.replace(target_path)
    except Exception as e:
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except OSError:
                pass # 임시 파일 정리 실패는 원래 저장 오류를 우선 보고한다.
        raise BudgetAppError(f"파일 저장 중 오류가 발생했습니다: {e}",
                             "여유 공간 및 파일 권한을 확인해주세요.") from e

def append_transaction(transaction: Transaction, data_dir: str | Path = DEFAULT_DATA_DIR) -> None:
    # Transaction 객체를 transactions.jsonl 파일에 추가하는 함수
    with get_transactions_file_path(data_dir).open("a", encoding="utf-8") as f:
        f.write(serialize_transaction(transaction) + "\n")

def rewrite_transactions(transactions: Iterable[Transaction], data_dir: str | Path = DEFAULT_DATA_DIR) -> None:
    # Transaction 객체 리스트로 transactions.jsonl 파일을 원자적 쓰기를 이용해 덮어쓰는 함수
    rewrite_jsonl_file(get_transactions_file_path(data_dir), transactions, serialize_transaction)

def iter_categories(data_dir: str | Path = DEFAULT_DATA_DIR) -> Iterator[Category]:
    # categories.jsonl 파일에서 Category 객체들을 순회하는 제너레이터 함수
    with get_categories_file_path(data_dir).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip(): # 빈 줄 무시
                yield deserialize_category(line)

def rewrite_categories(categories: Iterable[Category], data_dir: str | Path = DEFAULT_DATA_DIR) -> None:
    # Category 객체 리스트로 categories.jsonl 파일을 원자적 쓰기를 이용해 덮어쓰는 함수
    rewrite_jsonl_file(get_categories_file_path(data_dir), categories, serialize_category)

def iter_budgets(data_dir: str | Path = DEFAULT_DATA_DIR) -> Iterator[Budget]:
    # budgets.jsonl 파일에서 Budget 객체들을 순회하는 제너레이터 함수
    with get_budgets_file_path(data_dir).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip(): # 빈 줄 무시
                yield deserialize_budget(line)

def rewrite_budgets(budgets: Iterable[Budget], data_dir: str | Path = DEFAULT_DATA_DIR) -> None:
    # Budget 객체 리스트로 budgets.jsonl 파일을 원자적 쓰기를 이용해 덮어쓰는 함수
    rewrite_jsonl_file(get_budgets_file_path(data_dir), budgets, serialize_budget)
