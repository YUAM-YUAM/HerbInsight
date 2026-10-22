"""Small, explicit analysis contracts for independently sampled log2 expression."""
import hashlib
import json
import platform
from datetime import datetime, timezone
from io import BytesIO, StringIO
import csv
import zipfile

import numpy as np
import pandas as pd
import scipy
from scipy import stats

from src.enrichment_engine import benjamini_hochberg
from src.transcriptome_guide import align_sample_metadata


def read_analysis_table(upload):
    raw = upload.getvalue()
    if len(raw) > 30 * 1024 * 1024:
        raise ValueError("单个分析文件不得超过30 MB。")
    if not upload.name.lower().endswith((".csv", ".tsv", ".txt")):
        raise ValueError("请提供UTF-8 CSV或TSV文件。")
    sep = "\t" if upload.name.lower().endswith((".tsv", ".txt")) else ","
    text = raw.decode("utf-8-sig")
    header = next(csv.reader(StringIO(text), delimiter=sep), [])
    if not header or len(set(header)) != len(header) or any(not x.strip() for x in header):
        raise ValueError("表头为空或有重复列名；请核查样本名。")
    return pd.read_csv(StringIO(text), sep=sep, dtype=str)


def validate_expression(expression, metadata, control, case, minimum=3):
    if expression.shape[1] < 3 or expression.columns[0] != "gene_symbol":
        raise ValueError("表达矩阵首列应为gene_symbol，后续每列为一个样本。")
    if not 2 <= len(expression) <= 50000 or expression.shape[1] > 501:
        raise ValueError("支持2–50000个基因、最多500个样本。")
    genes = expression.iloc[:, 0]
    if genes.isna().any() or genes.astype(str).str.strip().eq("").any():
        raise ValueError("gene_symbol不能为空。")
    genes = genes.astype(str).str.strip()
    if genes.duplicated().any() or genes.str.upper().duplicated().any():
        raise ValueError("存在重复基因（含大小写重复），请按预定规则汇总后上传。")
    values = expression.iloc[:, 1:].apply(pd.to_numeric, errors="raise").to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("表达矩阵包含缺失值或非有限值，请先完成质控。")
    if len(set(expression.columns)) != len(expression.columns):
        raise ValueError("样本列名重复。")
    aligned = align_sample_metadata(list(expression.columns[1:]), metadata.copy())
    groups = aligned["group"].astype(str)
    if control == case or set(groups) != {control, case}:
        raise ValueError("仅支持恰好两个组，病例与对照名称须不同且覆盖全部样本。")
    if min((groups == control).sum(), (groups == case).sum()) < minimum:
        raise ValueError(f"每组至少需要{minimum}个独立样本。")
    for column in ("subject_id", "patient_id"):
        if column in aligned:
            ids = aligned[column].astype("string").str.strip()
            if ids.isna().any() or ids.eq("").any() or ids.duplicated().any():
                raise ValueError("患者ID缺失或重复。本流程仅支持每位独立患者一个样本；配对/重复测量需专门模型。")
    if "batch" in aligned and aligned["batch"].nunique(dropna=False) > 1:
        raise ValueError("检测到多个批次；当前两组流程不调整批次，请使用包含批次协变量的模型。")
    return pd.DataFrame(values, index=genes, columns=expression.columns[1:]), aligned


def differential_expression(expression, metadata, control, case):
    matrix, aligned = validate_expression(expression, metadata, control, case)
    a = matrix.loc[:, aligned.loc[aligned.group == control, "sample_id"]].to_numpy()
    b = matrix.loc[:, aligned.loc[aligned.group == case, "sample_id"]].to_numpy()
    variance = a.var(axis=1, ddof=1) / a.shape[1] + b.var(axis=1, ddof=1) / b.shape[1]
    valid = variance > 0
    p = np.full(len(matrix), np.nan)
    t = np.full(len(matrix), np.nan)
    test = stats.ttest_ind(b[valid], a[valid], axis=1, equal_var=False)
    t[valid], p[valid] = test.statistic, test.pvalue
    valid &= np.isfinite(p)
    adjusted = np.full(len(matrix), np.nan)
    adjusted[valid] = benjamini_hochberg(p[valid])
    result = pd.DataFrame({"gene_symbol": matrix.index, "mean_log2_control": a.mean(axis=1),
                           "mean_log2_case": b.mean(axis=1), "log2fc": b.mean(axis=1) - a.mean(axis=1),
                           "t_statistic": t, "p_value": p, "p_adjust": adjusted,
                           "status": np.where(valid, "tested", "not_testable_zero_variance")})
    return result.sort_values("p_adjust", na_position="last").reset_index(drop=True), matrix, aligned


