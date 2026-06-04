"""Dataclass definitions for budget app data."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Transaction:
    id: str = ""
    type: str = ""
    date: str = ""
    amount: int = 0
    category: str = ""
    memo: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Category:
    name: str = ""


@dataclass
class Budget:
    month: str = ""
    amount: int = 0

