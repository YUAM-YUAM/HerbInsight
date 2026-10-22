from src.symmap_guide import TABLES, FIELDS, symmap_markdown
from tests.ui_helpers import open_route


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
