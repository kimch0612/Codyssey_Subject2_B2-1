파일 기반 가계부 콘솔 프로그램 만들기
-------------

가계부 야호

### 구현 순서 체크리스트
- [x] `data_struct.py`에서 데이터 모델 확정하기
  - [x] `Transaction` 필드 확정: `id`, `type`, `date`, `amount`, `category`, `memo`, `tags`
  - [X] `Category`, `Budget` dataclass 필드 확정
  - [x] `tags`를 `list[str]`로 둘지, 저장 직전 문자열로 변환할지 기준 정하기

- [X] `budget_helper.py`에서 공통 도구 구현하기
  - [X] 사용자 입력 검증 함수 구현: 날짜, 월, 금액, 거래 타입
  - [ ] 카테고리 존재 여부 검증 함수 설계
  - [X] 스택트레이스 대신 `[오류]`, `[힌트]`를 출력할 예외 클래스 또는 처리 함수 만들기
  - [ ] 과제 요구용 데코레이터 구현: 예외 처리, 실행 로그, 실행 시간 측정 중 1개 이상

- [ ] `storage.py`에서 저장 방식 구현하기
  - [ ] 저장 포맷 결정: JSONL 또는 CSV 중 하나
  - [ ] `data/` 디렉터리와 기본 파일 3개 자동 생성
    - [ ] `transactions.<fmt>`
    - [ ] `categories.<fmt>`
    - [ ] `budgets.<fmt>`
  - [ ] `Transaction` 직렬화/역직렬화 함수 구현
  - [ ] 거래 파일을 한 줄씩 읽는 generator 구현
  - [ ] 거래 append 저장 함수 구현
  - [ ] update/delete에 사용할 임시 파일 + `os.replace()` 기반 원자적 재작성 함수 구현
  - [ ] 카테고리 목록 load/save 구현
  - [ ] 월 예산 load/save 구현

- [ ] `budget_service.py`에서 카테고리 기능부터 구현하기
  - [ ] 초기 카테고리 정책 결정: 기본 카테고리 자동 생성 또는 사용자가 먼저 추가
  - [ ] `category add`
  - [ ] `category list`
  - [ ] `category remove`
  - [ ] 사용 중인 카테고리 삭제 방지 또는 대체 카테고리 요구 처리

- [ ] `budget_service.py`에서 거래 생성 기능 구현하기
  - [ ] `add` 대화형 입력 흐름 만들기
  - [ ] 날짜, type, category, amount 검증 연결
  - [ ] 새 거래 id 생성 규칙 구현
  - [ ] 저장 성공 메시지에 생성된 id 출력

- [ ] `budget_service.py`에서 조회 기능 구현하기
  - [ ] `list` 최신순 출력
  - [ ] `list --limit N` 처리
  - [ ] 전체 파일을 리스트로 모두 들고 있지 않도록 generator 기반 흐름 유지
  - [ ] 출력 포맷 정리

- [ ] `budget_service.py`에서 검색 기능 구현하기
  - [ ] `search --from`, `--to` 기간 조건
  - [ ] `search --category`
  - [ ] `search --type`
  - [ ] `search --q` 메모 키워드
  - [ ] `search --tag`
  - [ ] 검색 결과 최신순 출력

- [ ] `budget_service.py`에서 월별 요약과 예산 구현하기
  - [ ] `summary --month YYYY-MM`
  - [ ] 총 수입, 총 지출, 잔액 계산
  - [ ] `--top N` 기준 카테고리별 지출 TOP N 출력
  - [ ] 데이터가 없는 달 처리
  - [ ] `budget set --month YYYY-MM --amount 금액`
  - [ ] summary에서 예산 사용률과 초과 경고 출력

- [ ] `budget_service.py`에서 수정/삭제 구현하기
  - [ ] update 방식을 옵션 기반 또는 대화형 기반 중 하나로 확정
  - [ ] `update --id <id>` 기반 수정 구현
  - [ ] 존재하지 않는 id 처리
  - [ ] `delete --id <id>` 구현
  - [ ] update/delete는 `storage.py`의 원자적 재작성 함수 사용

- [ ] `budget_service.py`와 `storage.py`에서 import/export 구현하기
  - [ ] import CSV 스키마 고정: `date`, `type`, `category`, `amount`, `memo`, `tags`
  - [ ] `import --from <csv>` 구현
  - [ ] import 성공/스킵 건수 출력
  - [ ] `export --out <csv> --month YYYY-MM` 구현
  - [ ] `export --out <csv> --from YYYY-MM-DD --to YYYY-MM-DD` 구현
  - [ ] export 조건이 없을 때 오류 처리

- [ ] `command.py`에서 CLI 옵션 연결하기
  - [ ] 모든 명령에 `--help`가 동작하는지 확인
  - [ ] `list --limit`
  - [ ] `search --from --to --category --type --q --tag`
  - [ ] `summary --month --top`
  - [ ] `budget set --month --amount`
  - [ ] `update --id`와 수정 옵션들
  - [ ] `delete --id`
  - [ ] `import --from`
  - [ ] `export --out --month --from --to`
  - [ ] 공통 `--data-dir` 옵션 추가 여부 결정

- [ ] `README.md`에 제출용 문서 작성하기
  - [ ] 실행 방법
  - [ ] 저장 파일 위치와 형식
  - [ ] 주요 명령 예시
  - [ ] import/export CSV 스키마
  - [ ] update 방식 명시
  - [ ] 모듈별 책임 설명
  - [ ] generator, decorator, type hint 사용 위치 설명

- [ ] 수동 테스트하기
  - [ ] 최초 실행 시 `data/`와 저장 파일 생성 확인
  - [ ] category add/list/remove
  - [ ] add 후 list/search/summary 확인
  - [ ] budget set 후 summary 예산 표시 확인
  - [ ] update/delete 후 파일 내용 확인
  - [ ] import/export 왕복 확인
  - [ ] 잘못된 날짜, 금액, type, category 오류 처리 확인
  - [ ] 오류 종료 code가 0이 아닌지 확인
