"""网络药理学教学实验使用的通用网络分析引擎。"""

from __future__ import annotations

from io import BytesIO
import math

import networkx as nx
import pandas as pd


def map_edge_columns(data, source_column, target_column, weight_column=None, score_scale="original"):
    """显式映射任意导出列；不猜测分数尺度或ID体系。"""
    if source_column == target_column:
        raise ValueError("起点与终点必须选择不同列。")
    selected = [source_column, target_column] + ([weight_column] if weight_column else [])
    if len(set(selected)) != len(selected) or any(c not in data.columns for c in selected):
        raise ValueError("请选择不同且存在的端点与权重列。")
    mapped = data.drop(columns=list(set(selected) | {"source", "target", "weight"}), errors="ignore").copy()
    mapped["source"] = data[source_column]
    mapped["target"] = data[target_column]
    mapped["weight"] = pd.to_numeric(data[weight_column], errors="coerce") if weight_column else 1.0
    if score_scale == "string_1000":
        if not weight_column:
            raise ValueError("转换STRING分数前必须选择分数列。")
        scores = mapped["weight"]
        if scores.isna().any() or not scores.between(0, 1000).all():
            raise ValueError("STRING 0–1000分数必须全部为该范围内的有限数值。")
        mapped["weight"] = scores / 1000.0
    elif score_scale != "original":
        raise ValueError("未知的分数尺度。")
    return mapped


def read_edge_table(uploaded_file) -> pd.DataFrame:
    """读取 CSV、TSV 或 Excel 边表。"""
    content = uploaded_file.getvalue()
    name = uploaded_file.name.lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(BytesIO(content))
    if name.endswith((".tsv", ".txt")):
        return pd.read_csv(BytesIO(content), sep="\t")
    return pd.read_csv(BytesIO(content), encoding="utf-8-sig")


def validate_edges(data: pd.DataFrame) -> pd.DataFrame:
    """标准化边表字段并清除无效关系。"""
    aliases = {
        "from": "source",
        "源节点": "source",
        "to": "target",
        "目标节点": "target",
        "score": "weight",
        "combined_score": "weight",
        "confidence": "weight",
    }
    cleaned = data.copy()
    lower_columns = {str(column).strip().lower(): column for column in cleaned.columns}
    for source_name, target_name in aliases.items():
        if target_name not in cleaned.columns and source_name in lower_columns:
            cleaned = cleaned.rename(columns={lower_columns[source_name]: target_name})

    missing = {"source", "target"} - set(cleaned.columns)
    if missing:
        raise ValueError("边表缺少必要字段：" + "、".join(sorted(missing)))

    cleaned = cleaned.dropna(subset=["source", "target"]).copy()
    cleaned["source"] = cleaned["source"].astype(str).str.strip()
    cleaned["target"] = cleaned["target"].astype(str).str.strip()
    if "weight" not in cleaned.columns:
        cleaned["weight"] = 1.0
    cleaned["weight"] = pd.to_numeric(cleaned["weight"], errors="coerce")

    for column in ["source_type", "target_type", "relation"]:
        if column not in cleaned.columns:
            cleaned[column] = "未标注" if column != "relation" else "关联"
        cleaned[column] = cleaned[column].fillna("未标注").astype(str).str.strip()

    return cleaned[
        (cleaned["source"] != "")
        & (cleaned["target"] != "")
        & cleaned["weight"].notna()
        & cleaned["weight"].map(math.isfinite)
    ].reset_index(drop=True)


