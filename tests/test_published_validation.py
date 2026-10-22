from pathlib import Path
import json
import pandas as pd
from tests.ui_helpers import open_route


def test_published_validation_artifacts():
    root = Path(__file__).resolve().parents[1] / 'validation/gse38713'
    data = pd.read_csv(root / 'paper_gene_comparison.csv')
    assert len(data) == 18 and not data[['gene_symbol','comparison']].duplicated().any()
    assert ((data.log2fc_ci95_low <= data.log2fc) & (data.log2fc <= data.log2fc_ci95_high)).all()
    summary = json.loads((root / 'summary.json').read_text(encoding='utf-8'))
    assert summary['tested_genes'] == 11753
    for record in summary['comparisons'].values():
        assert record['max_formula_p_error'] < 1e-10
        assert record['max_formula_bh_error'] < 1e-10
    sources = json.loads((root / 'sources.json').read_text())
    assert len(sources['files']) == 3
    assert all(len(row['sha256']) == 64 for row in sources['files'])
    # This asserts integrity of this archived run, not scientific truth.
    remission = data.query("comparison == 'remission_vs_control'").set_index('gene_symbol')
    assert (remission.loc[['REG4','S100P','SERPINB5','SLC16A1','DEFB1','AQP3','AQP8'], 'p_adjust'] < .05).all()


def test_published_validation_route():
    at = open_route('learn_transcriptome')
    assert not at.exception
    assert any('真实数据复核' in expander.label for expander in at.expander)
