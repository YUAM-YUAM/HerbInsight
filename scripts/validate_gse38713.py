"""Fetch public GEO processed data; preserve provenance; never modify original case."""
from pathlib import Path
import urllib.request
import json
import hashlib
import gzip
import sys
import csv
from io import StringIO
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'projects/wujisan_uc/raw/validation_gse38713'
OUT = ROOT / 'validation/gse38713'
sys.path.insert(0, str(ROOT))

# Fixed from the primary paper abstract BEFORE computation, not selected by our P values.
PAPER_GENES = ['REG4', 'S100P', 'SERPINB5', 'SLC16A1', 'DEFB1', 'AQP3', 'AQP8', 'REG1A', 'CXCL8']

URLS = {
    'series_matrix.txt.gz': 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE38nnn/GSE38713/matrix/GSE38713_series_matrix.txt.gz',
    'platform.annot.gz': 'https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/GPL570/annot/GPL570.annot.gz',
    'paper.json': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:23135761%20AND%20SRC:MED&format=json&resultType=core',
}

def fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    provenance = []
    for name, url in URLS.items():
        path = RAW / name
        if not path.exists():
            with urllib.request.urlopen(url, timeout=120) as response:
                data = response.read()
            path.write_bytes(data)
        data = path.read_bytes()
        provenance.append({'file': name, 'url': url, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
        print(name, len(data), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'sources.json').write_text(json.dumps({'retrieved_utc': datetime.now(timezone.utc).isoformat(), 'files': provenance}, indent=2), encoding='utf-8')

def analyze():
    import numpy as np
    import pandas as pd
    from scipy.special import betainc
    from scipy.stats import t as student_t
    from src.expression_analysis import differential_expression, analysis_fingerprint, method_record, result_zip
    with gzip.open(RAW / 'series_matrix.txt.gz', 'rt') as f:
        text = f.read()
    metadata = {}
    for row in csv.reader(text.splitlines(), delimiter='\t'):
        if row and row[0] in ('!Sample_title', '!Sample_geo_accession', '!Sample_source_name_ch1', '!Sample_data_processing'):
            metadata[row[0]] = row[1:]
    matrix_text = text.split('!series_matrix_table_begin\n')[1].split('!series_matrix_table_end')[0]
    matrix = pd.read_csv(StringIO(matrix_text), sep='\t', index_col=0)
    assert matrix.shape[1] == 43 and matrix.index.is_unique
    assert np.isfinite(matrix.to_numpy()).all()
    assert all('GC-RMA' in item and 'log2' in item for item in metadata['!Sample_data_processing'])
    with gzip.open(RAW / 'platform.annot.gz', 'rt') as f:
        platform_text = f.read()
    platform_table = platform_text.split('!platform_table_begin\n')[1].split('!platform_table_end')[0]
    platform = pd.read_csv(StringIO(platform_table), sep='\t', dtype=str, keep_default_na=False)
    symbols = platform.set_index('ID')['Gene symbol'].str.strip()
    # No first-match resolution of multi-gene probes; preserve an exclusion audit.
    mapping = pd.DataFrame({'probe_id': matrix.index, 'gene_symbol': symbols.reindex(matrix.index).to_numpy()})
    mapping['included'] = mapping.gene_symbol.notna() & mapping.gene_symbol.ne('') & ~mapping.gene_symbol.fillna('').str.contains('///', regex=False)
    mapping['expression_filter'] = (matrix.max(axis=1) >= 5).to_numpy()
    mapping['included'] &= mapping.expression_filter
    mapping.to_csv(OUT / 'probe_mapping_audit.csv', index=False)
    keep = mapping.loc[mapping.included]
    expression = matrix.loc[keep.probe_id].copy()
    expression.index = keep.gene_symbol.to_numpy()
    expression = expression.groupby(level=0, sort=True).median()
    expression.index.name = 'gene_symbol'
    samples = pd.DataFrame({'sample_id': metadata['!Sample_geo_accession'], 'title': metadata['!Sample_title'], 'source': metadata['!Sample_source_name_ch1']})
    def group(source):
        if 'non-inflammatory control' in source: return 'control'
        if 'in remission' in source: return 'remission'
        if 'non-involved' in source: return 'excluded_noninvolved'
        if 'active disease (involved mucosa)' in source: return 'active'
        raise ValueError(source)
    samples['group'] = samples.source.map(group)
    assert samples.groupby('group').size().to_dict() == {'active':15, 'control':13, 'excluded_noninvolved':7, 'remission':8}
    samples.to_csv(OUT / 'sample_audit.csv', index=False)
    summary = {'dataset': 'GSE38713', 'paper_pmid': '23135761', 'comparison_scope': 'Abstract-named genes; exploratory reanalysis, not independent cohort validation',
               'paper_genes_fixed_before_analysis': PAPER_GENES, 'input_probes': len(matrix), 'included_probes': len(keep), 'tested_genes': len(expression),
               'preprocessing': 'Depositor GC-RMA log2 values, no second log transform; max across all43 >=5; exclude empty/multi-symbol probes; median of log2 probes per gene',
               'platform_annotation_header': platform_text.split('!platform_table_begin')[0], 'groups': samples.groupby('group').size().to_dict(), 'comparisons': {}}
    combined = []
    for case in ('remission', 'active'):
        selected = samples.loc[samples.group.isin(['control', case]), ['sample_id','group']]
        data = expression[selected.sample_id].reset_index()
        results, numeric, aligned = differential_expression(data, selected, 'control', case)
        # Independent Welch formula via the incomplete beta identity, not ttest_ind.
        a = numeric.loc[:, aligned.loc[aligned.group == 'control','sample_id']].to_numpy()
        b = numeric.loc[:, aligned.loc[aligned.group == case,'sample_id']].to_numpy()
        va, vb = a.var(axis=1, ddof=1)/a.shape[1], b.var(axis=1, ddof=1)/b.shape[1]
        t = (b.mean(axis=1)-a.mean(axis=1))/np.sqrt(va+vb)
        df = (va+vb)**2/(va**2/(a.shape[1]-1)+vb**2/(b.shape[1]-1))
        p_ref = betainc(df/2, .5, df/(df+t*t))
        indexed = results.set_index('gene_symbol').loc[numeric.index]
        error = float(np.max(np.abs(indexed.p_value.to_numpy()-p_ref)))
        assert error < 1e-10
        order = np.argsort(p_ref)
        q_sorted = np.minimum.accumulate((p_ref[order] * len(p_ref) / np.arange(1,len(p_ref)+1))[::-1])[::-1].clip(0,1)
        q_ref = np.empty_like(p_ref)
        q_ref[order] = q_sorted
        q_error = float(np.max(np.abs(indexed.p_adjust.to_numpy()-q_ref)))
        assert q_error < 1e-10
        difference = b.mean(axis=1)-a.mean(axis=1)
        half_width = student_t.ppf(.975, df)*np.sqrt(va+vb)
        ci = pd.DataFrame({'gene_symbol':numeric.index, 'log2fc_ci95_low':difference-half_width, 'log2fc_ci95_high':difference+half_width})
        results = results.merge(ci, on='gene_symbol', validate='one_to_one')
        params = {'case':case, 'control':'control', 'method':'independent two-sided Welch', 'correction':'BH over all tested genes', 'probe_aggregation':'median of log2 values', 'threshold':'BH<0.05; no effect size cutoff in paper-gene comparison'}
        record = method_record('Welch differential expression', params, analysis_fingerprint(data, selected), 'GEO GSE38713 processed series matrix; GPL570 annotation')
        record['independent_formula_max_p_error'] = error
        record['independent_formula_max_bh_error'] = q_error
        record['confidence_interval'] = 'Pointwise Welch 95% CI for mean log2 difference, not simultaneous or equivalence intervals'
        result_tables = {'expression_log2.csv':data, 'sample_metadata.csv':selected, 'all_results.csv':results}
        # Full reusable upload inputs and results are local, not automatically redistributed.
        (RAW / f'{case}_validation.zip').write_bytes(result_zip(result_tables, record))
        results.to_csv(OUT / f'{case}_all_results.csv', index=False)
        (OUT / f'{case}_methods.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        key_results = results.set_index('gene_symbol').reindex(PAPER_GENES).reset_index()
        assert key_results.p_value.notna().all()
        key_results['comparison'] = case + '_vs_control'
        combined.append(key_results)
        summary['comparisons'][case] = {'n_control':a.shape[1], 'n_case':b.shape[1], 'fdr_significant':int((results.p_adjust<.05).sum()), 'max_formula_p_error':error, 'max_formula_bh_error':q_error}
    comparison = pd.concat(combined, ignore_index=True)
    comparison.to_csv(OUT / 'paper_gene_comparison.csv', index=False)
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(comparison[['comparison','gene_symbol','log2fc','p_value','p_adjust']].to_string(index=False))
    print(json.dumps(summary['comparisons'], indent=2))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    fetch()
    analyze()
