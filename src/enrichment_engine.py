"""可复现的过度富集分析（ORA）教学引擎。"""

from __future__ import annotations

from io import BytesIO
import re

import numpy as np
import pandas as pd
from scipy.stats import hypergeom


GENE_COLUMN_CANDIDATES = (
    "gene_symbol",
    "gene",
    "symbol",
    "target",
    "基因",
    "基因符号",
)


def read_table(uploaded_file) -> pd.DataFrame:
    """读取用户上传的 CSV、TSV 或 Excel 文件。"""
    name = uploaded_file.name.lower()
    content = uploaded_file.getvalue()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(BytesIO(content))
    if name.endswith(".tsv") or name.endswith(".txt"):
        return pd.read_csv(BytesIO(content), sep="\t")
    return pd.read_csv(BytesIO(content), encoding="utf-8-sig")


def normalize_gene(value) -> str:
    """将基因符号标准化为便于匹配的形式。"""
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def extract_genes(data: pd.DataFrame) -> tuple[set[str], str]:
    """自动识别基因列并返回去重后的基因集合。"""
    lower_columns = {str(column).strip().lower(): column for column in data.columns}
    selected = next(
        (lower_columns[name] for name in GENE_COLUMN_CANDIDATES if name in lower_columns),
        None,
    )
    if selected is None:
        if len(data.columns) != 1:
            raise ValueError(
                "无法识别基因列。请使用 gene_symbol、gene 或 symbol 作为列名。"
            )
        selected = data.columns[0]
    genes = {normalize_gene(value) for value in data[selected]}
    genes.discard("")
    return genes, str(selected)


def validate_annotations(data: pd.DataFrame) -> pd.DataFrame:
    """验证并清洗一行一个‘基因—条目’关系的注释表。"""
    aliases = {
        "gene": "gene_symbol",
        "symbol": "gene_symbol",
        "基因": "gene_symbol",
        "term": "term_id",
        "pathway_id": "term_id",
        "description": "term_name",
        "pathway_name": "term_name",
    }
    renamed = data.copy()
    lower_columns = {str(column).strip().lower(): column for column in renamed.columns}
    for source, target in aliases.items():
        if target not in renamed.columns and source in lower_columns:
            renamed = renamed.rename(columns={lower_columns[source]: target})

    required = {"gene_symbol", "term_id", "term_name"}
    missing = sorted(required - set(renamed.columns))
    if missing:
        raise ValueError("注释表缺少必要字段：" + "、".join(missing))

    cleaned = renamed.copy()
    cleaned["gene_symbol"] = cleaned["gene_symbol"].map(normalize_gene)
    cleaned["term_id"] = cleaned["term_id"].astype(str).str.strip()
    cleaned["term_name"] = cleaned["term_name"].astype(str).str.strip()
    if "category" not in cleaned.columns:
        cleaned["category"] = "未分类"
    cleaned["category"] = cleaned["category"].fillna("未分类").astype(str)
    cleaned = cleaned[
        (cleaned["gene_symbol"] != "")
        & (cleaned["term_id"] != "")
        & (cleaned["term_name"] != "")
    ]
    return cleaned.drop_duplicates(
        subset=["gene_symbol", "term_id", "term_name"]
    ).reset_index(drop=True)


def benjamini_hochberg(p_values) -> np.ndarray:
    """执行 Benjamini-Hochberg 多重检验校正。"""
    values = np.asarray(p_values, dtype=float)
    count = len(values)
    if count == 0:
        return values
    order = np.argsort(values)
    ranked = values[order]
    adjusted_ranked = ranked * count / np.arange(1, count + 1)
    adjusted_ranked = np.minimum.accumulate(adjusted_ranked[::-1])[::-1]
    adjusted = np.empty(count, dtype=float)
    adjusted[order] = np.clip(adjusted_ranked, 0, 1)
    return adjusted


