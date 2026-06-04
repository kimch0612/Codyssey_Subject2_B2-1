"""Budget app service layer.

Actual CRUD, search, summary, import, and export logic will live here.
"""

from __future__ import annotations
import argparse


def run_placeholder(args: argparse.Namespace) -> int:
    command = getattr(args, "command", None)
    detail = getattr(args, "budget_command", None) or getattr(
        args, "category_command", None
    )

    if detail:
        print(f"[준비 중] {command} {detail} 기능은 아직 구현되지 않았습니다.")
    else:
        print(f"[준비 중] {command} 기능은 아직 구현되지 않았습니다.")

    return 0

