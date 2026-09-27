# 数据分析小工具

一个轻量的 Python 数据分析小工具，用于读取 CSV、查看基础统计、计算相关性，并绘制热力图。适合快速摸底表格数据，也方便作为后续分析脚本的起点。

## 功能

- 读取 CSV 文件
- 输出描述性统计
- 计算数值列相关性
- 绘制并保存相关性热力图

## 环境要求

- Python 3.8+
- 依赖见 `requirements.txt`

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
python src/analyzer.py
```

默认会读取 `data/sample.csv`，在终端打印统计与相关性，并在当前目录生成 `correlation_heatmap.png`。

自定义数据路径：

```bash
python src/analyzer.py path/to/your.csv
```

## 项目结构

```text
.
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   └── analyzer.py      # DataAnalyzer 主程序
└── data/
    └── sample.csv       # 模拟股票小样数据
```

## 示例数据说明

`data/sample.csv` 为模拟行情，字段如下：

| 字段 | 说明 |
|------|------|
| date | 交易日 |
| code | 股票代码 |
| close | 收盘价 |
| volume | 成交量 |
| return | 日收益率 |

## 使用注意

- 请勿将体量较大的原始数据提交到仓库，本地大数据文件已在 `.gitignore` 中忽略。
- 相关性与热力图仅针对数值列计算。
