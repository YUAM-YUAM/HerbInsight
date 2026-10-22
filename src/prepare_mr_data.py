from pathlib import Path

import numpy as np
import pandas as pd


# 项目路径
ROOT = Path(__file__).resolve().parents[1]

PROJECT_DIR = ROOT / "projects" / "wujisan_uc"
RAW_DIR = (
    PROJECT_DIR
    / "raw"
    / "mendelian_randomization"
)
CORE_DIR = RAW_DIR / "core_genes"
PRESSO_DIR = RAW_DIR / "mr_presso"

PROCESSED_DIR = PROJECT_DIR / "processed"
RESULTS_DIR = PROJECT_DIR / "results"

GENES = [
    "CASP1",
    "COL1A1",
    "CTSB",
    "CXCL1",
    "IRF1",
    "SERPINA1",
]


def check_files():
    """检查MR输入文件是否完整。"""
    required = [
        RAW_DIR / "full_snp_summary.csv",
        RAW_DIR / "top50_snp_summary.csv",
        PRESSO_DIR / "mr_presso_summary.csv",
    ]

    for gene in GENES:
        required.extend(
            [
                CORE_DIR / gene / "mr_results.csv",
                CORE_DIR / gene / "heterogeneity.csv",
                CORE_DIR / gene / "pleiotropy.csv",
            ]
        )

    missing = [
        file for file in required
        if not file.exists()
    ]

    if missing:
        print("以下文件不存在：")

        for file in missing:
            print(f"  - {file}")

        raise FileNotFoundError(
            "孟德尔随机化输入文件不完整。"
        )


