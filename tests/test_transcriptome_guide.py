from pathlib import Path

import pandas as pd

from src.transcriptome_guide import (
    TRANSCRIPTOME_STEPS, TRANSCRIPTOME_FIELDS, align_sample_metadata, transcriptome_markdown,
)


def test_sample_alignment_uses_names_not_rows():
    meta = pd.DataFrame({"sample_id": ["B", "A"], "group": ["disease", "control"]})
    aligned = align_sample_metadata(["A", "B"], meta)
    assert aligned.sample_id.tolist() == ["A", "B"]
    assert aligned.group.tolist() == ["control", "disease"]
    assert meta.sample_id.tolist() == ["B", "A"], "input should not mutate"


def test_invalid_sample_design_is_not_silently_fixed():
    good = pd.DataFrame({"sample_id": ["A", "B"], "group": ["control", "disease"]})
    bad_inputs = [
        (["A", "A"], good), (["A", "C"], good), ([], good),
        (["A", "B"], good.assign(sample_id=["A", "A"])),
        (["A", "B"], good.assign(group=[None, "disease"])),
        (["A", "B"], good.assign(group=[" ", "disease"])),
        (["A", "B"], good.drop(columns="group")),
    ]
    for columns, meta in bad_inputs:
        try:
            align_sample_metadata(columns, meta)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid design accepted")


def test_transcriptome_templates_and_course_export():
    from src.learning_paths import course_markdown
    assert len(TRANSCRIPTOME_STEPS) == 7
    assert len(TRANSCRIPTOME_FIELDS) == 5
    for filename, fields in TRANSCRIPTOME_FIELDS.items():
        assert len(fields) == len({key for key, _ in fields})
        assert filename in transcriptome_markdown()
    assert transcriptome_markdown() in course_markdown()


def test_transcriptome_sample_demo_ui():
    from streamlit.testing.v1 import AppTest
    from tests.ui_helpers import open_route
    at = open_route("learn_transcriptome")
    assert not at.exception
    assert any(header.value == "转录组数据与设计" for header in at.header)
    assert not at.error
    options = at.radio(key="tx_guide_mode").options
    for option in options[1:]:
        at.radio(key="tx_guide_mode").set_value(option).run()
        assert not at.exception
        assert len(at.error) == 1
    at.radio(key="tx_guide_mode").set_value(options[0]).run()
    assert not at.exception
    assert not at.error
