from src.symmap_guide import TABLES, FIELDS, symmap_markdown
from tests.ui_helpers import open_route
import pandas as pd
from src.symmap_guide import prepare_symmap_export
from src.project_manager import STANDARD_FILES


def test_symmap_schemas():
    assert len(TABLES) == 4
    for grain, fields in TABLES.values():
        names = [name for name,_ in fields]
        assert len(names) == len(set(names))
    target = dict(TABLES['symmap_herb_targets.csv'][1])
    assert all(dest in target for _,dest,_ in FIELDS)
    text = symmap_markdown()
    assert 'By_ingredient' in text and '统一赋值' in text
    assert 'mapping_status=mapped' in text and 'included=yes' in text


def test_symmap_embedded_ui():
    at = open_route('learn_collection')
    assert not at.exception
    assert any('SymMap具体怎么查' in item.value for item in at.subheader)
    assert sum(exp.label.startswith('symmap_') for exp in at.expander) == 4
    assert not any(exp.label.startswith('compound_targets_standardized.csv') for exp in at.expander)
    at.radio(key='collection_route').set_value('其他来源的成分—靶点路线').run()
    assert not at.exception
    assert not any(exp.label.startswith('symmap_') for exp in at.expander)
    assert any(exp.label.startswith('compound_targets_standardized.csv') for exp in at.expander)


def test_symmap_exports_match_project_contract():
    row = dict(formula_name='示例方',herb_name='示例药',gene_symbol='TP53',target_species='Homo sapiens',mapping_status='mapped',included='yes',decision_reason='示例审核理由')
    table = pd.DataFrame([row,row,dict(row,gene_symbol='UNKNOWN',included='pending')])
    original = table.copy(deep=True)
    herbs, targets, genes = prepare_symmap_export(table)
    assert set(STANDARD_FILES['herbs']['required_columns']) <= set(herbs)
    assert set(STANDARD_FILES['compound_targets']['required_columns']) <= set(targets)
    assert len(targets) == 2 and genes == 'TP53\n'
    pd.testing.assert_frame_equal(table,original)
    for bad in [dict(row,mapping_status='pending'),dict(row,target_species=''),dict(row,decision_reason=''),dict(row,included='pending')]:
        try:
            prepare_symmap_export(pd.DataFrame([bad]))
        except ValueError:
            pass
        else:
            raise AssertionError('unreviewed row accepted')
