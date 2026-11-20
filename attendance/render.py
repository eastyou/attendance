"""把考勤表渲染成可打印的 A4 横向表格。"""

from __future__ import annotations

import html
from typing import Dict, List, Sequence

from .model import (
    DEFAULT_ROWS,
    MAX_ROWS,
    MIN_ROWS,
    AttendanceError,
    Student,
    check_rows,
    is_weekend,
    month_days,
    paginate,
)

PAGE_WIDTH_MM = 297.0
PAGE_HEIGHT_MM = 210.0
MARGIN_X_MM = 15.0
USABLE_WIDTH_MM = PAGE_WIDTH_MM - MARGIN_X_MM * 2

SEQ_WIDTH_MM = 12.0
NAME_WIDTH_MM = 26.0
TOTAL_WIDTH_MM = 12.0
FIXED_WIDTH_MM = SEQ_WIDTH_MM + NAME_WIDTH_MM + TOTAL_WIDTH_MM * 3


def _num(value: float) -> str:
    text = "%.2f" % value
    return text.rstrip("0").rstrip(".") if "." in text else text


def day_width_mm(days: int) -> float:
    """按可用宽度压缩日列宽度。"""
    if isinstance(days, bool) or not isinstance(days, int):
        raise AttendanceError("天数必须是整数")
    if not 28 <= days <= 31:
        raise AttendanceError("一个月只能有 28~31 天，当前是 %d" % days)
    return (USABLE_WIDTH_MM - FIXED_WIDTH_MM) / days


def row_height_mm(rows: int) -> float:
    """按每页行数计算行高，行数多时自动压缩。"""
    size = check_rows(rows)
    return min(7.0, 150.0 / size)


def name_font_pt(name: str) -> float:
    """按姓名长度选择字号。"""
    if not isinstance(name, str):
        raise AttendanceError("姓名必须是文本")
    length = len(name)
    if length <= 6:
        return 9.0
    if length <= 10:
        return 8.0
    if length <= 14:
        return 7.0
    return 6.0


def _widths(days: int) -> Dict[str, float]:
    day = day_width_mm(days)
    return {
        "seq": SEQ_WIDTH_MM,
        "name": NAME_WIDTH_MM,
        "day": day,
        "total": TOTAL_WIDTH_MM,
    }


def _head_markup(
    year: int,
    month: int,
    group: str,
    title: str,
    count: int,
    page: int,
    total: int,
) -> str:
    return (
        '<header class="head">'
        "<div><h1>%s</h1>"
        '<p class="sub">%d 年 %d 月 · %s</p></div>'
        '<div class="meta"><span>共 %d 人</span>'
        "<span>第 %d / %d 页</span></div>"
        "</header>"
        % (
            html.escape(title),
            year,
            month,
            html.escape(group),
            count,
            page,
            total,
        )
    )


def _colgroup(days: int) -> str:
    widths = _widths(days)
    parts = [
        '<col style="width:%smm">' % _num(widths["seq"]),
        '<col style="width:%smm">' % _num(widths["name"]),
    ]
    parts.extend(['<col style="width:%smm">' % _num(widths["day"])] * days)
    parts.extend(
        ['<col style="width:%smm">' % _num(widths["total"])] * 3
    )
    return "<colgroup>%s</colgroup>" % "".join(parts)


def _thead(days: int, year: int, month: int) -> str:
    cells = ["<th>序号</th>", "<th>姓名</th>"]
    for day in range(1, days + 1):
        css = ' class="weekend"' if is_weekend(year, month, day) else ""
        cells.append("<th%s>%d</th>" % (css, day))
    cells.extend(["<th>出勤</th>", "<th>请假</th>", "<th>迟到</th>"])
    return "<thead><tr>%s</tr></thead>" % "".join(cells)


def _tbody(
    students: Sequence[Student],
    start: int,
    rows: int,
    days: int,
    year: int,
    month: int,
) -> str:
    weekend = {day for day in range(1, days + 1) if is_weekend(year, month, day)}
    body: List[str] = []
    for offset in range(rows):
        if offset < len(students):
            student = students[offset]
            number = student.number or str(start + offset + 1)
            cells = [
                '<td class="seq">%s</td>' % html.escape(number),
                '<td class="name" style="font-size:%spt">%s</td>'
                % (_num(name_font_pt(student.name)), html.escape(student.name)),
            ]
            for day in range(1, days + 1):
                css = "day weekend" if day in weekend else "day"
                cells.append('<td class="%s"></td>' % css)
            cells.extend(['<td class="total"></td>'] * 3)
            body.append("<tr>%s</tr>" % "".join(cells))
        else:
            cells = ['<td class="seq"></td>', '<td class="name"></td>']
            for day in range(1, days + 1):
                css = "day weekend" if day in weekend else "day"
                cells.append('<td class="%s"></td>' % css)
            cells.extend(['<td class="total"></td>'] * 3)
            body.append('<tr class="empty">%s</tr>' % "".join(cells))
    return "<tbody>%s</tbody>" % "".join(body)


