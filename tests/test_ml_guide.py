from pathlib import Path

import pandas as pd

from src.ml_guide import ML_STEPS, ML_FIELDS, ml_markdown, audit_patient_split, evaluate_binary_predictions


def test_auc_confusion_threshold_and_ties():
    result = evaluate_binary_predictions([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])
    assert result["auc"] == 0.75
    assert (result["tp"], result["fp"], result["fn"], result["tn"]) == (1, 0, 1, 2)
    assert result["accuracy"] == 0.75
    assert result["sensitivity"] == 0.5
    assert result["specificity"] == 1
    assert evaluate_binary_predictions([0, 1], [0.5, 0.5])["auc"] == 0.5
    assert evaluate_binary_predictions([0, 1], [0.9, 0.1])["auc"] == 0
    no_positive = evaluate_binary_predictions([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8], 1)
    assert no_positive["auc"] == 0.75 and no_positive["precision"] is None
    assert no_positive["f1"] == 0


def test_prediction_validation():
    for labels, scores, threshold in [([], [], 0.5), ([0], [0.5], 0.5), ([0, 1], [1.1, 0.2], 0.5), ([0, 2], [0.1, 0.8], 0.5), ([0, 1], [float("nan"), 0.8], 0.5), ([0, 1], [0.1], 0.5), ([0, 1], [0.1, 0.8], 2)]:
        try:
            evaluate_binary_predictions(labels, scores, threshold)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid predictions accepted")


def test_patient_overlap_audit_and_invalid_identifiers():
    records = pd.DataFrame({"sample_id": ["S1", "S2", "S3"], "subject_id": ["P1", "P1", "P2"], "split": ["train", "train", "test"]})
    assert audit_patient_split(records) == []
    leak = records.copy()
    leak.loc[1, "split"] = "test"
    assert audit_patient_split(leak) == ["P1"]
    assert records.loc[1, "split"] == "train"
    for bad in [records.assign(sample_id=["S1", "S1", "S3"]), records.assign(subject_id=["P1", None, "P2"]), records.assign(subject_id=["P1", "P1 ", "P2"]), records.assign(split=["train", "other", "test"])]:
        try:
            audit_patient_split(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid split accepted")


def test_ml_course_templates_and_export():
    from src.learning_paths import course_markdown
    assert len(ML_STEPS) == 7 and len(ML_FIELDS) == 5
    assert ml_markdown() in course_markdown()
    for name, fields in ML_FIELDS.items():
        assert name in ml_markdown()
        assert len(fields) == len({key for key, _ in fields})


def test_ml_demo_updates_and_recovers():
    from streamlit.testing.v1 import AppTest
    from tests.ui_helpers import open_route
    at = open_route("learn_ml")
    assert not at.exception and not at.error
    assert any(header.value == "机器学习与评估" for header in at.header)
    assert next(m for m in at.metric if m.label == "演示ROC-AUC").value == "0.75"
    options = at.radio(key="ml_guide_split").options
    at.radio(key="ml_guide_split").set_value(options[1]).run()
    assert not at.exception and len(at.error) == 1
    at.radio(key="ml_guide_split").set_value(options[0]).run()
    assert not at.exception and not at.error
    at.slider(key="ml_guide_threshold").set_value(1.0).run()
    assert not at.exception
    assert next(m for m in at.metric if m.label == "演示ROC-AUC").value == "0.75"
    assert next(m for m in at.metric if m.label == "演示敏感度").value == "0.00"
