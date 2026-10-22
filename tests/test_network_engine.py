import pandas as pd

from src.network_engine import analyze_network, map_edge_columns


def test_network_metrics_and_cleaning():
    edges = pd.DataFrame(
        {
            "source": ["A", "A", "B", "C", "A"],
            "target": ["B", "B", "C", "A", "A"],
            "weight": [0.9, 0.8, 0.7, 0.6, 1.0],
        }
    )
    nodes, clean_edges, graph, diagnostics = analyze_network(edges)
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 3
    assert diagnostics["duplicate_count"] == 1
    assert diagnostics["self_loop_count"] == 1
    assert set(nodes["node_id"]) == {"A", "B", "C"}
    assert len(clean_edges) == 3


def test_string_mapping_and_scale():
    raw = pd.DataFrame({"#node1": ["TNF", "IL6"], "node2": ["IL6", "AKT1"], "combined_score": [900, 700]})
    mapped = map_edge_columns(raw, "#node1", "node2", "combined_score", "string_1000")
    assert mapped["weight"].tolist() == [0.9, 0.7]
    _, edges, _, _ = analyze_network(mapped, minimum_weight=0.8)
    assert len(edges) == 1
    try:
        map_edge_columns(raw.assign(combined_score=[900, 1001]), "#node1", "node2", "combined_score", "string_1000")
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range score accepted")


def test_nulls_nonfinite_and_reversed_types():
    raw = pd.DataFrame({"source": ["Z", None, "X"], "target": ["A", "B", "Y"], "weight": [1, 1, float("inf")], "source_type": ["protein", "", ""], "target_type": ["compound", "", ""]})
    nodes, edges, graph, _ = analyze_network(raw)
    assert set(graph) == {"A", "Z"}
    assert edges.iloc[0]["source"] == "A"
    assert edges.iloc[0]["source_type"] == "compound"
    assert dict(zip(nodes.node_id, nodes.node_type))["Z"] == "protein"
    try:
        analyze_network(raw, minimum_weight=2)
    except ValueError as error:
        assert "阈值" in str(error)
    else:
        raise AssertionError("empty network accepted")
