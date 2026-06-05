"""가계부 앱의 핵심 코어 모듈 | CRUD, search, summary, import, export 로직이 들어갈 예정"""

from __future__ import annotations
from .data_struct import Category, Transaction
from .budget_helper import (
    BudgetAppError,
    error_handler,
    parse_tags,
    validate_amount,
    validate_date_format,
    validate_transaction_type,
    generate_transaction_id,
)
from .storage import append_transaction, iter_transactions, init_storage, iter_categories, rewrite_categories


################# 카테고리 로직 #################

@error_handler
def run_category_list(args) -> int:
    init_storage()
    categories_data = list(iter_categories())

    if not categories_data:
        raise BudgetAppError("저장된 카테고리가 없습니다.") # 이 분기로 빠질 일이 있을까?

    for category in categories_data:
        print(f"- {category.name}")

    return 0

@error_handler
def run_category_add(args) -> int:
    init_storage()
    categories_data = list(iter_categories())
    category_names = {category.name for category in categories_data}

    new_category = input("카테고리명: ").strip()
    if not new_category:
        raise BudgetAppError("카테고리명은 최소 한 글자 이상을 입력해야 합니다.")
    elif new_category in category_names: # 중복 검사를 할 때 대소문자를 구분해야 하는가 고민중
        raise BudgetAppError("이미 존재하는 카테고리명입니다.")

    categories_data.append(Category(name=new_category))
    rewrite_categories(categories_data)
    
    print(f"[저장 완료] category={new_category}")

    return 0

@error_handler
def run_category_remove(args) -> int:
    init_storage()
    categories_data = list(iter_categories())
    category_names = {category.name for category in categories_data}

    remove_category = input("삭제할 카테고리명: ").strip()
    if not remove_category:
        raise BudgetAppError("카테고리명은 최소 한 글자 이상을 입력해야 합니다.")
    elif remove_category not in category_names:
        raise BudgetAppError("존재하지 않는 카테고리명입니다.")

    for transaction in iter_transactions():
        if transaction.category == remove_category:
            raise BudgetAppError(
                "사용 중인 카테고리는 삭제할 수 없습니다.",
                "먼저 해당 거래를 수정하거나 다른 카테고리로 옮겨주세요.",
            )

    categories_data = [category for category in categories_data if category.name != remove_category]
    rewrite_categories(categories_data)

    print(f"[삭제 완료] category={remove_category}")

    return 0

################# 거래 로직 #################

@error_handler
def run_transaction_add(args) -> int:
    init_storage()

    trans_date = input("날짜(YYYY-MM-DD): ").strip()
    if not trans_date:
        raise BudgetAppError("날짜를 입력해야 합니다.")
    trans_date = validate_date_format(1, trans_date)

    trans_type = input("타입(income/expense): ").strip()
    if not trans_type:
        raise BudgetAppError("거래 타입을 입력해야 합니다.")
    trans_type = validate_transaction_type(trans_type)
    
    trans_category = input("카테고리: ").strip()
    if not trans_category:
        raise BudgetAppError("카테고리를 입력해야 합니다.")
    category_names = {category.name for category in iter_categories()}
    if trans_category not in category_names:
        raise BudgetAppError(
            "존재하지 않는 카테고리입니다.",
            "먼저 category add로 카테고리를 추가해주세요.",
        )

    trans_amount = input("금액(양수): ").strip()
    if not trans_amount:
        raise BudgetAppError("금액을 입력해야 합니다.")
    trans_amount = validate_amount(trans_amount)

    trans_memo = input("메모(선택): ").strip()
    trans_tags = input("태그(쉼표로 구분, 없으면 엔터): ").strip()

    transactions_data = list(iter_transactions())
    trans_id = generate_transaction_id(transactions_data)
    
    new_transaction = Transaction(
        id=trans_id,
        date=trans_date,
        type=trans_type,
        category=trans_category,
        amount=trans_amount,
        memo=trans_memo,
        tags=parse_tags(trans_tags),
    )

    append_transaction(new_transaction)
    
    print(f"[저장 완료] id={new_transaction.id}")
    
    return 0