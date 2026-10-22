from pathlib import Path

import pandas as pd


# 项目路径
ROOT = Path(__file__).resolve().parents[1]

PROJECT_DIR = ROOT / "projects" / "wujisan_uc"
RAW_DIR = PROJECT_DIR / "raw" / "machine_learning"
PROCESSED_DIR = PROJECT_DIR / "processed"
RESULTS_DIR = PROJECT_DIR / "results"


FEATURE_FILES = {
    "LASSO-Logistic": "lasso_features.csv",
    "ElasticNet": "elasticnet_features.csv",
    "Random Forest": "random_forest_features.csv",
    "XGBoost": "xgboost_features.csv",
}


def check_input_files():
    """检查机器学习输入文件是否完整。"""
    required_files = [
        RAW_DIR / "training_metrics.csv",
        RAW_DIR / "validation_metrics.csv",
        RAW_DIR / "dataset_auc.csv",
    ]

    required_files.extend(
        RAW_DIR / filename
        for filename in FEATURE_FILES.values()
    )

    missing_files = [
        file for file in required_files
        if not file.exists()
    ]

    if missing_files:
        print("以下文件不存在：")
        for file in missing_files:
            print(f"  - {file}")

        raise FileNotFoundError(
            "机器学习输入文件不完整。"
        )


def prepare_model_metrics():
    """整合训练集和内部验证集性能指标。"""
    training = pd.read_csv(
        RAW_DIR / "training_metrics.csv",
        encoding="utf-8-sig"
    )

    validation = pd.read_csv(
        RAW_DIR / "validation_metrics.csv",
        encoding="utf-8-sig"
    )

    training.columns = training.columns.str.strip()
    validation.columns = validation.columns.str.strip()

    training["evaluation_set"] = "Training"
    validation["evaluation_set"] = "Internal validation"

    metrics = pd.concat(
        [training, validation],
        ignore_index=True
    )

    numeric_columns = [
        "Accuracy",
        "AUC_ROC",
        "Sensitivity",
        "Specificity",
        "Precision",
        "Recall",
        "F1",
        "MCC",
    ]

    for column in numeric_columns:
        if column in metrics.columns:
            metrics[column] = pd.to_numeric(
                metrics[column],
                errors="coerce"
            )

    metrics = metrics.sort_values(
        ["evaluation_set", "AUC_ROC", "Accuracy"],
        ascending=[True, False, False]
    )

    output_file = RESULTS_DIR / "ml_metrics.csv"
    metrics.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return metrics


def prepare_dataset_auc():
    """整理训练、内部验证和外部验证AUC。"""
    auc_data = pd.read_csv(
        RAW_DIR / "dataset_auc.csv",
        encoding="utf-8-sig"
    )

    auc_data.columns = auc_data.columns.str.strip()

    rename_mapping = {
        "训练集AUC": "Training",
        "内部验证集AUC": "Internal validation",
        "外部验证集AUC(GSE38713)": "External GSE38713",
    }

    auc_data = auc_data.rename(
        columns=rename_mapping
    )

    required_columns = {
        "Algorithm",
        "Training",
        "Internal validation",
        "External GSE38713",
    }

    if not required_columns.issubset(auc_data.columns):
        raise ValueError(
            "dataset_auc.csv 缺少必要字段。"
        )

    long_auc = auc_data.melt(
        id_vars="Algorithm",
        value_vars=[
            "Training",
            "Internal validation",
            "External GSE38713",
        ],
        var_name="evaluation_set",
        value_name="AUC"
    )

    long_auc["AUC"] = pd.to_numeric(
        long_auc["AUC"],
        errors="coerce"
    )

    long_auc = long_auc.dropna(
        subset=["Algorithm", "AUC"]
    )

    output_file = RESULTS_DIR / "ml_auc.csv"
    long_auc.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return long_auc


