from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


# 项目路径
ROOT = Path(__file__).resolve().parents[1]

PROJECT_DIR = ROOT / "projects" / "wujisan_uc"
RAW_DIR = (
    PROJECT_DIR
    / "raw"
    / "immune_infiltration"
)
PROCESSED_DIR = PROJECT_DIR / "processed"
RESULTS_DIR = PROJECT_DIR / "results"

SCORES_FILE = RAW_DIR / "ssgsea_scores.csv"
STATISTICS_FILE = RAW_DIR / "group_statistics.csv"
GROUP_FILE = RAW_DIR / "sample_groups.csv"
EXPRESSION_FILE = RAW_DIR / "expression_matrix.csv"

TRANSCRIPTOME_TARGET_FILE = (
    PROCESSED_DIR
    / "transcriptome_target_overlap.csv"
)

ML_CONSENSUS_FILE = (
    PROCESSED_DIR
    / "ml_feature_consensus.csv"
)

MR_RESULTS_FILE = RESULTS_DIR / "mr_results.csv"


def check_files():
    """检查免疫浸润输入文件。"""
    required_files = [
        SCORES_FILE,
        STATISTICS_FILE,
        GROUP_FILE,
        EXPRESSION_FILE,
    ]

    missing = [
        file for file in required_files
        if not file.exists()
    ]

    if missing:
        print("以下输入文件不存在：")

        for file in missing:
            print(f"  - {file}")

        raise FileNotFoundError(
            "免疫浸润输入文件不完整。"
        )


def benjamini_hochberg(p_values):
    """计算BH校正后的P值。"""
    values = pd.to_numeric(
        p_values,
        errors="coerce"
    ).to_numpy(dtype=float)

    adjusted = np.full(
        len(values),
        np.nan
    )

    valid_positions = np.where(
        np.isfinite(values)
    )[0]

    if len(valid_positions) == 0:
        return adjusted

    valid_values = values[valid_positions]
    order = np.argsort(valid_values)
    ranked = valid_values[order]
    count = len(ranked)

    ranked_adjusted = (
        ranked
        * count
        / np.arange(1, count + 1)
    )

    ranked_adjusted = np.minimum.accumulate(
        ranked_adjusted[::-1]
    )[::-1]

    ranked_adjusted = np.clip(
        ranked_adjusted,
        0,
        1
    )

    restored = np.empty(count)
    restored[order] = ranked_adjusted
    adjusted[valid_positions] = restored

    return adjusted


def cohen_d(control_values, uc_values):
    """计算UC相对于正常对照的Cohen's d。"""
    control = pd.to_numeric(
        control_values,
        errors="coerce"
    ).dropna()

    uc = pd.to_numeric(
        uc_values,
        errors="coerce"
    ).dropna()

    if len(control) < 2 or len(uc) < 2:
        return np.nan

    pooled_variance = (
        (
            (len(control) - 1)
            * control.var(ddof=1)
        )
        + (
            (len(uc) - 1)
            * uc.var(ddof=1)
        )
    ) / (
        len(control)
        + len(uc)
        - 2
    )

    if pooled_variance <= 0:
        return 0.0

    return (
        uc.mean() - control.mean()
    ) / np.sqrt(pooled_variance)


def prepare_scores():
    """标准化样本级ssGSEA得分。"""
    scores = pd.read_csv(
        SCORES_FILE,
        encoding="utf-8-sig"
    )

    scores.columns = (
        scores.columns
        .astype(str)
        .str.strip()
    )

    rename_mapping = {
        "样本名": "sample_id",
        "分组": "label",
    }

    scores = scores.rename(
        columns=rename_mapping
    )

    if "sample_id" not in scores.columns:
        raise ValueError(
            "ssGSEA得分表缺少样本名字段。"
        )

    groups = pd.read_csv(
        GROUP_FILE,
        encoding="utf-8-sig"
    )

    groups.columns = (
        groups.columns
        .astype(str)
        .str.strip()
    )

    groups["sample_id"] = (
        groups["sample_id"]
        .astype(str)
        .str.strip()
    )

    groups["label"] = (
        groups["label"]
        .astype(str)
        .str.strip()
    )

    scores["sample_id"] = (
        scores["sample_id"]
        .astype(str)
        .str.strip()
    )

    if "label" in scores.columns:
        scores = scores.drop(
            columns=["label"]
        )

    scores = scores.merge(
        groups,
        on="sample_id",
        how="left",
        validate="one_to_one"
    )

    label_mapping = {
        "0": "Control",
        "1": "UC",
    }

    scores["group"] = (
        scores["label"]
        .map(label_mapping)
    )

    if scores["group"].isna().any():
        raise ValueError(
            "部分样本无法识别为Control或UC。"
        )

    immune_columns = [
        column
        for column in scores.columns
        if column not in [
            "sample_id",
            "label",
            "group",
        ]
    ]

    for column in immune_columns:
        scores[column] = pd.to_numeric(
            scores[column],
            errors="coerce"
        )

    scores_output = (
        PROCESSED_DIR
        / "immune_scores.csv"
    )

    scores.to_csv(
        scores_output,
        index=False,
        encoding="utf-8-sig"
    )

    long_scores = scores.melt(
        id_vars=[
            "sample_id",
            "label",
            "group",
        ],
        value_vars=immune_columns,
        var_name="immune_cell",
        value_name="ssgsea_score"
    )

    long_scores_output = (
        PROCESSED_DIR
        / "immune_scores_long.csv"
    )

    long_scores.to_csv(
        long_scores_output,
        index=False,
        encoding="utf-8-sig"
    )

    return scores, long_scores, immune_columns


