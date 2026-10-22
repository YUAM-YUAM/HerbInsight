import pandas as pd

from src.enrichment_engine import benjamini_hochberg, run_over_representation, validate_annotations


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


def test_bh_includes_zero_hit_terms_before_display_filter():
    annotations = pd.DataFrame({"gene_symbol": list("ABCDE"), "term_id": ["T1", "T1", "T1", "T2", "T2"], "term_name": ["one", "one", "one", "two", "two"]})
    result, diagnostics = run_over_representation({"A", "B"}, annotations)
    assert diagnostics["term_count"] == 2
    assert abs(result.iloc[0]["p_value"] - 0.3) < 1e-10
    assert abs(result.iloc[0]["p_adjust"] - 0.6) < 1e-10
    empty, _ = run_over_representation({"A", "B"}, annotations, minimum_overlap=3)
    assert empty.empty and "p_adjust" in empty.columns


def test_missing_annotations_do_not_create_fake_terms():
    data = pd.DataFrame({"gene_symbol": ["A", "B", "C", None], "term_id": ["T1", None, "T3", "T4"], "term_name": ["one", "two", None, "four"]})
    clean = validate_annotations(data)
    assert len(clean) == 1 and clean.iloc[0]["term_id"] == "T1"


def test_inconsistent_term_names_are_not_separate_hypotheses():
    data = pd.DataFrame({"gene_symbol": ["A", "B"], "term_id": ["T1", "T1"], "term_name": ["name one", "other version name"]})
    try:
        validate_annotations(data)
    except ValueError:
        pass
    else:
        raise AssertionError("inconsistent annotation treated as independent hypotheses")
