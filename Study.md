공부 노트
------

### 데코레이터와 클래스 상속의 차이점

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

### 파일의 원자적 쓰기

핵심 키워드는 inode와 파일 시스템

원자적 쓰기는 파일 내용 자체를 덮어쓰는 게 아니라, 디렉터리 엔트리의 이름 -> 실제 파일 객체 매핑을 새 파일 쪽으로 원자적으로 바꾼다고 보면 된다
예를 들어서 아래와 같은 구조가 있다고 가정하자
```
transactions.jsonl  -> inode A
transactions.tmp    -> inode B
```

os.replace를 통해 tmp 파일을 jsonl로 바꾸려고 시도를 하게 되면, 파일 시스템에선 아래와 같이 구조가 변경되게 된다
```
transactions.jsonl  -> inode B
inode A는 이름에서 떨어짐
```

즉, 기존 transactions.jsonl 파일 내부를 한 줄씩 덮어쓰는 게 아니라, 파일 이름이 가리키는 대상(포인터)이 통째로 교체되는 방식이다
이를 통해 얻는 이득은, 프로세스가 old 파일 또는 new 파일 둘 중 하나만 본다는 것이다
중간에 반쯤 써진 파일을 보지 않는다

단, 원자적 쓰기엔 다음과 같은 조건이 존재한다
1. 같은 파일 시스템/같은 드라이브 안에서 교체해야 원자적이다.
2. 교체 대상은 파일 단위로 바뀌는 것이지, 여러 파일 묶음이 한 번에 바뀌는 것은 아니다.
3. 원자적 교체와 디스크 영구 반영은 다르다.
4. 이미 파일을 열고 있던 프로세스는 예전 파일을 계속 볼 수 있다.

1번의 경우에는 inode를 갈아치우는 방식은 같은 FS, 드라이브 내에 있어야만 성립한다
만약 다른 FS, 드라이브에 저장하는 경우, OS가 내부적으로 파일을 다른 드라이브에 복사 및 삭제 처리하는 방식으로 동작하기 때문에 원자적 쓰기라고 볼 수 없다

2번의 경우엔 transactions.jsonl 파일 하나를 RW하는 경우엔 원자적 쓰기를 보장할 수 있지만, categories.jsonl와 budgets.jsonl 파일까지 한꺼번에 수정하려고 하면 다음과 같은 문제가 발생할 수 있다
아래와 같은 방식으로 파일을 수정한다고 해보자
```python
os.replace("transactions.tmp", "transactions.jsonl")
os.replace("categories.tmp", "categories.jsonl")
os.replace("budgets.tmp", "budgets.jsonl")
```

첫번째 파일이 교체된 이후에 두번째 파일을 수정하는 단계에서 프로세스가 죽으면? 아래와 같은 구조가 될 수 있다
```
transactions.jsonl -> 새 버전
categories.jsonl   -> 예전 버전
budgets.jsonl      -> 예전 버전
```

즉, 파일 하나하나는 안전하게 교체됐지만, “세 파일 전체가 하나의 트랜잭션처럼 같이 성공하거나 같이 실패한다”는 보장이 없다
그렇기에 아래와 같은 전략을 사용한다
1. 여러 파일 사이의 강한 일관성이 필요 없게 설계한다.
2. 변경 순서를 조심해서 정한다.
3. backup/journal 파일을 둔다.
4. manifest 파일 하나가 현재 유효한 데이터 버전을 가리키게 한다.
5. 정말 복잡하면 SQLite 같은 DB를 쓴다.

3번의 경우엔 
"다른 프로세스가 볼 때 파일이 반쯤 바뀐 상태로 보이지 않는다. old 파일 또는 new 파일 둘 중 하나만 보인다." 이 말이 곧
"전원이 갑자기 나가도 새 파일이 반드시 디스크에 안전하게 남는다."를 의미하진 않는다
운영체제는 파일 쓰기를 바로 디스크에 박아 넣지 않고, 보통 메모리의 page cache에 먼저 저장했다가 나중에 적절한 시점이 되면 디스크에 flush를 한다
그래서 안전하게 쓰기 위해선 아래와 같은 구조를 가져야 한다
```python
with open(tmp_path, "w", encoding="utf-8") as f:
    f.write(content)
    f.flush()
    os.fsync(f.fileno())

os.replace(tmp_path, target_path)
```

