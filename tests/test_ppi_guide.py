from pathlib import Path

from src.ppi_guide import PPI_STEPS, PPI_FIELDS, ppi_markdown


def test_ppi_course_and_templates():
    from src.learning_paths import course_markdown
    assert len(PPI_STEPS) == 7
    assert len(PPI_FIELDS) == 4
    assert ppi_markdown() in course_markdown()
    for filename, fields in PPI_FIELDS.items():
        assert len(fields) == len({key for key, _ in fields})
        assert filename in ppi_markdown()
    assert {"source", "target", "weight"} <= {key for key, _ in PPI_FIELDS["ppi_edges_template.csv"]}
    assert "node_id" in {key for key, _ in PPI_FIELDS["ppi_node_attributes.csv"]}


def test_ppi_demo_updates_threshold():
    from streamlit.testing.v1 import AppTest
    from tests.ui_helpers import open_route
    at = open_route("learn_ppi")
    assert not at.exception
    assert any(header.value == "03 PPI构图" for header in at.header)
    assert next(m for m in at.metric if m.label == "演示保留边数").value == "2"
    at.slider(key="ppi_guide_cutoff").set_value(1.0).run()
    assert not at.exception
    assert next(m for m in at.metric if m.label == "演示保留边数").value == "0"
    at.slider(key="ppi_guide_cutoff").set_value(0.0).run()
    assert not at.exception
    assert next(m for m in at.metric if m.label == "演示保留边数").value == "3"
