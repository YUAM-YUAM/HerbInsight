from pathlib import Path

import math

from src.advanced_guides import ADVANCED_COURSES, advanced_markdown, ivw_formula_demo, node_removal_demo
from src.course_delivery import CAPABILITIES, ACCEPTANCE_CHECKS, capability_markdown, study_record


def test_remaining_course_coverage_and_export():
    from src.learning_paths import course_markdown
    assert set(ADVANCED_COURSES) == {"immune", "mr", "single_cell", "perturbation"}
    filenames = []
    for course in ADVANCED_COURSES.values():
        assert len(course["steps"]) >= 5
        assert course["boundary"] and course["links"]
        for name, fields in course["tables"].items():
            assert len(fields) == len({key for key, _ in fields})
            filenames.append(name)
            assert name in advanced_markdown()
    assert len(filenames) == len(set(filenames))
    assert advanced_markdown() in course_markdown()
    assert capability_markdown() in course_markdown()


def test_ivw_formula_analytic_case_and_wrong_direction():
    result = ivw_formula_demo([1, 2], [2, 4], [1, 1])
    assert abs(result["beta"] - 2) < 1e-12
    assert abs(result["se"] - math.sqrt(1 / 5)) < 1e-12
    assert result["q"] == 0 and result["q_df"] == 1 and result["q_p_value"] == 1
    wrong = ivw_formula_demo([1, 2], [2, -4], [1, 1])
    assert wrong["beta"] < 0 and wrong["q"] > result["q"]


def test_ivw_rejects_invalid_data():
    for x, y, se in [([1], [2], [1]), ([1, 2], [2], [1, 1]), ([0, 2], [2, 4], [1, 1]), ([1, 2], [2, 4], [1, 0]), ([1, 2], [2, float("nan")], [1, 1])]:
        try:
            ivw_formula_demo(x, y, se)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid formula inputs accepted")


def test_node_removal_is_fixed_graph_not_expression_prediction():
    before, leaf = node_removal_demo("NODE_A")
    _, hub = node_removal_demo("NODE_B")
    assert before == {"nodes": 5, "edges": 4, "components": 1}
    assert leaf == {"nodes": 4, "edges": 3, "components": 1}
    assert hub == {"nodes": 4, "edges": 1, "components": 3}
    assert node_removal_demo("NODE_A")[0] == before


def test_self_check_record_is_not_automatic_certification():
    assert len(CAPABILITIES) == 13 and len(ACCEPTANCE_CHECKS) == 18
    record = study_record("test project", "question", "MR not applicable", "", "small sample", {0})
    assert record.count("- [x]") == 1
    assert record.count("- [ ]") == 17
    assert "test project" in record and "MR not applicable" in record
    assert "未填写" in record
    assert "不表示平台核验" in record
    try:
        study_record("", "", "", "", "", {99})
    except ValueError:
        pass
    else:
        raise AssertionError("invalid check accepted")


def test_advanced_demos_and_delivery_ui():
    from streamlit.testing.v1 import AppTest
    from tests.ui_helpers import open_route
    at = open_route("learn_mr")
    assert not at.exception and not at.error
    assert any(header.value == "孟德尔随机化" for header in at.header)
    before = next(m for m in at.metric if m.label == "示意IVW beta").value
    at.toggle(key="mr_demo_wrong_direction").set_value(True).run()
    assert not at.exception
    assert next(m for m in at.metric if m.label == "示意IVW beta").value != before
    at.button(key="nav_learn_perturbation").click().run()
    at.selectbox(key="perturbation_demo_node").set_value("NODE_B").run()
    assert not at.exception
    at.button(key="nav_resources").click().run()
    at.text_input(key="delivery_title").set_value("learning project").run()
    at.checkbox(key="delivery_check_0").check().run()
    assert not at.exception
    assert any("自行确认 1/18" in caption.value for caption in at.caption)