4번은 간단한 문제다
우리는 코드로 "transactions.jsonl" 파일을 open하라고 짜지만, 실제 컴퓨터는 해당 파일이 있는 주소(inode)를 바라보고 있다고 보면 된다
그렇기 때문에 파일 원자적 쓰기를 통해 동일한 파일명, 다른 inode를 가지게 된 경우, 예전에 돌고 있던 프로세스는 구버전 inode를 보게 되고, 그렇기 때문에 예전 파일을 보는 문제가 발생할 수 있다
그리고 맥/리눅스의 경우엔 상관 없지만, 윈도우 환경에선 old 버전의 파일을 누가 lock을 걸고 선점하고 있다면, Permission Denied 문제가 발생하면서 원자적 쓰기에 문제가 발생할 수도 있다

### JSONL과 직렬화/역직렬화

이번 과제에서 저장 포맷으로 JSONL을 사용한다면 핵심은 “객체를 파일에 바로 저장할 수 없으니, 문자열로 바꿔서 저장하고 다시 객체로 복원한다”는 것이다

Python 객체는 대충 이런 구조다
```python
Transaction(
    id="TX-000001",
    type="expense",
    date="2024-01-15",
    amount=15000,
    category="food",
    memo="점심",
    tags=["meal"],
)
```

하지만 파일에는 객체 자체가 아니라 문자열만 저장된다
그래서 저장할 때는 아래처럼 JSON 문자열로 바꾼다
```python
{"id": "TX-000001", "type": "expense", "date": "2024-01-15", "amount": 15000, "category": "food", "memo": "점심", "tags": ["meal"]}
```

이 과정을 직렬화라고 한다
반대로 파일에서 읽은 JSON 문자열을 다시 Transaction 객체로 바꾸는 과정을 역직렬화라고 한다

```python
def serialize_transaction(transaction: Transaction) -> str:
    return json.dumps(asdict(transaction), ensure_ascii=False)


def deserialize_transaction(jsonl_str: str) -> Transaction:
    data = json.loads(jsonl_str)
    return Transaction(**data)
```

여기서 JSONL은 JSON Line의 줄임말이다
하나의 파일 전체가 커다란 JSON 배열인 게 아니라, 한 줄에 JSON 객체 하나씩 저장하는 방식이다

```json
{"id": "TX-000001", "type": "expense", "date": "2024-01-15", "amount": 15000}
{"id": "TX-000002", "type": "income", "date": "2024-01-16", "amount": 3000000}
```

이 방식의 장점은 파일을 한 줄씩 읽을 수 있다는 것이다
즉, 전체 파일을 메모리에 올리지 않고도 거래를 하나씩 처리할 수 있다

### dataclass와 타입 힌트

dataclass는 데이터를 담기 위한 클래스를 간단하게 만들 수 있게 해준다

일반 클래스로 쓰면 아래와 같이 직접 생성자를 작성해야 한다
```python
class Transaction:
    def __init__(self, id, type, date, amount, category, memo, tags):
        self.id = id
        self.type = type
        self.date = date
        self.amount = amount
        self.category = category
        self.memo = memo
        self.tags = tags
```

dataclass를 사용하면 아래처럼 데이터 구조에만 집중할 수 있다
```python
@dataclass
class Transaction:
    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)
```

여기서 중요한 점은 타입 힌트가 런타임 검증을 자동으로 해주는 것은 아니라는 점이다
예를 들어 amount: int라고 적어도, 사용자가 문자열을 넣는 상황 자체를 Python이 자동으로 막아주지는 않는다

그래서 과제에서는 타입 힌트와 입력 검증을 둘 다 사용해야 한다
```python
amount = validate_amount(input("금액(양수): "))
```

