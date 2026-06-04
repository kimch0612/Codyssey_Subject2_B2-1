"""Dataclass definitions for budget app data."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Transaction:
    id: str = ""        # unique 값
    type: str = ""      # 저장될 값을 income, expense로 제한
    date: str = ""      # YYYY-MM-DD
    amount: int = 0     # 금액
    category: str = ""  # 카테고리 이름 -> Category.name과 연결
    memo: str = ""      # 메모는 선택사항
    tags: list[str] = field(default_factory=list) # 최종적으론 이런 구조가 되는 게 어떨까: tags = ["식비", "영화", "월정액"]


@dataclass
class Category:
    name: str = ""
    #category_description: str = "" # 쓸 일이 있으려남


@dataclass
class Budget:
    month: str = ""     # YYYY-MM
    amount: int = 0