def analyze_network(
    edge_data: pd.DataFrame,
    minimum_weight: float = 0.0,
    directed: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, nx.Graph, dict]:
    """清洗边表、构建网络并计算常用拓扑指标。"""
    validated = validate_edges(edge_data)
    original_count = len(validated)
    filtered = validated[validated["weight"] >= minimum_weight].copy()
    self_loop_count = int((filtered["source"] == filtered["target"]).sum())
    filtered = filtered[filtered["source"] != filtered["target"]].copy()
    if filtered.empty:
        raise ValueError("当前阈值下没有可用于建网的边。")

    type_lookup = {}
    for _, row in filtered.iterrows():
        type_lookup.setdefault(row["source"], row["source_type"])
        type_lookup.setdefault(row["target"], row["target_type"])

    pair_columns = ["source", "target"]
    if not directed:
        reverse = filtered["source"] > filtered["target"]
        for first, second in [("source", "target"), ("source_type", "target_type")]:
            filtered.loc[reverse, [first, second]] = filtered.loc[reverse, [second, first]].to_numpy()

    duplicate_count = int(filtered.duplicated(pair_columns).sum())
    filtered = (
        filtered.sort_values("weight", ascending=False)
        .drop_duplicates(pair_columns, keep="first")
        .reset_index(drop=True)
    )
    if filtered.empty:
        raise ValueError("当前阈值下没有可用于建网的边。")
    if len(filtered) > 5000 or len(set(filtered["source"]) | set(filtered["target"])) > 500:
        raise ValueError("教学在线计算限500节点、5000条去重边；更大网络请用Cytoscape或本地脚本。")

    graph = nx.DiGraph() if directed else nx.Graph()
    for _, row in filtered.iterrows():
        graph.add_edge(
            row["source"], row["target"],
            weight=float(row["weight"]), relation=row["relation"],
        )

    degree = dict(graph.degree())
    degree_centrality = nx.degree_centrality(graph)
    betweenness = nx.betweenness_centrality(graph, weight=None, normalized=True)
    closeness = nx.closeness_centrality(graph)
    if directed:
        components = list(nx.weakly_connected_components(graph))
    else:
        components = list(nx.connected_components(graph))
    component_lookup = {
        node: index + 1
        for index, component in enumerate(
            sorted(components, key=len, reverse=True)
        )
        for node in component
    }

    node_rows = []
    for node in graph.nodes():
        row = {
            "node_id": node,
            "node_type": type_lookup.get(node, "未标注"),
            "degree": degree[node],
            "degree_centrality": degree_centrality[node],
            "betweenness": betweenness[node],
            "closeness": closeness[node],
            "component": component_lookup[node],
        }
        if directed:
            row["in_degree"] = graph.in_degree(node)
            row["out_degree"] = graph.out_degree(node)
        node_rows.append(row)

    nodes = pd.DataFrame(node_rows).sort_values(
        ["degree", "betweenness", "node_id"], ascending=[False, False, True]
    ).reset_index(drop=True)
    diagnostics = {
        "uploaded_edge_count": original_count,
        "edge_count": graph.number_of_edges(),
        "node_count": graph.number_of_nodes(),
        "filtered_edge_count": original_count - len(filtered),
        "self_loop_count": self_loop_count,
        "duplicate_count": duplicate_count,
        "component_count": len(components),
        "density": nx.density(graph),
        "average_degree": sum(degree.values()) / len(degree),
        "directed": directed,
    }
    return nodes, filtered, graph, diagnostics


def example_edge_file() -> bytes:
    """生成药材—成分—靶点教学网络示例。"""
    rows = [
        ("五积散", "半夏", "复方", "药材", "包含", 1.0),
        ("五积散", "陈皮", "复方", "药材", "包含", 1.0),
        ("五积散", "厚朴", "复方", "药材", "包含", 1.0),
        ("半夏", "quercetin", "药材", "成分", "含有", 0.90),
        ("陈皮", "hesperetin", "药材", "成分", "含有", 0.88),
        ("厚朴", "honokiol", "药材", "成分", "含有", 0.92),
        ("quercetin", "TNF", "成分", "靶点", "作用", 0.86),
        ("quercetin", "IL6", "成分", "靶点", "作用", 0.81),
        ("hesperetin", "TNF", "成分", "靶点", "作用", 0.79),
        ("hesperetin", "AKT1", "成分", "靶点", "作用", 0.84),
        ("honokiol", "AKT1", "成分", "靶点", "作用", 0.91),
        ("honokiol", "CASP3", "成分", "靶点", "作用", 0.83),
        ("TNF", "IL6", "靶点", "靶点", "PPI", 0.95),
        ("TNF", "AKT1", "靶点", "靶点", "PPI", 0.89),
        ("AKT1", "CASP3", "靶点", "靶点", "PPI", 0.87),
    ]
    table = pd.DataFrame(
        rows,
        columns=[
            "source", "target", "source_type", "target_type", "relation", "weight"
        ],
    )
    return table.to_csv(index=False).encode("utf-8-sig")
