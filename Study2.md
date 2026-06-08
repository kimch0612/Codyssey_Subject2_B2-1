# B2-1 과제 수행 정리

------

## 과제의 수행 목적

이번 과제의 목적은 단순히 가계부 기능을 만드는 것이 아니다
파일 기반 저장소를 사용하는 작은 콘솔 서비스를 만들면서, 프로그램을 어떻게 나누고, 데이터를 어떻게 안전하게 저장하고, 사용자 입력 오류를 어떻게 처리할지 연습하는 것이다

즉, 핵심은 아래와 같다

```text
터미널 명령어 입력
-> 명령어 해석
-> 사용자 입력 검증
-> 데이터 객체 생성/수정
-> 파일에 영구 저장
-> 결과 출력
```

이 흐름을 한 파일에 몰아넣지 않고, CLI / 서비스 / 저장소 / 데이터 구조 / 공통 도구로 나누어 구현하는 것이 중요하다

이번 과제를 끝내면 아래 내용을 설명할 수 있어야 한다

1. 파일 기반 저장으로 데이터를 영구 보존하는 방법
2. JSONL과 CSV의 차이와 사용 목적
3. dataclass로 데이터 모델을 정의하는 이유
4. generator로 파일을 한 줄씩 처리하는 이유
5. decorator로 공통 예외 처리를 분리하는 이유
6. CLI 인자를 해석하고 기능 함수로 연결하는 방식
7. update/delete에서 전체 재작성과 원자적 교체를 고려하는 이유
8. 오류를 스택트레이스가 아니라 원인과 힌트로 출력하는 방식

## 핵심 키워드

이번 과제에서 반드시 이해해야 할 키워드는 아래와 같다

```text
CLI
argparse
dataclass
type hint
JSONL
CSV
serialization
deserialization
generator
yield
streaming
decorator
exception handling
exit code
atomic replace
CRUD
module separation
```

각 키워드를 이번 과제 기준으로 풀어보면 다음과 같다

CLI는 사용자가 터미널에서 명령어를 입력해 프로그램을 실행하는 방식이다

argparse는 `python -m budget_app list --limit 3` 같은 입력을 Python 코드에서 다룰 수 있는 `args` 객체로 바꿔주는 표준 라이브러리다

dataclass는 `Transaction`, `Category`, `Budget` 같은 데이터 모델을 간결하게 정의하기 위한 도구다

type hint는 함수와 데이터 구조가 어떤 타입을 기대하는지 코드에 표시하는 계약이다

JSONL은 한 줄에 JSON 객체 하나씩 저장하는 파일 형식이다
거래 내역처럼 여러 데이터를 한 줄씩 읽고 쓰기에 적합하다

CSV는 외부 파일과 데이터를 주고받기 위한 표 형식의 텍스트 파일이다
이번 과제에서는 import/export에서 사용한다

serialization은 Python 객체를 파일에 저장 가능한 문자열로 바꾸는 과정이다

deserialization은 파일에서 읽은 문자열을 다시 Python 객체로 복원하는 과정이다

generator와 yield는 데이터를 한 번에 모두 메모리에 올리지 않고, 필요할 때 하나씩 처리하기 위한 방식이다

decorator는 함수의 앞뒤 실행 흐름을 감싸 공통 기능을 붙이는 방식이다
이번 과제에서는 오류 처리를 공통화하는 데 사용한다

exit code는 프로그램이 정상 종료됐는지 오류 종료됐는지를 운영체제에 알려주는 숫자다
정상 종료는 0, 오류 종료는 0이 아닌 값이다

atomic replace는 임시 파일에 새 내용을 다 쓴 뒤, 기존 파일과 한 번에 교체하는 방식이다
파일이 반쯤 써진 상태로 남는 위험을 줄인다

CRUD는 Create, Read, Update, Delete를 뜻한다
이번 과제에서는 거래 추가, 조회, 수정, 삭제가 여기에 해당한다

module separation은 역할별로 파일을 나누는 것이다
한 파일에 모든 기능을 넣는 대신, 수정 이유가 같은 코드끼리 묶는다

## 전체 모듈 구조

이번 과제의 코드는 아래 역할로 나누는 것이 자연스럽다