def prepare_group_statistics(
    scores,
    immune_columns
):
    """整理组间检验、均值和效应量。"""
    statistics = pd.read_csv(
        STATISTICS_FILE,
        encoding="utf-8-sig"
    )

    statistics.columns = (
        statistics.columns
        .astype(str)
        .str.strip()
    )

    statistics = statistics.rename(
        columns={
            "免疫细胞": "immune_cell",
            "显著性": "original_significance",
        }
    )

    statistics["immune_cell"] = (
        statistics["immune_cell"]
        .astype(str)
        .str.strip()
    )

    statistics["p_value"] = pd.to_numeric(
        statistics["p_value"],
        errors="coerce"
    )

    statistics["p_adjust"] = pd.to_numeric(
        statistics["p_adjust"],
        errors="coerce"
    )

    rows = []

    for immune_cell in immune_columns:
        control_values = scores.loc[
            scores["group"] == "Control",
            immune_cell
        ]

        uc_values = scores.loc[
            scores["group"] == "UC",
            immune_cell
        ]

        control_mean = control_values.mean()
        uc_mean = uc_values.mean()
        difference = uc_mean - control_mean

        effect_size = cohen_d(
            control_values,
            uc_values
        )

        rows.append(
            {
                "immune_cell": immune_cell,
                "control_mean": control_mean,
                "uc_mean": uc_mean,
                "mean_difference":
                    difference,
                "cohen_d": effect_size,
                "direction": (
                    "Higher in UC"
                    if difference > 0
                    else "Lower in UC"
                    if difference < 0
                    else "No difference"
                ),
            }
        )

    calculated = pd.DataFrame(rows)

    statistics = calculated.merge(
        statistics,
        on="immune_cell",
        how="left"
    )

    statistics["fdr_significant"] = (
        statistics["p_adjust"] < 0.05
    )

    statistics["effect_magnitude"] = pd.cut(
        statistics["cohen_d"].abs(),
        bins=[
            -np.inf,
            0.2,
            0.5,
            0.8,
            np.inf,
        ],
        labels=[
            "Negligible",
            "Small",
            "Medium",
            "Large",
        ],
        right=False
    )

    statistics = statistics.sort_values(
        [
            "fdr_significant",
            "p_adjust",
        ],
        ascending=[False, True]
    )

    output_file = (
        RESULTS_DIR
        / "immune_group_statistics.csv"
    )

    statistics.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return statistics


def prepare_cell_correlations(
    scores,
    immune_columns
):
    """计算免疫细胞之间的Spearman相关矩阵。"""
    matrix = scores[
        immune_columns
    ].corr(
        method="spearman"
    )

    matrix.index.name = "immune_cell"

    output_file = (
        RESULTS_DIR
        / "immune_cell_correlations.csv"
    )

    matrix.reset_index().to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return matrix


def prepare_pca(
    scores,
    immune_columns
):
    """根据免疫细胞得分计算PCA坐标。"""
    values = (
        scores[immune_columns]
        .apply(
            pd.to_numeric,
            errors="coerce"
        )
        .fillna(
            scores[immune_columns]
            .mean()
        )
        .to_numpy(dtype=float)
    )

    means = values.mean(
        axis=0,
        keepdims=True
    )

    standard_deviations = values.std(
        axis=0,
        ddof=1,
        keepdims=True
    )

    standard_deviations[
        standard_deviations == 0
    ] = 1

    standardized = (
        values - means
    ) / standard_deviations

    _, singular_values, vt = (
        np.linalg.svd(
            standardized,
            full_matrices=False
        )
    )

    coordinates = standardized @ vt.T

    explained_variance = (
        singular_values ** 2
    ) / (
        len(standardized) - 1
    )

    explained_ratio = (
        explained_variance
        / explained_variance.sum()
    )

    pca = pd.DataFrame(
        {
            "sample_id":
                scores["sample_id"],
            "group":
                scores["group"],
            "PC1":
                coordinates[:, 0],
            "PC2":
                coordinates[:, 1],
            "PC1_explained_percent":
                explained_ratio[0] * 100,
            "PC2_explained_percent":
                explained_ratio[1] * 100,
        }
    )

    output_file = (
        RESULTS_DIR
        / "immune_pca.csv"
    )

    pca.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return pca


