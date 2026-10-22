from pathlib import Path

from src.enrichment_guide import ENRICHMENT_STEPS, ENRICHMENT_FIELDS, GO_EXPORT_R, enrichment_markdown


def test_enrichment_course_inputs_and_export():
    from src.learning_paths import course_markdown
    assert len(ENRICHMENT_STEPS) == 7
    assert len(ENRICHMENT_FIELDS) == 4
    assert enrichment_markdown() in course_markdown()
    for name, fields in ENRICHMENT_FIELDS.items():
        assert name in enrichment_markdown()
        assert len(fields) == len({key for key, _ in fields})
    assert {key for key, _ in ENRICHMENT_FIELDS["term_annotations.csv"]} == {"gene_symbol", "term_id", "term_name", "category"}
    assert "GOALL" in GO_EXPORT_R and "file.exists" in GO_EXPORT_R


def test_background_demo_changes_without_errors():
    from streamlit.testing.v1 import AppTest
    from tests.ui_helpers import open_route
    at = open_route("learn_enrichment")
    assert not at.exception
    assert any(header.value == "04 GO/KEGG富集" for header in at.header)
    expected = lambda: next(m for m in at.metric if m.label == "随机期望命中数").value
    assert expected() == "1.00"
    at.slider(key="ora_guide_population").set_value(20).run()
    assert not at.exception
    assert expected() == "5.00"
    at.slider(key="ora_guide_population").set_value(200).run()
    assert not at.exception
    assert expected() == "0.50"
