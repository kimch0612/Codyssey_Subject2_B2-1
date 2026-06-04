"""파일 핸들링 및 데이터 직렬화/역직렬화 관련 함수들을 모아놓은 모듈"""

from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from typing import Iterator
from .data_struct import Transaction, Category, Budget

import os, json

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