```text
budget_app/
├── __main__.py        -> python -m budget_app 실행 진입점
├── command.py         -> CLI 명령어와 옵션 처리
├── data_struct.py     -> dataclass 데이터 모델
├── storage.py         -> 파일 I/O, JSONL 직렬화/역직렬화
├── budget_service.py  -> 실제 기능 로직
└── budget_helper.py   -> 검증 함수, 예외 클래스, 데코레이터
```

실행 흐름은 대략 아래와 같다

```text
사용자 명령어
-> __main__.py
-> command.py
-> budget_service.py
-> budget_helper.py / storage.py / data_struct.py
-> 결과 출력
```

각 파일의 책임을 더 자세히 보면 다음과 같다

`__main__.py`는 `python -m budget_app` 실행 시 호출되는 진입점이다
직접 기능을 처리하지 않고 `command.main()`을 호출한다

`command.py`는 명령어를 정의한다
예를 들어 `add`, `list`, `search`, `summary` 같은 명령어와 `--limit`, `--month`, `--from` 같은 옵션을 등록한다

`data_struct.py`는 데이터를 담는 구조를 정의한다
이번 과제에서는 `Transaction`, `Category`, `Budget`이 핵심 데이터 모델이다

`storage.py`는 파일과 직접 대화한다
JSONL 문자열로 바꾸고, 파일에서 한 줄씩 읽고, 임시 파일을 이용해 다시 쓰는 역할을 담당한다

`budget_service.py`는 기능의 실제 흐름을 담당한다
예를 들어 거래 추가 시 입력을 받고, 검증하고, ID를 만들고, 저장하는 흐름이 이 파일에 있다

`budget_helper.py`는 여러 기능에서 공통으로 쓰는 도구를 모아둔다
날짜 검증, 금액 검증, 거래 타입 검증, 에러 처리 데코레이터 등이 여기에 해당한다

## 데이터 구조

이번 과제의 핵심 데이터는 3가지다

```python
Transaction
Category
Budget
```

Transaction은 거래 내역이다

```text
id       -> 거래 고유 ID
type     -> income 또는 expense
date     -> YYYY-MM-DD
amount   -> 양수 정수
category -> 등록된 카테고리명
memo     -> 선택 메모
tags     -> 선택 태그 목록
```

Category는 카테고리다

```text
name -> 카테고리명
```

Budget은 월 예산이다

```text
month  -> YYYY-MM
amount -> 예산 금액
```

이 데이터들은 파일에 직접 객체로 저장되지 않는다
저장할 때는 JSON 문자열로 직렬화되고, 읽을 때는 다시 dataclass 객체로 역직렬화된다

## 저장 파일 구조

과제는 데이터를 3개 이상 파일로 분리해 영구 저장하라고 요구한다

이번 구조에서는 아래처럼 나눈다

```text
data/
├── transactions.jsonl
├── categories.jsonl
└── budgets.jsonl
```

`transactions.jsonl`에는 거래 내역을 저장한다

`categories.jsonl`에는 카테고리 목록을 저장한다

`budgets.jsonl`에는 월별 예산을 저장한다

이렇게 나누는 이유는 데이터의 성격이 다르기 때문이다
거래 내역은 계속 추가되고 검색되는 데이터이고, 카테고리는 거래를 분류하기 위한 기준이며, 예산은 월별 요약에 붙는 별도 설정값이다

## 기능 흐름 1. 초기화

모든 기능은 실제 작업 전에 저장소 초기화를 먼저 수행한다

```text
명령 실행
-> data 디렉터리 확인
-> transactions.jsonl 확인
-> categories.jsonl 확인
-> budgets.jsonl 확인
-> 없으면 생성
-> categories.jsonl이 비어 있으면 기본 카테고리 생성
```

이 단계가 필요한 이유는 처음 실행하는 사용자가 따로 파일을 만들지 않아도 프로그램이 동작해야 하기 때문이다

## 기능 흐름 2. category list

카테고리 목록 조회 흐름은 단순하다

```text
python -m budget_app category list
-> init_storage()
-> iter_categories()
-> 한 줄씩 Category 객체로 복원
-> "- 카테고리명" 형식으로 출력
```

여기서 중요한 점은 category list도 저장 파일에서 데이터를 읽어온다는 것이다
즉, 메모리에 고정된 카테고리 목록을 보여주는 것이 아니라, 실제 저장된 파일 내용을 보여준다