def train_classifier(expression, metadata, control, case, model="logistic", features=50, seed=42):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_selection import SelectKBest, f_classif, VarianceThreshold
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, balanced_accuracy_score, confusion_matrix, average_precision_score
    from sklearn.model_selection import StratifiedKFold, train_test_split, cross_val_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    matrix, aligned = validate_expression(expression, metadata, control, case, minimum=8)
    if len(matrix) > 20000 or matrix.shape[1] > 300:
        raise ValueError("当前机器学习限20000基因、300样本。")
    x = matrix.T
    y = (aligned.group == case).astype(int).to_numpy()
    train, test = train_test_split(np.arange(len(y)), test_size=0.25, stratify=y, random_state=seed)
    if model not in ("logistic", "random_forest"):
        raise ValueError("未知模型。")
    estimator = (LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed)
                 if model == "logistic" else RandomForestClassifier(n_estimators=200, max_depth=5,
                    min_samples_leaf=2, class_weight="balanced", random_state=seed, n_jobs=1))
    # Unsupervised constant removal and supervised selection are fitted inside each training fold.
    pipeline = Pipeline([("variance", VarianceThreshold()), ("scale", StandardScaler()),
                         ("select", SelectKBest(f_classif, k=min(int(features), len(matrix)))), ("model", estimator)])
    folds = min(5, int(np.bincount(y[train]).min()))
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    scores = cross_val_score(pipeline, x.iloc[train], y[train], cv=cv, scoring="roc_auc", error_score="raise", n_jobs=1)
    pipeline.fit(x.iloc[train], y[train])
    probability = pipeline.predict_proba(x.iloc[test])[:, 1]
    predicted = (probability >= 0.5).astype(int)
    selected = matrix.index[pipeline.named_steps["variance"].get_support()][pipeline.named_steps["select"].get_support()]
    weight = (pipeline.named_steps["model"].coef_[0] if model == "logistic"
              else pipeline.named_steps["model"].feature_importances_)
    importance = pd.DataFrame({"gene_symbol": selected, "weight": weight})
    importance = importance.assign(abs_weight=np.abs(weight)).sort_values("abs_weight", ascending=False)
    split = aligned.copy()
    split["split"] = "train"
    split.loc[test, "split"] = "test"
    prediction = pd.DataFrame({"sample_id": x.index[test], "true_label": y[test], "probability": probability, "predicted_label": predicted})
    metrics = {"cv_auc_mean": float(scores.mean()), "cv_auc_sd": float(scores.std()),
               "test_auc": float(roc_auc_score(y[test], probability)),
               "test_average_precision": float(average_precision_score(y[test], probability)),
               "test_balanced_accuracy": float(balanced_accuracy_score(y[test], predicted)),
               "cv_folds": folds, "test_n": len(test), "train_n": len(train), "threshold": 0.5,
               "confusion_matrix": confusion_matrix(y[test], predicted, labels=[0, 1]).tolist()}
    return metrics, prediction, importance, split, pd.DataFrame({"fold": range(1, folds+1), "roc_auc": scores})


def analysis_fingerprint(*items):
    digest = hashlib.sha256()
    for item in items:
        data = item.to_csv(index=False) if isinstance(item, pd.DataFrame) else str(item)
        digest.update(data.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def method_record(method, params, fingerprint, source):
    import importlib.metadata
    versions = {n: importlib.metadata.version(n) for n in ("pandas", "numpy", "scipy", "streamlit")}
    if method == "classification":
        versions["scikit-learn"] = importlib.metadata.version("scikit-learn")
    return {"method": method, "parameters": params, "input_sha256": fingerprint,
            "source": source, "created_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(), "versions": versions}


def result_zip(tables, record):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, table in tables.items():
            archive.writestr(name, table.to_csv(index=False).encode("utf-8-sig"))
        archive.writestr("methods.json", json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8"))
    return buffer.getvalue()


def expression_example():
    rng = np.random.default_rng(140)
    values = rng.normal(6, 0.6, size=(120, 24))
    values[:15, 12:] += 2
    values[15:30, 12:] -= 2
    frame = pd.DataFrame(values, columns=[f"S{i+1:02}" for i in range(24)])
    frame.insert(0, "gene_symbol", [f"DEMO_{i+1:03}" for i in range(120)])
    meta = pd.DataFrame({"sample_id": frame.columns[1:], "group": ["control"]*12+["case"]*12,
                         "subject_id": [f"PERSON_{i+1:02}" for i in range(24)]})
    annotation = pd.DataFrame([{"gene_symbol": f"DEMO_{i+1:03}", "term_id": f"DEMO_TERM_{j+1}",
                               "term_name": f"虚构功能集合{j+1}", "category": "DEMO"}
                              for j, indices in enumerate([range(15), range(15,30), range(30,80), range(50,120)])
                              for i in indices])
    return frame, meta, annotation
