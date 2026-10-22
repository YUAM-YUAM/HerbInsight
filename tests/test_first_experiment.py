from io import BytesIO
import json
import zipfile

from src.first_experiment import experiment_inputs, run_first_experiment, exact_tail
from src.expression_analysis import result_zip
from src.learning_exercises import learning_record_markdown
from tests.ui_helpers import open_route


def test_first_experiment_reference_and_inputs():
    previous_p = 1.0
    for hits in range(1, 11):
        targets, background, annotations = experiment_inputs(hits)
        assert len(targets) == targets.gene_symbol.nunique() == 20
        assert len(background) == 100
        assert set(targets.gene_symbol) <= set(background.gene_symbol)
        result, diagnostics, record, tables = run_first_experiment(hits)
        assert len(result) == diagnostics["term_count"] == 10
        first = result.loc[result.term_id == "DEMO_SET_01"].iloc[0]
        assert first["count"] == hits
        assert 0 <= first.p_value <= previous_p
        previous_p = first.p_value
        assert record["reference_check"]["passed"]
        assert abs(first.p_value - exact_tail(100, 10, 20, hits)) < 1e-12
        # Independent BH check with explicit cumulative minima over 10 tests.
        ranked = result.sort_values("p_value")
        values = [min(1.0, float(p)*10/(i+1)) for i, p in enumerate(ranked.p_value)]
        expected = [min(values[i:]) for i in range(10)]
        assert all(abs(a-b) < 1e-12 for a,b in zip(expected, ranked.p_adjust))
        with zipfile.ZipFile(BytesIO(result_zip(tables, record))) as archive:
            assert set(archive.namelist()) == {"target_genes.csv", "background_genes.csv", "term_annotations.csv", "all_results.csv", "methods.json"}
            assert json.loads(archive.read("methods.json"))["input_sha256"] == record["input_sha256"]


def test_first_experiment_ui_and_stale_result():
    at = open_route("learn_home")
    assert "first_experiment" not in at.session_state
    at.button(key="first_run").click().run()
    assert not at.exception
    assert len(at.metric) == 3
    assert at.session_state["first_experiment"]["hits"] == 5
    at.slider(key="first_hits").set_value(8).run()
    assert len(at.metric) == 0
    assert any("旧结果" in message.value for message in at.info)
    at.button(key="first_run").click().run()
    assert at.session_state["first_experiment"]["hits"] == 8
    assert len(at.metric) == 3
    assert not at.exception


def test_readable_learning_record_separates_attempts():
    text = learning_record_markdown({"collection": {"attempts": 2, "passed": True, "first_attempt_passed": False}})
    assert "首次：需纠正；最近：正确；提交次数：2" in text
    assert "未作答" in text
