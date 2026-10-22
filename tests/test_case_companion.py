from src.case_companion import CASES, STEP_CASES, case_table, companion_markdown, overlap_audit
from tests.ui_helpers import open_route


def test_case_files_and_evidence_boundaries():
    assert set(STEP_CASES.values()) == set(CASES)
    for key in CASES:
        table, digest = case_table(key)
        assert len(table) > 0 and len(digest) == 64
        text = companion_markdown(key, digest, len(table))
        assert '非原操作日志' in text and '待补' in text
        assert digest in text
    audit = overlap_audit()
    assert audit['current_table_intersection'] >= 0
    assert audit['saved_overlap'] >= 0


def test_case_panels_in_existing_courses():
    for route, expected in [('learn_collection',3),('learn_disease',2),('learn_ppi',2),
                            ('learn_enrichment',1),('learn_transcriptome',1),('learn_ml',1)]:
        at = open_route(route)
        assert not at.exception
        panels = [expander for expander in at.expander if expander.label.startswith('五积散案例对照')]
        assert len(panels) == expected, (route,len(panels))