def benjamini_hochberg(p_values):
    """计算Benjamini-Hochberg校正P值。"""
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
    ranked_values = valid_values[order]

    count = len(ranked_values)

    ranked_adjusted = (
        ranked_values
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

    valid_adjusted = np.empty(count)
    valid_adjusted[order] = ranked_adjusted
    adjusted[valid_positions] = valid_adjusted

    return adjusted


def prepare_summary_file(
    input_file,
    strategy_name
):
    """标准化一套MR汇总结果。"""
    data = pd.read_csv(
        input_file,
        encoding="utf-8-sig"
    )

    data.columns = data.columns.str.strip()

    rename_mapping = {
        "基因": "gene_symbol",
        "SNP筛选策略": "source_strategy",
        "筛选阈值": "instrument_threshold",
        "原始SNP数": "initial_snp_count",
        "最终有效SNP数": "valid_snp_count",
        "OR值": "odds_ratio",
        "OR_95.CI_L": "ci_lower",
        "OR_95.CI_U": "ci_upper",
        "P值": "p_value",
        "GWAS_ID": "outcome_gwas_id",
        "表型": "outcome",
    }

    data = data.rename(
        columns=rename_mapping
    )

    required_columns = {
        "gene_symbol",
        "valid_snp_count",
        "odds_ratio",
        "ci_lower",
        "ci_upper",
        "p_value",
    }

    if not required_columns.issubset(
        data.columns
    ):
        missing = sorted(
            required_columns - set(data.columns)
        )

        raise ValueError(
            f"{input_file.name} 缺少字段：{missing}"
        )

    data["gene_symbol"] = (
        data["gene_symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    numeric_columns = [
        "initial_snp_count",
        "valid_snp_count",
        "odds_ratio",
        "ci_lower",
        "ci_upper",
        "p_value",
    ]

    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

    data["instrument_strategy"] = strategy_name
    data["mr_method"] = (
        "Inverse variance weighted"
    )

    data["direction"] = np.select(
        [
            data["odds_ratio"] > 1,
            data["odds_ratio"] < 1,
        ],
        [
            "Risk direction",
            "Protective direction",
        ],
        default="Null direction"
    )

    data["nominal_significant"] = (
        data["p_value"] < 0.05
    )

    # 6个基因的Bonferroni阈值
    bonferroni_threshold = 0.05 / len(GENES)

    data["bonferroni_significant"] = (
        data["p_value"]
        < bonferroni_threshold
    )

    data["fdr_adjusted_p"] = (
        benjamini_hochberg(
            data["p_value"]
        )
    )

    data["fdr_significant"] = (
        data["fdr_adjusted_p"] < 0.05
    )

    data["log_odds_ratio"] = np.log(
        data["odds_ratio"]
    )

    data["minus_log10_p"] = -np.log10(
        data["p_value"].clip(lower=1e-300)
    )

    return data


def prepare_main_results():
    """整理全SNP与Top 50 SNP两种策略。"""
    full_snp = prepare_summary_file(
        RAW_DIR / "full_snp_summary.csv",
        "All available instruments"
    )

    top50 = prepare_summary_file(
        RAW_DIR / "top50_snp_summary.csv",
        "Top 50 instruments"
    )

    combined = pd.concat(
        [full_snp, top50],
        ignore_index=True
    )

    combined = combined.sort_values(
        [
            "instrument_strategy",
            "p_value",
        ],
        ascending=[True, True]
    )

    output_file = RESULTS_DIR / "mr_results.csv"

    combined.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return combined


def prepare_method_results():
    """整理各基因多种MR估计方法。"""
    tables = []

    for gene in GENES:
        file_path = (
            CORE_DIR
            / gene
            / "mr_results.csv"
        )

        data = pd.read_csv(
            file_path,
            encoding="utf-8-sig"
        )

        data.columns = data.columns.str.strip()
        data["gene_symbol"] = gene

        rename_mapping = {
            "nsnp": "snp_count",
            "b": "beta",
            "pval": "p_value",
            "lo_ci": "beta_ci_lower",
            "up_ci": "beta_ci_upper",
            "or": "odds_ratio",
            "or_lci95": "ci_lower",
            "or_uci95": "ci_upper",
        }

        data = data.rename(
            columns=rename_mapping
        )

        numeric_columns = [
            "snp_count",
            "beta",
            "se",
            "p_value",
            "beta_ci_lower",
            "beta_ci_upper",
            "odds_ratio",
            "ci_lower",
            "ci_upper",
        ]

        for column in numeric_columns:
            if column in data.columns:
                data[column] = pd.to_numeric(
                    data[column],
                    errors="coerce"
                )

        data["nominal_significant"] = (
            data["p_value"] < 0.05
        )

        tables.append(data)

    method_results = pd.concat(
        tables,
        ignore_index=True
    )

    preferred_columns = [
        "gene_symbol",
        "method",
        "snp_count",
        "beta",
        "se",
        "p_value",
        "odds_ratio",
        "ci_lower",
        "ci_upper",
        "nominal_significant",
        "id.outcome",
        "outcome",
    ]

    available_columns = [
        column
        for column in preferred_columns
        if column in method_results.columns
    ]

    method_results = method_results[
        available_columns
    ]

    output_file = (
        PROCESSED_DIR
        / "mr_method_results.csv"
    )

    method_results.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return method_results


def prepare_sensitivity_results():
    """整合异质性与水平多效性检验。"""
    rows = []

    for gene in GENES:
        heterogeneity_file = (
            CORE_DIR
            / gene
            / "heterogeneity.csv"
        )

        pleiotropy_file = (
            CORE_DIR
            / gene
            / "pleiotropy.csv"
        )

        heterogeneity = pd.read_csv(
            heterogeneity_file,
            encoding="utf-8-sig"
        )

        pleiotropy = pd.read_csv(
            pleiotropy_file,
            encoding="utf-8-sig"
        )

        heterogeneity.columns = (
            heterogeneity.columns.str.strip()
        )

        pleiotropy.columns = (
            pleiotropy.columns.str.strip()
        )

        ivw_row = heterogeneity[
            heterogeneity["method"]
            .astype(str)
            .str.contains(
                "Inverse variance weighted",
                case=False,
                regex=False,
                na=False
            )
        ]

        if ivw_row.empty:
            heterogeneity_q = np.nan
            heterogeneity_p = np.nan
        else:
            heterogeneity_q = pd.to_numeric(
                ivw_row.iloc[0].get("Q"),
                errors="coerce"
            )

            heterogeneity_p = pd.to_numeric(
                ivw_row.iloc[0].get("Q_pval"),
                errors="coerce"
            )

        if pleiotropy.empty:
            egger_intercept = np.nan
            pleiotropy_p = np.nan
        else:
            egger_intercept = pd.to_numeric(
                pleiotropy.iloc[0].get(
                    "egger_intercept"
                ),
                errors="coerce"
            )

            pleiotropy_p = pd.to_numeric(
                pleiotropy.iloc[0].get("pval"),
                errors="coerce"
            )

        heterogeneity_flag = (
            pd.notna(heterogeneity_p)
            and heterogeneity_p < 0.05
        )

        pleiotropy_flag = (
            pd.notna(pleiotropy_p)
            and pleiotropy_p < 0.05
        )

        if pleiotropy_flag:
            quality_status = (
                "Horizontal pleiotropy concern"
            )
        elif heterogeneity_flag:
            quality_status = (
                "Heterogeneity concern"
            )
        else:
            quality_status = (
                "No statistical concern detected"
            )

        rows.append(
            {
                "gene_symbol": gene,
                "ivw_q_statistic":
                    heterogeneity_q,
                "heterogeneity_p_value":
                    heterogeneity_p,
                "egger_intercept":
                    egger_intercept,
                "pleiotropy_p_value":
                    pleiotropy_p,
                "heterogeneity_flag":
                    heterogeneity_flag,
                "pleiotropy_flag":
                    pleiotropy_flag,
                "quality_status":
                    quality_status,
            }
        )

    sensitivity = pd.DataFrame(rows)

    output_file = (
        PROCESSED_DIR
        / "mr_sensitivity_results.csv"
    )

    sensitivity.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return sensitivity


def parse_presso_p_value(value):
    """将MR-PRESSO字符型P值转换为数值。"""
    if pd.isna(value):
        return np.nan

    text = str(value).strip()

    if text.startswith("<"):
        text = text[1:].strip()

    return pd.to_numeric(
        text,
        errors="coerce"
    )


def prepare_presso_results():
    """整理MR-PRESSO全局检验结果。"""
    data = pd.read_csv(
        PRESSO_DIR / "mr_presso_summary.csv",
        encoding="utf-8-sig"
    )

    data.columns = data.columns.str.strip()

    data = data.rename(
        columns={
            "基因": "gene_symbol",
            "全局检验P值": "global_test_p_value_raw",
            "异常值数量": "outlier_count",
            "原始Beta": "original_beta",
            "原始P值": "original_p_value",
        }
    )

    data["gene_symbol"] = (
        data["gene_symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    data["global_test_p_value"] = (
        data["global_test_p_value_raw"]
        .apply(parse_presso_p_value)
    )

    data["outlier_count"] = pd.to_numeric(
        data["outlier_count"],
        errors="coerce"
    )

    data["global_test_significant"] = (
        data["global_test_p_value"] < 0.05
    )

    data["presso_interpretation"] = np.where(
        data["global_test_significant"],
        (
            "Potential horizontal pleiotropy "
            "or outlier concern"
        ),
        "No MR-PRESSO global concern detected"
    )

    output_file = RESULTS_DIR / "mr_presso.csv"

    data.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return data


def prepare_strategy_comparison(main_results):
    """比较两种SNP筛选策略的结论一致性。"""
    selected_columns = [
        "gene_symbol",
        "instrument_strategy",
        "odds_ratio",
        "ci_lower",
        "ci_upper",
        "p_value",
        "nominal_significant",
        "fdr_significant",
        "direction",
        "valid_snp_count",
    ]

    comparison = main_results[
        selected_columns
    ].pivot(
        index="gene_symbol",
        columns="instrument_strategy"
    )

    comparison.columns = [
        (
            f"{str(strategy).lower().replace(' ', '_')}"
            f"__{column}"
        )
        for column, strategy
        in comparison.columns
    ]

    comparison = comparison.reset_index()

    full_prefix = (
        "all_available_instruments"
    )

    top50_prefix = (
        "top_50_instruments"
    )

    full_or = (
        f"{full_prefix}__odds_ratio"
    )

    top50_or = (
        f"{top50_prefix}__odds_ratio"
    )

    full_sig = (
        f"{full_prefix}__nominal_significant"
    )

    top50_sig = (
        f"{top50_prefix}__nominal_significant"
    )

    comparison["direction_consistent"] = (
        np.sign(
            comparison[full_or] - 1
        )
        == np.sign(
            comparison[top50_or] - 1
        )
    )

    comparison[
        "significance_consistent"
    ] = (
        comparison[full_sig]
        == comparison[top50_sig]
    )

    comparison["strategy_status"] = np.select(
        [
            (
                comparison["direction_consistent"]
                & comparison[
                    "significance_consistent"
                ]
            ),
            comparison["direction_consistent"],
        ],
        [
            "Direction and significance consistent",
            "Direction consistent; significance differs",
        ],
        default="Direction differs"
    )

    output_file = (
        PROCESSED_DIR
        / "mr_strategy_comparison.csv"
    )

    comparison.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return comparison


def prepare_evidence_table(
    main_results,
    sensitivity,
    comparison
):
    """生成综合MR证据表。"""
    full_results = main_results[
        main_results["instrument_strategy"]
        == "All available instruments"
    ].copy()

    evidence = full_results.merge(
        sensitivity,
        on="gene_symbol",
        how="left"
    )

    evidence = evidence.merge(
        comparison[
            [
                "gene_symbol",
                "direction_consistent",
                "significance_consistent",
                "strategy_status",
            ]
        ],
        on="gene_symbol",
        how="left"
    )

    evidence["evidence_level"] = "Exploratory"

    strong_mask = (
        evidence["fdr_significant"]
        & evidence["direction_consistent"]
        & ~evidence["pleiotropy_flag"].fillna(False)
    )

    moderate_mask = (
        evidence["nominal_significant"]
        & evidence["direction_consistent"]
        & ~evidence["pleiotropy_flag"].fillna(False)
    )

    evidence.loc[
        moderate_mask,
        "evidence_level"
    ] = "Moderate"

    evidence.loc[
        strong_mask,
        "evidence_level"
    ] = "Relatively stronger"

    evidence.loc[
        evidence["pleiotropy_flag"].fillna(False),
        "evidence_level"
    ] = "Sensitivity concern"

    evidence["interpretation"] = np.select(
        [
            evidence["pleiotropy_flag"].fillna(False),
            ~evidence["direction_consistent"].fillna(False),
            (
                evidence["nominal_significant"]
                & evidence["direction_consistent"]
            ),
        ],
        [
            (
                "存在水平多效性信号，"
                "因果解释需谨慎"
            ),
            (
                "不同SNP策略方向不一致，"
                "结果稳定性有限"
            ),
            (
                "两种策略方向一致且全SNP结果显著，"
                "可作为候选遗传证据"
            ),
        ],
        default=(
            "当前结果不足以支持稳定遗传关联"
        )
    )

    output_file = (
        RESULTS_DIR
        / "mr_evidence_summary.csv"
    )

    evidence.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return evidence


def prepare_overall_summary(
    main_results,
    sensitivity,
    comparison,
    presso
):
    """生成网页统计摘要。"""
    full_results = main_results[
        main_results["instrument_strategy"]
        == "All available instruments"
    ]

    top50_results = main_results[
        main_results["instrument_strategy"]
        == "Top 50 instruments"
    ]

    summary = pd.DataFrame(
        [
            ["analyzed_genes", len(GENES)],
            [
                "full_snp_nominal_significant",
                int(
                    full_results[
                        "nominal_significant"
                    ].sum()
                ),
            ],
            [
                "full_snp_fdr_significant",
                int(
                    full_results[
                        "fdr_significant"
                    ].sum()
                ),
            ],
            [
                "top50_nominal_significant",
                int(
                    top50_results[
                        "nominal_significant"
                    ].sum()
                ),
            ],
            [
                "direction_consistent_genes",
                int(
                    comparison[
                        "direction_consistent"
                    ].sum()
                ),
            ],
            [
                "pleiotropy_concerns",
                int(
                    sensitivity[
                        "pleiotropy_flag"
                    ].sum()
                ),
            ],
            [
                "presso_global_concerns",
                int(
                    presso[
                        "global_test_significant"
                    ].sum()
                ),
            ],
        ],
        columns=["metric", "value"]
    )

    output_file = RESULTS_DIR / "mr_summary.csv"

    summary.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )


def main():
    print("开始处理第五天孟德尔随机化数据……")

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    check_files()

    main_results = prepare_main_results()
    method_results = prepare_method_results()
    sensitivity = prepare_sensitivity_results()
    presso = prepare_presso_results()

    comparison = prepare_strategy_comparison(
        main_results
    )

    evidence = prepare_evidence_table(
        main_results,
        sensitivity,
        comparison
    )

    prepare_overall_summary(
        main_results,
        sensitivity,
        comparison,
        presso
    )

    full_results = main_results[
        main_results["instrument_strategy"]
        == "All available instruments"
    ]

    top50_results = main_results[
        main_results["instrument_strategy"]
        == "Top 50 instruments"
    ]

    print()
    print("孟德尔随机化数据处理完成")
    print(f"分析基因数：{len(GENES)}")
    print(f"两种策略结果记录：{len(main_results)}")
    print(f"多方法MR记录：{len(method_results)}")
    print(
        "全SNP名义显著基因："
        f"{full_results['nominal_significant'].sum()}"
    )
    print(
        "Top 50名义显著基因："
        f"{top50_results['nominal_significant'].sum()}"
    )
    print(
        "两种策略方向一致基因："
        f"{comparison['direction_consistent'].sum()}"
    )
    print(
        "水平多效性风险："
        f"{sensitivity['pleiotropy_flag'].sum()}"
    )
    print(
        "MR-PRESSO全局风险："
        f"{presso['global_test_significant'].sum()}"
    )
    print(
        f"综合证据记录：{len(evidence)}"
    )


if __name__ == "__main__":
    main()