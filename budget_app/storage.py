from collections.abc import Iterator, Iterable
from pathlib import Path
from dataclasses import asdict # dataclass 객체를 dict로 변환해줌

from .models import Transaction

import json, os, tempfile

class TransactionRepository:
    def __init__(self, data_dir: Path) -> None:
        if not data_dir.exists(): # exist_ok가 있어서 굳이 필요 없다곤 하는데..
            data_dir.mkdir(parents=True, exist_ok=True)

        self.path = data_dir / "transactions.jsonl"
        self.path.touch(exist_ok=True)

    def add(self, transaction: Transaction) -> None:
        transaction_data = asdict(transaction)
        json_line = json.dumps(transaction_data, ensure_ascii=False)
        # dump랑 dumps랑 다름; dump는 파일에 직접 쓰고 dumps는 데이터를 json 형식으로 변환함

        with self.path.open("a", encoding="utf-8") as f:
            f.write(json_line + "\n")

    def iter_transactions(self) -> Iterator[Transaction]:
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                transaction = Transaction(**data)
                yield transaction # 하나씩 투척

    def replace_all(
        self,
        transactions: Iterable[Transaction]
    ) -> None:
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                delete=False
            ) as f:
                temp_file_path = Path(f.name)
                for transaction in transactions:
                    transaction_data = asdict(transaction)
                    json_line = json.dumps(transaction_data, ensure_ascii=False)
                    f.write(json_line + "\n")
            os.replace(temp_file_path, self.path) # 순식간에 휙 교체
        finally:
            if temp_file_path and temp_file_path.exists():
                os.remove(temp_file_path)

class CategoryStore:
    def __init__(self, data_dir: Path) -> None:
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
        
        self.path = data_dir / "categories.jsonl"
        self.path.touch(exist_ok=True)

    def add(self, name: str) -> None:
        data = {"name": name}
        json_line = json.dumps(data, ensure_ascii=False) # 딕셔너리를 JSON 문자열로 직렬화

        with self.path.open("a", encoding="utf-8") as f:
            f.write(json_line + "\n")

    def iter_categories(self) -> Iterator[str]:
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                yield data["name"]