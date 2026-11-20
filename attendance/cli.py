"""命令行入口：生成可打印的班级考勤表。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from .model import (
    DEFAULT_ROWS,
    MAX_ROWS,
    MIN_ROWS,
    AttendanceError,
    Student,
    current_month,
    load_roster,
    parse_month,
)
from .render import render_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="attendance",
        description="班级考勤表：名单一键生成 A4 横向可打印考勤表",
    )
    parser.add_argument("--version", action="version", version="attendance 0.1.0")
    parser.add_argument(
        "-i", "--input", required=True, help="学生名单，txt 每行一名或 CSV（学号,姓名）"
    )
    parser.add_argument(
        "-o", "--output", default="考勤表.html", help="输出 HTML 路径"
    )
    parser.add_argument(
        "--month", default=None, help="月份 YYYY-MM，默认当月"
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help="每页行数 %d~%d，默认 %d" % (MIN_ROWS, MAX_ROWS, DEFAULT_ROWS),
    )
    parser.add_argument("--group", default="班级", help="班级名称")
    parser.add_argument("--title", default="考勤表", help="页面标题")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        month_value = args.month if args.month is not None else current_month()
        year, month = parse_month(month_value)
        students: List[Student] = load_roster(args.input)
        page = render_html(
            students,
            year,
            month,
            rows=args.rows,
            group=args.group,
            title=args.title,
        )
    except AttendanceError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("错误: 读取名单失败: %s" % exc, file=sys.stderr)
        return 1

    try:
        Path(args.output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    pages = (len(students) + args.rows - 1) // args.rows
    print(
        "已生成 %s：%d 年 %d 月，%d 名学生，每页 %d 人，共 %d 页"
        % (args.output, year, month, len(students), args.rows, pages)
    )
    print("用浏览器打开后按 Ctrl/Cmd + P，纸张选 A4 横向即可打印")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
