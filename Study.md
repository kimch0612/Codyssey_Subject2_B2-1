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