def select_candidate_genes():
    """选择同时获得转录组和多模型支持的候选基因。"""
    transcriptome_genes = set()
    machine_learning_genes = set()
    mr_genes = set()

    if TRANSCRIPTOME_TARGET_FILE.exists():
        transcriptome = pd.read_csv(
            TRANSCRIPTOME_TARGET_FILE,
            encoding="utf-8-sig"
        )

        if "gene_symbol" in transcriptome.columns:
            transcriptome_genes = set(
                transcriptome[
                    "gene_symbol"
                ]
                .dropna()
                .astype(str)
                .str.strip()
                .str.upper()
            )

    if ML_CONSENSUS_FILE.exists():
        ml_data = pd.read_csv(
            ML_CONSENSUS_FILE,
            encoding="utf-8-sig"
        )

        if {
            "gene_symbol",
            "model_count",
        }.issubset(ml_data.columns):
            model_counts = pd.to_numeric(
                ml_data["model_count"],
                errors="coerce"
            )

            machine_learning_genes = set(
                ml_data.loc[
                    model_counts >= 2,
                    "gene_symbol"
                ]
                .dropna()
                .astype(str)
                .str.strip()
                .str.upper()
            )

    if MR_RESULTS_FILE.exists():
        mr_data = pd.read_csv(
            MR_RESULTS_FILE,
            encoding="utf-8-sig"
        )

        if "gene_symbol" in mr_data.columns:
            mr_genes = set(
                mr_data[
                    "gene_symbol"
                ]
                .dropna()
                .astype(str)
                .str.strip()
                .str.upper()
            )

    if (
        transcriptome_genes
        and machine_learning_genes
    ):
        candidate_genes = (
            transcriptome_genes
            & machine_learning_genes
        )
    elif transcriptome_genes:
        candidate_genes = transcriptome_genes
    else:
        candidate_genes = machine_learning_genes

    evidence_rows = []

    for gene in sorted(candidate_genes):
        evidence_rows.append(
            {
                "gene_symbol": gene,
                "transcriptome_supported":
                    gene in transcriptome_genes,
                "machine_learning_supported":
                    gene in machine_learning_genes,
                "mr_analyzed":
                    gene in mr_genes,
            }
        )

    evidence = pd.DataFrame(
        evidence_rows
    )

    return sorted(candidate_genes), evidence


def prepare_gene_correlations(
    scores,
    immune_columns
):
    """计算候选基因表达与免疫得分的相关性。"""
    expression = pd.read_csv(
        EXPRESSION_FILE,
        encoding="utf-8-sig"
    )

    expression.columns = (
        expression.columns
        .astype(str)
        .str.strip()
    )

    sample_column = expression.columns[0]

    expression = expression.rename(
        columns={
            sample_column: "sample_id"
        }
    )

    expression["sample_id"] = (
        expression["sample_id"]
        .astype(str)
        .str.strip()
    )

    column_lookup = {}

    for column in expression.columns:
        if column == "sample_id":
            continue

        normalized_name = (
            str(column)
            .strip()
            .upper()
        )

        if normalized_name not in column_lookup:
            column_lookup[
                normalized_name
            ] = column

    candidate_genes, evidence = (
        select_candidate_genes()
    )

    available_genes = [
        gene
        for gene in candidate_genes
        if gene in column_lookup
    ]

    merged = scores[
        [
            "sample_id",
            "group",
        ]
        + immune_columns
    ].merge(
        expression,
        on="sample_id",
        how="inner"
    )

    rows = []

    for gene in available_genes:
        gene_column = column_lookup[gene]

        gene_values = pd.to_numeric(
            merged[gene_column],
            errors="coerce"
        )

        for immune_cell in immune_columns:
            immune_values = pd.to_numeric(
                merged[immune_cell],
                errors="coerce"
            )

            valid = (
                gene_values.notna()
                & immune_values.notna()
            )

            if valid.sum() < 5:
                correlation = np.nan
                p_value = np.nan
            else:
                result = spearmanr(
                    gene_values[valid],
                    immune_values[valid]
                )

                correlation = result.statistic
                p_value = result.pvalue

            rows.append(
                {
                    "gene_symbol": gene,
                    "immune_cell":
                        immune_cell,
                    "spearman_r":
                        correlation,
                    "p_value":
                        p_value,
                    "sample_count":
                        int(valid.sum()),
                }
            )

    correlations = pd.DataFrame(rows)

    if not correlations.empty:
        correlations[
            "adjusted_p_value"
        ] = benjamini_hochberg(
            correlations["p_value"]
        )

        correlations[
            "fdr_significant"
        ] = (
            correlations[
                "adjusted_p_value"
            ] < 0.05
        )

        correlations[
            "correlation_direction"
        ] = np.select(
            [
                correlations["spearman_r"] > 0,
                correlations["spearman_r"] < 0,
            ],
            [
                "Positive",
                "Negative",
            ],
            default="None"
        )

        correlations = correlations.merge(
            evidence,
            on="gene_symbol",
            how="left"
        )

        correlations = correlations.sort_values(
            [
                "fdr_significant",
                "adjusted_p_value",
                "spearman_r",
            ],
            ascending=[
                False,
                True,
                False,
            ]
        )

    output_file = (
        RESULTS_DIR
        / "immune_gene_correlations.csv"
    )

    correlations.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return correlations, evidence


