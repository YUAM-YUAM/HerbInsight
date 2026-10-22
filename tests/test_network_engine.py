import pandas as pd

from src.network_engine import analyze_network


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
