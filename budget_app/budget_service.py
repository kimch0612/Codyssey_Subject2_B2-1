"""가계부 앱의 핵심 코어 모듈 | CRUD, search, summary, import, export 로직이 들어갈 예정"""

from __future__ import annotations
import argparse
from .budget_helper import BudgetAppError
from .storage import init_storage, iter_categories


################# 카테고리 로직 #################

def run_category_list(args) -> int:
    init_storage()
    categories_data = list(iter_categories())

    if not categories_data:
        raise BudgetAppError("저장된 카테고리가 없습니다.") # 이 분기로 빠질 일이 있을까?

    for category in categories_data:
        print(f"- {category.name}")

    return 0