def prepare_summary(
    scores,
    immune_columns,
    statistics,
    gene_correlations,
    evidence,
    pca
):
    """生成免疫模块摘要。"""
    significant_cells = int(
        statistics[
            "fdr_significant"
        ].sum()
    )

    uc_higher = int(
        (
            statistics[
                "fdr_significant"
            ]
            & (
                statistics["direction"]
                == "Higher in UC"
            )
        ).sum()
    )

    uc_lower = int(
        (
            statistics[
                "fdr_significant"
            ]
            & (
                statistics["direction"]
                == "Lower in UC"
            )
        ).sum()
    )

    significant_gene_correlations = 0

    if (
        not gene_correlations.empty
        and "fdr_significant"
        in gene_correlations.columns
    ):
        significant_gene_correlations = int(
            gene_correlations[
                "fdr_significant"
            ].sum()
        )

    summary = pd.DataFrame(
        [
            ["sample_count", len(scores)],
            [
                "control_samples",
                int(
                    (
                        scores["group"]
                        == "Control"
                    ).sum()
                ),
            ],
            [
                "uc_samples",
                int(
                    (
                        scores["group"]
                        == "UC"
                    ).sum()
                ),
            ],
            [
                "immune_cell_count",
                len(immune_columns),
            ],
            [
                "significant_immune_cells",
                significant_cells,
            ],
            [
                "significant_higher_in_uc",
                uc_higher,
            ],
            [
                "significant_lower_in_uc",
                uc_lower,
            ],
            [
                "candidate_gene_count",
                len(evidence),
            ],
            [
                "significant_gene_cell_correlations",
                significant_gene_correlations,
            ],
            [
                "pca_pc1_explained_percent",
                pca[
                    "PC1_explained_percent"
                ].iloc[0],
            ],
            [
                "pca_pc2_explained_percent",
                pca[
                    "PC2_explained_percent"
                ].iloc[0],
            ],
        ],
        columns=[
            "metric",
            "value",
        ]
    )

    output_file = (
        RESULTS_DIR
        / "immune_summary.csv"
    )

    summary.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )


def main():
    print("开始处理第六天免疫浸润数据……")

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    check_files()

    scores, long_scores, immune_columns = (
        prepare_scores()
    )

    statistics = prepare_group_statistics(
        scores,
        immune_columns
    )

    prepare_cell_correlations(
        scores,
        immune_columns
    )

    pca = prepare_pca(
        scores,
        immune_columns
    )

    gene_correlations, evidence = (
        prepare_gene_correlations(
            scores,
            immune_columns
        )
    )

    prepare_summary(
        scores,
        immune_columns,
        statistics,
        gene_correlations,
        evidence,
        pca
    )

    print()
    print("免疫浸润数据处理完成")
    print(f"样本数量：{len(scores)}")
    print(
        "正常对照："
        f"{(scores['group'] == 'Control').sum()}"
    )
    print(
        "UC样本："
        f"{(scores['group'] == 'UC').sum()}"
    )
    print(
        f"免疫细胞类型：{len(immune_columns)}"
    )
    print(
        "FDR显著差异免疫细胞："
        f"{statistics['fdr_significant'].sum()}"
    )
    print(
        "候选基因数量："
        f"{len(evidence)}"
    )
    print(
        "基因-免疫细胞相关记录："
        f"{len(gene_correlations)}"
    )

    if not gene_correlations.empty:
        print(
            "FDR显著基因-免疫相关："
            f"{gene_correlations['fdr_significant'].sum()}"
        )


if __name__ == "__main__":
    main()