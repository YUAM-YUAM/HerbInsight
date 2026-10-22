from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "wujisan_uc"
PROJECT_DIR = ROOT / "projects" / PROJECT_ID
CONFIG_PATH = PROJECT_DIR / "project.yaml"
RESULTS_DIR = PROJECT_DIR / "results"


def read_project_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def read_data(data_files, key):
    relative_path = data_files.get(key)
    if not relative_path:
        return pd.DataFrame()

    file_path = PROJECT_DIR / relative_path
    if not file_path.exists():
        print(f"未找到文件：{file_path}")
        return pd.DataFrame()

    return pd.read_csv(file_path)


def to_boolean(series):
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes"])
    )


def main():
    config = read_project_config()
    data_files = config.get("data_files", {})

    network = read_data(data_files, "target_overlap")
    ppi = read_data(data_files, "ppi_nodes")
    transcriptome = read_data(data_files, "transcriptome_target_overlap")
    machine_learning = read_data(data_files, "ml_feature_consensus")
    mr = read_data(data_files, "mr_evidence_summary")
    immune = read_data(data_files, "immune_gene_correlations")

    # 收集所有分析中出现过的基因
    gene_sets = []
    for table in [
        network,
        ppi,
        transcriptome,
        machine_learning,
        mr,
        immune,
    ]:
        if not table.empty and "gene_symbol" in table.columns:
            gene_sets.append(set(table["gene_symbol"].dropna().astype(str)))

    all_genes = sorted(set().union(*gene_sets))
    evidence = pd.DataFrame({"gene_symbol": all_genes})

    # 1. 网络药理学证据
    if not network.empty:
        network_table = (
            network[["gene_symbol"]]
            .drop_duplicates()
            .assign(network_supported=True)
        )
        evidence = evidence.merge(network_table, on="gene_symbol", how="left")

    # 2. PPI网络拓扑信息
    if not ppi.empty:
        ppi_table = ppi[
            [
                "gene_symbol",
                "degree",
                "degree_centrality",
                "betweenness",
                "closeness",
            ]
        ].drop_duplicates("gene_symbol")

        ppi_table["ppi_rank"] = (
            ppi_table["degree"]
            .rank(method="min", ascending=False)
            .astype("Int64")
        )
        ppi_table["ppi_top20_hub"] = ppi_table["ppi_rank"] <= 20

        evidence = evidence.merge(ppi_table, on="gene_symbol", how="left")

    # 3. 转录组证据
    if not transcriptome.empty:
        transcriptome_table = transcriptome[
            [
                "gene_symbol",
                "logFC",
                "adjusted_p_value",
                "regulation",
            ]
        ].drop_duplicates("gene_symbol")

        transcriptome_table = transcriptome_table.rename(
            columns={
                "adjusted_p_value": "transcriptome_fdr",
                "regulation": "transcriptome_direction",
            }
        )
        transcriptome_table["transcriptome_supported"] = True

        evidence = evidence.merge(
            transcriptome_table,
            on="gene_symbol",
            how="left",
        )

    # 4. 机器学习证据
    if not machine_learning.empty:
        ml_table = machine_learning[
            [
                "gene_symbol",
                "model_count",
                "models",
                "mean_normalized_importance",
                "best_rank",
            ]
        ].drop_duplicates("gene_symbol")

        ml_table = ml_table.rename(
            columns={
                "model_count": "ml_model_count",
                "models": "ml_models",
                "mean_normalized_importance": "ml_mean_importance",
                "best_rank": "ml_best_rank",
            }
        )
        ml_table["ml_supported"] = True

        evidence = evidence.merge(ml_table, on="gene_symbol", how="left")

    # 5. 孟德尔随机化证据
    if not mr.empty:
        mr_columns = [
            "gene_symbol",
            "odds_ratio",
            "ci_lower",
            "ci_upper",
            "p_value",
            "fdr_adjusted_p",
            "fdr_significant",
            "direction",
            "quality_status",
            "evidence_level",
        ]
        mr_columns = [column for column in mr_columns if column in mr.columns]
        mr_table = mr[mr_columns].drop_duplicates("gene_symbol")

        mr_table = mr_table.rename(
            columns={
                "odds_ratio": "mr_odds_ratio",
                "ci_lower": "mr_ci_lower",
                "ci_upper": "mr_ci_upper",
                "p_value": "mr_p_value",
                "fdr_adjusted_p": "mr_fdr",
                "fdr_significant": "mr_fdr_supported",
                "direction": "mr_direction",
                "quality_status": "mr_quality_status",
                "evidence_level": "mr_evidence_level",
            }
        )
        mr_table["mr_analyzed"] = True

        if "mr_fdr_supported" in mr_table.columns:
            mr_table["mr_fdr_supported"] = to_boolean(
                mr_table["mr_fdr_supported"]
            )

        evidence = evidence.merge(mr_table, on="gene_symbol", how="left")

    # 6. 基因—免疫细胞相关证据
    if not immune.empty:
        immune = immune.copy()
        immune["fdr_significant"] = to_boolean(
            immune["fdr_significant"]
        )
        immune["absolute_r"] = immune["spearman_r"].abs()

        tested_counts = (
            immune.groupby("gene_symbol")
            .size()
            .rename("immune_cells_tested")
            .reset_index()
        )

        significant_immune = immune[immune["fdr_significant"]].copy()

        if not significant_immune.empty:
            immune_summary = (
                significant_immune.groupby("gene_symbol")
                .agg(
                    immune_significant_cells=("immune_cell", "nunique"),
                    immune_min_fdr=("adjusted_p_value", "min"),
                    immune_max_abs_r=("absolute_r", "max"),
                )
                .reset_index()
            )

            strongest_rows = significant_immune.loc[
                significant_immune.groupby("gene_symbol")[
                    "absolute_r"
                ].idxmax()
            ][
                [
                    "gene_symbol",
                    "immune_cell",
                    "spearman_r",
                    "correlation_direction",
                ]
            ].rename(
                columns={
                    "immune_cell": "immune_top_cell",
                    "spearman_r": "immune_top_r",
                    "correlation_direction": "immune_top_direction",
                }
            )

            immune_summary = immune_summary.merge(
                strongest_rows,
                on="gene_symbol",
                how="left",
            )
            immune_summary["immune_supported"] = True
        else:
            immune_summary = pd.DataFrame(
                columns=["gene_symbol", "immune_supported"]
            )

        immune_summary = tested_counts.merge(
            immune_summary,
            on="gene_symbol",
            how="left",
        )
        evidence = evidence.merge(
            immune_summary,
            on="gene_symbol",
            how="left",
        )

    # 补齐布尔字段
    boolean_columns = [
        "network_supported",
        "ppi_top20_hub",
        "transcriptome_supported",
        "ml_supported",
        "mr_analyzed",
        "mr_fdr_supported",
        "immune_supported",
    ]

    for column in boolean_columns:
        if column not in evidence.columns:
            evidence[column] = False
        evidence[column] = evidence[column].fillna(False).astype(bool)

    # 补齐计数字段
    integer_columns = [
        "degree",
        "ppi_rank",
        "ml_model_count",
        "ml_best_rank",
        "immune_cells_tested",
        "immune_significant_cells",
    ]

    for column in integer_columns:
        if column not in evidence.columns:
            evidence[column] = 0
        evidence[column] = (
            pd.to_numeric(evidence[column], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    # 综合证据层数
    evidence_layers = [
        "network_supported",
        "transcriptome_supported",
        "ml_supported",
        "mr_fdr_supported",
        "immune_supported",
    ]

    evidence["evidence_layer_count"] = (
        evidence[evidence_layers].astype(int).sum(axis=1)
    )

    def evidence_label(row):
        labels = []

        if row["network_supported"]:
            labels.append("网络药理学")
        if row["transcriptome_supported"]:
            labels.append("转录组")
        if row["ml_supported"]:
            labels.append("机器学习")
        if row["mr_fdr_supported"]:
            labels.append("MR-FDR显著")
        elif row["mr_analyzed"]:
            labels.append("MR已分析")
        if row["immune_supported"]:
            labels.append("免疫相关")

        return "；".join(labels) if labels else "待补充"

    evidence["evidence_sources"] = evidence.apply(
        evidence_label,
        axis=1,
    )

    def priority_tier(count):
        if count >= 4:
            return "A：多模块重点候选"
        if count == 3:
            return "B：较强候选"
        if count == 2:
            return "C：初步候选"
        return "D：单一来源"

    evidence["priority_tier"] = evidence[
        "evidence_layer_count"
    ].apply(priority_tier)

    tier_order = {
        "A：多模块重点候选": 1,
        "B：较强候选": 2,
        "C：初步候选": 3,
        "D：单一来源": 4,
    }
    evidence["_tier_order"] = evidence["priority_tier"].map(tier_order)

    evidence = evidence.sort_values(
        by=[
            "_tier_order",
            "evidence_layer_count",
            "mr_fdr_supported",
            "degree",
        ],
        ascending=[True, False, False, False],
    ).drop(columns="_tier_order")

    evidence.insert(
        0,
        "priority_rank",
        range(1, len(evidence) + 1),
    )

    # 汇总表
    top_genes = evidence.head(10)["gene_symbol"].tolist()

    summary = pd.DataFrame(
        [
            ["total_integrated_genes", len(evidence)],
            [
                "network_supported_genes",
                int(evidence["network_supported"].sum()),
            ],
            [
                "transcriptome_supported_genes",
                int(evidence["transcriptome_supported"].sum()),
            ],
            [
                "machine_learning_supported_genes",
                int(evidence["ml_supported"].sum()),
            ],
            [
                "mr_analyzed_genes",
                int(evidence["mr_analyzed"].sum()),
            ],
            [
                "mr_fdr_supported_genes",
                int(evidence["mr_fdr_supported"].sum()),
            ],
            [
                "immune_supported_genes",
                int(evidence["immune_supported"].sum()),
            ],
            [
                "priority_a_genes",
                int(
                    (
                        evidence["priority_tier"]
                        == "A：多模块重点候选"
                    ).sum()
                ),
            ],
            ["top_10_genes", "；".join(top_genes)],
            [
                "methodological_note",
                "证据层数表示不同分析模块的支持类别数量，"
                "不代表相互独立的重复验证，也不直接代表因果关系。",
            ],
        ],
        columns=["metric", "value"],
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    evidence_path = RESULTS_DIR / "integrated_evidence_matrix.csv"
    summary_path = RESULTS_DIR / "integrated_evidence_summary.csv"

    evidence.to_csv(
        evidence_path,
        index=False,
        encoding="utf-8-sig",
    )
    summary.to_csv(
        summary_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("综合证据整合完成")
    print(f"整合基因数：{len(evidence)}")
    print(
        "A级重点候选："
        f"{(evidence['priority_tier'] == 'A：多模块重点候选').sum()}"
    )
    print(f"结果文件：{evidence_path}")
    print(f"汇总文件：{summary_path}")


if __name__ == "__main__":
    main()