공부 노트
------

#### 데코레이터와 클래스 상속의 차이점

클래스 상속은 아래와 같은 구조다
```python
class Repository:
    def ensure_file_exists(self):
        ...

class TransactionRepository(Repository):
    def save(self, transaction):
        ...
```
이 구조의 경우 TransactionRepository는 Repository의 한 종류라고 말할 수 있다

데코레이터는 대충 이런 구조다
```python
def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print(f"[오류] {e}")
            return 1
    return wrapper


@handle_errors
def add_transaction():
    ...
```
데코레이터를 사용했다고 해서 add_transaction이 handle_errors의 한 종류가 되는 건 아니다
add_transaction 함수를 실행할 때 앞뒤로 예외 처리 기능을 감싸는 기능을 제공할 뿐이다

즉,
상속: 기능을 물려받아서 객체 구조를 만든다
데코레이터: 기존 함수의 실행 흐름을 감싸서 기능을 덧붙인다

데코레이터를 사용하지 않고 클래스 상속 방식으로도 기능을 구현할 수는 있으나, add, list, summary 같은 명령을 전부 클래스로 만들어야 해서 구조가 무거워지고, 비효율적이게 된다