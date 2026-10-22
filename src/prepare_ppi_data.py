from pathlib import Path

import networkx as nx
import pandas as pd


# 项目路径
ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = (
    ROOT
    / "projects"
    / "wujisan_uc"
    / "raw"
    / "STRING_PPI_high_confidence_0700.tsv"
)

GENE_FILE = (
    ROOT
    / "projects"
    / "wujisan_uc"
    / "processed"
    / "ppi_input_genes.txt"
)

PROCESSED_DIR = (
    ROOT
    / "projects"
    / "wujisan_uc"
    / "processed"
)

EDGES_FILE = PROCESSED_DIR / "ppi_edges.csv"
NODES_FILE = PROCESSED_DIR / "ppi_nodes.csv"


def main():
    # 读取 STRING 高置信度互作数据
    edges = pd.read_csv(RAW_FILE, sep="\t")

    # 统一字段名称
    edges = edges.rename(
        columns={
            "#node1": "source",
            "node2": "target",
            "node1_string_id": "source_string_id",
            "node2_string_id": "target_string_id",
            "combined_score": "score",
        }
    )

    required_columns = {"source", "target", "score"}

    missing_columns = required_columns - set(edges.columns)

    if missing_columns:
        raise ValueError(
            f"STRING 文件缺少必要字段：{sorted(missing_columns)}"
        )

    # 清理基因名称和分数
    edges["source"] = edges["source"].astype(str).str.strip()
    edges["target"] = edges["target"].astype(str).str.strip()
    edges["score"] = pd.to_numeric(
        edges["score"],
        errors="coerce"
    )

    edges = edges.dropna(
        subset=["source", "target", "score"]
    )

    # 再次保证只保留高置信度互作
    edges = edges[edges["score"] >= 0.7].copy()

    # 删除自身互作
    edges = edges[
        edges["source"] != edges["target"]
    ].copy()

    # 防止同一条无向边重复
    edges["pair_key"] = edges[
        ["source", "target"]
    ].apply(
        lambda row: "||".join(sorted(row.astype(str))),
        axis=1
    )

    edges = (
        edges.sort_values(
            "score",
            ascending=False
        )
        .drop_duplicates(
            subset="pair_key",
            keep="first"
        )
        .drop(columns="pair_key")
        .reset_index(drop=True)
    )

    # 调整主要字段的排列顺序
    preferred_columns = [
        "source",
        "target",
        "score",
        "source_string_id",
        "target_string_id",
        "neighborhood_on_chromosome",
        "gene_fusion",
        "phylogenetic_cooccurrence",
        "homology",
        "coexpression",
        "experimentally_determined_interaction",
        "database_annotated",
        "automated_textmining",
    ]

    remaining_columns = [
        column
        for column in edges.columns
        if column not in preferred_columns
    ]

    ordered_columns = [
        column
        for column in preferred_columns
        if column in edges.columns
    ] + remaining_columns

    edges = edges[ordered_columns]

    # 保存标准化边数据
    edges.to_csv(
        EDGES_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # 建立无向网络
    graph = nx.from_pandas_edgelist(
        edges,
        source="source",
        target="target",
        edge_attr="score",
        create_using=nx.Graph()
    )

    # 加入无互作记录的输入基因，确保保留全部191个基因
    input_genes = pd.read_csv(
        GENE_FILE,
        header=None,
        names=["gene_symbol"]
    )

    input_genes["gene_symbol"] = (
        input_genes["gene_symbol"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    graph.add_nodes_from(
        input_genes["gene_symbol"].tolist()
    )

    # 计算节点拓扑指标
    degree = dict(graph.degree())
    degree_centrality = nx.degree_centrality(graph)
    betweenness = nx.betweenness_centrality(
        graph,
        normalized=True,
        weight=None
    )
    closeness = nx.closeness_centrality(graph)

    nodes = pd.DataFrame(
        {
            "gene_symbol": list(graph.nodes()),
            "degree": [
                degree.get(node, 0)
                for node in graph.nodes()
            ],
            "degree_centrality": [
                degree_centrality.get(node, 0.0)
                for node in graph.nodes()
            ],
            "betweenness": [
                betweenness.get(node, 0.0)
                for node in graph.nodes()
            ],
            "closeness": [
                closeness.get(node, 0.0)
                for node in graph.nodes()
            ],
        }
    )

    nodes["connected"] = nodes["degree"] > 0

    nodes = nodes.sort_values(
        ["degree", "betweenness"],
        ascending=[False, False]
    ).reset_index(drop=True)

    nodes.to_csv(
        NODES_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    component_count = nx.number_connected_components(graph)

    print("PPI 数据处理完成")
    print(f"节点数：{graph.number_of_nodes()}")
    print(f"互作边数：{graph.number_of_edges()}")
    print(f"连通分量数：{component_count}")
    print(f"边文件：{EDGES_FILE}")
    print(f"节点文件：{NODES_FILE}")


if __name__ == "__main__":
    main()