## 기능 흐름 3. category add

카테고리 추가는 대화형 입력 방식이다

```text
python -m budget_app category add
-> init_storage()
-> 기존 카테고리 목록 읽기
-> input("카테고리명: ")
-> 빈 문자열인지 검증
-> 이미 존재하는 카테고리인지 검증
-> Category 객체 생성
-> categories.jsonl 재작성
-> 저장 완료 메시지 출력
```

중복 검사를 하는 이유는 같은 이름의 카테고리가 여러 번 저장되면 거래 검증과 출력이 애매해지기 때문이다

## 기능 흐름 4. category remove

카테고리 삭제는 단순히 카테고리 파일에서 이름을 지우는 것만으로 끝나면 안 된다
거래 내역에서 해당 카테고리를 사용 중일 수 있기 때문이다

```text
python -m budget_app category remove
-> init_storage()
-> 삭제할 카테고리명 입력
-> 카테고리 존재 여부 확인
-> transactions.jsonl을 순회하며 사용 중인지 확인
-> 사용 중이면 삭제 중단
-> 사용 중이 아니면 categories.jsonl 재작성
-> 삭제 완료 메시지 출력
```

이 흐름은 데이터 일관성을 지키기 위한 것이다
거래가 `food` 카테고리를 사용 중인데 `food` 카테고리를 삭제하면, 나중에 search나 summary에서 기준이 깨질 수 있다

## 기능 흐름 5. add

거래 추가는 이번 과제의 기본 CRUD 중 Create에 해당한다

```text
python -m budget_app add
-> init_storage()
-> 날짜 입력
-> 타입 입력
-> 카테고리 입력
-> 금액 입력
-> 메모 입력
-> 태그 입력
-> 날짜 검증
-> 타입 검증
-> 카테고리 존재 검증
-> 금액 검증
-> 새 거래 ID 생성
-> Transaction 객체 생성
-> transactions.jsonl 저장
-> 생성된 ID 출력
```

여기서 검증 순서가 중요하다
잘못된 데이터가 저장 파일에 들어가면 이후 기능이 복잡해진다
그래서 저장 전에 입력값을 최대한 확인한다

태그는 쉼표로 입력받은 문자열을 리스트로 바꾼다

```text
"meal, friend" -> ["meal", "friend"]
```

## 기능 흐름 6. list

거래 목록 조회는 Read에 해당한다

```text
python -m budget_app list --limit 3
-> init_storage()
-> --limit 값 검증
-> iter_transactions()로 거래 파일을 한 줄씩 읽기
-> 최신 N개 선택
-> 거래 라인 출력
```

과제에서 list는 스트리밍 처리를 요구한다
그래서 파일을 읽는 기본 방식은 generator여야 한다

다만 최신순으로 N개만 출력해야 하므로 단순히 앞에서 N개를 출력하면 안 된다
파일 전체에서 최신 N개를 골라야 한다

이때 `heapq.nlargest()` 같은 방식을 사용하면 전체 정렬보다 더 적은 비용으로 최신 N개를 선택할 수 있다

## 기능 흐름 7. search

거래 검색은 조건 기반 Read다

```text
python -m budget_app search --category food
python -m budget_app search --from 2024-01-01 --to 2024-01-31
python -m budget_app search --type expense
python -m budget_app search --q 점심
python -m budget_app search --tag meal
```

처리 흐름은 아래와 같다

```text
명령 실행
-> init_storage()
-> 검색 옵션 검증
-> 거래 파일을 generator로 읽기
-> 조건에 맞지 않는 거래는 건너뛰기
-> 조건에 맞는 거래만 출력
```

검색 조건은 여러 개가 동시에 올 수 있다

```text
--from / --to  -> 기간 조건
--category     -> 카테고리 조건
--type         -> income 또는 expense
--q            -> 메모 키워드
--tag          -> 태그 조건
```

최신순 출력과 스트리밍 처리를 동시에 만족하려면 정렬 방식에 주의해야 한다
`sorted()`를 사용하면 검색 결과 전체를 메모리에 모으게 된다
그래서 파일을 날짜순으로 저장하고, 검색 시 역방향 generator로 읽는 방식을 사용할 수 있다

## 기능 흐름 8. update