즉,
타입 힌트: 이 데이터가 어떤 형태여야 하는지 코드에 표시하는 계약
입력 검증: 실제 입력값이 그 계약에 맞는지 확인하는 실행 로직

그리고 list 같은 mutable 객체는 기본값을 그냥 []로 두면 안 된다
여러 객체가 같은 리스트를 공유할 수 있기 때문이다
그래서 dataclass에서는 아래처럼 작성한다

```python
tags: list[str] = field(default_factory=list)
```

### generator와 yield

generator는 데이터를 한 번에 전부 만들어서 돌려주는 게 아니라, 필요할 때 하나씩 만들어서 넘겨주는 객체다

일반적인 list 방식은 아래와 같다
```python
def load_transactions():
    transactions = []
    for line in file:
        transactions.append(deserialize_transaction(line))
    return transactions
```

이 방식은 파일이 커질수록 메모리에 부담이 생긴다
반면 yield를 사용하면 아래처럼 동작한다

```python
def iter_transactions():
    for line in file:
        yield deserialize_transaction(line)
```

이 함수는 실행되자마자 모든 거래를 읽는 것이 아니다
for문에서 다음 값이 필요할 때마다 한 줄씩 읽고, yield 지점에서 값을 넘긴 뒤 잠시 멈춘다

```python
for transaction in iter_transactions():
    print(transaction)
```

즉, generator의 핵심은 “전체 목록”이 아니라 “흐름”이다

다만 generator를 사용했다고 해서 무조건 스트리밍 처리가 유지되는 것은 아니다
아래처럼 쓰면 결국 전체 데이터를 메모리에 모으게 된다

```python
transactions = list(iter_transactions())
matches = sorted(iter_transactions())
```

그래서 list/search 같은 기능에서는 조심해야 한다
이번 과제에서 list는 최신 N개만 필요하므로 heapq.nlargest 같은 방식을 사용할 수 있고, search는 최신순 출력을 위해 파일 저장 순서나 역방향 읽기 전략을 같이 고민해야 한다

### 최신순 출력과 파일 저장 순서

가계부에서 최신순이란 보통 date가 큰 거래가 먼저 나온다는 뜻이다
예를 들어 아래 두 거래가 있다면 2024-02-01이 먼저 출력되어야 한다

```text
TX-000001 | 2024-02-01 | expense | food | 2000
TX-000002 | 2024-01-01 | expense | food | 1000
```

그런데 파일은 기본적으로 앞에서 뒤로 읽는다
만약 파일이 오래된 거래부터 최신 거래 순서로 정렬되어 있다면, 파일을 뒤에서 앞으로 읽는 방식으로 최신순 출력이 가능하다

```text
transactions.jsonl
1번째 줄: 2024-01-01 거래
2번째 줄: 2024-02-01 거래
```

이 파일을 역방향 generator로 읽으면 아래 순서가 된다

```text
2024-02-01 거래
2024-01-01 거래
```

이렇게 하면 search 결과를 sorted로 전부 모아서 정렬하지 않아도, 읽는 흐름 자체가 최신순이 된다
즉, “데이터를 어떤 순서로 저장할 것인가”도 스트리밍 처리에 영향을 준다

### argparse와 명령어 구조

argparse는 터미널 명령어를 Python 객체로 바꿔주는 표준 라이브러리다

터미널에서 아래처럼 입력하면
```bash
python -m budget_app list --limit 3
```

argparse는 대략 이런 형태로 해석한다
```python
args.command == "list"
args.limit == 3
```

그리고 set_defaults를 사용하면 명령어와 실행 함수를 연결할 수 있다
```python
list_parser.set_defaults(handler=run_transaction_list)
```

이후 main에서는 handler만 실행하면 된다
```python
handler = getattr(args, "handler", None)
return handler(args)
```

이 구조의 장점은 command.py가 실제 기능을 직접 구현하지 않아도 된다는 것이다
command.py는 “명령어를 해석하고 알맞은 함수로 연결하는 역할”만 담당한다

### 계층 분리

이번 과제는 한 파일에 모든 코드를 몰아넣지 말고, 역할별로 모듈을 나누는 것이 중요하다

