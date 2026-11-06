# 多年份 WEO 数据库构建器 v2.0

本程序面向未来批量上传多个 IEA World Energy Outlook PDF。它会增量写入 SQLite，使用 SHA-256 去重，并建立适合毕业论文的 projections、realized_values 与 projection_errors 数据结构。

## 快速运行

```bash
pip install -r requirements.txt
python run_pipeline.py ./你的WEO目录 --db weo_research.db --out exports
```

以后加入新 PDF 后，重复运行同一条命令即可。已经导入的相同文件会自动跳过。

## 数据库核心表

- `documents`：WEO 版本、年份、文件哈希和页数
- `pages`：逐页文本，支持后续检索与人工复核
- `mentions`：逐页情景和技术词频
- `projections`：经过核对的历史技术投影
- `realized_values`：实际实现值
- `projection_errors`：自动连接投影与实际值，计算 error、absolute_error、percentage_error、sMAPE

## 论文数据录入工作流

1. 批量运行 PDF 导入。
2. 使用 `exports/projections_import_template.csv` 录入经过人工核对的表格数值、页码和证据文本。
3. 使用 `exports/realized_values_import_template.csv` 录入实际值及来源。
4. 导入：

```bash
python -m weo_db_builder.import_data --db weo_research.db --projections exports/projections_import_template.csv --realized exports/realized_values_import_template.csv
```

5. 再次运行主程序导出更新后的 `projection_errors.csv`。

## 重要方法说明

WEO 情景并非普通概率预测。因此应按 scenario、publication_year、forecast_horizon、technology 和 indicator 分层比较。只有 `review_status=verified` 的投影才进入误差视图。单位、地区和指标名称必须完全一致，避免错误匹配。

## 当前自动化边界

程序自动抽取文档元数据、逐页文本、情景和技术提及。复杂 Annex 表格的数值仍应人工核对后导入，防止 PDF 表格布局导致列错位。该设计优先保证论文数据库的可审计性，而不是生成未经验证的大量数值。