거래 수정은 CRUD 중 Update에 해당한다
이번 구조에서는 옵션 기반 방식으로 고정한다

```bash
python -m budget_app update --id TX-000001 --amount 20000 --memo 저녁
```

처리 흐름은 아래와 같다

```text
명령 실행
-> init_storage()
-> transactions.jsonl 읽기
-> --id에 해당하는 거래 찾기
-> 수정 옵션이 1개 이상 있는지 확인
-> 입력된 필드만 검증 후 수정
-> 전체 거래 목록 재작성
-> 수정 완료 메시지 출력
```

JSONL은 파일 중간의 특정 줄만 바꾸는 데 적합하지 않다
그래서 수정이 필요한 경우 새 파일을 다시 쓰고, 기존 파일과 교체하는 방식이 자연스럽다

존재하지 않는 id는 “없는 데이터”로 처리해야 한다
즉, 조용히 넘어가면 안 되고 사용자에게 오류 메시지를 출력해야 한다

## 기능 흐름 9. delete

거래 삭제는 CRUD 중 Delete에 해당한다

```bash
python -m budget_app delete --id TX-000001
```

처리 흐름은 아래와 같다

```text
명령 실행
-> init_storage()
-> transactions.jsonl 읽기
-> 삭제할 id가 존재하는지 확인
-> 해당 id를 제외한 거래 흐름 생성
-> transactions.jsonl 재작성
-> 삭제 완료 메시지 출력
```

삭제 역시 파일 중간의 한 줄을 직접 지우기보다는, 삭제 대상만 제외한 새 내용을 임시 파일에 쓰고 교체하는 방식이 안정적이다

## 기능 흐름 10. budget set

예산 설정은 월별 예산 데이터를 저장하는 기능이다

```bash
python -m budget_app budget set --month 2024-01 --amount 500000
```

처리 흐름은 아래와 같다

```text
명령 실행
-> init_storage()
-> --month 형식 검증
-> --amount 검증
-> 기존 budgets.jsonl 읽기
-> 같은 month가 있으면 amount 수정
-> 없으면 새 Budget 추가
-> budgets.jsonl 재작성
-> 저장 완료 메시지 출력
```

예산 자체는 summary에서 사용된다
즉, budget set은 데이터를 저장하는 기능이고, 예산 사용률 계산은 summary에서 수행한다

## 기능 흐름 11. summary

summary는 특정 월의 가계부 상태를 요약하는 기능이다

```bash
python -m budget_app summary --month 2024-01 --top 3
```

처리 흐름은 아래와 같다

```text
명령 실행
-> init_storage()
-> --month 검증
-> --top 검증
-> transactions.jsonl을 한 줄씩 순회
-> 해당 월 거래만 선택
-> income은 총 수입에 더하기
-> expense는 총 지출에 더하기
-> expense는 카테고리별 합계에도 더하기
-> 총 수입 / 총 지출 / 잔액 출력
-> budgets.jsonl에서 해당 월 예산 확인
-> 예산이 있으면 사용률과 초과 경고 출력
-> 지출 TOP N 출력
```

summary는 단순 조회보다 계산이 많다
하지만 거래를 순회하면서 합계를 누적하면 되므로, 거래 전체를 리스트로 만들 필요는 없다

데이터가 없는 달은 “데이터 없음”을 명확히 출력해야 한다

## 기능 흐름 12. import

import는 외부 CSV 파일을 읽어서 거래로 등록하는 기능이다

```bash
python -m budget_app import --from import.csv
```

CSV 최소 스키마는 아래와 같다

```text
date,type,category,amount,memo,tags
```

처리 흐름은 아래와 같다

```text
명령 실행
-> init_storage()
-> CSV 파일 존재 확인
-> CSV 헤더 확인
-> 한 줄씩 읽기
-> 날짜/타입/카테고리/금액 검증
-> 새 거래 ID 생성
-> Transaction 객체 생성
-> 유효한 거래는 저장 대상에 추가
-> 실패한 row는 skipped로 계산
-> transactions.jsonl에 반영
-> imported/skipped 건수 출력
```

import에서 중요한 점은 CSV라고 해서 아무 데이터를 그대로 받아들이면 안 된다는 것이다
외부 파일에서 들어온 데이터도 사용자가 직접 입력한 데이터와 똑같이 검증해야 한다

