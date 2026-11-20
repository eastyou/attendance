"""render 模块单元测试。"""

from __future__ import annotations

import unittest
from typing import List

from attendance.model import AttendanceError, Student
from attendance.render import (
    NAME_WIDTH_MM,
    SEQ_WIDTH_MM,
    TOTAL_WIDTH_MM,
    USABLE_WIDTH_MM,
    day_width_mm,
    name_font_pt,
    render_html,
    row_height_mm,
)


def make_students(count: int) -> List[Student]:
    return [Student(name="学生%02d" % index) for index in range(1, count + 1)]


class WidthTest(unittest.TestCase):
    def test_usable_width(self) -> None:
        self.assertEqual(USABLE_WIDTH_MM, 267.0)

    def test_day_width_shrinks(self) -> None:
        self.assertGreater(day_width_mm(28), day_width_mm(31))

    def test_total_width(self) -> None:
        total = SEQ_WIDTH_MM + NAME_WIDTH_MM + TOTAL_WIDTH_MM * 3
        self.assertAlmostEqual(total + 31 * day_width_mm(31), USABLE_WIDTH_MM, places=6)

    def test_bad_days(self) -> None:
        with self.assertRaises(AttendanceError):
            day_width_mm(27)
        with self.assertRaises(AttendanceError):
            day_width_mm(True)  # type: ignore[arg-type]

    def test_row_height(self) -> None:
        self.assertEqual(row_height_mm(10), 7.0)
        self.assertAlmostEqual(row_height_mm(40), 3.75)
        with self.assertRaises(AttendanceError):
            row_height_mm(5)

    def test_name_font(self) -> None:
        self.assertEqual(name_font_pt("张三"), 9.0)
        self.assertEqual(name_font_pt("欧阳修文"), 9.0)
        self.assertEqual(name_font_pt("字" * 8), 8.0)
        self.assertEqual(name_font_pt("字" * 12), 7.0)
        self.assertEqual(name_font_pt("字" * 20), 6.0)

    def test_name_font_non_text(self) -> None:
        with self.assertRaises(AttendanceError):
            name_font_pt(1)  # type: ignore[arg-type]


class RenderHtmlTest(unittest.TestCase):
    def test_basic_document(self) -> None:
        page = render_html(make_students(5), 2026, 11, rows=10)
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("A4 landscape", page)
        self.assertIn("2026 年 11 月", page)
        self.assertIn("267mm", page)

    def test_column_headers(self) -> None:
        page = render_html(make_students(5), 2026, 11, rows=10)
        headers = page.count("<th>") + page.count('<th class="weekend">')
        self.assertEqual(headers, 35)
        for label in ("序号", "姓名", "出勤", "请假", "迟到"):
            self.assertIn("<th>%s</th>" % label, page)
        self.assertIn("<th>30</th>", page)

    def test_weekend_header_shading(self) -> None:
        page = render_html(make_students(5), 2026, 11, rows=10)
        self.assertEqual(page.count('<th class="weekend">'), 9)
        self.assertIn('<th class="weekend">1</th>', page)
        self.assertIn('<th class="weekend">29</th>', page)

    def test_weekend_body_shading(self) -> None:
        page = render_html(make_students(5), 2026, 11, rows=10)
        self.assertEqual(page.count('<td class="day weekend"></td>'), 90)

    def test_pagination(self) -> None:
        page = render_html(make_students(25), 2026, 11, rows=10)
        self.assertEqual(page.count('<section class="sheet">'), 3)
        self.assertEqual(page.count("<th>序号</th>"), 3)

    def test_second_page_students(self) -> None:
        page = render_html(make_students(25), 2026, 11, rows=10)
        parts = page.split('<section class="sheet">')
        self.assertIn("学生21", parts[3])
        self.assertIn('<td class="seq">21</td>', parts[3])
        self.assertIn("学生25", parts[3])
        self.assertEqual(parts[3].count('<tr class="empty">'), 5)
        self.assertIn("学生01", parts[1])
        self.assertNotIn("学生11", parts[1])

    def test_blank_rows(self) -> None:
        page = render_html(make_students(3), 2026, 11, rows=10)
        self.assertEqual(page.count('<tr class="empty">'), 7)

    def test_student_number(self) -> None:
        page = render_html(
            [Student(name="张三", number="2026001")], 2026, 11, rows=10
        )
        self.assertIn('<td class="seq">2026001</td>', page)

    def test_auto_number(self) -> None:
        page = render_html([Student(name="张三")], 2026, 11, rows=10)
        self.assertIn('<td class="seq">1</td>', page)

    def test_group_label(self) -> None:
        page = render_html(make_students(3), 2026, 11, rows=10, group="初二（3）班")
        self.assertIn("初二（3）班", page)

    def test_title_escaped(self) -> None:
        page = render_html(make_students(3), 2026, 11, rows=10, title="<考勤>")
        self.assertIn("&lt;考勤&gt;", page)

    def test_legend(self) -> None:
        page = render_html(make_students(3), 2026, 11, rows=10)
        self.assertIn("✓ 出勤", page)
        self.assertIn("○ 请假", page)
        self.assertIn("△ 迟到", page)

    def test_february(self) -> None:
        page = render_html(make_students(3), 2024, 2, rows=10)
        self.assertIn("<th>29</th>", page)

    def test_empty_students(self) -> None:
        with self.assertRaises(AttendanceError):
            render_html([], 2026, 11)

    def test_non_student(self) -> None:
        with self.assertRaises(AttendanceError):
            render_html(["张三"], 2026, 11)  # type: ignore[list-item]

    def test_non_sequence(self) -> None:
        with self.assertRaises(AttendanceError):
            render_html("张三", 2026, 11)  # type: ignore[arg-type]

    def test_duplicate_names(self) -> None:
        with self.assertRaises(AttendanceError):
            render_html([Student("张三"), Student("张三")], 2026, 11)

    def test_bad_month(self) -> None:
        with self.assertRaises(AttendanceError):
            render_html(make_students(3), 2026, 13)

    def test_bad_rows(self) -> None:
        with self.assertRaises(AttendanceError):
            render_html(make_students(3), 2026, 11, rows=5)

    def test_bad_group(self) -> None:
        with self.assertRaises(AttendanceError):
            render_html(make_students(3), 2026, 11, group=1)  # type: ignore[arg-type]

    def test_long_group(self) -> None:
        with self.assertRaises(AttendanceError):
            render_html(make_students(3), 2026, 11, group="字" * 21)

    def test_empty_title(self) -> None:
        with self.assertRaises(AttendanceError):
            render_html(make_students(3), 2026, 11, title=" ")

    def test_page_numbers(self) -> None:
        page = render_html(make_students(25), 2026, 11, rows=10)
        self.assertIn("第 1 / 3 页", page)
        self.assertIn("第 3 / 3 页", page)


if __name__ == "__main__":
    unittest.main()