현재 구조를 기준으로 보면 대략 아래처럼 나뉜다

```text
command.py        -> CLI 인자 처리
data_struct.py    -> dataclass 데이터 구조
storage.py        -> 파일 I/O, 직렬화, 역직렬화
budget_service.py -> 실제 기능 로직
budget_helper.py  -> 검증, 에러 처리 데코레이터, 공통 도구
```

이 분리의 핵심은 “수정 이유가 같은 코드끼리 모아둔다”는 것이다

예를 들어 저장 포맷을 JSONL에서 CSV로 바꾸고 싶다면 storage.py 중심으로 수정해야 한다
거래 추가 방식을 바꾸고 싶다면 budget_service.py를 수정해야 한다
명령어 옵션 이름을 바꾸고 싶다면 command.py를 수정해야 한다

이렇게 나누면 코드가 많아져도 어디를 봐야 하는지 덜 헷갈린다

### 입력 검증과 도메인 오류

가계부 앱에서 사용자가 잘못 입력할 수 있는 값은 많다

```text
날짜: 2024-13-40
금액: -1000
타입: spend
카테고리: 등록되지 않은 값
```

이런 값을 그대로 저장하면 나중에 summary나 search 같은 기능이 깨질 수 있다
그래서 저장 전에 검증해야 한다

```python
date = validate_date_format(1, date)
amount = validate_amount(amount)
transaction_type = validate_transaction_type(transaction_type)
```

여기서 단순히 ValueError를 그대로 터뜨리면 사용자는 내부 코드 흐름을 보게 된다
과제에서는 스택트레이스가 아니라 원인과 힌트를 출력하라고 했기 때문에, 앱 전용 오류 클래스를 두는 것이 좋다

```python
raise BudgetAppError(
    "금액은 양수여야 합니다.",
    "0보다 큰 숫자를 입력해주세요.",
)
```

그리고 데코레이터에서 이 오류를 공통으로 처리하면 각 기능 함수마다 try/except를 반복해서 쓰지 않아도 된다

```python
@error_handler
def run_transaction_add(args) -> int:
    ...
```

### import/export와 CSV

이번 과제에서 메인 저장 방식은 JSONL이지만, import/export는 CSV를 사용한다
즉, JSONL은 프로그램 내부 저장용이고 CSV는 외부 파일과 주고받기 위한 형식이다

CSV는 표처럼 생긴 텍스트 파일이다

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,점심,meal
```

여기서 첫 줄은 헤더다
과제에서 고정한 최소 스키마는 아래와 같다

```text
date, type, category, amount, memo, tags
```

import를 할 때는 CSV 한 줄을 읽어서 Transaction 객체로 바꾼다
이때도 날짜, 타입, 금액, 카테고리를 검증해야 한다

export를 할 때는 반대로 Transaction 객체를 CSV 한 줄로 바꿔서 쓴다

즉,
import: CSV -> Transaction -> JSONL 저장
export: JSONL 읽기 -> Transaction -> CSV

### update/delete와 전체 재작성

JSONL은 append에는 편하지만, 중간의 특정 줄만 수정하거나 삭제하는 데에는 불편하다

예를 들어 TX-000003만 삭제하고 싶어도 파일 중간의 한 줄을 안전하게 빼내는 작업은 생각보다 까다롭다
그래서 보통 아래 방식으로 처리한다

1. 기존 파일을 읽는다.
2. 수정 또는 삭제가 반영된 새 데이터 흐름을 만든다.
3. 임시 파일에 새 내용을 전부 쓴다.
4. os.replace로 원래 파일과 교체한다.

개념적으로는 아래와 같다

```python
new_transactions = (
    transaction
    for transaction in iter_transactions()
    if transaction.id != target_id
)
rewrite_transactions(new_transactions)
```

이 방식은 “한 줄만 고치는 것”보다 비용은 더 들지만, 파일 기반 저장에서는 구조가 단순하고 안정적이다
그래서 update/delete 같은 기능에서는 전체 재작성과 원자적 교체를 같이 사용하는 것이 자연스럽다
