"""attendance：A4 横向可打印班级考勤表。"""

from __future__ import annotations

from .model import (
    DEFAULT_ROWS,
    MAX_NAME,
    MAX_ROWS,
    MAX_YEAR,
    MIN_ROWS,
    MIN_YEAR,
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
from .render import (
    USABLE_WIDTH_MM,
    day_width_mm,
    name_font_pt,
    render_html,
    row_height_mm,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_ROWS",
    "MAX_NAME",
    "MAX_ROWS",
    "MAX_YEAR",
    "MIN_ROWS",
    "MIN_YEAR",
    "USABLE_WIDTH_MM",
    "AttendanceError",
    "Student",
    "check_rows",
    "current_month",
    "day_width_mm",
    "is_weekend",
    "load_roster",
    "month_days",
    "month_label",
    "name_font_pt",
    "paginate",
    "parse_month",
    "parse_roster",
    "render_html",
    "row_height_mm",
    "weekend_days",
    "__version__",
]
