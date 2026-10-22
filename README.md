# HerbInsight —— 中药复方多组学机制分析平台

面向初学者的中药网络药理学教学与在线实训平台，并提供多组学证据展示。
第一个示范项目：**五积散 干预 溃疡性结肠炎**。

> 本系统用于科研辅助和教育展示，不用于临床诊断、治疗决策或未经验证的疗效宣传。

## 技术架构

Python + Streamlit + Pandas + NetworkX + Plotly

## 教学实训模式

平台采用“学原理—备数据—做分析—读结果—交作业”的统一教学结构。
GO/KEGG 在线实验室已支持用户上传目标基因、背景基因和功能注释表，
现场执行超几何检验与 Benjamini-Hochberg 校正，并导出结果和方法记录。
后续将依次接入网络药理学、机器学习、孟德尔随机化与计算扰动实验。

## 快速开始（Windows）

```powershell
cd C:\Users\32330\Desktop\HerbInsight
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

浏览器打开 http://localhost:8501

## 目录结构

```
HerbInsight/
├── app.py                  # Streamlit 入口（主程序）
├── requirements.txt        # Python 依赖
├── config/                 # 平台级配置
├── projects/               # 项目目录（每个复方-疾病一个项目）
│   └── wujisan_uc/         # 示范项目：五积散-溃疡性结肠炎
│       ├── project.yaml    # 项目配置（模块开关 + 数据文件路径）
│       ├── raw/            # 原始数据（只读，勿改动）
│       ├── processed/      # 标准化后的数据
│       ├── results/        # 分析结果
│       ├── figures/        # 图表
│       ├── reports/        # 报告
│       └── metadata/       # 元数据/来源记录
├── src/                    # 分析模块代码
└── tests/                  # 测试
```

## 数据规范（核心 CSV 文件）

每条重要记录至少保留：来源数据库、查询日期、原始ID、证据类型、物种、筛选条件、备注。

| 文件 | 说明 | 关键字段 |
|---|---|---|
| herbs.csv | 药材清单 | herb_name, latin_name, source_db, evidence_type |
| compound_targets.csv | 成分-靶点 | herb, compound, gene_symbol, source_db, query_date |
| disease_genes.csv | 疾病基因 | gene_symbol, source_db, evidence_score, screening_criteria |
| target_overlap.csv | 交集靶点 | gene_symbol, herb_count, evidence_type |
| ppi_nodes.csv | PPI节点 | node_id, gene_symbol, degree, betweenness, closeness |
| ppi_edges.csv | PPI边 | source, target, combined_score |
| go_enrichment.csv | GO富集 | term_id, term_name, category, gene_ratio, p_adjust, genes |
| kegg_enrichment.csv | KEGG富集 | pathway_id, pathway_name, gene_ratio, p_adjust, genes |
| deg_results.csv | 差异表达 | gene_symbol, log2fc, p_value, p_adjust, dataset |
| ml_metrics.csv | 机器学习 | model, auc, acc, feature, importance |
| mr_results.csv | 孟德尔随机化 | exposure, outcome, method, or, ci_low, ci_high, p_value |

## 从"原材料"目录接入数据

1. 现有材料位于 `C:\Users\32330\Desktop\原材料`（只读，勿改动）。
2. 将整理好的 CSV 副本放入 `projects\wujisan_uc\processed\` 和 `results\`。
3. 更新 `project.yaml` 中 `data_files` 字段。
4. 重启 `streamlit run app.py` 即可看到数据。

> 原始材料只读保存，平台处理结果另存，避免破坏已有研究成果。
