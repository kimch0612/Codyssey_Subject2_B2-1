# 나만의 용돈 기입장 프로그램 만들기

Python 표준 라이브러리로 만든 콘솔 가계부입니다. 요구사항의 기준은 [Subject.txt](Subject.txt)입니다.

## 실행 방법

Python 3.10 이상이 필요하며 별도 패키지 설치는 필요하지 않습니다. `budget_app` 폴더가 있는 과제 디렉터리에서 실행합니다.

```bash
cd /Users/charles/Documents/Dev/Codyssey/Subject2/B2-1
python -m budget_app --help
python -m budget_app <command> [options]
```

모든 명령에서 `--help`를 사용할 수 있습니다. 일반 옵션은 `--limit`과 `-limit`처럼 두 표기를 지원하며, 아래 예시는 `--`를 사용합니다.

## 저장 위치와 형식

기본 저장 위치는 실행한 작업 폴더의 `./data`입니다. 저장 폴더를 바꾸려면 명령 앞에 `--data-dir`를 지정합니다.

```bash
python -m budget_app --data-dir /tmp/budget-practice category list
```

저장 폴더와 필요한 파일은 없으면 자동 생성됩니다. 내부 저장 형식은 한 줄에 JSON 객체 하나를 저장하는 JSONL입니다.

| 파일 | 내용 |
| --- | --- |
| `transactions.jsonl` | 거래 ID, 날짜, 타입, 금액, 카테고리, 메모, 태그 |
| `categories.jsonl` | 등록된 카테고리 이름 |
| `budgets.jsonl` | 월별 예산 금액 |

카테고리가 비어 있으면 `category add`로 먼저 등록해야 하며, 거래 추가는 등록 전까지 차단됩니다.

## 주요 명령

### 카테고리와 거래 추가

```bash
python -m budget_app category add
python -m budget_app category list
python -m budget_app add
```

`category add`는 이름을 입력받습니다. `add`는 금액, 태그, 날짜, 타입, 카테고리, 메모를 순서대로 입력받습니다. 거래 금액은 양수 정수, 날짜는 `YYYY-MM-DD`, 타입은 `income` 또는 `expense`이며 카테고리는 등록된 이름이어야 합니다. 메모와 태그는 생략할 수 있고, 여러 태그는 쉼표로 구분합니다.

### 목록과 검색

```bash
python -m budget_app list --limit 3
python -m budget_app search --from 2026-09-01 --to 2026-09-30
python -m budget_app search --category food --type expense --q 점심 --tag meal
```

목록과 검색 결과는 최신순으로 출력합니다. list의 기본 조회 개수는 10개입니다.

### 수정과 삭제

update는 **옵션 방식**입니다. ID는 실제 조회된 거래의 값으로 바꿔 입력합니다.

```bash
python -m budget_app update --id TX-000001 --amount 15000
python -m budget_app update --id TX-000001 --memo "점심" --tags "meal,lunch"
python -m budget_app delete --id TX-000001
python -m budget_app category remove
```

update는 지정한 필드만 수정합니다. `--date`, `--type`, `--category`, `--amount`, `--memo`, `--tags`를 사용할 수 있습니다. `--memo ""` 또는 `--tags ""`는 해당 내용을 지웁니다. `category remove`는 이름을 입력받으며, 거래에서 사용 중인 카테고리는 삭제하지 않습니다.

### 예산과 월별 요약

```bash
python -m budget_app budget set --month 2026-09 --amount 300000
python -m budget_app summary --month 2026-09 --top 3
```

summary는 총수입·총지출·잔액과 카테고리별 지출 TOP N을 출력합니다. 예산이 있으면 사용률과 초과 경고를 함께 보여줍니다. 예산은 0 이상의 정수이며 0원은 사용률 계산 불가로 표시합니다.

### CSV 가져오기·내보내기

```bash
python -m budget_app export --out september.csv --month 2026-09
python -m budget_app export --out period.csv --from 2026-09-01 --to 2026-09-15
python -m budget_app import --from september.csv
```

export에는 월 또는 시작일·종료일 범위가 필요합니다. 출력 파일이 이미 있으면 덮어쓰지 않습니다. import는 정상 행을 저장하고, 값 검증에 실패한 행은 데이터 행 번호(헤더 제외), 원인, 해결 힌트를 출력한 뒤 건너뜁니다. CSV 구조 오류 등으로 중단되어도 `imported`는 이미 저장된 건수, `skipped`는 값 오류로 건너뛴 건수를 출력합니다. 중단시킨 행과 읽지 않은 나머지 행은 이 건수에 포함하지 않습니다. 같은 CSV를 다시 가져오면 거래가 중복 등록될 수 있으므로, 중도 실패 후 재시도할 때는 이미 반영된 행을 제외하세요.

## CSV 스키마

UTF-8 인코딩과 헤더를 사용합니다. 내부 저장은 JSONL이고 CSV는 가져오기·내보내기용입니다.

| 컬럼 | 필수 | 값 |
| --- | --- | --- |
| date | Y | `YYYY-MM-DD` |
| type | Y | `income` 또는 `expense` |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표로 구분한 태그 문자열 |

```csv
date,type,category,amount,memo,tags
2026-09-11,expense,food,10000,"점심, 식사","meal,lunch"
```

쉼표가 들어 있는 값은 위처럼 큰따옴표로 감쌉니다. export는 위 6개 컬럼을 출력합니다. import는 필수 4개 컬럼이 필요하며, memo와 tags는 생략할 수 있습니다.

구현 확인 항목은 [CHECK.md](CHECK.md), 공부 노트는 [Study.md](Study.md)를 참고하세요.
