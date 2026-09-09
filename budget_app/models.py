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