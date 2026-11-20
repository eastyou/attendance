"""考勤数据模型：名单解析、月份校验与分页。"""

from __future__ import annotations

import calendar
import csv
import io
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

MAX_NAME = 20
MAX_NUMBER = 12
MIN_ROWS = 10
MAX_ROWS = 40
DEFAULT_ROWS = 30
MIN_YEAR = 1900
MAX_YEAR = 2100

NAME_HEADERS = {"姓名", "名字", "学生", "学生姓名"}
NUMBER_HEADERS = {"学号", "编号", "序号"}
_MONTH_PATTERN = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


class AttendanceError(ValueError):
    """名单、月份或参数不合法。"""


@dataclass(frozen=True)
class Student:
    """一名学生：可选学号与姓名。"""

    name: str
    number: str = ""

    def __post_init__(self) -> None:
        name = _clean(self.name, "姓名")
        number = _clean(self.number, "学号")
        if not name:
            raise AttendanceError("姓名不能为空")
        if len(name) > MAX_NAME:
            raise AttendanceError(
                "姓名最多 %d 个字符，当前 %d 个：%s" % (MAX_NAME, len(name), name)
            )
        if len(number) > MAX_NUMBER:
            raise AttendanceError(
                "学号最多 %d 个字符，当前 %d 个：%s"
                % (MAX_NUMBER, len(number), number)
            )
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "number", number)


def _clean(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise AttendanceError("%s必须是文本，当前是 %r" % (label, value))
    return value.strip()


def _decode(data: bytes) -> str:
    if not isinstance(data, (bytes, bytearray)):
        raise AttendanceError("文件内容必须是字节")
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return bytes(data).decode(encoding)
        except UnicodeDecodeError:
            continue
    raise AttendanceError("无法识别文件编码，请另存为 UTF-8 或 GBK 后重试")


def _is_header(cells: Sequence[str]) -> bool:
    if len(cells) == 1:
        return cells[0] in NAME_HEADERS
    if len(cells) >= 2:
        return cells[0] in NUMBER_HEADERS and cells[1] in NAME_HEADERS
    return False


def parse_roster(text: str, source: str = "输入内容") -> List[Student]:
    """解析名单：txt 每行一名，或 CSV「姓名」/「学号,姓名」，表头可选。"""
    if not isinstance(text, str):
        raise AttendanceError("名单内容必须是文本")
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text))
    students: List[Student] = []
    seen: Dict[str, int] = {}
    header_checked = False
    for line_no, row in enumerate(reader, start=1):
        cells = [cell.strip() for cell in row]
        if not any(cells):
            continue
        if not header_checked:
            header_checked = True
            if _is_header(cells):
                continue
        if len(cells) > 2:
            raise AttendanceError(
                "%s 第 %d 行有 %d 列，最多 2 列（学号,姓名）"
                % (source, line_no, len(cells))
            )
        if len(cells) == 1:
            number, name = "", cells[0]
        else:
            number, name = cells[0], cells[1]
        if not name:
            raise AttendanceError("%s 第 %d 行缺少姓名" % (source, line_no))
        if name in seen:
            raise AttendanceError(
                "%s 第 %d 行与第 %d 行姓名重复：%s"
                % (source, line_no, seen[name], name)
            )
        try:
            students.append(Student(name=name, number=number))
        except AttendanceError as exc:
            raise AttendanceError("%s 第 %d 行：%s" % (source, line_no, exc)) from exc
        seen[name] = line_no
    if not students:
        raise AttendanceError("%s 中没有有效的学生姓名" % source)
    return students


def load_roster(path: Union[str, Path]) -> List[Student]:
    """读取名单文件并解析。"""
    target = Path(path)
    return parse_roster(_decode(target.read_bytes()), source=str(target))


def parse_month(value: str) -> Tuple[int, int]:
    """严格解析 YYYY-MM，返回（年, 月）。"""
    if not isinstance(value, str):
        raise AttendanceError("月份必须是 YYYY-MM 格式的文本")
    text = value.strip()
    match = _MONTH_PATTERN.match(text)
    if not match:
        raise AttendanceError("月份格式必须是 YYYY-MM，例如 2026-11")
    year, month = int(match.group(1)), int(match.group(2))
    if not MIN_YEAR <= year <= MAX_YEAR:
        raise AttendanceError(
            "年份必须在 %d~%d 之间，当前是 %d" % (MIN_YEAR, MAX_YEAR, year)
        )
    try:
        calendar.monthrange(year, month)
    except (ValueError, calendar.IllegalMonthError) as exc:
        raise AttendanceError("月份不存在：%s" % text) from exc
    return year, month


def current_month() -> str:
    """当前月份，格式 YYYY-MM。"""
    today = date.today()
    return "%04d-%02d" % (today.year, today.month)


def month_days(year: int, month: int) -> int:
    """某月的天数。"""
    if isinstance(year, bool) or not isinstance(year, int):
        raise AttendanceError("年份必须是整数")
    if isinstance(month, bool) or not isinstance(month, int):
        raise AttendanceError("月份必须是整数")
    if not MIN_YEAR <= year <= MAX_YEAR:
        raise AttendanceError("年份超出范围：%d" % year)
    if not 1 <= month <= 12:
        raise AttendanceError("月份必须在 1~12 之间，当前是 %d" % month)
    return calendar.monthrange(year, month)[1]


def is_weekend(year: int, month: int, day: int) -> bool:
    """判断某天是否周末。"""
    days = month_days(year, month)
    if isinstance(day, bool) or not isinstance(day, int):
        raise AttendanceError("日期必须是整数")
    if not 1 <= day <= days:
        raise AttendanceError(
            "%d 年 %d 月只有 %d 天，没有第 %d 天" % (year, month, days, day)
        )
    return date(year, month, day).weekday() >= 5


def weekend_days(year: int, month: int) -> List[int]:
    """某月所有周末日期。"""
    return [
        day
        for day in range(1, month_days(year, month) + 1)
        if is_weekend(year, month, day)
    ]


def check_rows(rows: int) -> int:
    """校验每页行数。"""
    if isinstance(rows, bool) or not isinstance(rows, int):
        raise AttendanceError("每页行数必须是整数")
    if not MIN_ROWS <= rows <= MAX_ROWS:
        raise AttendanceError(
            "每页行数必须在 %d~%d 之间，当前是 %d" % (MIN_ROWS, MAX_ROWS, rows)
        )
    return rows


def paginate(students: Sequence[Student], rows: int = DEFAULT_ROWS) -> List[List[Student]]:
    """按每页行数分页，未填满的一页保留。"""
    if not isinstance(students, (list, tuple)) or not students:
        raise AttendanceError("学生名单不能为空")
    for student in students:
        if not isinstance(student, Student):
            raise AttendanceError("名单里出现了非 Student 对象")
    size = check_rows(rows)
    pages: List[List[Student]] = []
    for start in range(0, len(students), size):
        pages.append(list(students[start : start + size]))
    return pages


def month_label(year: int, month: int) -> str:
    """中文月份标题，例如「2026 年 11 月」。"""
    month_days(year, month)
    return "%d 年 %d 月" % (year, month)
