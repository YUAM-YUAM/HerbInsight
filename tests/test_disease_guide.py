from pathlib import Path

from src.disease_guide import DISEASE_STEPS, DISEASE_TABLES, disease_markdown, intersect_gene_lists


def test_intersection_cleaning_and_counts():
    result = intersect_gene_lists(" TNF \nIL6\nIL6\n\nAKT1", "IL6\nSTAT3\nakt1")
    assert result["common"] == ["IL6"]
    assert result["drug_only"] == ["AKT1", "TNF"]
    assert result["disease_only"] == ["STAT3", "akt1"]
    assert result["drug_duplicates"] == 1
    assert result["union_count"] == result["drug_count"] + result["disease_count"] - len(result["common"])
    assert intersect_gene_lists("A", "B")["common"] == []


def test_intersection_rejects_missing_or_multicolumn_inputs():
    for bad in ["", " \n", "TNF,IL6", "TNF\tIL6", "gene_symbol\nTNF", "TNF IL6", "TNF；IL6"]:
        try:
            intersect_gene_lists(bad, "IL6")
        except ValueError:
            pass
        else:
            raise AssertionError("invalid input accepted: " + repr(bad))


def test_disease_course_and_schemas():
    from src.learning_paths import course_markdown
    assert len(DISEASE_STEPS) == 6
    for filename, fields in DISEASE_TABLES.items():
        assert len(fields) == len({key for key, _ in fields})
        assert filename in disease_markdown()
    assert disease_markdown() in course_markdown()


def test_disease_practice_ui_recalculates_without_stale_results():
    from streamlit.testing.v1 import AppTest
    from tests.ui_helpers import open_route
    at = open_route("learn_disease")
    assert not at.exception
    assert any(header.value == "02 疾病基因与交集" for header in at.header)
    at.checkbox(key="disease_practice_confirm").check().run()
    assert not at.exception
    assert next(m for m in at.metric if m.label == "共同基因").value == "2"
    at.text_area(key="disease_practice_genes").set_value("STAT3").run()
    assert not at.exception
    assert next(m for m in at.metric if m.label == "共同基因").value == "0"
    at.text_area(key="disease_practice_genes").set_value("gene_symbol\nIL6").run()
    assert not at.exception
    assert at.error
    assert not any(m.label == "共同基因" for m in at.metric)
