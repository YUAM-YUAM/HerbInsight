from pathlib import Path

import pandas as pd


# 项目根目录
ROOT = Path(__file__).resolve().parents[1]

PROJECT_DIR = ROOT / "projects" / "wujisan_uc"
RAW_DIR = PROJECT_DIR / "raw" / "transcriptomics" / "GSE38713"
PROCESSED_DIR = PROJECT_DIR / "processed"
RESULTS_DIR = PROJECT_DIR / "results"

EXPRESSION_FILE = RAW_DIR / "expression_matrix.csv"
GROUP_FILE = RAW_DIR / "sample_groups.csv"
DEG_FILE = RAW_DIR / "significant_genes.csv"
TARGET_FILE = PROCESSED_DIR / "target_overlap.csv"


def check_files():
    """检查所需输入文件是否存在。"""
    required_files = [
        EXPRESSION_FILE,
        GROUP_FILE,
        DEG_FILE,
        TARGET_FILE,
    ]

    missing_files = [file for file in required_files if not file.exists()]

    if missing_files:
        print("以下文件不存在：")
        for file in missing_files:
            print(f"  - {file}")
        raise FileNotFoundError("输入文件不完整，请先检查文件路径。")


def prepare_sample_groups():
    """整理样本分组信息。"""
    groups = pd.read_csv(GROUP_FILE, encoding="utf-8-sig")
    groups.columns = groups.columns.str.strip()

    required_columns = {"sample_id", "label"}
    if not required_columns.issubset(groups.columns):
        raise ValueError(
            f"样本分组表必须包含这些列：{sorted(required_columns)}"
        )

    groups["sample_id"] = groups["sample_id"].astype(str).str.strip()
    groups["label"] = groups["label"].astype(str).str.strip()

    label_mapping = {
        "0": "Control",
        "1": "UC",
    }

    groups["group"] = groups["label"].map(label_mapping)

    if groups["group"].isna().any():
        unknown_labels = groups.loc[
            groups["group"].isna(), "label"
        ].unique()
        raise ValueError(f"发现无法识别的分组标签：{unknown_labels}")

    groups["dataset"] = "GSE38713"
    groups["disease"] = "Ulcerative colitis"

    output_file = PROCESSED_DIR / "transcriptome_samples.csv"
    groups.to_csv(output_file, index=False, encoding="utf-8-sig")

    return groups


def prepare_differential_genes():
    """整理显著差异基因。"""
    degs = pd.read_csv(DEG_FILE, encoding="utf-8-sig")
    degs.columns = degs.columns.str.strip()

    required_columns = {
        "Gene",
        "logFC",
        "P.Value",
        "adj.P.Val",
    }

    if not required_columns.issubset(degs.columns):
        raise ValueError(
            f"差异基因表必须包含这些列：{sorted(required_columns)}"
        )

    degs = degs.rename(
        columns={
            "Gene": "gene_symbol",
            "P.Value": "p_value",
            "adj.P.Val": "adjusted_p_value",
            "AveExpr": "average_expression",
        }
    )

    degs["gene_symbol"] = (
        degs["gene_symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    degs["logFC"] = pd.to_numeric(degs["logFC"], errors="coerce")
    degs["p_value"] = pd.to_numeric(degs["p_value"], errors="coerce")
    degs["adjusted_p_value"] = pd.to_numeric(
        degs["adjusted_p_value"], errors="coerce"
    )

    degs = degs.dropna(
        subset=["gene_symbol", "logFC", "adjusted_p_value"]
    )

    # 再次执行显著性筛选，保证标准统一
    degs = degs[
        (degs["adjusted_p_value"] < 0.05)
        & (degs["logFC"].abs() > 0.58)
    ].copy()

    degs["regulation"] = degs["logFC"].apply(
        lambda value: "Up" if value > 0 else "Down"
    )
    degs["dataset"] = "GSE38713"
    degs["comparison"] = "UC vs Control"
    degs["evidence_type"] = "Transcriptomic differential expression"

    degs = degs.sort_values(
        by=["adjusted_p_value", "logFC"],
        ascending=[True, False],
    )

    output_file = PROCESSED_DIR / "transcriptome_degs.csv"
    degs.to_csv(output_file, index=False, encoding="utf-8-sig")

    return degs


def prepare_target_overlap(degs):
    """计算差异基因与网络药理学共同靶点的交集。"""
    targets = pd.read_csv(TARGET_FILE, encoding="utf-8-sig")
    targets.columns = targets.columns.str.strip()

    if "gene_symbol" not in targets.columns:
        raise ValueError("target_overlap.csv 中缺少 gene_symbol 列。")

    targets["gene_symbol"] = (
        targets["gene_symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    targets = targets.drop_duplicates(subset=["gene_symbol"])

    overlap = targets.merge(
        degs,
        on="gene_symbol",
        how="inner",
        suffixes=("_network", "_transcriptome"),
    )

    overlap["integrated_evidence"] = (
        "网络药理学共同靶点 + UC转录组差异表达"
    )

    overlap = overlap.sort_values(
        by=["adjusted_p_value", "logFC"],
        ascending=[True, False],
    )

    output_file = (
        PROCESSED_DIR / "transcriptome_target_overlap.csv"
    )
    overlap.to_csv(output_file, index=False, encoding="utf-8-sig")

    return overlap


def prepare_summary(groups, degs, overlap):
    """生成网页需要使用的统计摘要。"""
    # 只读取表达矩阵表头，避免重复加载全部数据
    expression_columns = pd.read_csv(
        EXPRESSION_FILE,
        nrows=0,
        encoding="utf-8-sig",
    ).columns

    gene_count = max(len(expression_columns) - 1, 0)

    summary = pd.DataFrame(
        [
            ["dataset", "GSE38713"],
            ["comparison", "UC vs Control"],
            ["control_samples", int((groups["group"] == "Control").sum())],
            ["uc_samples", int((groups["group"] == "UC").sum())],
            ["expression_genes", gene_count],
            ["significant_degs", len(degs)],
            ["upregulated_genes", int((degs["regulation"] == "Up").sum())],
            ["downregulated_genes", int((degs["regulation"] == "Down").sum())],
            ["network_supported_degs", len(overlap)],
            ["fdr_threshold", 0.05],
            ["absolute_logfc_threshold", 0.58],
        ],
        columns=["metric", "value"],
    )

    output_file = RESULTS_DIR / "transcriptome_summary.csv"
    summary.to_csv(output_file, index=False, encoding="utf-8-sig")


def main():
    print("开始处理第三天转录组数据……")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    check_files()

    groups = prepare_sample_groups()
    degs = prepare_differential_genes()
    overlap = prepare_target_overlap(degs)
    prepare_summary(groups, degs, overlap)

    print()
    print("转录组数据处理完成")
    print(f"样本总数：{len(groups)}")
    print(f"正常对照：{(groups['group'] == 'Control').sum()}")
    print(f"UC样本：{(groups['group'] == 'UC').sum()}")
    print(f"显著差异基因：{len(degs)}")
    print(f"上调基因：{(degs['regulation'] == 'Up').sum()}")
    print(f"下调基因：{(degs['regulation'] == 'Down').sum()}")
    print(f"具有转录组证据的共同靶点：{len(overlap)}")


if __name__ == "__main__":
    main()