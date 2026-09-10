from dataclasses import dataclass, field

@dataclass
class Transaction:    # e.g.
    id: str             # TX-000012
    type: str           # income or expense
    date: str           # "2026-09-09"
    amount: int         # 21000
    category: str       # "food", "transit"
    memo: str = ""      # "처갓집 슈프림치킨"
    tags: list[str] = field(default_factory=list) # ["외식", "치킨"]

@dataclass
class MonthlySummary:
    month: str                          # 거래 월
    transaction_count: int              # 거래 건수 (거래가 없는 달인가??)
    total_income: int                   # 수입 합계
    total_expense: int                  # 지출 합계
    balance: int                        # 총수입 − 총지출
    category_expenses: dict[str, int]   # 카테고리별 지출 합계
    budget_amount: int | None = None    # 설정된 월 예산(있으면)