def run_over_representation(
    target_genes: set[str],
    annotations: pd.DataFrame,
    background_genes: set[str] | None = None,
    minimum_overlap: int = 1,
) -> tuple[pd.DataFrame, dict]:
    """使用单侧超几何检验完成过度富集分析。"""
    clean_annotations = validate_annotations(annotations)
    annotated_genes = set(clean_annotations["gene_symbol"])
    if background_genes is None:
        background = annotated_genes
    else:
        background = {normalize_gene(gene) for gene in background_genes}
        background.discard("")
        background &= annotated_genes

    normalized_targets = {normalize_gene(gene) for gene in target_genes}
    normalized_targets.discard("")
    targets_in_background = normalized_targets & background
    ignored_targets = normalized_targets - background

    if not background:
        raise ValueError("背景基因与注释集没有交集，无法计算。")
    if not targets_in_background:
        raise ValueError("目标基因与背景基因没有交集，无法计算。")

    filtered = clean_annotations[clean_annotations["gene_symbol"].isin(background)]
    population_size = len(background)
    sample_size = len(targets_in_background)
    rows = []

    for (term_id, term_name, category), group in filtered.groupby(
        ["term_id", "term_name", "category"], dropna=False
    ):
        term_genes = set(group["gene_symbol"])
        overlap = sorted(targets_in_background & term_genes)
        overlap_count = len(overlap)
        if overlap_count < minimum_overlap:
            continue
        term_size = len(term_genes)
        p_value = hypergeom.sf(
            overlap_count - 1,
            population_size,
            term_size,
            sample_size,
        )
        expected = sample_size * term_size / population_size
        rows.append(
            {
                "category": category,
                "term_id": term_id,
                "term_name": term_name,
                "count": overlap_count,
                "term_size": term_size,
                "target_size": sample_size,
                "background_size": population_size,
                "gene_ratio": overlap_count / sample_size,
                "background_ratio": term_size / population_size,
                "fold_enrichment": overlap_count / expected if expected else np.nan,
                "p_value": p_value,
                "gene_list": "/".join(overlap),
            }
        )

    result = pd.DataFrame(rows)
    if not result.empty:
        result["p_adjust"] = benjamini_hochberg(result["p_value"])
        result = result.sort_values(
            ["p_adjust", "p_value", "fold_enrichment"],
            ascending=[True, True, False],
        ).reset_index(drop=True)

    diagnostics = {
        "uploaded_target_count": len(normalized_targets),
        "target_count": sample_size,
        "background_count": population_size,
        "annotation_count": len(filtered),
        "term_count": filtered["term_id"].nunique(),
        "ignored_target_count": len(ignored_targets),
        "ignored_targets": sorted(ignored_targets),
    }
    return result, diagnostics


def split_gene_text(text: str) -> set[str]:
    """解析粘贴的逗号、空格或换行分隔基因。"""
    return {
        normalize_gene(item)
        for item in re.split(r"[,;\s]+", text or "")
        if normalize_gene(item)
    }


def example_files() -> dict[str, bytes]:
    """返回可直接用于教学演示的三个 CSV 模板。"""
    targets = pd.DataFrame(
        {"gene_symbol": ["TNF", "IL6", "AKT1", "MAPK1", "CASP3", "TP53"]}
    )
    background = pd.DataFrame(
        {
            "gene_symbol": [
                "TNF", "IL6", "AKT1", "MAPK1", "CASP3", "TP53", "EGFR",
                "VEGFA", "JUN", "STAT3", "BCL2", "NFKB1", "RELA", "MMP9",
                "PTGS2", "CXCL8", "TLR4", "MAPK14", "PIK3CA", "PIK3R1",
            ]
        }
    )
    relations = {
        "GO:0033554": ("cellular response to stress", "GO-BP", ["TNF", "IL6", "AKT1", "MAPK1", "CASP3", "TP53", "JUN"]),
        "GO:0006954": ("inflammatory response", "GO-BP", ["TNF", "IL6", "NFKB1", "RELA", "CXCL8", "TLR4"]),
        "GO:0043067": ("regulation of programmed cell death", "GO-BP", ["AKT1", "CASP3", "TP53", "BCL2", "JUN"]),
        "hsa04010": ("MAPK signaling pathway", "KEGG", ["TNF", "MAPK1", "JUN", "MAPK14", "EGFR"]),
        "hsa04151": ("PI3K-Akt signaling pathway", "KEGG", ["AKT1", "EGFR", "VEGFA", "PIK3CA", "PIK3R1", "BCL2"]),
        "TRAIN:BACKGROUND": ("background annotation example", "教学占位", list(background["gene_symbol"])),
    }
    annotation_rows = []
    for term_id, (term_name, category, genes) in relations.items():
        annotation_rows.extend(
            {
                "gene_symbol": gene,
                "term_id": term_id,
                "term_name": term_name,
                "category": category,
            }
            for gene in genes
        )
    annotations = pd.DataFrame(annotation_rows)
    return {
        "target_genes.csv": targets.to_csv(index=False).encode("utf-8-sig"),
        "background_genes.csv": background.to_csv(index=False).encode("utf-8-sig"),
        "term_annotations.csv": annotations.to_csv(index=False).encode("utf-8-sig"),
    }
