"""命令行入口单元测试。"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import List

from attendance.cli import main


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.roster = self.root / "roster.txt"
        names = ["学生%02d" % index for index in range(1, 26)]
        self.roster.write_text("\n".join(names) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, argv: List[str]) -> int:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return main(argv)

    def test_generate(self) -> None:
        target = self.root / "roll.html"
        code = self.run_cli(
            ["-i", str(self.roster), "-o", str(target), "--month", "2026-11"]
        )
        self.assertEqual(code, 0)
        page = target.read_text(encoding="utf-8")
        self.assertIn("2026 年 11 月", page)
        self.assertIn("A4 landscape", page)

    def test_rows_pagination(self) -> None:
        target = self.root / "roll.html"
        code = self.run_cli(
            [
                "-i", str(self.roster), "-o", str(target),
                "--month", "2026-11", "--rows", "10",
            ]
        )
        self.assertEqual(code, 0)
        page = target.read_text(encoding="utf-8")
        self.assertEqual(page.count('<section class="sheet">'), 3)

    def test_group_and_title(self) -> None:
        target = self.root / "roll.html"
        code = self.run_cli(
            [
                "-i", str(self.roster), "-o", str(target),
                "--month", "2026-11", "--rows", "10",
                "--group", "初二（3）班", "--title", "初二考勤",
            ]
        )
        self.assertEqual(code, 0)
        page = target.read_text(encoding="utf-8")
        self.assertIn("初二（3）班", page)
        self.assertIn("初二考勤", page)

    def test_default_month(self) -> None:
        target = self.root / "roll.html"
        code = self.run_cli(
            ["-i", str(self.roster), "-o", str(target), "--rows", "30"]
        )
        self.assertEqual(code, 0)
        self.assertIn("年", target.read_text(encoding="utf-8"))

    def test_invalid_month(self) -> None:
        target = self.root / "bad.html"
        code = self.run_cli(
            ["-i", str(self.roster), "-o", str(target), "--month", "2026-13"]
        )
        self.assertEqual(code, 2)
        self.assertFalse(target.exists())

    def test_invalid_rows(self) -> None:
        target = self.root / "bad.html"
        code = self.run_cli(
            ["-i", str(self.roster), "-o", str(target), "--month", "2026-11", "--rows", "5"]
        )
        self.assertEqual(code, 2)

    def test_duplicate_name(self) -> None:
        bad = self.root / "dup.txt"
        bad.write_text("张三\n张三\n", encoding="utf-8")
        code = self.run_cli(["-i", str(bad), "-o", str(self.root / "x.html")])
        self.assertEqual(code, 2)

    def test_missing_file(self) -> None:
        code = self.run_cli(
            ["-i", str(self.root / "missing.txt"), "-o", str(self.root / "x.html")]
        )
        self.assertEqual(code, 1)

    def test_missing_input_argument(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["-o", str(self.root / "x.html")])
        self.assertEqual(ctx.exception.code, 2)

    def test_help(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
