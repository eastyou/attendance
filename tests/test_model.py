"""model 模块单元测试。"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path
from typing import List

from attendance.model import (
    MAX_NAME,
    MAX_ROWS,
    MIN_ROWS,
    AttendanceError,
    Student,
    check_rows,
    current_month,
    is_weekend,
    load_roster,
    month_days,
    month_label,
    paginate,
    parse_month,
    parse_roster,
    weekend_days,
)


def make_students(count: int) -> List[Student]:
    return [Student(name="学生%02d" % index) for index in range(1, count + 1)]


class ParseRosterTest(unittest.TestCase):
    def test_plain_lines(self) -> None:
        students = parse_roster("张三\n李四\n王五\n")
        self.assertEqual([student.name for student in students], ["张三", "李四", "王五"])
        self.assertEqual(students[0].number, "")

    def test_name_header(self) -> None:
        students = parse_roster("姓名\n张三\n李四\n")
        self.assertEqual(len(students), 2)

    def test_student_number_header(self) -> None:
        students = parse_roster("学号,姓名\n2026001,张三\n")
        self.assertEqual(students[0].number, "2026001")
        self.assertEqual(students[0].name, "张三")

    def test_csv_without_header(self) -> None:
        students = parse_roster("2026001,张三\n2026002,李四\n")
        self.assertEqual(students[1].number, "2026002")

    def test_extra_column(self) -> None:
        with self.assertRaises(AttendanceError) as ctx:
            parse_roster("2026001,张三,备注\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_empty_name(self) -> None:
        with self.assertRaises(AttendanceError) as ctx:
            parse_roster("张三\n李四,\n")
        self.assertIn("第 2 行", str(ctx.exception))

    def test_duplicate_name(self) -> None:
        with self.assertRaises(AttendanceError) as ctx:
            parse_roster("张三\n李四\n张三\n")
        self.assertIn("第 3 行", str(ctx.exception))
        self.assertIn("第 1 行", str(ctx.exception))

    def test_name_too_long(self) -> None:
        with self.assertRaises(AttendanceError) as ctx:
            parse_roster("字" * (MAX_NAME + 1) + "\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_number_too_long(self) -> None:
        with self.assertRaises(AttendanceError) as ctx:
            parse_roster("1" * 13 + ",张三\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_bom(self) -> None:
        students = parse_roster("\ufeff张三\n")
        self.assertEqual(students[0].name, "张三")

    def test_non_text(self) -> None:
        with self.assertRaises(AttendanceError):
            parse_roster(123)  # type: ignore[arg-type]

    def test_empty(self) -> None:
        with self.assertRaises(AttendanceError):
            parse_roster("\n\n")

    def test_load_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roster.txt"
            path.write_text("张三\n李四\n", encoding="utf-8")
            self.assertEqual(len(load_roster(path)), 2)

    def test_load_gbk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roster.txt"
            path.write_bytes("张三\n李四\n".encode("gbk"))
            self.assertEqual(load_roster(path)[0].name, "张三")

    def test_unknown_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roster.txt"
            path.write_bytes(b"\xff\xff\xff")
            with self.assertRaises(AttendanceError):
                load_roster(path)

    def test_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_roster("/tmp/definitely-missing-attendance.txt")


class StudentTest(unittest.TestCase):
    def test_trim(self) -> None:
        student = Student(name=" 张三 ", number=" 001 ")
        self.assertEqual(student.name, "张三")
        self.assertEqual(student.number, "001")

    def test_empty_name(self) -> None:
        with self.assertRaises(AttendanceError):
            Student(name="  ")

    def test_non_text(self) -> None:
        with self.assertRaises(AttendanceError):
            Student(name=1)  # type: ignore[arg-type]


class MonthTest(unittest.TestCase):
    def test_valid(self) -> None:
        self.assertEqual(parse_month("2026-11"), (2026, 11))
        self.assertEqual(parse_month(" 2024-02 "), (2024, 2))

    def test_bad_format(self) -> None:
        for value in ("2026-1", "2026/11", "abc", "2026-13", "2026-00"):
            with self.assertRaises(AttendanceError):
                parse_month(value)

    def test_year_range(self) -> None:
        for value in ("1899-01", "2101-12"):
            with self.assertRaises(AttendanceError):
                parse_month(value)

    def test_non_text(self) -> None:
        with self.assertRaises(AttendanceError):
            parse_month(202611)  # type: ignore[arg-type]

    def test_current_month(self) -> None:
        value = current_month()
        self.assertRegex(value, re.compile(r"^\d{4}-\d{2}$"))
        self.assertEqual(parse_month(value)[0] > 2000, True)

    def test_month_days(self) -> None:
        self.assertEqual(month_days(2024, 2), 29)
        self.assertEqual(month_days(2023, 2), 28)
        self.assertEqual(month_days(2026, 11), 30)
        self.assertEqual(month_days(2026, 12), 31)

    def test_month_days_bad(self) -> None:
        with self.assertRaises(AttendanceError):
            month_days(2026, 0)
        with self.assertRaises(AttendanceError):
            month_days(2026, 13)
        with self.assertRaises(AttendanceError):
            month_days(2026, True)  # type: ignore[arg-type]
        with self.assertRaises(AttendanceError):
            month_days(1800, 1)

    def test_weekend(self) -> None:
        self.assertTrue(is_weekend(2026, 11, 21))
        self.assertTrue(is_weekend(2026, 11, 1))
        self.assertFalse(is_weekend(2026, 11, 20))
        self.assertFalse(is_weekend(2026, 11, 30))

    def test_weekend_bad_day(self) -> None:
        with self.assertRaises(AttendanceError):
            is_weekend(2026, 11, 0)
        with self.assertRaises(AttendanceError):
            is_weekend(2026, 11, 31)
        with self.assertRaises(AttendanceError):
            is_weekend(2026, 11, True)  # type: ignore[arg-type]

    def test_weekend_days(self) -> None:
        self.assertEqual(
            weekend_days(2026, 11),
            [1, 7, 8, 14, 15, 21, 22, 28, 29],
        )

    def test_month_label(self) -> None:
        self.assertEqual(month_label(2026, 11), "2026 年 11 月")
        with self.assertRaises(AttendanceError):
            month_label(2026, 13)


class PaginationTest(unittest.TestCase):
    def test_check_rows(self) -> None:
        self.assertEqual(check_rows(MIN_ROWS), MIN_ROWS)
        self.assertEqual(check_rows(MAX_ROWS), MAX_ROWS)

    def test_check_rows_bad(self) -> None:
        for value in (MIN_ROWS - 1, MAX_ROWS + 1, True, "20"):
            with self.assertRaises(AttendanceError):
                check_rows(value)  # type: ignore[arg-type]

    def test_paginate(self) -> None:
        pages = paginate(make_students(45), rows=30)
        self.assertEqual([len(page) for page in pages], [30, 15])

    def test_paginate_exact(self) -> None:
        pages = paginate(make_students(20), rows=10)
        self.assertEqual([len(page) for page in pages], [10, 10])

    def test_paginate_empty(self) -> None:
        with self.assertRaises(AttendanceError):
            paginate([])

    def test_paginate_non_student(self) -> None:
        with self.assertRaises(AttendanceError):
            paginate(["张三"])  # type: ignore[list-item]

    def test_paginate_bad_rows(self) -> None:
        with self.assertRaises(AttendanceError):
            paginate(make_students(10), rows=5)


if __name__ == "__main__":
    unittest.main()
