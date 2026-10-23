from io import BytesIO
import json
import zipfile
import numpy as np
import pandas as pd
from scipy import stats
from src.expression_analysis import (expression_example, differential_expression, validate_expression,
    train_classifier, compare_classifiers, MODEL_LABELS, read_analysis_table, result_zip,
    method_record, analysis_fingerprint)
from src.enrichment_engine import benjamini_hochberg
from src.advanced_analysis import run_mr, mr_example, immune_ssgsea


def rejects(function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except ValueError:
        return
    raise AssertionError("Expected invalid input to be rejected")


def test_welch_matches_reference_and_sample_order():
    e, m, _ = expression_example()
    e.loc[119, e.columns[1:]] = 6
    result, _, aligned = differential_expression(e, m.iloc[::-1], "control", "case")
    lookup = result.set_index("gene_symbol")
    expected = stats.ttest_ind(e.iloc[:119, 13:].to_numpy(float), e.iloc[:119, 1:13].to_numpy(float), axis=1, equal_var=False)
    assert np.allclose(lookup.loc[e.gene_symbol[:119], "p_value"], expected.pvalue)
    assert np.allclose(lookup.loc[e.gene_symbol[:119], "p_adjust"], benjamini_hochberg(expected.pvalue))
    assert lookup.loc["DEMO_120", "status"] == "not_testable_zero_variance"
    assert pd.isna(lookup.loc["DEMO_120", "p_adjust"])
    assert aligned.sample_id.tolist() == list(e.columns[1:])
    reverse, _, _ = differential_expression(e, m, "case", "control")
    assert np.allclose(lookup.log2fc.sort_index(), -reverse.set_index("gene_symbol").log2fc.sort_index())


def test_expression_input_rejects_misleading_designs():
    e, m, _ = expression_example()
    bad = e.copy(); bad.iloc[0, 1] = np.nan
    rejects(validate_expression, bad, m, "control", "case")
    bad = e.copy(); bad.iloc[1, 0] = bad.iloc[0, 0]
    rejects(validate_expression, bad, m, "control", "case")
    badmeta = m.copy(); badmeta.loc[1, "subject_id"] = badmeta.loc[0, "subject_id"]
    rejects(validate_expression, e, badmeta, "control", "case")
    badmeta = m.copy(); badmeta["batch"] = ["A"]*12+["B"]*12
    rejects(validate_expression, e, badmeta, "control", "case")
    rejects(validate_expression, e, m.iloc[:-1], "control", "case")
    file = BytesIO(b"gene_symbol,S1,S1\nA,1,2\n"); file.name = "duplicate.csv"
    rejects(read_analysis_table, file)


def test_ml_split_reproducible_and_feature_selection_train_only():
    e, m, _ = expression_example()
    first = train_classifier(e, m, "control", "case", features=12)
    second = train_classifier(e, m, "control", "case", features=12)
    assert first[1].equals(second[1]) and first[2].equals(second[2])
    split = first[3]
    assert set(split.loc[split.split == "train", "subject_id"]).isdisjoint(split.loc[split.split == "test", "subject_id"])
    # Changing test expressions must not affect trained feature weights or training CV.
    perturbed = e.copy()
    for sample in split.loc[split.split == "test", "sample_id"]:
        perturbed[sample] = np.random.default_rng(9).normal(10, 3, len(e))
    changed = train_classifier(perturbed, m, "control", "case", features=12)
    assert first[2].equals(changed[2]) and first[4].equals(changed[4])
    assert 0 <= train_classifier(e, m, "control", "case", model="random_forest")[0]["test_auc"] <= 1


def test_ml_models_share_split_and_cv_select_before_test():
    e, m, _ = expression_example()
    output = compare_classifiers(e, m, "control", "case", features=12, seed=42)
    metrics, predictions, importance, split, folds, comparison = output
    assert set(comparison.model) == set(MODEL_LABELS)
    assert folds.groupby("model").fold.count().nunique() == 1
    assert metrics["model"] == comparison.iloc[0].model
    assert metrics["selection_rule"].startswith("highest mean training-CV")
    assert set(predictions.sample_id) == set(split.loc[split.split == "test", "sample_id"])
    assert {"test_auc", "test_f1", "test_specificity", "test_recall_sensitivity"} <= set(metrics)
    # Constants are removed safely even when the requested feature limit is larger than what remains.
    small = e.iloc[:8].copy()
    small.loc[1:, small.columns[1:]] = 6
    result = train_classifier(small, m, "control", "case", model="elastic_net", features=50)
    assert len(result[2]) == 1
    assert 0 <= train_classifier(e, m, "control", "case", model="svm_rbf", features=12)[0]["test_auc"] <= 1


def test_mr_harmonization_and_reference():
    e = mr_example()
    e["beta_exposure"] = [0.1,0.2,0.3,0.4]
    e["beta_outcome"] = [0.2,-0.4,0.6,0.8]
    result, audit, loo = run_mr(e)
    assert abs(result.beta.iloc[0]-2) < 1e-12
    assert set(audit.status) == {"kept_same", "kept_swapped", "kept_complement"}
    assert np.allclose(loo.beta, 2)
    e.loc[3, "other_allele_exposure"] = "T"
    _, audit, _ = run_mr(e)
    assert audit.status.iloc[3] == "excluded_palindromic"
    e.loc[2, "se_exposure"] = 1
    rejects(run_mr, e)


def test_ssgsea_scores_and_coverage():
    e, m, a = expression_example()
    signatures = a.rename(columns={"term_id":"signature_id"})
    scores, comparison, coverage = immune_ssgsea(e, m, signatures, "control", "case")
    assert len(scores) == 24*4 and len(comparison) == 4
    assert coverage.included.all()
    assert np.isfinite(scores.NES).all()
    assert np.allclose(comparison.p_adjust, benjamini_hochberg(comparison.p_value))
    assert comparison.set_index("signature_id").loc["DEMO_TERM_1", "median_case"] > comparison.set_index("signature_id").loc["DEMO_TERM_1", "median_control"]


def test_download_bundle_and_fingerprint():
    e,m,_ = expression_example()
    fp = analysis_fingerprint(e,m)
    record = method_record("test", {"threshold":0.05}, fp, "synthetic")
    data = result_zip({"expression.csv":e}, record)
    with zipfile.ZipFile(BytesIO(data)) as z:
        assert set(z.namelist()) == {"expression.csv", "methods.json"}
        assert json.loads(z.read("methods.json"))["input_sha256"] == fp
    assert analysis_fingerprint(e,m,"changed") != fp


def test_expression_ui_calculation_chain_and_stale_results():
    from tests.ui_helpers import open_route
    at = open_route("learn_transcriptome")
    at.button(key="run_differential").click().run()
    assert not at.exception and not at.error
    at.button(key="run_de_ora").click().run()
    assert not at.exception and not at.error
    assert len(at.session_state["de_ora_run"]["result"]) == 4
    at.selectbox(key="de_control").set_value("case").run()
    assert "de_run" not in at.session_state
    at.button(key="run_differential").click().run()
    assert not at.exception and at.error


def test_ml_mr_immune_ui_runs():
    from tests.ui_helpers import open_route
    for route, button, state in [("learn_ml", "train_model", "ml_computed"),
                                  ("learn_immune", "run_immune", "immune_computed"),
                                  ("learn_mr", "run_mr", "mr_computed")]:
        at = open_route(route)
        at.button(key=button).click().run()
        assert not at.exception and not at.error, (route, at.exception, at.error)
        assert state in at.session_state
