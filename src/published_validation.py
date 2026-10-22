"""Actual aggregate reanalysis, separate from synthetic practice."""
from pathlib import Path
import json


def render_published_validation():
    import pandas as pd
    import streamlit as st
    root = Path(__file__).resolve().parents[1] / 'validation/gse38713'
    with st.expander('真实数据复核：GSE38713与原论文摘要对照'):
        st.write('已用本站正式Welch差异分析函数重算公开GC-RMA log2表达；不是模拟练习，也不是直接展示作者结果。')
        st.caption('验证范围：同一发现数据的探索性再分析，对照论文摘要具名结论；非独立外部验证。全文访问受限，未开展全文严格复现，不用于推断五积散疗效。')
        st.markdown('[GEO数据](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE38713) · [原论文：Planell et al., Gut 2013](https://pubmed.ncbi.nlm.nih.gov/23135761/)')
        summary = json.loads((root / 'summary.json').read_text(encoding='utf-8'))
        st.caption(f"对照13例、缓解期8例、活动期受累黏膜15例；排除7份配对非受累黏膜。共{summary['tested_genes']:,}个基因，分别做全基因BH校正。")
        st.write('结果：摘要点名的7个缓解期异常基因，本次均BH<0.05。REG1A和IL8/CXCL8在活动期升高，缓解期未检出显著差异。未显著不等于正常或等效。')
        table = pd.read_csv(root / 'paper_gene_comparison.csv')
        view = table[['gene_symbol','comparison','log2fc','p_adjust','log2fc_ci95_low','log2fc_ci95_high']].rename(columns={'gene_symbol':'基因','comparison':'比较','log2fc':'平均log2差','p_adjust':'全基因BH校正P','log2fc_ci95_low':'95%CI下限','log2fc_ci95_high':'95%CI上限'})
        st.dataframe(view, hide_index=True, width='stretch')
        st.caption('95%CI为逐基因区间，未作同时校正。摘要未逐一列出7个基因的升降方向，不宣称方向全部复现。未校正年龄、性别、药物等混杂，未重做CEL质控或作者独立验证队列。')
        st.download_button('下载真实数据复核报告', (root / 'README.md').read_bytes(), 'GSE38713_reanalysis.md', 'text/markdown', key='real_validation_report')
        st.download_button('下载论文具名基因对照结果', (root / 'paper_gene_comparison.csv').read_bytes(), 'GSE38713_paper_comparison.csv', 'text/csv', key='real_validation_comparison')
        st.download_button('下载数据来源与原始文件校验值', (root / 'sources.json').read_bytes(), 'GSE38713_sources.json', 'application/json', key='real_validation_sources')
