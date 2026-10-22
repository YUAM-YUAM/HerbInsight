"""课程与计算入口的Streamlit交互回归测试。"""
from tests.ui_helpers import open_route
from src.learning_paths import LESSONS, course_markdown


def test_course_and_labs_render():
    at = open_route("learn_home")
    at.button(key="start_learn_collection").click().run()
    assert not at.exception
    assert any(header.value == "最终表格长什么样？" for header in at.subheader)
    assert any("compound_targets_standardized.csv" in block.label for block in at.expander)
    at.button(key="nav_lesson_steps").click().run()
    selector = next(item for item in at.selectbox if len(item.options) == len(LESSONS))
    for index, lesson in enumerate(LESSONS):
        selector.set_value(index).run()
        assert not at.exception
        assert any(item.value == lesson["question"] for item in at.subheader)
        selector = next(item for item in at.selectbox if len(item.options) == len(LESSONS))
    assert all(lesson["title"] in course_markdown() for lesson in LESSONS)
    at.button(key="nav_learn_ppi").click().run()
    next(item for item in at.button if item.label == "开始构建并分析网络").click().run()
    assert not at.exception
    assert at.session_state["network_diagnostics"]["node_count"] == 11
    assert at.session_state["network_diagnostics"]["edge_count"] == 15
    at.number_input[0].set_value(2.0).run()
    next(item for item in at.button if item.label == "开始构建并分析网络").click().run()
    assert not at.exception
    assert len(at.error) == 1
    assert "network_nodes" not in at.session_state
    at.button(key="nav_learn_enrichment").click().run()
    next(item for item in at.button if item.label == "开始计算富集分析").click().run()
    assert not at.exception
    assert at.session_state["ora_diagnostics"]["term_count"] == 6
    at.number_input[0].set_value(20).run()
    next(item for item in at.button if item.label == "开始计算富集分析").click().run()
    assert not at.exception
    assert at.session_state["ora_result"].empty
