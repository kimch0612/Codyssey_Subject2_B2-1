# 파일 기반 가계부 콘솔 프로그램 만들기

## 미션 개요

Python 표준 라이브러리만 사용해 파일 기반 가계부 콘솔 프로그램을 구현했다. 거래, 카테고리, 예산 데이터를 JSONL 파일로 분리 저장하고, CLI 명령으로 추가/조회/검색/요약/수정/삭제/import/export를 수행한다.

## 실행 방법

```bash
python -m budget_app <command> [options]
```

모든 명령은 `--help`를 지원한다.

```bash
python -m budget_app --help
python -m budget_app list --help
python -m budget_app category add --help
```

기본 저장 디렉터리는 `./data`이며, 각 명령에서 `--data-dir <dir>`로 변경할 수 있다.

## 저장 파일

저장 포맷은 JSONL이다. 한 줄에 JSON 객체 하나를 저장한다.

```text
data/
├── transactions.jsonl
├── categories.jsonl
└── budgets.jsonl
```

초기 실행 시 저장 디렉터리와 3개 파일이 자동 생성된다. `categories.jsonl`이 비어 있으면 기본 카테고리 `외식`, `교통비`, `쇼핑`, `월급`, `기타`를 자동 생성한다.

## 모듈 구조

```text
budget_app/
├── __main__.py
├── command.py
├── data_struct.py
├── storage.py
├── budget_service.py
└── budget_helper.py
```

- `command.py`: `argparse` 기반 CLI 명령과 옵션 연결
- `data_struct.py`: `Transaction`, `Category`, `Budget` dataclass 정의
- `storage.py`: JSONL 직렬화/역직렬화, 파일 I/O, generator, 원자적 재작성
- `budget_service.py`: 카테고리/거래/예산/요약/import/export 서비스 로직
- `budget_helper.py`: 검증 함수, 태그 파싱, 예외 처리 데코레이터

## 주요 명령

### 거래 추가

```bash
python -m budget_app add
```

대화형으로 날짜, 타입, 카테고리, 금액, 메모, 태그를 입력한다.

```text
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: 외식
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000001
```

### 거래 목록

```bash
python -m budget_app list --limit 3
```

최신순으로 출력한다.

```text
TX-000003 | 2024-01-15 | expense | food | 15000 | lunch
TX-000002 | 2024-01-14 | income  | salary | 3000000 |
TX-000001 | 2024-01-12 | expense | transport | 20000 |
```

### 거래 검색

```bash
python -m budget_app search --from 2024-01-01 --to 2024-01-31
python -m budget_app search --category 외식
python -m budget_app search --type expense
python -m budget_app search --q 점심
python -m budget_app search --tag meal
```

### 거래 수정

`update`는 옵션 기반 방식으로 고정했다.

```bash
python -m budget_app update --id TX-000001 --amount 20000 --memo 저녁
python -m budget_app update --id TX-000001 --date 2024-01-16 --type expense --category 외식 --tags dinner,meal
```

### 거래 삭제

```bash
python -m budget_app delete --id TX-000001
```

존재하지 않는 id는 오류 메시지로 처리한다.

### 월별 요약

```bash
python -m budget_app summary --month 2024-01 --top 3
```

총 수입, 총 지출, 잔액, 카테고리별 지출 TOP N을 출력한다. 예산이 설정된 달이면 예산 사용률과 초과 경고도 함께 출력한다.

### 예산 설정

```bash
python -m budget_app budget set --month 2024-01 --amount 500000
```

### 카테고리 관리

```bash
python -m budget_app category add
python -m budget_app category list
python -m budget_app category remove
```

카테고리 삭제 시 해당 카테고리를 사용하는 거래가 있으면 삭제를 막는다.

## Import / Export CSV 스키마

CSV는 UTF-8, 헤더 포함 형식이다.

| column | required | 설명 |
| --- | --- | --- |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` 또는 `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양수 정수 |
| `memo` | N | 문자열 |
| `tags` | N | 쉼표로 구분한 문자열 |

### 가져오기

```bash
python -m budget_app import --from import.csv
```

### 내보내기

```bash
python -m budget_app export --out export.csv --month 2024-01
python -m budget_app export --out export.csv --from 2024-01-01 --to 2024-01-31
```

`export`는 `--month` 또는 `--from`/`--to` 조건이 필요하다.

## 구현 포인트

- `iter_transactions()`와 `iter_transactions_reverse()`는 `yield` 기반 generator로 거래 파일을 한 줄씩 읽는다.
- `list`는 generator를 기반으로 최신 N개만 선택해 `--limit`을 처리한다.
- `search`는 거래 파일을 역방향 generator로 읽어 전체 검색 결과를 한 번에 정렬하지 않고 최신순으로 출력한다.
- `rewrite_jsonl_file()`은 임시 파일에 기록한 뒤 `replace()`로 교체해 update/delete 저장 안정성을 높였다.
- `error_handler` 데코레이터는 `BudgetAppError`를 잡아 `[오류]`, `[힌트]` 형식으로 출력하고 오류 종료 코드 `1`을 반환한다.
- `Transaction`, `Category`, `Budget`은 dataclass와 타입 힌트로 데이터 계약을 명확히 했다.
