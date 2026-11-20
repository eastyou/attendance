# attendance

[![CI](https://github.com/eastyou/attendance/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/attendance/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

给班主任用的班级考勤表：把名单整理成每行一个名字，一条命令生成 A4 横向可打印考勤表。**零依赖，不联网，打印即用。**

表格按自然月生成 1 日到月末的日列，周末自动浅色底，名单超过每页行数时自动分页并重复表头，右侧留出勤、请假、迟到三列做统计。

## 特性

- **整月日列**：按 `--month` 自动计算 28~31 天，闰年 2 月也能正确显示
- **周末标色**：周六、周日的日列自动浅灰底、红色表头，一眼看清
- **自动分页**：`--rows` 设置每页 10~40 人，超出自动分页，每页重复表头
- **宽度自适应**：日列按可用宽度 267mm 自动压缩，整月 31 天也不挤
- **学号可选**：名单可只写姓名，也可用「学号,姓名」两列；没学号时自动填序号
- **名单宽松**：纯文本每行一名，或 CSV；表头可选，空行自动跳过
- **逐行校验**：空姓名、重名、超长姓名或学号都会指出具体行号
- **编码兼容**：UTF-8（含 BOM）与 GBK 自动识别，Excel 导出的 CSV 可直接用
- **页脚图例**：✓ 出勤、○ 请假、△ 迟到，学生一看就懂
- **77 个单元测试**：覆盖名单解析、月份校验、周末判断、分页、排版与命令行

## 安装

```bash
pip install attendance
```

也可以直接下载源码，在项目目录里运行：

```bash
python -m attendance --help
```

## 用法

准备名单 `名单.csv`：

```csv
学号,姓名
2026001,张三
2026002,李四
```

生成 2026 年 11 月的考勤表：

```bash
python -m attendance -i 名单.csv --month 2026-11
```

每页 15 人、带上班级名：

```bash
python -m attendance -i 名单.csv --month 2026-11 --rows 15 --group 初二3班
```

不传 `--month` 时默认当月。

### 参数

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `-i, --input` | 名单文件，txt 每行一名或 CSV（学号,姓名） | 必填 |
| `-o, --output` | 输出 HTML 路径 | `考勤表.html` |
| `--month` | 月份 `YYYY-MM` | 当月 |
| `--rows` | 每页行数 10~40 | `30` |
| `--group` | 班级名称 | `班级` |
| `--title` | 页面标题 | `考勤表` |

### 名单格式

支持三种写法：

```text
张三
李四
```

```csv
姓名
张三
李四
```

```csv
学号,姓名
2026001,张三
2026002,李四
```

- 表头可有可无，支持 `姓名/名字/学生`、`学号/编号/序号`
- 姓名最多 20 个字符，学号最多 12 个字符
- 姓名不能重复，重复会指出两次出现的行号
- 编码支持 UTF-8（含 BOM）与 GBK

## 打印

用浏览器打开生成的 HTML，按 `Ctrl/Cmd + P`：

- 纸张：A4 横向
- 边距：无 / 默认
- 勾选「背景图形」，周末底色才会打印

打印后可直接发给学生每日勾选，也可由老师统一登记。

## 项目结构

```text
attendance/
├── attendance/
│   ├── model.py    # 名单解析、月份校验、周末判断与分页
│   ├── render.py   # A4 横向考勤表排版
│   └── cli.py      # 命令行入口
├── tests/          # 77 个单元测试
└── examples/       # 示例名单
```

## 开发

```bash
python -m unittest discover -s tests
```

## 许可证

[MIT](LICENSE) © 2026 eastyou
