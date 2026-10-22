import pandas as pd

from src.enrichment_engine import benjamini_hochberg, run_over_representation


def test_bh_adjustment_is_monotonic_in_rank_order():
    adjusted = benjamini_hochberg([0.01, 0.04, 0.03, 0.002])
    assert all(0 <= value <= 1 for value in adjusted)
    assert adjusted[3] <= adjusted[0] <= adjusted[2] <= adjusted[1]


def test_over_representation_returns_expected_hit():
    annotations = pd.DataFrame(
        [
            ["A", "T1", "term one", "GO-BP"],
            ["B", "T1", "term one", "GO-BP"],
            ["C", "T1", "term one", "GO-BP"],
            ["D", "T2", "term two", "KEGG"],
            ["E", "T2", "term two", "KEGG"],
        ],
        columns=["gene_symbol", "term_id", "term_name", "category"],
    )
    result, diagnostics = run_over_representation(
        {"A", "B"}, annotations, {"A", "B", "C", "D", "E"}
    )
    assert result.iloc[0]["term_id"] == "T1"
    assert result.iloc[0]["count"] == 2
    assert diagnostics["target_count"] == 2
    assert "p_adjust" in result.columns
