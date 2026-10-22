from src.collection_guide import COLLECTION_STEPS, TABLE_SCHEMAS, collection_markdown


def test_collection_guide_complete_and_consistent():
    assert len(COLLECTION_STEPS) == 6
    assert len(TABLE_SCHEMAS) == 6
    filenames = {name for name, _, _ in TABLE_SCHEMAS}
    for step in COLLECTION_STEPS:
        assert step["table"] in filenames
        assert all(step[key] for key in ["need", "where", "actions", "save", "check", "links"])
    schemas = {name: {key for key, _, _ in fields} for name, _, fields in TABLE_SCHEMAS}
    for name, _, fields in TABLE_SCHEMAS:
        assert len(fields) == len(schemas[name]), "duplicate column"
        assert name in collection_markdown()
    assert {"original_id", "original_id_type", "species", "gene_symbol", "included", "mapping_status"} <= schemas["compound_targets_standardized.csv"]
    assert {"original_id", "original_id_type", "species", "gene_symbol", "included", "mapping_status"} <= schemas["id_mapping_register.csv"]