## 기능 흐름 13. export

export는 저장된 거래를 CSV 파일로 내보내는 기능이다

```bash
python -m budget_app export --out export.csv --month 2024-01
python -m budget_app export --out export.csv --from 2024-01-01 --to 2024-01-31
```

처리 흐름은 아래와 같다

```text
명령 실행
-> init_storage()
-> --out 확인
-> --month 또는 --from/--to 조건 확인
-> 조건 날짜 형식 검증
-> transactions.jsonl을 한 줄씩 읽기
-> 조건에 맞는 거래만 CSV row로 쓰기
-> 처리 건수 출력
```

과제에서는 export 조건을 필수로 요구한다
즉, 아무 조건 없이 전체 거래를 내보내는 방식은 과제 요구와 맞지 않는다

## 오류 처리 흐름

오류 처리는 각 기능마다 따로 try/except를 작성하지 않고 데코레이터로 공통 처리한다

```text
기능 함수 실행
-> 정상 처리면 0 반환
-> BudgetAppError 발생
-> [오류] 원인 출력
-> [힌트] 해결 방향 출력
-> 1 반환
```

이 방식의 장점은 기능 함수가 핵심 로직에 집중할 수 있다는 것이다

예를 들어 add 함수 안에서는 아래처럼 쓰면 된다

```python
if not category:
    raise BudgetAppError("카테고리를 입력해야 합니다.")
```

출력 형식과 종료 코드는 데코레이터가 담당한다

argparse에서 발생하는 옵션 누락 오류도 사용자 입장에서는 앱 오류다
그래서 이 경우에도 스택트레이스 대신 사용법과 힌트를 출력하는 것이 좋다

## 구현 순서 정리

이번 과제를 처음부터 구현한다면 아래 순서가 가장 자연스럽다

1. `data_struct.py`에서 `Transaction`, `Category`, `Budget` 정의
2. `storage.py`에서 JSONL 직렬화/역직렬화 구현
3. `storage.py`에서 저장 파일 초기화 구현
4. `budget_helper.py`에서 검증 함수와 오류 처리 데코레이터 구현
5. `command.py`에서 CLI 명령어 뼈대 구성
6. `category list/add/remove` 구현
7. `add` 구현
8. `list` 구현
9. `search` 구현
10. `update/delete` 구현
11. `budget set` 구현
12. `summary` 구현
13. `import/export` 구현
14. README와 학습 문서 정리
15. 임시 data-dir로 전체 기능 테스트

이 순서가 좋은 이유는 뒤 기능이 앞 기능에 의존하기 때문이다

예를 들어 거래 추가를 하려면 카테고리가 있어야 한다
검색과 요약을 하려면 거래 데이터가 있어야 한다
예산 사용률을 보려면 budget set이 먼저 있어야 한다
import/export는 데이터 모델, 저장소, 검증 로직이 모두 준비된 뒤 구현하는 것이 편하다

## 최종적으로 확인해야 할 것

과제를 제출하기 전에 아래 항목을 확인해야 한다

```text
python -m budget_app --help
python -m budget_app add
python -m budget_app list --limit 3
python -m budget_app search --category food
python -m budget_app update --id TX-000001 --memo test
python -m budget_app delete --id TX-000001
python -m budget_app category list
python -m budget_app budget set --month 2024-01 --amount 500000
python -m budget_app summary --month 2024-01 --top 3
python -m budget_app import --from import.csv
python -m budget_app export --out export.csv --month 2024-01
```

또한 아래 조건도 확인해야 한다

1. 저장 파일이 3개로 나뉘어 있는가
2. `--help`가 모든 명령에서 동작하는가
3. 옵션 표기가 `--`로 통일되어 있는가
4. 잘못된 입력에서 스택트레이스가 출력되지 않는가
5. 오류 종료 시 exit code가 0이 아닌가
6. list/search가 generator 기반 흐름을 유지하는가
7. update/delete가 임시 파일 재작성과 교체 방식으로 처리되는가
8. README에 실행 방법, 저장 파일, 주요 명령, CSV 스키마가 있는가

이 과제는 기능 개수보다 구조가 더 중요하다
기능이 동작하는 것에서 끝나는 게 아니라, 왜 이 파일에 이 코드가 있어야 하는지 설명할 수 있어야 한다