def prepare_feature_importance():
    """整合不同模型的特征基因重要性。"""
    feature_tables = []

    for algorithm, filename in FEATURE_FILES.items():
        file_path = RAW_DIR / filename

        data = pd.read_csv(
            file_path,
            encoding="utf-8-sig"
        )

        data.columns = data.columns.str.strip()

        if not {"Gene", "Importance"}.issubset(
            data.columns
        ):
            raise ValueError(
                f"{filename} 缺少 Gene 或 Importance 字段。"
            )

        data = data.rename(
            columns={
                "Gene": "gene_symbol",
                "Importance": "raw_importance",
            }
        )

        data["gene_symbol"] = (
            data["gene_symbol"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        data["raw_importance"] = pd.to_numeric(
            data["raw_importance"],
            errors="coerce"
        )

        data = data.dropna(
            subset=["gene_symbol", "raw_importance"]
        )

        data["absolute_importance"] = (
            data["raw_importance"].abs()
        )

        maximum_importance = (
            data["absolute_importance"].max()
        )

        if maximum_importance > 0:
            data["normalized_importance"] = (
                data["absolute_importance"]
                / maximum_importance
            )
        else:
            data["normalized_importance"] = 0.0

        data["feature_rank"] = (
            data["absolute_importance"]
            .rank(
                method="first",
                ascending=False
            )
            .astype(int)
        )

        data["Algorithm"] = algorithm

        feature_tables.append(data)

    features = pd.concat(
        feature_tables,
        ignore_index=True
    )

    features = features.sort_values(
        ["Algorithm", "feature_rank"]
    )

    output_file = (
        PROCESSED_DIR / "ml_feature_importance.csv"
    )

    features.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return features


def prepare_feature_consensus(features):
    """计算被多个模型共同支持的特征基因。"""
    consensus = (
        features
        .groupby("gene_symbol")
        .agg(
            model_count=(
                "Algorithm",
                "nunique"
            ),
            models=(
                "Algorithm",
                lambda values: "；".join(
                    sorted(set(values))
                )
            ),
            mean_normalized_importance=(
                "normalized_importance",
                "mean"
            ),
            maximum_normalized_importance=(
                "normalized_importance",
                "max"
            ),
            best_rank=(
                "feature_rank",
                "min"
            ),
        )
        .reset_index()
    )

    consensus = consensus.sort_values(
        [
            "model_count",
            "mean_normalized_importance",
            "best_rank",
        ],
        ascending=[False, False, True]
    )

    output_file = (
        PROCESSED_DIR / "ml_feature_consensus.csv"
    )

    consensus.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return consensus


def prepare_quality_flags(metrics, auc_data):
    """识别需要谨慎解释的模型结果。"""
    flags = []

    internal_validation = metrics[
        metrics["evaluation_set"]
        == "Internal validation"
    ]

    for _, row in internal_validation.iterrows():
        algorithm = row["Algorithm"]

        specificity = row.get("Specificity")
        auc_value = row.get("AUC_ROC")

        if pd.notna(specificity) and specificity <= 0.05:
            flags.append(
                {
                    "Algorithm": algorithm,
                    "issue_type": "Threshold performance",
                    "severity": "High",
                    "description": (
                        "内部验证特异度接近0，"
                        "说明当前分类阈值可能无法正确识别对照样本。"
                    ),
                }
            )

        if pd.notna(auc_value) and auc_value >= 0.999:
            flags.append(
                {
                    "Algorithm": algorithm,
                    "issue_type": "Perfect internal AUC",
                    "severity": "Medium",
                    "description": (
                        "内部验证AUC接近或等于1.0，"
                        "需要进一步排查过拟合和数据泄漏。"
                    ),
                }
            )

    external_auc = auc_data[
        auc_data["evaluation_set"]
        == "External GSE38713"
    ]

    for _, row in external_auc.iterrows():
        if row["AUC"] >= 0.999:
            flags.append(
                {
                    "Algorithm": row["Algorithm"],
                    "issue_type": "Perfect external AUC",
                    "severity": "Medium",
                    "description": (
                        "外部验证AUC等于1.0，"
                        "建议使用更多独立队列进行复现。"
                    ),
                }
            )

    flags_df = pd.DataFrame(
        flags,
        columns=[
            "Algorithm",
            "issue_type",
            "severity",
            "description",
        ]
    )

    output_file = (
        RESULTS_DIR / "ml_quality_flags.csv"
    )

    flags_df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return flags_df


def prepare_summary(
    metrics,
    auc_data,
    features,
    consensus,
    quality_flags
):
    """生成机器学习模块摘要。"""
    model_count = metrics["Algorithm"].nunique()

    external_auc = auc_data[
        auc_data["evaluation_set"]
        == "External GSE38713"
    ]

    best_external_auc = (
        external_auc["AUC"].max()
    )

    best_models = external_auc.loc[
        external_auc["AUC"] == best_external_auc,
        "Algorithm"
    ].tolist()

    repeated_features = int(
        (consensus["model_count"] >= 2).sum()
    )

    summary = pd.DataFrame(
        [
            ["model_count", model_count],
            [
                "best_external_auc",
                best_external_auc
            ],
            [
                "best_external_models",
                "；".join(best_models)
            ],
            [
                "feature_records",
                len(features)
            ],
            [
                "multi_model_features",
                repeated_features
            ],
            [
                "quality_flag_count",
                len(quality_flags)
            ],
        ],
        columns=["metric", "value"]
    )

    output_file = RESULTS_DIR / "ml_summary.csv"

    summary.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )


def main():
    print("开始处理第四天机器学习结果……")

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    check_input_files()

    metrics = prepare_model_metrics()
    auc_data = prepare_dataset_auc()
    features = prepare_feature_importance()
    consensus = prepare_feature_consensus(features)

    quality_flags = prepare_quality_flags(
        metrics,
        auc_data
    )

    prepare_summary(
        metrics,
        auc_data,
        features,
        consensus,
        quality_flags
    )

    print()
    print("机器学习结果处理完成")
    print(
        f"模型数量："
        f"{metrics['Algorithm'].nunique()}"
    )
    print(
        f"性能记录：{len(metrics)}"
    )
    print(
        f"AUC记录：{len(auc_data)}"
    )
    print(
        f"特征重要性记录：{len(features)}"
    )
    print(
        "多模型共同支持基因："
        f"{(consensus['model_count'] >= 2).sum()}"
    )
    print(
        f"质量风险提示：{len(quality_flags)}"
    )


if __name__ == "__main__":
    main()