def render_html(
    students: Sequence[Student],
    year: int,
    month: int,
    rows: int = DEFAULT_ROWS,
    group: str = "班级",
    title: str = "考勤表",
) -> str:
    """生成完整 HTML：A4 横向，名单跨页并重复表头。"""
    if not isinstance(students, (list, tuple)) or not students:
        raise AttendanceError("学生名单不能为空")
    for student in students:
        if not isinstance(student, Student):
            raise AttendanceError("名单里出现了非 Student 对象")
    names = [student.name for student in students]
    if len(set(names)) != len(names):
        raise AttendanceError("学生名单里有重复姓名，请先去重")
    days = month_days(year, month)
    size = check_rows(rows)
    if not isinstance(group, str):
        raise AttendanceError("班级名称必须是文本")
    group = group.strip()
    if len(group) > 20:
        raise AttendanceError("班级名称最多 20 个字符")
    if not isinstance(title, str) or not title.strip():
        raise AttendanceError("标题不能为空")

    pages = paginate(students, size)
    total = len(pages)
    height = row_height_mm(size)
    sheets: List[str] = []
    for page_index, page_students in enumerate(pages):
        start = page_index * size
        head = _head_markup(
            year,
            month,
            group,
            title.strip(),
            len(students),
            page_index + 1,
            total,
        )
        table = (
            '<table class="roll" style="font-size:8pt">'
            + _colgroup(days)
            + _thead(days, year, month)
            + _tbody(page_students, start, size, days, year, month)
            + "</table>"
        )
        foot = (
            '<footer class="foot">'
            "<span>图例：✓ 出勤　○ 请假　△ 迟到　空白待填</span>"
            "<span>attendance · A4 横向</span></footer>"
        )
        sheets.append(
            '<section class="sheet">%s%s%s</section>' % (head, table, foot)
        )

    toolbar = (
        '<div class="toolbar"><strong>%s</strong>'
        "<span>%d 年 %d 月 · %s · 共 %d 人 · 每页 %d 人 · 共 %d 页</span></div>"
        % (
            html.escape(title.strip()),
            year,
            month,
            html.escape(group),
            len(students),
            size,
            total,
        )
    )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n%s\n</body>\n</html>\n"
        % (
            html.escape(title.strip()),
            _style(height),
            toolbar,
            "\n".join(sheets),
        )
    )


def _style(height: float) -> str:
    template = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 7mm 0 10mm;
    background: #e2e8f0;
    color: #0f172a;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  }
  .toolbar {
    width: 297mm;
    margin: 0 auto 5mm;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    color: #334155;
    font-size: 13px;
  }
  .toolbar strong { font-size: 15px; letter-spacing: 1px; }
  .toolbar span { color: #64748b; font-size: 12px; }
  .sheet {
    width: 297mm;
    height: 210mm;
    margin: 0 auto 7mm;
    padding: 10mm 15mm 9mm;
    background: #fff;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.14);
    display: flex;
    flex-direction: column;
    page-break-after: always;
    break-after: page;
    overflow: hidden;
  }
  .sheet:last-child { page-break-after: auto; break-after: auto; }
  .head {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding-bottom: 3mm;
    border-bottom: 0.5mm solid #0f172a;
  }
  .head h1 {
    margin: 0 0 1mm;
    font-size: 18pt;
    font-weight: 600;
    letter-spacing: 4pt;
  }
  .head .sub { margin: 0; font-size: 10pt; color: #334155; }
  .head .meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 1mm;
    font-size: 8.5pt;
    color: #64748b;
  }
  table.roll {
    width: 267mm;
    margin-top: 3mm;
    border-collapse: collapse;
    table-layout: fixed;
  }
  table.roll th,
  table.roll td {
    border: 0.2mm solid #94a3b8;
    text-align: center;
    vertical-align: middle;
    padding: 0;
    overflow: hidden;
    white-space: nowrap;
  }
  table.roll th {
    height: 7mm;
    background: #f1f5f9;
    font-weight: 600;
    font-size: 7.5pt;
  }
  table.roll td { height: __ROW_HEIGHT__mm; }
  table.roll td.name {
    text-align: left;
    padding-left: 1.5mm;
    overflow-wrap: anywhere;
    white-space: normal;
    line-height: 1.15;
  }
  table.roll td.seq { font-size: 7.5pt; color: #475569; }
  table.roll th.weekend,
  table.roll td.weekend { background: #f8fafc; }
  table.roll th.weekend { color: #b91c1c; }
  table.roll td.total { background: #fcfcfd; }
  table.roll tr.empty td { color: #cbd5e1; }
  .foot {
    margin-top: auto;
    padding-top: 2mm;
    display: flex;
    justify-content: space-between;
    font-size: 8pt;
    color: #64748b;
    border-top: 0.2mm solid #e2e8f0;
  }
  @page { size: A4 landscape; margin: 0; }
  @media print {
    body { background: #fff; padding: 0; }
    .toolbar { display: none; }
    .sheet { margin: 0; box-shadow: none; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""
    return template.replace("__ROW_HEIGHT__", _num(height))
