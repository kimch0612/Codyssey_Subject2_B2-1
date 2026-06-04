"""데코레이터, 검증 함수 등 서비스에 필요로 하는 함수를 모아둔 파일"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from datetime import datetime


P = ParamSpec("P")
R = TypeVar("R")

class BudgetAppError(Exception):
    # General하게 에러/예외를 출력해주는 클래스. 적절하게 상속받아서 쓰자.
    def __init__(self, message: str, hint: str = ""):
        self.message = message
        self.hint = hint
        super().__init__(message)

def passthrough(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    return wrapper

################# 데코레이터 함수 파트 #################

def error_handler(func: Callable[P, R]) -> Callable[P, R]:
    # 예외 처리를 담당하는 데코레이터 함수
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except BudgetAppError as e:
            print(f"[오류] {e.message}")
            if e.hint: print(f"[힌트] {e.hint}")
            return 1
        except Exception as e:
            print(f"[오류] 핸들링되지 않은 에러가 발생했습니다: {e}")
            return 1

    return wrapper

################# 검증 함수 파트 #################

def validate_date_format(mode: int, date_str: str) -> str:
    # 날짜 데이터의 형식이 올바른지 검증하는 함수
    # mode: 1 -> YYYY-MM-DD, 2 -> YYYY-MM
    date_str = date_str.strip()

    if mode == 1:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise BudgetAppError(f"날짜 형식이 올바르지 않거나 존재하지 않는 날짜입니다.", hint="YYYY-MM-DD 형식으로 입력해주세요.")
        if len(date_str) != 10 or date_str[4] != '-' or date_str[7] != '-':
            raise BudgetAppError(f"날짜 형식이 올바르지 않습니다.", hint="YYYY-MM-DD 형식으로 입력해주세요.")
    elif mode == 2:
        try:
            datetime.strptime(date_str, "%Y-%m")
        except ValueError:
            raise BudgetAppError(f"날짜 형식이 올바르지 않거나 존재하지 않는 날짜입니다.", hint="YYYY-MM 형식으로 입력해주세요.")
        if len(date_str) != 7 or date_str[4] != '-':
            raise BudgetAppError(f"날짜 형식이 올바르지 않습니다.", hint="YYYY-MM 형식으로 입력해주세요.")
    else:
        raise BudgetAppError(f"validate_date_format에 알 수 없는 mode 값이 들어왔다.\n발생해서는 안 되는 오류. mode: {mode}")
    
    return date_str

def validate_amount(amount_str: str) -> int:
    # 금액이 양수인지 검증하는 함수
    amount_str = amount_str.strip()

    if not amount_str.isdigit():
        raise BudgetAppError("금액은 숫자로만 이루어져있어야 합니다.", hint="숫자만 입력해주세요.")
    amount = int(amount_str)
    if amount <= 0:
        raise BudgetAppError("금액은 양수여야 합니다.", hint="0보다 큰 숫자를 입력해주세요.")
    return amount

def validate_transaction_type(transaction_type: str) -> str:
    # transaction_type이 income, expense 중 하나인지 검증하는 함수
    transaction_type = transaction_type.strip().lower()
    
    if transaction_type not in {"income", "expense"}:
        raise BudgetAppError("거래 유형은 'income' 또는 'expense'이어야 합니다.", hint="거래 유형으로 'income' 또는 'expense'를 입력해주세요.")
    return transaction_type

################# 헬퍼 함수 파트 #################

def parse_tags(tags_str: str) -> list[str]:
    # 태그 문자열을 리스트로 변환하는 함수
    # "식비, 영화, 월정액" -> ["식비", "영화", "월정액"]
    return [tag.strip() for tag in tags_str.split(",") if tag.strip()]
