from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import Any


def measure_time(func: Callable[..., int]) -> Callable[..., int]:
    """정수 종료 코드를 반환하는 함수의 실행 시간을 출력한다."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> int:
        started = perf_counter()
        result = func(*args, **kwargs)
        elapsed = perf_counter() - started

        print(f"[실행 시간] {elapsed:.3f}초")
        return result

    return wrapper

def input_interrupt(func: Callable[..., int]) -> Callable[..., int]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> int:
        try:
            result = func(*args, **kwargs)
            return result
        except EOFError:
            print("[오류] 입력이 종료되어 작업을 완료하지 못했습니다.")
            print("[힌트] 명령을 다시 실행하고 필요한 값을 입력하세요.")
            return 1 
        except KeyboardInterrupt:
            print("[오류] 입력이 종료되어 작업을 완료하지 못했습니다.")
            print("[힌트] 명령을 다시 실행하고 필요한 값을 입력하세요.")
            return 1
    
    return wrapper
    